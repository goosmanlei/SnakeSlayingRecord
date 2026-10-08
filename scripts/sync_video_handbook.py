#!/usr/bin/env python3
"""Derive the reading page from the sole handbook source; never rewrite other tabs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import mimetypes

MEDIA_DIRECTORY = Path('content/production-approach-assets')
MEDIA_MANIFEST = Path('production/seedance-handbook/demos/manifest.json')
MEDIA_LINK = re.compile(r'(!?)\[([^\]]+)\]\(\.\./content/production-approach-assets/([a-z0-9][a-z0-9._-]*)\)')

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("production/seedance-video-handbook.md")
DESTINATION = Path("content/production-approach.json")
TAB = "video-handbook"


def derive(raw, root=ROOT):
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("handbook needs one title")
    title, lead, sections, current, pending = lines[0][2:], None, [], None, None
    i = 1
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        anchor = re.fullmatch(r"<!-- section: ?([a-z0-9]+(?:-[a-z0-9]+)*) -->", line)
        if anchor:
            if pending:
                raise ValueError("section anchor without heading")
            pending = anchor[1]
            continue
        if line.startswith("## "):
            if not pending or any(s["id"] == pending for s in sections):
                raise ValueError("each section needs a unique explicit anchor")
            current = {"id": pending, "title": line[3:], "blocks": []}
            sections.append(current)
            pending = None
            continue
        if pending:
            raise ValueError("section anchor must precede its heading")
        if current is None:
            if lead is not None or line.startswith(("#", "<", "|", "```", "- ")):
                raise ValueError("exactly one introductory paragraph is supported")
            lead = line
            continue
        blocks = current["blocks"]
        media = MEDIA_LINK.fullmatch(line)
        if media:
            filename = media[3]
            path = root / MEDIA_DIRECTORY / filename
            mime = mimetypes.guess_type(filename)[0] or ''
            kind = mime.split('/')[0]
            if kind not in ('image', 'audio', 'video') or path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.webm', '.mp3', '.wav'):
                raise ValueError('unsupported handbook media')
            if bool(media[1]) != (kind == 'image') or path.parent.resolve() != root.resolve() / MEDIA_DIRECTORY or path.is_symlink() or path.parent.is_symlink() or not path.is_file():
                raise ValueError('missing or invalid handbook media')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''): digest.update(chunk)
            block = {'type': 'media', 'kind': kind, 'file': filename, 'caption': media[2], 'sha256': digest.hexdigest()}
            if kind in ('image', 'video'):
                manifest = json.loads((root / MEDIA_MANIFEST).read_text(encoding='utf-8'))
                entries = manifest['images' if kind == 'image' else 'videos']
                matches = [item for item in entries if item['file'] == (MEDIA_DIRECTORY / filename).as_posix()]
                if len(matches) != 1 or matches[0]['sha256'] != block['sha256']:
                    raise ValueError('handbook media metadata differs from original')
                dimensions = matches[0] if kind == 'image' else matches[0]['output']
                for key in ('width', 'height'):
                    if type(dimensions.get(key)) is not int or not 0 < dimensions[key] <= 32768:
                        raise ValueError('handbook media needs accurate positive dimensions')
                    block[key] = dimensions[key]
            blocks.append(block)
        elif line.startswith("```"):
            language = line[3:]
            if not re.fullmatch(r"[a-z0-9-]*", language):
                raise ValueError("unsupported code fence")
            code = []
            while i < len(lines) and lines[i] != "```":
                code.append(lines[i]); i += 1
            if i == len(lines):
                raise ValueError("unclosed code fence")
            i += 1
            blocks.append({"type": "code", "language": language, "text": "\n".join(code)})
        elif re.match(r"#{3,4} ", line):
            prefix, heading = line.split(" ", 1)
            blocks.append({"type": "heading", "level": len(prefix), "text": heading})
        elif line.startswith("|"):
            def cells(row):
                if not row.endswith("|") or "\\|" in row:
                    raise ValueError("tables require outer pipes and no escaped pipes")
                return [cell.strip() for cell in row[1:-1].split("|")]
            columns = cells(line)
            if i >= len(lines) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells(lines[i])):
                raise ValueError("table header separator missing")
            if len(cells(lines[i])) != len(columns):
                raise ValueError("table separator width differs")
            i += 1
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                row = cells(lines[i]); i += 1
                if len(row) != len(columns):
                    raise ValueError("table row width differs")
                rows.append(row)
            blocks.append({"type": "table", "columns": columns, "rows": rows})
        elif re.match(r"(?:- |\d+\. )", line):
            ordered = not line.startswith("- ")
            items = [re.sub(r"^(?:- |\d+\. )", "", line)]
            pattern = r"\d+\. " if ordered else r"- "
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append(re.sub(r"^(?:- |\d+\. )", "", lines[i])); i += 1
            blocks.append({"type": "list", "ordered": ordered, "items": items})
        else:
            if line.startswith(("#", ">", "<", "  ")) or "![" in line:
                raise ValueError("unsupported handbook markup: " + line[:50])
            paragraph = [line]
            while i < len(lines) and lines[i].strip() and not re.match(r"(?:#|<|```|\||- |\d+\. |  )", lines[i]):
                if "![" in lines[i]:
                    raise ValueError("handbook embeds are forbidden")
                paragraph.append(lines[i]); i += 1
            blocks.append({"type": "paragraph", "text": "\n".join(paragraph)})
    if pending or not lead or not sections or any(not s["blocks"] for s in sections):
        raise ValueError("incomplete handbook")
    return {"id": TAB, "label": "视频生成手册", "title": title, "lead": lead,
            "source": {"path": SOURCE.as_posix(), "sha256": hashlib.sha256(raw).hexdigest()},
            "sections": sections}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the reading copy differs")
    args = parser.parse_args()
    tab = derive((ROOT / SOURCE).read_bytes())
    path = ROOT / DESTINATION
    value = json.loads(path.read_text(encoding="utf-8"))
    tabs = [tab if t['id'] == TAB else t for t in value['tabs']]
    if not any(t['id'] == TAB for t in value['tabs']):
        tabs.append(tab)
    expected = {**value, "schema_version": 2, "tabs": tabs}
    if args.check:
        if value != expected:
            raise SystemExit("handbook reading copy is stale; run scripts/sync_video_handbook.py")
        print("handbook source and complete reading copy match")
    else:
        path.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("updated handbook reading copy; other tabs preserved")


if __name__ == "__main__":
    main()
