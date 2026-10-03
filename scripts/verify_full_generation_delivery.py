#!/usr/bin/env python3
"""Read-only audit of this task's complete generation and restored bundle.

Run after production_review.py snapshot/recover. Image qualification is the
recorded visual review, not a new visual judgment or automatic user adoption.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import wave

from verify_production_review import read_tables
from register_generation_batch import validate_builtin_plan, validate_reference_authorization

ROOT = Path(__file__).resolve().parents[1]
PASS = {"self_pass", "passed", "ready_for_user_review"}
TASK = "task-20261002-0003"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(snapshot, restored, baseline, allow_incomplete=False):
    source, recovered = read_tables(snapshot), read_tables(restored / ".runtime/review.sqlite3")
    require(source.keys() == recovered.keys(), "restored schema differs")
    require(all(Counter(source[k]) == Counter(recovered[k]) for k in source),
            "restored business table contents differ")
    old = read_tables(baseline)
    for name in ("revisions", "dependencies", "comments", "comment_events", "material_members"):
        require(not (Counter(old[name]) - Counter(source[name])), "old history missing: " + name)

    manifest = json.loads((ROOT / "export/manifest.json").read_text())
    replay = json.loads((ROOT / "production/replay.json").read_text())
    require(digest(ROOT / "export/manifest.json") == replay["base_manifest_sha256"],
            "replay does not describe this export")
    for name, sha in manifest["files"].items():
        require(digest(ROOT / "export" / name) == sha, "export changed: " + name)
        require(digest(restored / "export" / name) == sha, "restored export differs: " + name)
    for name, sha in replay["files"].items():
        require(digest(ROOT / name) == sha and digest(restored / name) == sha,
                "production file differs: " + name)

    db = sqlite3.connect(snapshot.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    revisions = {}
    for row in db.execute("SELECT r.*, o.kind FROM revisions r JOIN objects o ON o.id=r.object_id"):
        record = dict(row)
        record["payload"] = json.loads(record["payload"])
        revisions[record["id"]] = record
    heads = {r["id"]: revisions[r["current_revision"]] for r in db.execute("SELECT * FROM objects")}
    db.close()

    def lookup(ref, kinds):
        row = revisions[ref["revision_id"]]
        require(row["object_id"] == ref["object_id"] and row["kind"] in kinds, "invalid exact reference")
        return row

    def reference(row):
        return {"object_id": row["object_id"], "revision_id": row["id"]}

    recipes = json.loads((ROOT / "production/full-generation/recipes.json").read_text())
    qa = json.loads((ROOT / "production/full-generation/representative-review.json").read_text())["items"]
    require(len(recipes["images"]) == 251 and len(recipes["voices"]) == 42, "locked scope changed")
    all_recipes = recipes["images"] + recipes["voices"] + recipes["withdrawn_images"]
    by = {x["id"]: x for x in all_recipes}
    require(len(by) == len(all_recipes), "duplicate recipe")
    image_ids = {x["id"] for x in recipes["images"]}
    voice_ids = {x["id"] for x in recipes["voices"]}
    require(len({i["id"] for i in qa}) == len(qa), "duplicate original in review")
    qualified = {i: [] for i in image_ids}
    calls, voices, native, seconds, sizes = [], set(), 0, 0.0, Counter()
    for item in qa:
        label = item["id"]
        asset, call = heads["asset-" + label], heads["call-" + label]
        payload = asset["payload"]
        require(call["payload"]["status"] == "completed", "original lacks completed call: " + label)
        require(reference(asset) in call["payload"]["outputs"], "call output differs: " + label)
        original = next(c for c in payload["components"] if c["id"] == "original")
        require(original["sha256"] == item["sha256"] == digest(ROOT / item["file"]), "original mismatch: " + label)
        for component in payload["components"]:
            require(manifest["files"]["assets/" + component["file"]] == component["sha256"],
                    "asset component absent from full export: " + label)
        x = by[item["recipe_id"]]
        require(payload["states"] == ([x["state"]] if item["media_type"] == "image" else x["coverage"]),
                "state association differs: " + label)
        require(reference(call) in x["execution"]["actual_calls"] and
                reference(asset) in x["execution"]["actual_assets"], "recipe call link missing: " + label)
        request = json.loads((ROOT / "production/requests" / (label + ".json")).read_text())
        if request.get("tool") == "image_gen.imagegen":
            plan = lookup(request["requirement"], {"REQUIREMENT"})["payload"]["generation"]
            validate_builtin_plan(plan, request)
            refs = [i["reference"] for i in request.get("references", [])]
            validate_reference_authorization(lookup, request, refs, [request["state"]], request["entity"], "image")
            receipt = json.loads((ROOT / "production/receipts" / (label + "-builtin-complete.json")).read_text())
            require(receipt["request_file_sha256"] == digest(ROOT / "production/requests" / (label + ".json")),
                    "actual request changed: " + label)
            require(receipt["sha256"] == item["sha256"] and
                    (receipt["width"], receipt["height"]) == (item["width"], item["height"]),
                    "native image receipt differs: " + label)
            native += 1
        if item["media_type"] == "image":
            lineage = payload["lineage"]
            parents = [lookup(ref, {"ASSET"}) for ref in lineage.get("references", [])]
            expected_depth = 1 + max(p["payload"]["lineage"]["i2i_depth"] for p in parents) if parents else 0
            require(lineage["i2i_depth"] == expected_depth <= 2, "lineage depth invalid: " + label)
            sizes[f'{item["width"]}x{item["height"]}'] += 1
            if item["recipe_id"] in image_ids and item.get("in_current_scope", True) and item["self_review_status"] in PASS:
                qualified[item["recipe_id"]].append({"asset": reference(asset), "file": item["file"],
                                                     "sha256": item["sha256"]})
        else:
            require(item["recipe_id"] in voice_ids, "unlocked voice")
            with wave.open(str(ROOT / item["file"]), "rb") as audio:
                require((audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (48000, 2, 2),
                        "voice specification differs")
                seconds += audio.getnframes() / audio.getframerate()
            voices.add(item["recipe_id"])
        calls.append(reference(call))
    missing = sorted(k for k, v in qualified.items() if not v)
    require(allow_incomplete or not missing, "unqualified image states: " + ", ".join(missing))
    require(voices == voice_ids, "new voice originals incomplete")
    task_calls = [r for r in heads.values() if r["kind"] == "CALL" and
                  (r["object_id"].startswith("call-fg3-") or r["payload"].get("task") == TASK)]
    failures = [r for r in task_calls if r["payload"]["status"] == "failed"]
    require(len(failures) == 4, "input rejection count changed")
    for row in failures:
        require(not row["payload"]["outputs"] and len(row["payload"]["components"]) == 2,
                "failed call has fabricated output")
        require(any(reference(row) in x["execution"]["actual_calls"] for x in all_recipes),
                "failed call missing from recipes")
    require(len(task_calls) == len(calls) + len(failures), "unresolved or unlisted task call")
    accepted_audio = [i for i in qa if i["media_type"] == "audio" and i.get("user_accepted")]
    require(all(i.get("listener") == "user" and i.get("listening_evidence") for i in accepted_audio),
            "listening approval lacks actual listener evidence")
    return {
        "format": "full-generation-delivery-verification-v1",
        "task": TASK, "all_business_tables_equal": True,
        "new_originals_and_completed_calls_verified": len(calls),
        "images": sum(sizes.values()), "qualified_image_states": len(qualified) - len(missing),
        "locked_image_states": 251, "missing_or_unqualified_image_states": missing,
        "input_validation_failures_verified": len(failures),
        "builtin_calls_with_exact_plan_and_authorized_lineage": native,
        "image_native_dimensions": dict(sorted(sizes.items())),
        "new_voice_originals": len(voices), "audio_seconds": round(seconds, 2),
        "audio_specification": "48000 Hz stereo PCM16 WAV",
        "voice_state_associations": sum(len(x["coverage"]) for x in recipes["voices"]),
        "user_listened_and_accepted": len(accepted_audio),
        "user_listening_pending": len(voices) - len(accepted_audio),
        "restored_production_files_sha256_verified": len(replay["files"]),
        "full_manifest_files_verified": len(manifest["files"]),
        "old_comments_preserved": len(old["comments"]), "total_comments": len(source["comments"]),
        "ui_verification": "separate actual browser evidence; checksum equality is not page acceptance",
        "user_acceptance_or_shot_adoption_inferred": False,
        "qualified_originals_by_state": dict(sorted(qualified.items()))
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("snapshot", "restored", "baseline", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    result = audit(args.snapshot, args.restored, args.baseline, args.allow_incomplete)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "qualified_originals_by_state"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
