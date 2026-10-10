#!/usr/bin/env python3
"""Derive the first approach tab from the sole vision Markdown source."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from sync_video_handbook import derive as derive_markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('production/system-vision.md')
DESTINATION = Path('content/production-approach.json')
SECTION_IDS = ('practice', 'review-desk', 'methods', 'delivery')


def derive(raw):
    # The approved source stays byte-for-byte intact. Stable reading anchors are
    # supplied to the existing Schema 2 Markdown converter, not added to prose.
    lines, count, layout = [], 0, None
    for line in raw.decode('utf-8').splitlines():
        if line.startswith('<!-- layout: '):
            if layout is not None:
                raise ValueError('duplicate vision layout')
            match = re.fullmatch(r'<!-- layout: (.+) -->', line)
            layout = json.loads(match[1]) if match else None
            if not isinstance(layout, dict) or set(layout) != {'type', 'return_label'} or layout['type'] != 'cycle' or not isinstance(layout['return_label'], str) or not layout['return_label'].strip():
                raise ValueError('invalid vision cycle layout')
            continue
        if line.startswith('## '):
            if count == len(SECTION_IDS):
                raise ValueError('vision sections changed; assign their stable reading anchors')
            lines.append('<!-- section: ' + SECTION_IDS[count] + ' -->')
            count += 1
        lines.append(line)
    if count != len(SECTION_IDS):
        raise ValueError('vision sections changed; preserve or revise their reading anchors')
    tab = derive_markdown(('\n'.join(lines) + '\n').encode(), root=ROOT)
    return {**tab, 'id': 'vision', 'label': tab['title'],
            **({'layout': layout} if layout else {}),
            'source': {'path': SOURCE.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()}}


def update(value, raw):
    return {**value, 'schema_version': 2,
            'tabs': [derive(raw)] + [tab for tab in value['tabs'] if tab['id'] != 'vision']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / DESTINATION
    value = json.loads(path.read_text())
    expected = update(value, (ROOT / SOURCE).read_bytes())
    if args.check:
        if value != expected:
            raise SystemExit('vision reading copy is stale; run scripts/sync_system_vision.py')
        print('vision source and first reading tab match')
    else:
        path.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n')
        print('updated first vision tab; all existing tabs preserved')


if __name__ == '__main__':
    main()
