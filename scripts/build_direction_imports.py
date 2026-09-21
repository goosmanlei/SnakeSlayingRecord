"""Build review-desk JSON imports from the clean, human-readable stories."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def blocks_from_markdown(text, prefix):
    chunks = re.split(r"^## (.+)$", text, flags=re.M)
    if len(chunks) != 21:
        raise ValueError(f"expected 10 sections, got {(len(chunks) - 1) // 2}")
    blocks = []
    identifiers = ["overview", *(f"s{i}" for i in range(1, 8)), "characters", "plan"]
    for index, block_id in enumerate(identifiers):
        heading, body = chunks[1 + 2 * index], chunks[2 + 2 * index]
        paragraphs = [part.strip().replace("\n", "") for part in body.strip().split("\n\n")]
        if not all(paragraphs):
            raise ValueError("empty paragraph")
        blocks.append({"id": f"{prefix}-{block_id}", "text": heading + "\n" + "\n\n".join(paragraphs)})
    return blocks


for number in (1, 2, 3):
    prefix = f"d{number:02d}"
    source_path = ROOT / "imports" / f"task-0002-direction-{number:02d}.json"
    markdown_path = ROOT / "imports" / f"direction-{number:02d}-clean.md"
    data = json.loads(source_path.read_text())
    if len(data) != 1:
        raise ValueError("expected one direction per import")
    source = data[0]
    source["blocks"] = blocks_from_markdown(markdown_path.read_text(), prefix)
    source["collected_at"] = "2026-09-22"
    source["notes"] = "本项目原创完整扩写；七场连续正文，前有故事概览与主题，后有人物说明和25分钟制作规划。"
    source_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
