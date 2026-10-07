#!/usr/bin/env python3
"""Guard the reviewed system fast-forward; use --apply only after user confirmation.

This does not deploy services, import databases, push, or mark the story task
complete. Its receipt stays in the task worktree's untracked runtime directory.
"""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def check(system_main, system_worktree, expected_target, candidate):
    if git(system_main, "branch", "--show-current") != "main":
        raise ValueError("system target is not main")
    if git(system_worktree, "rev-parse", "HEAD") != candidate:
        raise ValueError("system candidate changed; prepare and confirm again")
    for repo in (system_main, system_worktree):
        if git(repo, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError("tracked system files changed; do not overwrite")
    common = Path(git(system_main, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    other = Path(git(system_worktree, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if common.resolve() != other.resolve():
        raise ValueError("system checkouts belong to different repositories")
    target = git(system_main, "rev-parse", "HEAD")
    if target not in (expected_target, candidate):
        raise ValueError("system main changed; inspect difference before integration")
    subprocess.run(["git", "-C", str(system_main), "merge-base", "--is-ancestor",
                    expected_target, candidate], check=True, capture_output=True)
    return {"target_branch": "main", "target_before": target,
            "expected_target": expected_target, "candidate": candidate,
            "already_integrated": target == candidate,
            "tracked_files_clean": True, "push": False, "deploy": False,
            "database_write": False}, common


def integrate(system_main, system_worktree, expected_target, candidate, receipt=None):
    result, common = check(system_main, system_worktree, expected_target, candidate)
    if receipt is None:
        return {**result, "preflight_only": True}
    receipt = receipt.resolve()
    runtime = (ROOT / ".runtime").resolve()
    if runtime not in receipt.parents:
        raise ValueError("receipt must stay in this task's runtime directory")
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous.get("candidate") != candidate or previous.get("target_after") != candidate:
            raise ValueError("existing receipt describes a different delivery")
    with (common / "full-generation-system-integration.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result, _ = check(system_main, system_worktree, expected_target, candidate)
        if not result["already_integrated"]:
            subprocess.run(["git", "-C", str(system_main), "merge", "--ff-only", "--no-edit", candidate],
                           check=True, capture_output=True, text=True)
        after = git(system_main, "rev-parse", "HEAD")
        if after != candidate:
            raise ValueError("system target does not match approved candidate")
        result.update(target_after=after, preflight_only=False)
        if receipt.exists():
            previous = json.loads(receipt.read_text())
            return previous
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "production/full-generation/system-delivery.json")
    parser.add_argument("--system-main", type=Path)
    parser.add_argument("--system-worktree", type=Path)
    parser.add_argument("--expected-target")
    parser.add_argument("--candidate")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--receipt", type=Path,
                        default=ROOT / ".runtime/full-generation/system-integration/receipt.json")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if plan.get("format") != "generation-system-delivery-v1":
        parser.error("unsupported delivery plan")
    if plan.get("task_delivery"):
        import task_repository_delivery
        value = plan["task_delivery"]
        if args.apply:
            result = task_repository_delivery.apply(value, args.receipt)
        else:
            task_repository_delivery.validate(value)
            result = {"backend": "codex.task", "preflight_only": True}
        print(json.dumps(result, ensure_ascii=False))
        return
    story_main = Path(git(ROOT, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve().parent
    system_main = args.system_main or story_main / plan["system_main_from_story_main"]
    system_worktree = args.system_worktree or ROOT / plan["system_worktree"]
    result = integrate(system_main.resolve(), system_worktree.resolve(),
                       args.expected_target or plan["expected_target"], args.candidate or plan["candidate"],
                       args.receipt if args.apply else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
