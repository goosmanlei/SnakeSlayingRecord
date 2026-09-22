"""Build the review-desk import for the first clean story refinement."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_PATH = ROOT / "imports" / "story-refinement-01-clean.md"
IMPORT_PATH = ROOT / "imports" / "story-refinement-01.json"


def blocks_from_markdown(text):
    chunks = re.split(r"^## (.+)$", text, flags=re.M)
    headings = 11
    if len(chunks) != 1 + headings * 2:
        raise ValueError(f"expected {headings} sections, got {(len(chunks) - 1) // 2}")
    identifiers = ["overview", *(f"s{i}" for i in range(1, 9)), "characters", "plan"]
    blocks = []
    for index, block_id in enumerate(identifiers):
        heading, body = chunks[1 + 2 * index], chunks[2 + 2 * index]
        paragraphs = [part.strip().replace("\n", "") for part in body.strip().split("\n\n")]
        if not all(paragraphs):
            raise ValueError("empty paragraph")
        blocks.append({"id": f"r01-{block_id}", "text": heading + "\n" + "\n\n".join(paragraphs)})
    return blocks


document = {
    "id": "refinement-01-lantern-home-v1",
    "title": "故事精修一：《把灯带回家》第一版",
    "version_type": "本项目原创·故事精修第一版",
    "origin": "基于扩写方向三《把灯带回家》及截至2026-09-23的十条当前审阅评论独立重构",
    "source_url": "https://github.com/goosmanlei/SnakeSlayingRecord",
    "collected_at": "2026-09-23",
    "notes": "独立、完整、无修订痕迹的第一版精修稿；不覆盖扩写方向三原稿，供下一轮审阅。",
    "group": "story-refinements",
    "order": 1,
    "text_heading": "故事精修第一版 · 把灯带回家",
    "blocks": blocks_from_markdown(MARKDOWN_PATH.read_text()),
    "assets": [],
}

IMPORT_PATH.write_text(json.dumps([document], ensure_ascii=False, indent=2) + "\n")
