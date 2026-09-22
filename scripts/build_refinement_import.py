"""Build the existing refinement import from its clean, complete novel."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_PATH = ROOT / "imports" / "story-refinement-01-clean.md"
IMPORT_PATH = ROOT / "imports" / "story-refinement-01.json"


def blocks_from_markdown(text):
    chunks = re.split(r"^## (.+)$", text, flags=re.M)
    if chunks[0].strip() != "# 把灯带回家" or len(chunks) < 3:
        raise ValueError("expected the novel title and chapter headings")
    blocks = []
    for index in range((len(chunks) - 1) // 2):
        heading, body = chunks[1 + 2 * index], chunks[2 + 2 * index]
        if not re.fullmatch(r"第[一二三四五六七八九十百零两\d]+章 .+", heading) or not body.strip():
            raise ValueError("expected a named chapter with non-empty prose")
        blocks.append({"id": f"novel-c{index + 1:02d}", "text": heading + "\n\n" + body.strip()})
    return blocks


document = {
    "id": "refinement-01-lantern-home-v1",
    "title": "故事精修一：《把灯带回家》第一版",
    "version_type": "本项目原创·完本小说",
    "origin": "基于扩写方向三《把灯带回家》及截至2026-09-23的十条当前审阅评论独立重构",
    "source_url": "https://github.com/goosmanlei/SnakeSlayingRecord",
    "collected_at": "2026-09-23",
    "notes": "基于原故事精修逐片段创作并完成全稿修订的小说。正文为完整干净稿，供审阅。",
    "edition": "小说完本稿",
    "group": "story-refinements",
    "order": 1,
    "text_heading": "把灯带回家 · 小说全文",
    "blocks": blocks_from_markdown(MARKDOWN_PATH.read_text()),
    "assets": [],
}

IMPORT_PATH.write_text(json.dumps([document], ensure_ascii=False, indent=2) + "\n")
