"""Verify this story's complete screenplay, preservation and empty-store restore.

Run with PYTHONPATH pointing at the selected review-desk checkout. No formal
database writes: --baseline is opened read-only; the candidate is this instance.
"""
import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from urllib.request import urlopen

from review_desk.bundle import export, restore
from review_desk.screenplay import snapshot, validate_document
from review_desk.store import Store


def verify(root, baseline, url=None):
    document = json.loads((root / "imports/screenplay-01.json").read_text())
    store = Store(root / ".runtime/review.sqlite3")
    try:
        validate_document(store, document)
        versions = snapshot(store)["versions"]
        version = next(v for v in versions if v["object_id"] == document["id"])
        assert len(version["episodes"]) == len(document["episodes"]) == 17
        chapters, seconds, scenes = set(), 0, 0
        for episode, actual in zip(document["episodes"], version["episodes"]):
            assert all(actual["payload"][key] == value for key, value in episode.items())
            assert 180 <= episode["estimated_seconds"] <= 300
            seconds += episode["estimated_seconds"]
            scenes += len(episode["scenes"])
            chapters.update(episode["source_chapters"])
        assert chapters == {f"novel-c{i:02d}" for i in range(1, 11)}
        assert all(c["anchor_state"]["valid"] for c in store.context())
        kept = {}
        with sqlite3.connect(f"file:{baseline / '.runtime/review.sqlite3'}?mode=ro", uri=True) as original:
            for table in ("sources", "comments", "comment_events", "objects", "revisions", "dependencies", "configurations", "configuration_events"):
                before = original.execute("SELECT * FROM " + table).fetchall()
                after = {tuple(row) for row in store.db.execute("SELECT * FROM " + table).fetchall()}
                assert set(before) <= after, "baseline changed or missing: " + table
                if table not in ("objects", "revisions", "dependencies"):
                    assert len(before) == len(after), "unexpected mutation: " + table
                kept[table] = len(before)
            for key in ("story", "structure"):
                ref = document["basis"][key]
                row = original.execute("SELECT current_revision FROM objects WHERE id=?", (ref["object_id"],)).fetchone()
                assert row and row[0] == ref["revision_id"], "formal input changed: " + key
        # The generic bundle must preserve exact bytes, including old comments.
        with tempfile.TemporaryDirectory(prefix="screenplay-restore-") as directory:
            temp = Path(directory)
            out = temp / "export"; out.mkdir()
            (out / "assets").symlink_to(root / "export/assets", target_is_directory=True)
            recovered = Store(temp / ".runtime/review.sqlite3")
            try:
                restore(recovered, root / "export")
                assert snapshot(recovered) == snapshot(store)
                assert recovered.comments() == store.comments()
                assert recovered.events() == store.events()
                assert all(c["anchor_state"]["valid"] for c in recovered.context())
                export(recovered, out)
                files = list(json.loads((root / "export/manifest.json").read_text())["files"]) + ["manifest.json"]
                assert all((out / name).read_bytes() == (root / "export" / name).read_bytes() for name in files)
            finally:
                recovered.close()
        if url:
            with urlopen(url.rstrip("/") + "/api/screenplays") as response:
                assert json.load(response) == snapshot(store)
        return {"passed": True, "screenplay_id": document["id"], "revision": version["id"],
                "input_sha256": hashlib.sha256((root / "imports/screenplay-01.json").read_bytes()).hexdigest(),
                "episodes": 17, "scenes": scenes, "estimated_seconds": seconds,
                "duration_is_measured": False, "covered_chapters": sorted(chapters),
                "baseline_rows_preserved": kept, "restored_files_equal": len(files),
                "comments_with_valid_anchors": len(store.comments()), "api_equal": bool(url),
                "basis": document["basis"]}
    finally:
        store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, default=Path("."))
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--url")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.instance.resolve(), args.baseline.resolve(), args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
