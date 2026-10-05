"""Deterministic guard tests: no daemon, real Goals, threads, or project ledger writes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

SOURCE = Path(__file__).resolve().parents[1] / "scripts/autonomous_optimization_guard.py"
spec = importlib.util.spec_from_file_location("autonomous_guard", SOURCE)
guard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard_module)
Guard, GuardError = guard_module.Guard, guard_module.GuardError


def uid():
    return str(uuid.uuid4())


class FakeRPC:
    def __init__(self):
        self.threads, self.goals, self.calls = {}, {}, []
        self.fail = {}
        self.offline = False
        self.sticky_interrupts = set()
        self.before_mutation = None
        self.page_size = 32

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        thread_id = params["threadId"]
        if self.offline or self.fail.get((method, thread_id), 0):
            if not self.offline:
                self.fail[method, thread_id] -= 1
            raise GuardError("fake transport offline")
        if method == "thread/read":
            thread = copy.deepcopy(self.threads[thread_id])
            if not params.get("includeTurns"):
                thread["turns"] = []
            return {"thread": thread}
        if method == "thread/turns/list":
            turns = copy.deepcopy(self.threads[thread_id]["turns"])
            if params.get("sortDirection") == "desc":
                turns.reverse()
            offset, limit = int(params.get("cursor", "0")), min(params["limit"], self.page_size)
            data = turns[offset:offset+limit]
            for turn in data:
                turn["items"] = []
                turn["itemsView"] = "notLoaded"
            return {"data": data, "nextCursor": str(offset+limit) if offset+limit < len(turns) else None}
        if method == "thread/items/list":
            turn = next(t for t in self.threads[thread_id]["turns"] if t["id"] == params["turnId"])
            offset, limit = int(params.get("cursor", "0")), params["limit"]
            data = [{"turnId": turn["id"], "item": copy.deepcopy(item)}
                    for item in turn["items"][offset:offset+limit]]
            return {"data": data, "nextCursor": str(offset+limit) if offset+limit < len(turn["items"]) else None}
        if method == "thread/goal/get":
            return {"goal": copy.deepcopy(self.goals.get(thread_id))}
        if self.before_mutation:
            self.before_mutation(method, params)
        if method == "thread/goal/set":
            assert params == {"threadId": thread_id, "status": "paused"}
            self.goals[thread_id]["status"] = "paused"
            return {"goal": copy.deepcopy(self.goals[thread_id])}
        if method == "turn/steer":
            assert any(t["id"] == params["expectedTurnId"] and t["status"] == "inProgress"
                       for t in self.threads[thread_id]["turns"])
            return {"turnId": params["expectedTurnId"]}
        if method == "turn/interrupt":
            if thread_id not in self.sticky_interrupts:
                self.threads[thread_id]["status"] = {"type": "idle"}
                for turn in self.threads[thread_id]["turns"]:
                    if turn["id"] == params["turnId"]:
                        turn["status"] = "interrupted"
            return {}
        raise AssertionError("Forbidden RPC: " + method)

    def mutations(self):
        return [(method, params) for method, params in self.calls
                if method not in {"thread/read", "thread/turns/list", "thread/items/list", "thread/goal/get"}]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.worktree, self.project = base / "worktree", base / "main"
        self.worktree.mkdir()
        self.project.mkdir()
        (self.worktree / "planning").mkdir()
        (self.worktree / guard_module.REPORT).write_text("# Current tested checkpoint\n", encoding="utf-8")
        self.task, self.root, self.lease, self.marker = "task-20261004-0001", uid(), uid(), uid()
        self.t0 = 1_800_000_000
        self.now = self.t0 + 100
        self.record = {"id": self.task, "status": "running", "execution_mode": "mrun",
                       "session_id": self.root, "lease": self.lease, "run_marker": self.marker,
                       "codex_home": str(base / "codex"), "attempts": 1}
        self.env = {"CODEX_THREAD_ID": self.root, "CODEX_PROJECT_TASK_LEASE": self.lease,
                    "CODEX_HOME": self.record["codex_home"]}
        self.rpc = FakeRPC()
        self.rpc.threads[self.root] = {
            "id": self.root, "source": "cli", "cwd": str(self.worktree),
            "createdAt": self.t0 - 86400, "status": {"type": "active"},
            "historyMode": "legacy", "turns": [self.execution_turn(self.marker, self.t0)],
        }
        self.rpc.goals[self.root] = {"threadId": self.root, "status": "active"}
        self.active_checks = []
        self.guard = Guard(self.worktree, clock=lambda: self.now, rpc=self.rpc,
                           ledger=lambda project: {"tasks": {self.task: self.record}},
                           environment=self.env,
                           execution_directory=lambda project, record: self.worktree,
                           active_run=lambda project, record: self.active_checks.append(record["lease"]))

    def execution_turn(self, marker, started, task=None, mode="mrun"):
        content = (f"CODEX_PROJECT_TASK_RUN:{marker}\n\n通过 task {mode} 执行项目任务。\n\n"
                   + "任务内容：" + json.dumps({"id": task or self.task}, ensure_ascii=False))
        return {"id": uid(), "startedAt": started, "status": "inProgress",
                "items": [{"type": "userMessage", "content": [{"type": "text", "text": content}]}]}

    def start(self):
        return self.guard.start(self.project, self.task)

    def child(self, parent=None):
        child = uid()
        parent = parent or self.root
        self.rpc.threads[child] = {
            "id": child, "parentThreadId": parent,
            "source": {"subAgent": {"thread_spawn": {"parent_thread_id": parent, "depth": 1}}},
            "status": {"type": "active"},
            "turns": [{"id": uid(), "status": "inProgress", "items": []}],
        }
        self.rpc.goals[child] = {"threadId": child, "status": "active"}
        return child

    def later_turn(self, thread_id):
        for turn in self.rpc.threads[thread_id]["turns"]:
            turn["status"] = "completed"
        turn = {"id": uid(), "status": "inProgress", "items": []}
        self.rpc.threads[thread_id]["turns"].append(turn)
        self.rpc.threads[thread_id]["status"] = {"type": "active"}
        return turn["id"]

    def finish_converged(self, elapsed=21600):
        self.now = self.t0 + elapsed
        self.rpc.goals[self.root]["status"] = "complete"
        return self.guard.finish("converged")

    def test_delayed_start_uses_execution_not_creation_or_now(self):
        self.now = self.t0 + 18000
        self.rpc.threads[self.root]["turns"].insert(0, {
            "id": uid(), "startedAt": self.t0 - 86000, "status": "completed", "items": []})
        state = self.start()
        self.assertEqual(state["t0"], self.t0)
        self.assertEqual(state["deadlines"], {"floor": self.t0 + 21600,
                         "closeout": self.t0 + 32400, "deadline": self.t0 + 36000})
        self.assertEqual(state["initialized_at"], self.now)
        self.assertEqual(self.rpc.mutations(), [])

    def test_missing_state_on_resume_recovers_earliest_marker(self):
        old_marker = uid()
        self.record["attempts"] = 3
        self.rpc.threads[self.root]["turns"] = [self.execution_turn(old_marker, self.t0),
                                                        self.execution_turn(self.marker, self.t0 + 12000)]
        self.now = self.t0 + 15000
        self.rpc.page_size = 1
        self.rpc.threads[self.root]["historyMode"] = "paginated"
        state = self.start()
        self.assertEqual((state["t0"], state["first_run_marker"]), (self.t0, old_marker))

    def test_isolated_run_recovers_first_execution_and_enforces_deadline(self):
        self.record.update(execution_mode="run", worktree={"path": "worktree"})
        old_marker = uid()
        self.rpc.threads[self.root]["turns"] = [
            self.execution_turn(old_marker, self.t0, mode="run"),
            self.execution_turn(self.marker, self.t0 + 20000, mode="run")]
        self.rpc.page_size = 1
        self.now = self.t0 + 21000
        self.env.pop("CODEX_PROJECT_TASK_LEASE")
        state = self.start()
        self.assertEqual((state["t0"], state["first_run_marker"], state["execution_mode"]),
                         (self.t0, old_marker, "run"))
        self.assertEqual(self.active_checks, [self.lease])
        child = self.child()
        self.guard.register(child)
        self.now = self.t0 + 36000
        stopped = self.guard.check()
        self.assertEqual(stopped["phase"], "finished")
        self.assertEqual(stopped["stop"]["reason"], "deadline")
        for thread in [self.root, child]:
            self.assertEqual(self.rpc.goals[thread]["status"], "paused")
            self.assertEqual(self.rpc.threads[thread]["status"]["type"], "idle")

    def test_run_requires_isolation_and_matching_execution_input(self):
        self.record["execution_mode"] = "run"
        with self.assertRaisesRegex(GuardError, "隔离 worktree"):
            self.start()
        self.record["worktree"] = {"path": "worktree"}
        with self.assertRaisesRegex(GuardError, "对应入口证据"):
            self.start()
        self.assertFalse(self.guard.state_path.exists())
        self.assertEqual(self.rpc.mutations(), [])

    def test_mode_drift_never_rearms_or_stops_another_execution(self):
        state = self.start()
        self.record.update(execution_mode="run", worktree={"path": "worktree"})
        with self.assertRaisesRegex(GuardError, "恢复入口"):
            self.start()
        self.now = self.t0 + 36000
        self.rpc.calls.clear()
        result = self.guard.check()
        self.assertEqual(result["phase"], "stopping")
        self.assertEqual(result["t0"], state["t0"])
        self.assertFalse(result["stop"]["complete"])
        self.assertEqual(self.rpc.calls, [])

    def test_legacy_mrun_state_without_mode_remains_resumable(self):
        state = self.start()
        del state["execution_mode"]
        self.guard.save(state)
        self.now = self.t0 + 1000
        self.assertEqual(self.start()["t0"], self.t0)

    def test_register_at_deadline_latches_without_registering_or_reading_child(self):
        self.start()
        child = self.child()
        self.now = self.t0 + 36000
        self.rpc.calls.clear()
        with self.assertRaisesRegex(GuardError, "硬截止"):
            self.guard.register(child)
        state = self.guard.load()
        self.assertEqual(state["children"], {})
        self.assertEqual(state["phase"], "stopping")
        self.assertEqual(state["stop"]["reason"], "deadline")
        self.assertEqual(self.rpc.calls, [])

    def test_register_while_stopping_preserves_scope_and_reason(self):
        state = self.start()
        self.guard.request_stop(state, "user_stop", self.now)
        self.rpc.calls.clear()
        with self.assertRaisesRegex(GuardError, "正在停止"):
            self.guard.register(self.child())
        state = self.guard.load()
        self.assertEqual(state["children"], {})
        self.assertEqual(state["stop"]["reason"], "user_stop")
        self.assertEqual(self.rpc.calls, [])

    def test_registration_crossing_deadline_does_not_commit_new_scope(self):
        self.start()
        child = self.child()
        self.now = self.t0 + 35999
        call = self.rpc.call
        def advance_on_read(method, params):
            result = call(method, params)
            if method == "thread/read":
                self.now = self.t0 + 36000
            return result
        with patch.object(self.rpc, "call", side_effect=advance_on_read):
            with self.assertRaisesRegex(GuardError, "硬截止"):
                self.guard.register(child)
        state = self.guard.load()
        self.assertEqual(state["children"], {})
        self.assertEqual(state["stop"]["reason"], "deadline")
        self.assertEqual(self.rpc.mutations(), [])

    def test_resume_does_not_reset_time_or_reminder(self):
        state = self.start()
        self.now = self.t0 + 32401
        self.guard.check()
        self.record["lease"] = self.env["CODEX_PROJECT_TASK_LEASE"] = uid()
        self.record["run_marker"] = uid()
        self.record["attempts"] = 2
        self.rpc.calls.clear()
        resumed = self.start()
        self.assertEqual(resumed["t0"], state["t0"])
        self.assertEqual(resumed["deadlines"], state["deadlines"])
        self.assertIsNotNone(resumed["closeout_notified_at"])
        self.assertEqual(self.rpc.mutations(), [])

    def test_ambiguous_or_incomplete_first_execution_rejected(self):
        cases = ["timestamp", "marker", "foreign_task"]
        original = copy.deepcopy(self.rpc.threads[self.root])
        for case in cases:
            with self.subTest(case=case):
                thread = self.rpc.threads[self.root] = copy.deepcopy(original)
                if case == "timestamp":
                    thread["turns"][0]["startedAt"] = None
                elif case == "marker":
                    thread["turns"][0] = self.execution_turn(uid(), self.t0)
                elif case == "foreign_task":
                    turn = self.execution_turn(self.marker, self.t0, "task-20261004-0002")
                    turn["items"][0]["content"][0]["text"] += "\n依赖：" + self.task
                    thread["turns"][0] = turn
                with self.assertRaises(GuardError):
                    self.start()
                self.assertFalse(self.guard.state_path.exists())

    def test_first_start_after_deadline_latches_before_remote_actions(self):
        self.now = self.t0 + 40000
        state = self.start()
        self.assertEqual(state["phase"], "stopping")
        self.assertEqual(state["t0"], self.t0)
        self.assertEqual(self.rpc.mutations(), [])
        self.assertTrue(self.guard.receipt_path.exists())
        stopped = self.guard.check()
        self.assertEqual(stopped["phase"], "finished")
        self.assertEqual(stopped["stop"]["reason"], "deadline")

    def test_six_hour_floor_and_six_to_nine_hour_finish(self):
        self.start()
        self.now = self.t0 + 21599
        self.rpc.goals[self.root]["status"] = "complete"
        with self.assertRaises(GuardError):
            self.guard.finish("converged")
        self.assertEqual(self.guard.load()["phase"], "armed")
        child = self.child()
        self.guard.register(child)
        state = self.finish_converged()
        self.assertEqual(state["phase"], "finished")
        self.assertTrue(state["stop"]["complete"])
        self.assertEqual(self.rpc.goals[child]["status"], "paused")
        self.assertFalse(any(p["threadId"] == self.root for m, p in self.rpc.mutations()))
        self.assertEqual(self.rpc.threads[child]["status"]["type"], "idle")

    def test_normal_finish_requires_achieved_goal_and_durable_report(self):
        self.start()
        self.now = self.t0 + 22000
        with self.assertRaises(GuardError):
            self.guard.finish("converged")
        self.rpc.goals[self.root]["status"] = "complete"
        (self.worktree / guard_module.REPORT).unlink()
        with self.assertRaises(GuardError):
            self.guard.finish("converged")
        self.assertEqual(self.rpc.mutations(), [])

    def test_nine_hour_reminder_targets_current_turn_once(self):
        self.start()
        turn = self.later_turn(self.root)
        self.now = self.t0 + 32399
        self.guard.check()
        self.assertEqual(self.rpc.mutations(), [])
        self.now += 1
        self.guard.check()
        self.guard.check()
        reminders = [(m, p) for m, p in self.rpc.mutations() if m == "turn/steer"]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0][1]["expectedTurnId"], turn)
        self.assertEqual(reminders[0][1]["threadId"], self.root)

    def test_nine_hour_idle_does_not_wake_and_retries_when_active(self):
        self.start()
        self.rpc.threads[self.root]["status"] = {"type": "idle"}
        self.now = self.t0 + 32400
        self.guard.check()
        self.assertEqual(self.rpc.mutations(), [])
        self.later_turn(self.root)
        self.now += 100
        self.guard.check()
        self.assertEqual([m for m, p in self.rpc.mutations()], ["turn/steer"])

    def test_deadline_stops_only_root_and_registered_descendants(self):
        self.start()
        child, foreign = self.child(), self.child(uid())
        grandchild = self.child(child)
        self.guard.register(grandchild)  # Also registers its verified ancestor.
        root_turn, child_turn = self.later_turn(self.root), self.later_turn(child)
        self.rpc.calls.clear()
        self.now = self.t0 + 36000
        state = self.guard.check()
        self.assertEqual(state["phase"], "finished")
        mutations = self.rpc.mutations()
        self.assertEqual({p["threadId"] for m, p in mutations}, {self.root, child, grandchild})
        self.assertNotIn(foreign, {p["threadId"] for m, p in self.rpc.calls})
        self.assertEqual(mutations[0], ("thread/goal/set", {"threadId": self.root, "status": "paused"}))
        self.assertEqual(mutations[1], ("turn/interrupt", {"threadId": self.root, "turnId": root_turn}))
        self.assertIn(("turn/interrupt", {"threadId": child, "turnId": child_turn}), mutations)
        self.assertFalse(any(m == "turn/steer" for m, p in mutations))

    def test_sibling_or_parent_conflict_registration_rejected(self):
        self.start()
        foreign_root = uid()
        self.rpc.threads[foreign_root] = {"id": foreign_root, "source": "cli", "turns": []}
        sibling = self.child(foreign_root)
        with self.assertRaises(GuardError):
            self.guard.register(sibling)
        conflict = self.child()
        self.rpc.threads[conflict]["parentThreadId"] = foreign_root
        with self.assertRaises(GuardError):
            self.guard.register(conflict)
        self.assertEqual(self.guard.load()["children"], {})

    def test_manual_stop_before_six_records_first_then_stops(self):
        self.start()
        child = self.child()
        self.guard.register(child)
        def verify_receipt(method, params):
            receipt = guard_module.read_json(self.guard.receipt_path)
            self.assertEqual(receipt["phase"], "stopping")
            self.assertFalse(receipt["complete"])
            self.assertEqual(receipt["report"]["path"], guard_module.REPORT)
            self.assertTrue(receipt["report"]["available"])
        self.rpc.before_mutation = verify_receipt
        state = self.guard.finish("user_stop")
        self.assertEqual(state["phase"], "stopping")
        self.assertEqual(self.rpc.mutations(), [])
        state = self.guard.check()
        self.assertTrue(state["stop"]["complete"])
        self.assertEqual(state["stop"]["reason"], "user_stop")
        self.assertEqual(self.rpc.goals[self.root]["status"], "paused")

    def test_finished_guard_never_rearms_or_wakes(self):
        self.start()
        state = self.finish_converged()
        self.now = self.t0 + 100000
        self.rpc.calls.clear()
        self.start()
        self.guard.check()
        self.guard.finish("deadline")
        self.assertEqual(self.rpc.calls, [])
        self.assertEqual(self.guard.load()["stop"], state["stop"])
        self.assertEqual(self.guard.status()["elapsed_seconds"], 21600)
        with self.assertRaises(GuardError):
            self.guard.register(self.child())

    def test_deadline_cannot_be_labelled_converged(self):
        self.start()
        self.now = self.t0 + 36000
        self.rpc.goals[self.root]["status"] = "complete"
        with self.assertRaises(GuardError):
            self.guard.finish("converged")
        self.assertEqual(self.guard.load()["stop"]["reason"], "deadline")
        self.assertEqual(self.guard.check()["phase"], "finished")

    def test_convergence_cleanup_crossing_deadline_becomes_deadline(self):
        self.start()
        child = self.child()
        self.guard.register(child)
        self.now = self.t0 + 35999
        self.rpc.goals[self.root]["status"] = "complete"
        original_call = self.rpc.call
        failed_once = []
        def slow_child_failure(method, params):
            if method == "thread/goal/set" and params["threadId"] == child and not failed_once:
                failed_once.append(True)
                self.now = self.t0 + 36001
                self.rpc.fail[method, child] = 1
            return original_call(method, params)
        with patch.object(self.rpc, "call", side_effect=slow_child_failure):
            state = self.guard.finish("converged")
        self.assertEqual(state["stop"]["requested_reason"], "converged")
        self.assertEqual(state["stop"]["reason"], "deadline")
        self.assertEqual(state["phase"], "finished")
        self.assertTrue(state["stop"]["failure_history"])
        self.assertTrue(any(child in error and "offline" in error
                            for error in state["stop"]["first_failure"]["errors"]))
        self.assertTrue(any(m == "turn/interrupt" and p["threadId"] == self.root
                            for m, p in self.rpc.calls))

    def test_early_deadline_request_rejected(self):
        self.start()
        with self.assertRaises(GuardError):
            self.guard.finish("deadline")
        self.assertEqual(self.guard.load()["phase"], "armed")

    def test_offline_deadline_receipt_and_recovery_without_time_reset(self):
        self.start()
        self.rpc.offline = True
        self.now = self.t0 + 37000
        pending = self.guard.check()
        self.assertEqual(pending["phase"], "stopping")
        self.assertFalse(pending["stop"]["complete"])
        self.assertTrue(pending["stop"]["errors"])
        self.rpc.offline = False
        self.rpc.calls.clear()
        state = self.guard.check()
        self.assertEqual(state["phase"], "finished")
        self.assertEqual(state["t0"], self.t0)
        self.assertEqual(state["stop"]["attempts"], 2)
        self.assertTrue(state["stop"]["failure_history"])
        self.assertIn("offline", " ".join(state["stop"]["first_failure"]["errors"]))
        self.assertFalse(any(m == "turn/steer" for m, p in self.rpc.calls))

    def test_partial_child_goal_failure_still_interrupts_and_retries(self):
        self.start()
        child = self.child()
        self.guard.register(child)
        self.rpc.fail["thread/goal/set", child] = 1
        self.now = self.t0 + 36000
        pending = self.guard.check()
        self.assertEqual(pending["phase"], "stopping")
        self.assertEqual(self.rpc.threads[child]["status"]["type"], "idle")
        self.assertEqual(self.rpc.goals[child]["status"], "active")
        root_interrupt = next(i for i, (m, p) in enumerate(self.rpc.calls)
                              if m == "turn/interrupt" and p["threadId"] == self.root)
        failed_child_pause = next(i for i, (m, p) in enumerate(self.rpc.calls)
                                 if m == "thread/goal/set" and p["threadId"] == child)
        self.assertLess(root_interrupt, failed_child_pause)
        self.assertFalse(guard_module.read_json(self.guard.receipt_path)["complete"])
        state = self.guard.check()
        self.assertEqual(state["phase"], "finished")
        self.assertEqual(self.rpc.goals[child]["status"], "paused")

    def test_interrupt_ack_is_not_stop_confirmation(self):
        self.start()
        self.rpc.sticky_interrupts.add(self.root)
        self.now = self.t0 + 36000
        state = self.guard.check()
        self.assertEqual(state["phase"], "stopping")
        self.assertFalse(state["stop"]["complete"])
        self.rpc.sticky_interrupts.clear()
        self.assertEqual(self.guard.check()["phase"], "finished")

    def test_rpc_goal_identity_mismatch_remains_partial(self):
        self.start()
        self.rpc.goals[self.root]["threadId"] = uid()
        self.now = self.t0 + 36000
        state = self.guard.check()
        self.assertEqual(state["phase"], "stopping")
        self.assertFalse(any(m == "thread/goal/set" for m, p in self.rpc.calls))

    def test_scope_ledger_drift_blocks_all_remote_mutations(self):
        self.start()
        self.record["session_id"] = uid()
        self.now = self.t0 + 36000
        self.rpc.calls.clear()
        state = self.guard.check()
        self.assertEqual(state["phase"], "stopping")
        self.assertFalse(state["stop"]["complete"])
        self.assertEqual(self.rpc.calls, [])

    def test_live_identity_lease_and_launcher_fallback(self):
        original = copy.deepcopy(self.record)
        for key, value in [("status", "published"), ("execution_mode", "run"),
                           ("session_id", uid()), ("lease", uid()), ("codex_home", "/different")]:
            with self.subTest(key=key):
                self.record.clear()
                self.record.update(original)
                self.record[key] = value
                with self.assertRaises(GuardError):
                    self.start()
        self.record.clear()
        self.record.update(original)
        self.env.pop("CODEX_PROJECT_TASK_LEASE")
        self.start()
        self.assertEqual(self.active_checks, [self.lease])
        self.guard.active_run = lambda *args: (_ for _ in ()).throw(GuardError("launcher gone"))
        with self.assertRaises(GuardError):
            self.start()

    def test_root_child_and_worktree_mismatch_rejected(self):
        self.rpc.threads[self.root]["parentThreadId"] = uid()
        with self.assertRaises(GuardError):
            self.start()
        self.rpc.threads[self.root].pop("parentThreadId")
        self.rpc.threads[self.root]["cwd"] = str(self.project)
        with self.assertRaises(GuardError):
            self.start()
        self.assertFalse(self.guard.state_path.exists())

    def test_corrupt_budget_and_symlink_runtime_rejected(self):
        self.start()
        state = self.guard.load()
        state["deadlines"]["deadline"] -= 1
        guard_module.atomic_json(self.guard.state_path, state)
        with self.assertRaises(GuardError):
            self.guard.check()
        other = Path(self.temp.name) / "other"
        other.mkdir()
        (other / ".runtime").symlink_to(self.worktree / ".runtime", target_is_directory=True)
        with self.assertRaises(GuardError):
            Guard(other).prepare_directory()

    def test_receipt_write_crash_recovered_from_canonical_stop_latch(self):
        self.start()
        real = guard_module.atomic_json
        def fail_receipt(path, value):
            if path == self.guard.receipt_path:
                raise OSError("simulated receipt write failure")
            return real(path, value)
        with patch.object(guard_module, "atomic_json", side_effect=fail_receipt):
            with self.assertRaises(OSError):
                self.guard.finish("user_stop")
        self.assertEqual(self.guard.load()["phase"], "stopping")
        self.assertEqual(self.rpc.mutations(), [])
        self.assertEqual(self.guard.check()["phase"], "finished")
        self.assertTrue(guard_module.read_json(self.guard.receipt_path)["complete"])

    def test_finished_watcher_exits_without_sleep_or_rpc(self):
        self.start()
        self.finish_converged()
        self.rpc.calls.clear()
        with patch.object(guard_module.time, "sleep", side_effect=AssertionError("must exit")):
            self.guard.watch()
        self.assertEqual(self.rpc.calls, [])
        self.assertFalse(self.guard.status()["watcher"]["supervision_confirmed"])

    def test_existing_live_watcher_does_not_spawn_another_process(self):
        self.start()
        with patch.object(self.guard, "watcher_status", return_value={"supervision_confirmed": True}), \
                patch.object(guard_module.subprocess, "Popen") as popen:
            self.guard.launch_watch()
        popen.assert_not_called()

    def test_launch_failure_does_not_claim_supervision(self):
        self.start()
        process = SimpleNamespace(poll=lambda: 1)
        with patch.object(guard_module.subprocess, "Popen", return_value=process), \
                patch.object(guard_module.time, "sleep"):
            with self.assertRaises(GuardError):
                self.guard.launch_watch()
        self.assertFalse(self.guard.status()["watcher"]["supervision_confirmed"])
        self.assertEqual(self.guard.load()["t0"], self.t0)

    def test_watcher_uses_near_boundary_and_exits_on_finish(self):
        self.start()
        self.now = self.t0 + 32395
        armed = self.guard.load()
        finished = dict(armed, phase="finished")
        def advance(seconds):
            self.assertEqual(seconds, 5)
            self.now += seconds
        with patch.object(self.guard, "check", side_effect=[armed, finished]) as check, \
                patch.object(guard_module.time, "sleep", side_effect=advance):
            self.guard.watch()
        self.assertEqual(check.call_count, 2)
        self.assertFalse(self.guard.status()["watcher"]["supervision_confirmed"])

    def test_paused_and_offline_time_still_counts(self):
        self.start()
        self.rpc.goals[self.root]["status"] = "paused"
        self.record["status"], self.record["lease"] = "interrupted", None
        self.now = self.t0 + 36000
        state = self.guard.check()
        self.assertEqual(state["phase"], "finished")
        self.assertEqual(state["stop"]["reason"], "deadline")

    def test_overall_rpc_deadline_is_installed_and_restored(self):
        rpc = guard_module.SharedRPC(Path(self.temp.name))
        handlers = []
        def set_handler(sig, handler):
            handlers.append(handler)
        class Session:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def call(self, method, params):
                handlers[0]()  # Emulate a stream of notifications exceeding the total timeout.
        manager = SimpleNamespace(inspect=lambda: SimpleNamespace(socket_path=Path("/unused")))
        transport = SimpleNamespace(ManagedAppServer=lambda *args, **kwargs: manager,
                                    AppServerSession=Session)
        runtime = SimpleNamespace(daemon_transport=lambda: transport)
        signal_sentinel = object()
        with patch.object(guard_module, "installed", return_value=runtime), \
                patch.object(guard_module.shutil, "which", return_value="/unused/codex"), \
                patch.object(guard_module.signal, "signal", side_effect=set_handler), \
                patch.object(guard_module.signal, "getsignal", return_value=signal_sentinel), \
                patch.object(guard_module.signal, "getitimer", return_value=(0, 0)), \
                patch.object(guard_module.signal, "setitimer") as timer:
            with self.assertRaisesRegex(GuardError, "8 秒"):
                rpc.call("thread/goal/get", {"threadId": self.root})
        self.assertEqual(timer.call_args_list[0].args[1], 8)
        self.assertEqual(timer.call_args_list[-1].args[1], 0)
        self.assertIs(handlers[-1], signal_sentinel)

    def test_rpc_wrapper_never_allows_goal_resume_or_new_thread(self):
        rpc = guard_module.SharedRPC(Path(self.temp.name))
        for method, params in [("thread/start", {}), ("thread/resume", {}),
                               ("thread/goal/set", {"threadId": self.root, "status": "active"}),
                               ("thread/goal/set", {"threadId": self.root, "status": "complete"})]:
            with self.assertRaises(GuardError):
                rpc.call(method, params)


if __name__ == "__main__":
    unittest.main()
