#!/usr/bin/env python3
"""Task-local wall-clock guard. See planning/autonomous-optimization-runtime.md.

start/register/finish authenticate the root mrun; check/watch use its verified scope.
No command creates/resumes a thread, starts a Goal, or edits the task ledger.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

FLOOR, CLOSEOUT, DEADLINE = 21600, 32400, 36000
REPORT = "planning/autonomous-optimization-run-report.md"


class GuardError(RuntimeError):
    pass


def installed(name):
    directory = Path.home() / "bin/codex.project.d/scripts"
    if not directory.is_dir():
        raise GuardError("找不到已安装的 codex.project scripts")
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    return importlib.import_module(name)


class SharedRPC:
    """Connect only to the existing shared daemon; inspect never starts it."""
    def __init__(self, codex_home):
        self.home = Path(codex_home)

    def call(self, method, params):
        if method not in {"thread/read", "thread/turns/list", "thread/items/list",
                          "thread/goal/get", "thread/goal/set",
                          "turn/steer", "turn/interrupt"}:
            raise GuardError("守卫不允许此 RPC")
        if method == "thread/goal/set" and params != {
                "threadId": params.get("threadId"), "status": "paused"}:
            raise GuardError("守卫仅允许明确停止时暂停现有 Goal")
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        started = time.monotonic()
        def timeout(*_):
            raise GuardError("共享 App Server 整次请求超过 8 秒，保留待重试状态")
        signal.signal(signal.SIGALRM, timeout)
        signal.setitimer(signal.ITIMER_REAL, 8)
        try:
            transport = installed("task_runtime").daemon_transport()
            executable = shutil.which("codex")
            if not executable:
                raise GuardError("找不到 Codex CLI")
            info = transport.ManagedAppServer(executable, codex_home=self.home, timeout=5).inspect()
            if info is None:
                raise GuardError("共享 App Server 未运行；未启动新服务")
            with transport.AppServerSession(info.socket_path, expected_codex_home=self.home,
                                            timeout=5) as session:
                return dict(session.call(method, params))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
            if previous_timer[0]:
                signal.setitimer(signal.ITIMER_REAL,
                                max(0.001, previous_timer[0] - (time.monotonic() - started)),
                                previous_timer[1])


def read_json(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, encoding="utf-8") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise GuardError(f"不是普通文件：{path}")
        return json.load(handle)


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix=".guard-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def lock(path, *, nonblocking=False):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise GuardError("锁文件不是普通文件")
        fcntl.flock(descriptor, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        yield
    finally:
        os.close(descriptor)


def valid_uuid(value):
    try:
        if str(uuid.UUID(value)) == value:
            return value
    except (TypeError, ValueError, AttributeError):
        pass
    raise GuardError("会话或租约 ID 无效")


def parent_id(thread):
    source = thread.get("source")
    source = source.get("subAgent", {}) if isinstance(source, dict) else {}
    spawn = source.get("thread_spawn", {}) if isinstance(source, dict) else {}
    by_source = spawn.get("parent_thread_id")
    by_field = thread.get("parentThreadId")
    if by_field and by_source and by_field != by_source:
        raise GuardError("子会话父级证据冲突")
    result = by_field or by_source
    return valid_uuid(result) if result else None


def first_execution(thread, task_id, current_marker, now):
    """Recover execution time, including when initialization was delayed on resume.

    A task draft can precede mrun in the same retained thread. Its creation time,
    earlier turns, and the task's publication time must never become T0.
    """
    if thread.get("historyMode", "legacy") != "legacy":
        raise GuardError("分页历史不能证明首次执行时间；拒绝以不完整历史重置预算")
    executions = []
    markers = set()
    for turn in thread.get("turns", []):
        if turn.get("itemsView", "full") != "full":
            raise GuardError("轮次内容不完整，不能证明首次执行时间")
        for item in turn.get("items", []):
            if item.get("type") != "userMessage":
                continue
            text = "\n".join(c.get("text", "") for c in item.get("content", [])
                             if c.get("type") == "text")
            match = re.match(r"CODEX_PROJECT_TASK_RUN:([0-9a-f-]{36})(?:\n|$)", text)
            if not match:
                continue
            marker = valid_uuid(match.group(1))
            # A dependency mentioning our ID is not proof that this is our task.
            details = re.search(r"(?m)^任务内容：(.*)$", text)
            try:
                identity = json.loads(details.group(1)) if details else {}
            except ValueError:
                identity = {}
            if identity.get("id") != task_id or "通过 task mrun 执行项目任务。" not in text:
                raise GuardError("执行标记缺少本任务 mrun 证据，拒绝猜测 T0")
            started = turn.get("startedAt")
            if not isinstance(started, (int, float)) or isinstance(started, bool) or not math.isfinite(started):
                raise GuardError("执行轮次缺少 startedAt，不能以当前时间重置预算")
            if started > now or started <= 0:
                raise GuardError("执行起点在未来或无效")
            executions.append((started, turn["id"], marker))
            markers.add(marker)
    if not executions or current_marker not in markers:
        raise GuardError("无法核对首次 mrun 执行轮次和当前任务标记；不启动新计时")
    return min(executions)


class Guard:
    def __init__(self, worktree, *, clock=time.time, rpc=None, ledger=None,
                 environment=None, active_run=None, execution_directory=None):
        self.worktree = Path(worktree).resolve()
        self.directory = self.worktree / ".runtime/autonomous-optimization"
        self.state_path = self.directory / "state.json"
        self.receipt_path = self.directory / "stop-receipt.json"
        self.clock, self.rpc_override, self.ledger = clock, rpc, ledger
        self.env = os.environ if environment is None else environment
        self.active_run, self.execution_directory = active_run, execution_directory

    def prepare_directory(self):
        for path in (self.worktree / ".runtime", self.directory):
            if path.is_symlink():
                raise GuardError("运行目录不能是符号链接")
            path.mkdir(mode=0o700, exist_ok=True)

    def record(self, project, task_id):
        store = self.ledger(Path(project)) if self.ledger else installed("task_store").read_store(Path(project))
        record = store.get("tasks", {}).get(task_id)
        if not isinstance(record, dict) or record.get("id") != task_id:
            raise GuardError("主项目任务账本没有此任务")
        return record

    def expected_directory(self, project, record):
        callback = self.execution_directory or installed("task_worktree").execution_directory
        return Path(callback(Path(project), record)).resolve()

    def authenticate(self, project, task_id):
        record = self.record(project, task_id)
        root = valid_uuid(self.env.get("CODEX_THREAD_ID"))
        lease = valid_uuid(record.get("lease"))
        if record.get("status") != "running" or record.get("execution_mode") != "mrun":
            raise GuardError("必须在正在执行的 task mrun 中初始化或结束守卫")
        if record.get("session_id") != root:
            raise GuardError("当前会话未绑定本任务；先运行 task _bind_session")
        if self.expected_directory(project, record) != self.worktree:
            raise GuardError("脚本不在账本登记的本任务 worktree")
        home = Path(self.env.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
        if Path(record.get("codex_home", "")).resolve() != home:
            raise GuardError("任务 CODEX_HOME 不匹配")
        if self.env.get("CODEX_PROJECT_TASK_LEASE"):
            if self.env["CODEX_PROJECT_TASK_LEASE"] != lease:
                raise GuardError("当前执行租约不匹配")
        else:
            # Shared daemon tools do not inherit the mrun launcher's environment.
            callback = self.active_run or installed("task_store").require_active_run
            callback(Path(project), record)
        valid_uuid(record.get("run_marker"))
        return record

    def rpc(self, state):
        return self.rpc_override or SharedRPC(state["codex_home"])

    def thread(self, state, thread_id):
        result = self.rpc(state).call("thread/read", {"threadId": thread_id, "includeTurns": False})
        thread = result.get("thread")
        if not isinstance(thread, dict) or thread.get("id") != thread_id:
            raise GuardError("共享服务返回的会话身份不匹配")
        return thread

    def recover_execution(self, state, marker):
        """Read chronological turn headers and initial input, never full long histories."""
        root, cursor, seen, candidates = state["root_thread_id"], None, set(), []
        while True:
            params = {"threadId": root, "limit": 32, "sortDirection": "asc", "itemsView": "notLoaded"}
            if cursor:
                params["cursor"] = cursor
            page = self.rpc(state).call("thread/turns/list", params)
            if not isinstance(page.get("data"), list):
                raise GuardError("无法读取执行轮次页")
            for turn in page["data"]:
                item_cursor, item_seen, first_user = None, set(), None
                while True:
                    params = {"threadId": root, "turnId": turn["id"], "limit": 8, "sortDirection": "asc"}
                    if item_cursor:
                        params["cursor"] = item_cursor
                    items = self.rpc(state).call("thread/items/list", params)
                    if not isinstance(items.get("data"), list):
                        raise GuardError("无法读取轮次输入页")
                    for entry in items.get("data", []):
                        if entry.get("turnId") != turn["id"]:
                            raise GuardError("轮次输入归属不匹配")
                        if entry.get("item", {}).get("type") == "userMessage":
                            first_user = entry["item"]
                            break
                    if first_user or not items.get("nextCursor"):
                        break
                    item_cursor = items["nextCursor"]
                    if item_cursor in item_seen:
                        raise GuardError("轮次输入分页游标重复")
                    item_seen.add(item_cursor)
                if first_user:
                    candidate = dict(turn, items=[first_user], itemsView="full")
                    candidates.append(candidate)
                    text = "\n".join(c.get("text", "") for c in first_user.get("content", [])
                                     if c.get("type") == "text")
                    if text.startswith("CODEX_PROJECT_TASK_RUN:" + marker + "\n"):
                        return first_execution({"turns": candidates}, state["task_id"], marker, self.clock())
            cursor = page.get("nextCursor")
            if not cursor:
                raise GuardError("全部可见历史中找不到本任务首次执行证据；不重置预算")
            if cursor in seen:
                raise GuardError("轮次分页游标重复")
            seen.add(cursor)

    def goal(self, state, thread_id):
        goal = self.rpc(state).call("thread/goal/get", {"threadId": thread_id}).get("goal")
        if goal is not None and (not isinstance(goal, dict) or goal.get("threadId") != thread_id):
            raise GuardError("共享服务返回的 Goal 身份不匹配")
        return goal

    def load(self):
        state = read_json(self.state_path)
        if (state.get("schema_version") != 1 or state.get("worktree") != str(self.worktree)
                or state.get("deadlines") != {"floor": state.get("t0", 0) + FLOOR,
                                               "closeout": state.get("t0", 0) + CLOSEOUT,
                                               "deadline": state.get("t0", 0) + DEADLINE}):
            raise GuardError("运行状态版本、路径或固定时间预算不匹配")
        return state

    def save(self, state):
        atomic_json(self.state_path, state)
        if state.get("stop") is not None:
            atomic_json(self.receipt_path, {
                "task_id": state["task_id"], "root_thread_id": state["root_thread_id"],
                "t0": state["t0"], "deadlines": state["deadlines"],
                "phase": state["phase"], **state["stop"],
            })

    def snapshot_report(self):
        path = self.worktree / REPORT
        if not path.is_file() or path.is_symlink():
            return {"path": REPORT, "available": False}
        content = path.read_bytes()
        return {"path": REPORT, "available": bool(content.strip()), "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(), "mtime": path.stat().st_mtime}

    def now(self, state):
        # Never undo an observed deadline after a backwards wall-clock adjustment.
        now = max(self.clock(), state.get("observed_at", state["t0"]))
        state["observed_at"] = now
        return now

    def scope_record(self, state):
        record = self.record(state["project"], state["task_id"])
        if (record.get("session_id") != state["root_thread_id"]
                or record.get("execution_mode") != "mrun"
                or record.get("status") not in {"running", "interrupted", "completed"}
                or record.get("codex_home") != state["codex_home"]
                or self.expected_directory(state["project"], record) != self.worktree):
            raise GuardError("任务账本身份变化；保留待停止回执，不操作其他会话")
        return record

    def start(self, project, task_id):
        self.prepare_directory()
        with lock(self.directory / "state.lock"):
            if self.state_path.exists():
                state = self.load()
                if state["task_id"] != task_id or state["project"] != str(Path(project).resolve()):
                    raise GuardError("此运行目录已绑定其他任务")
                if state["phase"] == "finished":
                    return state  # A completed/expired budget cannot be rearmed.
                record = self.authenticate(project, task_id)
                if record["session_id"] != state["root_thread_id"]:
                    raise GuardError("恢复会话不是原任务根会话")
            else:
                record = self.authenticate(project, task_id)
                state = {"schema_version": 1, "project": str(Path(project).resolve()),
                         "task_id": task_id, "worktree": str(self.worktree),
                         "root_thread_id": record["session_id"], "codex_home": record["codex_home"]}
                thread = self.thread(state, record["session_id"])
                if parent_id(thread) or (isinstance(thread.get("source"), dict)
                                         and "subAgent" in thread["source"]):
                    raise GuardError("子代理不能成为任务根会话")
                if Path(thread.get("cwd", "")).resolve() != self.worktree:
                    raise GuardError("根会话工作区与任务不匹配")
                t0, turn_id, marker = self.recover_execution(state, record["run_marker"])
                state.update(t0=t0, first_turn_id=turn_id, first_run_marker=marker,
                             t0_source="app-server chronological turn pages and initial task input",
                             initialized_at=self.clock(), observed_at=t0, phase="armed",
                             deadlines={"floor": t0 + FLOOR, "closeout": t0 + CLOSEOUT,
                                        "deadline": t0 + DEADLINE},
                             children={}, closeout_notified_at=None,
                             closeout_message_id=str(uuid.uuid4()), stop=None, last_error=None)
            state["lease_digest"] = hashlib.sha256(record["lease"].encode()).hexdigest()
            self.save(state)
            if self.now(state) >= state["deadlines"]["deadline"]:
                self.request_stop(state, "deadline", self.now(state))
            if state["phase"] == "stopping":
                # CLI starts the independent watcher before the first self-interrupt.
                return state
            return self.tick(state)

    def current_turn(self, state, thread):
        if thread.get("status", {}).get("type") in {"idle", "notLoaded"}:
            return None
        if thread.get("status", {}).get("type") != "active":
            raise GuardError("无法确认会话的活动状态")
        page = self.rpc(state).call("thread/turns/list", {
            "threadId": thread["id"], "limit": 1, "sortDirection": "desc", "itemsView": "notLoaded"})
        turns = [t["id"] for t in page.get("data", []) if t.get("status") == "inProgress"]
        if len(turns) != 1:
            raise GuardError("无法唯一确定当前活动回合；不猜测中断目标")
        return turns[0]

    def register(self, child):
        valid_uuid(child)
        with lock(self.directory / "state.lock"):
            state = self.load()
            self.authenticate(state["project"], state["task_id"])
            if state["phase"] == "finished":
                raise GuardError("守卫已结束，不能登记新的子会话")
            root, chain, current = state["root_thread_id"], {}, child
            if current == root:
                raise GuardError("根会话不是子会话")
            while current != root:
                if current in chain or len(chain) >= 64:
                    raise GuardError("子会话谱系循环或过深")
                thread = self.thread(state, current)
                parent = parent_id(thread)
                if not parent:
                    raise GuardError("此会话不是本任务后代；拒绝登记兄弟或无关会话")
                chain[current] = {"parent_thread_id": parent, "registered_at": self.clock()}
                current = parent
            state["children"].update(chain)
            self.save(state)
            return self.tick(state)

    def request_stop(self, state, reason, now):
        if state.get("stop") is None:
            state["stop"] = {"reason": reason, "requested_reason": reason,
                             "requested_at": now, "attempts": 0, "complete": False,
                             "report": self.snapshot_report(), "threads": {}, "errors": [],
                             "failure_history": []}
        elif reason == "deadline":
            state["stop"]["reason"] = "deadline"
        state["phase"] = "stopping"
        # Stop latch and report hash are durable before any remote mutation.
        self.save(state)

    def pause_goal(self, state, thread_id):
        goal = self.goal(state, thread_id)
        if goal is None or goal.get("status") in {"paused", "complete"}:
            return "absent" if goal is None else goal["status"]
        result = self.rpc(state).call("thread/goal/set", {"threadId": thread_id, "status": "paused"})
        goal = result.get("goal", {})
        if goal.get("threadId") != thread_id or goal.get("status") != "paused":
            raise GuardError("服务未确认 Goal 暂停")
        return "paused"

    def stop(self, state):
        receipt, root = state["stop"], state["root_thread_id"]
        receipt["attempts"] += 1
        receipt["last_attempt_at"] = self.now(state)
        receipt["errors"] = []
        root_interrupt = receipt["reason"] in {"deadline", "user_stop"}
        # Pause root first so it cannot autonomously schedule another turn.
        try:
            if root_interrupt:
                root_goal = self.pause_goal(state, root)
            else:
                goal = self.goal(state, root)
                if not goal or goal.get("status") != "complete":
                    raise GuardError("正常收敛须先由执行代理将已实现的 Goal 标为 complete")
                root_goal = "complete"
            receipt["threads"][root] = {"goal": root_goal, "turn": "pending" if root_interrupt else "finish_allowed"}
        except Exception as error:
            receipt["errors"].append(f"{root}: {error}")
        self.save(state)
        # Descendant Goals must also stop; a child can otherwise restart itself.
        # The durable latch exists already. Stop root before possibly slow child
        # RPCs; the independent watcher continues if an in-turn check is killed.
        targets = ([root] if root_interrupt else []) + list(state["children"])
        for thread_id in targets:
            try:
                thread = self.thread(state, thread_id)
                if thread_id != root:
                    if parent_id(thread) != state["children"][thread_id]["parent_thread_id"]:
                        raise GuardError("已登记子会话的父级变化")
                    try:
                        goal_status = self.pause_goal(state, thread_id)
                    except Exception as error:
                        goal_status = "unconfirmed"
                        receipt["errors"].append(f"{thread_id} Goal: {error}")
                else:
                    goal_status = receipt["threads"].get(root, {}).get("goal", "unconfirmed")
                turn = self.current_turn(state, thread)
                if turn:
                    self.rpc(state).call("turn/interrupt", {"threadId": thread_id, "turnId": turn})
                    # An accepted interrupt request is not proof that execution stopped.
                    if self.current_turn(state, self.thread(state, thread_id)) is not None:
                        raise GuardError("中断请求已接收，但回合仍活动；等待重试确认")
                receipt["threads"][thread_id] = {"goal": goal_status, "turn": "inactive",
                                                  "checked_at": self.now(state)}
            except Exception as error:
                receipt["errors"].append(f"{thread_id}: {error}")
            self.save(state)
        if not root_interrupt and self.now(state) >= state["deadlines"]["deadline"]:
            # Cleanup RPCs can cross the boundary after a valid 6–10h request.
            # Never seal that attempt as convergence beyond the hard deadline.
            if receipt["errors"]:
                self.remember_failure(state)
            self.request_stop(state, "deadline", self.now(state))
            return self.stop(state)
        receipt["complete"] = not receipt["errors"]
        if receipt["complete"]:
            state["phase"] = "finished"
            receipt["finished_at"] = self.now(state)
        state["last_error"] = "; ".join(receipt["errors"]) or None
        if receipt["errors"]:
            self.remember_failure(state)
        self.save(state)
        return state

    def remember_failure(self, state):
        receipt = state["stop"]
        failure = {"at": self.now(state), "attempt": receipt["attempts"],
                   "errors": list(receipt["errors"])}
        receipt.setdefault("first_failure", failure)
        receipt["failure_history"] = (receipt.get("failure_history", []) + [failure])[-100:]

    def tick(self, state):
        if state["phase"] == "finished":
            self.save(state)  # Repair a receipt write lost after the canonical state write.
            return state
        now = self.now(state)
        if now >= state["deadlines"]["deadline"]:
            self.request_stop(state, "deadline", now)
        try:
            record = self.scope_record(state)
            if state["phase"] == "stopping":
                return self.stop(state)
            if record["status"] == "completed":
                self.request_stop(state, "task_completed", now)
                return self.stop(state)
            if now >= state["deadlines"]["closeout"] and not state["closeout_notified_at"]:
                thread = self.thread(state, state["root_thread_id"])
                turn = self.current_turn(state, thread)
                if turn:
                    result = self.rpc(state).call("turn/steer", {
                        "threadId": state["root_thread_id"], "expectedTurnId": turn,
                        "clientUserMessageId": state["closeout_message_id"],
                        "input": [{"type": "text", "text":
                            "本任务已到 T0+9 小时，立即进入自检与收尾：停止新大项，冻结范围，"
                            "核对遗漏、实际 diff、验证、独立审查、运行报告和候选。T0+10 小时硬截止不延长。"
                            "先持久化报告和检查点，不再委派无法在截止前完成的工作。"}],
                    })
                    if result.get("turnId") != turn:
                        raise GuardError("收尾提示的回合确认不匹配")
                    state["closeout_notified_at"] = self.now(state)
            state["last_error"] = None
        except Exception as error:
            state["last_error"] = str(error)
            if state.get("stop"):
                state["stop"]["errors"] = [str(error)]
                state["stop"]["complete"] = False
                self.remember_failure(state)
        self.save(state)
        return state

    def check(self):
        with lock(self.directory / "state.lock"):
            return self.tick(self.load())

    def finish(self, reason):
        if reason not in {"converged", "user_stop", "deadline"}:
            raise GuardError("无效结束原因")
        with lock(self.directory / "state.lock"):
            state = self.load()
            if state["phase"] == "finished":
                return state
            self.authenticate(state["project"], state["task_id"])
            now = self.now(state)
            if state["phase"] == "stopping":
                return self.tick(state)
            if reason == "converged":
                if not state["deadlines"]["floor"] <= now < state["deadlines"]["deadline"]:
                    if now >= state["deadlines"]["deadline"]:
                        self.request_stop(state, "deadline", now)
                    raise GuardError("正常收敛仅允许在 T0+6 小时至 T0+10 小时之前")
                if not self.snapshot_report()["available"]:
                    raise GuardError(f"正常结束前须持久化报告：{REPORT}")
                goal = self.goal(state, state["root_thread_id"])
                if not goal or goal.get("status") != "complete":
                    raise GuardError("先将已实现的本任务 Goal 标为 complete，再 finish converged")
            if reason == "deadline" and now < state["deadlines"]["deadline"]:
                raise GuardError("尚未到十小时截止；用户明确提前结束应使用 user_stop")
            if now >= state["deadlines"]["deadline"]:
                reason = "deadline"
            self.request_stop(state, reason, now)
            # User stop / deadline is executed by the independent watcher, with a
            # durable receipt already present even if interrupt kills this CLI.
            return self.tick(state) if reason == "converged" else state

    def watcher_status(self):
        path = self.directory / "watcher.json"
        if not path.exists():
            return {"supervision_confirmed": False}
        heartbeat = read_json(path)
        descriptor = os.open(self.directory / "watch.lock", os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                held = False
            except BlockingIOError:
                held = True
        finally:
            os.close(descriptor)
        age = max(0, self.clock() - heartbeat.get("checked_at", 0))
        return dict(heartbeat, lock_held=held, heartbeat_age_seconds=age,
                    supervision_confirmed=bool(held and heartbeat.get("running") and age < 45))

    def status(self):
        if not self.state_path.exists():
            return {"initialized": False, "state_path": str(self.state_path)}
        state = self.load()
        now = max(self.clock(), state.get("observed_at", state["t0"]))
        end = state["stop"]["finished_at"] if state["phase"] == "finished" else now
        result = dict(state, elapsed_seconds=max(0, end - state["t0"]),
                      state_path=str(self.state_path), receipt_path=str(self.receipt_path))
        result["times_utc"] = {key: datetime.fromtimestamp(value, timezone.utc).isoformat()
                               for key, value in {"t0": state["t0"], **state["deadlines"]}.items()}
        result["watcher"] = self.watcher_status()
        return result

    def watch(self):
        self.prepare_directory()
        try:
            with lock(self.directory / "watch.lock", nonblocking=True):
                while True:
                    atomic_json(self.directory / "watcher.json", {
                        "pid": os.getpid(), "checked_at": self.clock(), "running": True,
                        "stage": "checking"})
                    state = self.check()
                    atomic_json(self.directory / "watcher.json", {
                        "pid": os.getpid(), "checked_at": self.clock(),
                        "running": state["phase"] != "finished", "last_error": state["last_error"]})
                    if state["phase"] == "finished":
                        return
                    boundary = next((state["deadlines"][key] for key in ("closeout", "deadline")
                                     if state["deadlines"][key] > self.clock()), self.clock() + 15)
                    time.sleep(max(0.1, min(15, boundary - self.clock())))
        except BlockingIOError:
            return  # Another watcher already owns this task's private lock.

    def launch_watch(self):
        if self.load()["phase"] == "finished":
            return
        if self.watcher_status()["supervision_confirmed"]:
            return
        log_path = self.directory / "watch.log"
        descriptor = os.open(log_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "a") as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "watch"],
                                       cwd=self.worktree, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=log, start_new_session=True, close_fds=True)
        # Report an actual heartbeat, not merely the existence of a Popen object.
        for _ in range(30):
            time.sleep(0.1)
            path = self.directory / "watcher.json"
            if path.exists():
                if self.watcher_status()["supervision_confirmed"]:
                    return
            if self.load()["phase"] == "finished":
                return
            if process.poll() is not None:
                break
        raise GuardError("计时已保存，但未确认监督进程心跳；运行 watch 并检查 watch.log 后才能继续实验")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="认证正在执行的 mrun、恢复原 T0 并启动独立监督进程")
    start.add_argument("--project", type=Path, required=True, help="启动器给出的主项目目录")
    start.add_argument("--task", required=True, help="本任务 task ID")
    commands.add_parser("status", help="只读查看持久化时间、回执与监督进程最近心跳")
    commands.add_parser("check", help="立即检查并补执行到期动作；不唤醒任何会话")
    register = commands.add_parser("register", help="根代理登记已启动的后代；同时验证并登记中间祖先")
    register.add_argument("--thread", required=True)
    finish = commands.add_parser("finish", help="持久化结束原因并停止登记的子会话；user_stop 仅限用户明确要求结束")
    finish.add_argument("--reason", choices=("converged", "user_stop", "deadline"), required=True)
    watch = commands.add_parser("watch", help="监督已初始化的本任务；重复进程由独占锁去重")
    watch.add_argument("--daemon", action="store_true", help="在后台启动并核对心跳")
    args = parser.parse_args(argv)
    guard = Guard(Path(__file__).resolve().parents[1])
    try:
        if args.command == "start":
            guard.start(args.project, args.task)
            guard.launch_watch()
        elif args.command == "check":
            guard.check()
        elif args.command == "register":
            guard.register(args.thread)
        elif args.command == "finish":
            guard.finish(args.reason)
            guard.launch_watch()
        elif args.command == "watch":
            guard.launch_watch() if args.daemon else guard.watch()
        result = guard.status()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2 if result.get("last_error") else 0
    except Exception as error:
        print(json.dumps({"error": str(error), "state_path": str(guard.state_path),
                          "receipt_path": str(guard.receipt_path)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
