#!/usr/bin/env python3
"""Register an explicitly returned built-in input-validation error; never infer failure from a timeout."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

try:
    from .material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility
except ImportError:
    from material_model_io import read_json as material_read_json, read_bytes as material_read_bytes, sqlite_compatibility

ROOT = Path(__file__).resolve().parents[1]
ERROR = "`referenced_image_paths` must contain at most 5 paths"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", nargs="+", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("registration already exists; inspect rather than duplicate")
    sys.path[:0] = [str(ROOT / ".runtime/review-desk-worktree"), str(ROOT / "scripts")]
    from review_desk import production as p
    from review_desk.production_media import ingest
    from review_desk.store import Store
    from register_generation_batch import validate_reference_authorization
    instance = ROOT / ".runtime/full-generation/all-pending/review"
    store = Store(instance / ".runtime/review.sqlite3")
    try:
        heads = {r["object_id"]: r["id"] for r in p.current_records(store)}
        records = []
        for label in args.ids:
            request_path = ROOT / "production/requests" / (label + ".json")
            request_bytes = material_read_bytes(request_path)
            q = json.loads(request_bytes)
            attempt = json.loads((ROOT / ".runtime/full-generation/all-pending" / (label + "-attempt.json")).read_text())
            outcome = json.loads((ROOT / ".runtime/full-generation/all-pending" / (label + "-tool-error.json")).read_text())
            assert outcome == {"id": label, "error": ERROR, "source": "image_gen.imagegen returned error"}
            assert q["tool"] == "image_gen.imagegen" and len(q["request"]["referenced_image_paths"]) > 5
            assert attempt["request_sha256"] == hashlib.sha256(request_bytes).hexdigest()
            assert not (ROOT / "production/receipts" / (label + "-builtin-complete.json")).exists()
            call_id = "call-" + label
            assert call_id not in heads and "asset-" + label not in heads
            plan = p.ref_record(store, q["requirement"], {"REQUIREMENT"})["payload"]["generation"]
            assert plan["prompt"] == q["request"]["prompt"]
            parameters = {k: v for k, v in q["request"].items() if k != "prompt"}
            assert parameters == plan["parameters"]
            inputs = [{**r["reference"], "component_id": r["component_id"], **{k: r[k] for k in ("crop", "range") if k in r}}
                      for r in q.get("references", [])]
            validate_reference_authorization(lambda r, kinds: p.ref_record(store, r, kinds),
                                             q, inputs, [q["state"]], q["entity"], "image")
            receipt = {"id": label, "status": "FAILED", "tool": q["tool"], "failure_stage": "tool_input_validation",
                       "error": ERROR, "output_files": [], "provider_call_id": None, "underlying_model_id": None,
                       "metered_usage": None, "request_file_sha256": hashlib.sha256(request_bytes).hexdigest(),
                       "note": "工具明确返回输入校验错误，无返回图像。服务端接收、底层调用和扣量均未暴露，不推定为零。原提交尝试保留。"}
            receipt_path = ROOT / "production/receipts" / (label + "-builtin-failed.json")
            with receipt_path.open("x") as f:
                json.dump(receipt, f, ensure_ascii=False, indent=2); f.write("\n")
            components = []
            for cid, path in [("request", request_path), ("receipt", receipt_path)]:
                with path.open("rb") as stream: c = ingest(instance, stream, path.name)
                with path.open("rb") as stream: assert ingest(ROOT, stream, path.name)["sha256"] == c["sha256"]
                components.append({**c, "id": cid, "role": "metadata"})
            payload = {"format": "production-call-v1", "title": plan.get("title", label) + " · 输入校验拒绝",
                       "blocks": [{"id": "description", "text": "工具明确返回：" + ERROR + "。无原件，不计入状态完成；新请求将重新适配参考输入。"}],
                       "method": "generation", "tool": q["tool"], "model": q["model"], "status": "failed",
                       "prompt": q["request"]["prompt"], "parameters": parameters,
                       "inputs": [q["entity"], q["state"], *inputs], "outputs": [], "prepared_plan": q["requirement"],
                       "request_file_sha256": receipt["request_file_sha256"], "receipt": receipt,
                       "components": components, "usage": {"metered_usage": None, "note": receipt["note"]},
                       "lineage": q["lineage"], "task": "task-20261002-0003"}
            for k in ("master_approval", "master_approvals", "same_state_repair"):
                if k in q: payload[k] = deepcopy(q[k])
            records.append({"object_id": call_id, "kind": "CALL", "expected_version": 0, "payload": payload})
        batch = {"format": "production-import-v1", "expected_heads": heads, "records": records}
        p.import_records(store, batch, validate_only=True); p.import_records(store, batch)
        document = {"format": "full-generation-registration-v1", "batches": [batch],
                    "summary": {"new_calls": len(records), "failed_input_validation": len(records), "new_assets": 0}}
        args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(document["summary"]))
    finally:
        store.close()


if __name__ == "__main__":
    main()
