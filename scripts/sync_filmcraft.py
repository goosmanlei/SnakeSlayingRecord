#!/usr/bin/env python3
"""Derive the complete filmcraft page and source catalogue from their sole inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('production/filmcraft')
FILES = ['README.md', '01-narrative.md', '02-coverage.md', '03-cinematography.md',
         '04-camera.md', '05-staging.md', '06-lighting.md', '07-color.md', '08-design.md',
         '09-performance.md', '10-editing.md', '11-sound.md', '12-animation-ai.md',
         'applications.md', 'quick-reference.md', 'sources.md']
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\(([^\s)]+)\)')
SOURCE_KINDS = {
    'creator-interview': '主创访谈', 'foundation-teaching': '基金会教学材料',
    'industry-training': '行业培训资料', 'manufacturer-education': '厂商技术教学',
    'national-film-institution-education': '国家电影机构教学',
    'official-documentation': '官方文档', 'official-guide': '官方指南',
    'official-production-notes': '官方制作手册', 'official-tutorial': '官方教程',
    'official-white-paper': '官方技术白皮书', 'practitioner-essay': '从业者原文',
    'practitioner-teaching': '从业者教学', 'primary-essay': '作者原文',
    'primary-film-observation': '影片原件观察', 'primary-interview': '原始访谈',
    'primary-interview-text-introduction': '原始访谈的文字简介',
    'primary-project-description': '项目官方说明', 'publicity-still': '公开宣传剧照',
    'school-curriculum': '专业院校课程说明', 'school-guide': '专业院校指南',
    'standards-publication-page': '标准发布及正文', 'studio-museum-education': '工作室与博物馆教学',
    'studio-process': '工作室流程说明', 'university-guide': '大学教学材料',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def slug(text):
    return re.sub(r'[^\w\-\s]', '', text.lower()).strip().replace(' ', '-')


def section_id(filename):
    return {'README.md': 'start'}.get(filename, re.sub(r'^\d+-', '', Path(filename).stem))


def anchor_id(section, heading):
    value = slug(heading)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        value = digest(heading.encode())[:12]
    return section + '-' + value


def source_catalog(root):
    sources = []
    for group in ('space', 'light', 'post'):
        value = json.loads((root / BASE / f'sources-{group}.json').read_text())
        sources.extend(value if isinstance(value, list) else value['sources'])
    ids, urls = set(), set()
    lines = ['# 来源与阅读依据', '', '每条记录列出实际读取范围与支持的判断；作者经验、技术事实与本项目推导仍以正文的条件说明为准。', '']
    for source in sources:
        for key in ('id', 'author', 'title', 'url', 'published', 'accessed', 'locator', 'domains', 'supports', 'read_scope', 'kind'):
            if not source.get(key):
                raise ValueError(f'source {source.get("id")} lacks {key}')
        id = source['id']
        if id.lower() in ids:
            raise ValueError('duplicate source identity: ' + id)
        ids.add(id.lower())
        url = source['url'].rstrip('/')
        if url in urls:
            raise ValueError('duplicate source URL: ' + url)
        urls.add(url)
        kind = SOURCE_KINDS.get(source['kind'], source['kind'])
        locator = source['locator'].rstrip('。；. ')
        scope = source['read_scope'].rstrip('。；. ')
        supports = '；'.join(item.rstrip('。；. ') for item in source['supports'])
        href = quote(source['url'], safe=":/?#[]@!$&'*+,;=%~")
        lines += [f'## {id}', '', f'**{source["title"]}** — {source["author"]}。', '',
                  f'发表或适用时间：{source["published"]}；读取时点：{source["accessed"]}。材料类型：{kind}。', '',
                  f'[回查原始材料]({href})。定位：{locator}。', '',
                  f'实际阅读范围：{scope}。', '', f'支持的判断：{supports}。', '']
    return '\n'.join(lines).encode(), sources


def derive(root=ROOT):
    source_raw, sources = source_catalog(root)
    docs = {name: source_raw if name == 'sources.md' else (root / BASE / name).read_bytes() for name in FILES}
    anchors = {}
    for name, raw in docs.items():
        lines = raw.decode().splitlines()
        if not lines or not lines[0].startswith('# '):
            raise ValueError('document needs one title: ' + name)
        section = section_id(name)
        anchors[(name, '')] = section
        for line in lines:
            if re.match(r'#{1,3} ', line):
                title = line.split(' ', 1)[1]
                key = (name, slug(title))
                if key in anchors:
                    raise ValueError('duplicate heading: ' + name + ' ' + title)
                anchors[key] = section if line.startswith('# ') else anchor_id(section, title)

    def rewrite(text, name):
        def replace(match):
            label, href = match.groups()
            if href.startswith(('https://', '/?')):
                return match[0]
            url = urlsplit(href)
            target = (root / BASE / (url.path or name)).resolve()
            fragment = unquote(url.fragment).lower()
            if target.parent == (root / BASE).resolve() and target.name in docs:
                key = (target.name, fragment)
                if key not in anchors:
                    raise ValueError(f'unknown local anchor in {name}: {href}')
                return f'[{label}](/?workspace=production.approach&tab=filmcraft#approach-filmcraft-{anchors[key]})'
            if target == (root / 'production/seedance-video-handbook.md').resolve():
                return f'[{label}](/?workspace=production.approach&tab=video-handbook)'
            if target.is_file() and target.is_relative_to(root.resolve()) and not target.is_relative_to(root / '.runtime'):
                return f'[{label}](https://github.com/goosmanlei/SnakeSlayingRecord/blob/main/{target.relative_to(root.resolve()).as_posix()})'
            raise ValueError(f'unknown or unsafe link in {name}: {href}')
        return LINK.sub(replace, text)

    media = {}
    sections = []
    for name, raw in docs.items():
        lines = raw.decode().splitlines()
        section = {'id': section_id(name), 'title': lines[0][2:], 'blocks': []}
        blocks = section['blocks']; i = 1
        while i < len(lines):
            line = lines[i]; i += 1
            if not line.strip(): continue
            if re.match(r'#{2,3} ', line):
                hashes, title = line.split(' ', 1)
                blocks.append({'type': 'heading', 'level': len(hashes) + 1, 'text': rewrite(title, name), 'id': anchor_id(section['id'], title)})
            elif line.startswith('```'):
                code = []; language = line[3:]
                while i < len(lines) and lines[i] != '```': code.append(lines[i]); i += 1
                if i == len(lines): raise ValueError('unclosed code in ' + name)
                i += 1; blocks.append({'type': 'code', 'language': language, 'text': '\n'.join(code)})
            elif match := re.fullmatch(r'!\[([^\]]+)\]\((diagrams/[a-z0-9_-]+\.svg)\)', line):
                caption, path = match.groups(); image = root / BASE / path
                if image.is_symlink() or not image.is_file(): raise ValueError('missing diagram: ' + path)
                image_raw = image.read_bytes(); svg = ET.fromstring(image_raw)
                filename = 'filmcraft-' + image.name
                dimensions = {k: int(svg.attrib[k]) for k in ('width', 'height')}
                media[filename] = image_raw
                blocks.append({'type': 'media', 'kind': 'image', 'file': filename, 'caption': caption, 'sha256': digest(image_raw), **dimensions})
            elif line.startswith('|'):
                def cells(row):
                    if not row.endswith('|') or '\\|' in row: raise ValueError('invalid table in ' + name)
                    return [rewrite(v.strip(), name) for v in row[1:-1].split('|')]
                columns = cells(line)
                if i >= len(lines) or not all(re.fullmatch(r':?-{3,}:?', v) for v in cells(lines[i])): raise ValueError('table separator in ' + name)
                i += 1; rows = []
                while i < len(lines) and lines[i].startswith('|'):
                    row = cells(lines[i]); i += 1
                    if len(row) != len(columns): raise ValueError('table width in ' + name)
                    rows.append(row)
                blocks.append({'type': 'table', 'columns': columns, 'rows': rows})
            elif re.match(r'(?:- |\d+\. )', line):
                ordered = not line.startswith('- '); items = [rewrite(re.sub(r'^(?:- |\d+\. )', '', line), name)]
                pattern = r'\d+\. ' if ordered else r'- '
                while i < len(lines) and re.match(pattern, lines[i]): items.append(rewrite(re.sub(r'^(?:- |\d+\. )', '', lines[i]), name)); i += 1
                blocks.append({'type': 'list', 'ordered': ordered, 'items': items})
            else:
                if line.startswith(('#', '>', '<', '  ')) or '![' in line: raise ValueError('unsupported markup in ' + name + ': ' + line[:60])
                paragraph = [line]
                while i < len(lines) and lines[i].strip() and not re.match(r'(?:#|>|<|```|\||- |\d+\. |  |!\[)', lines[i]): paragraph.append(lines[i]); i += 1
                blocks.append({'type': 'paragraph', 'text': rewrite('\n'.join(paragraph), name)})
        if not blocks: raise ValueError('empty chapter: ' + name)
        sections.append(section)
    inputs = {str(BASE / name): digest(raw) for name, raw in docs.items()}
    for name in ('sources-space.json', 'sources-light.json', 'sources-post.json'):
        inputs[str(BASE / name)] = digest((root / BASE / name).read_bytes())
    for filename, raw in media.items(): inputs[str(BASE / 'diagrams' / filename.removeprefix('filmcraft-'))] = digest(raw)
    tab = {'id': 'filmcraft', 'label': '影视专业知识', 'title': '影视专业知识',
           'lead': '从叙事目的理解镜头、空间、光色、表演与声画，再把选择转化为二维漫剧的制作与检查。',
           'source': {'path': BASE.as_posix(), 'sha256': digest(json.dumps(inputs, sort_keys=True).encode()), 'files': inputs},
           'sections': sections}
    return tab, source_raw, media, sources


def synchronize(root=ROOT, check=False):
    tab, sources_raw, media, sources = derive(root)
    path = root / 'content/production-approach.json'
    original = json.loads(path.read_text())
    tabs = [tab if t['id'] == 'filmcraft' else t for t in original['tabs']]
    if not any(t['id'] == 'filmcraft' for t in original['tabs']): tabs.append(tab)
    updated = {**original, 'schema_version': 2, 'tabs': tabs}
    expected = {root / BASE / 'sources.md': sources_raw,
                **{root / 'content/production-approach-assets' / k: v for k, v in media.items()}}
    if check:
        if original != updated: raise ValueError('filmcraft reading copy is stale')
        for target, raw in expected.items():
            if not target.is_file() or target.read_bytes() != raw: raise ValueError('missing or stale derived file: ' + str(target))
    else:
        for target, raw in expected.items(): target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'consistent' if check else 'updated', 'chapters': len(tab['sections']), 'sources': len(sources), 'diagrams': len(media)}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true')
    synchronize(check=parser.parse_args().check)
