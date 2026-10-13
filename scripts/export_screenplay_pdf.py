#!/usr/bin/env python3
"""Render a published screenplay's clean Markdown without rewriting its content.

Requires reportlab. Run from the project root; pass a Chinese TrueType font
available on the host. Temporary output is replaced only after a valid build.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak, Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents


class ScriptDocument(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        if flowable.style.name in ('Episode', 'Scene'):
            title = flowable.getPlainText()
            key = 'section-' + hashlib.sha256(title.encode()).hexdigest()[:20]
            self.canv.bookmarkPage(key)
            level = 0 if flowable.style.name == 'Episode' else 1
            self.canv.addOutlineEntry(title, key, level=level)
            if level == 0:
                self.notify('TOCEntry', (0, title, self.page, key))


def paragraph_text(text, size, width=A4[0] - 110):
    """Preserve text and avoid Chinese closing punctuation at line starts."""
    lines = []
    for original in text.splitlines():
        remaining = original
        while remaining:
            end, used = 0, 0
            for character in remaining:
                advance = pdfmetrics.stringWidth(character, 'ScriptChinese', size)
                if used + advance > width - 1:
                    break
                used += advance
                end += 1
            end = max(1, end)
            while end > 1 and end < len(remaining) and (
                remaining[end] in '，。！？；：、）】》”’…—'
                or remaining[end - 1] in '（【《“‘'
            ):
                end -= 1
            lines.append(escape(remaining[:end]))
            remaining = remaining[end:]
    return '<br/>'.join(lines)


def build(source, output, font_path, export_date):
    raw = source.read_text(encoding='utf-8')
    font = TTFont('ScriptChinese', str(font_path), subfontIndex=0)
    pdfmetrics.registerFont(font)
    missing = sorted({c for c in raw if not c.isspace() and ord(c) not in font.face.charToGlyph})
    if missing:
        raise ValueError('Font lacks characters: ' + ''.join(missing))
    common = dict(fontName='ScriptChinese', wordWrap='CJK', textColor=colors.HexColor('#222222'))
    styles = {
        'body': ParagraphStyle('Body', fontSize=11, leading=18, spaceAfter=8,
                               allowWidows=0, allowOrphans=0, **common),
        'meta': ParagraphStyle('Metadata', fontSize=9.5, leading=16, spaceAfter=12,
                               keepWithNext=True, **common),
        'episode': ParagraphStyle('Episode', fontSize=21, leading=30, spaceAfter=16,
                                  keepWithNext=True, **common),
        'contents': ParagraphStyle('ContentsTitle', fontSize=21, leading=30, spaceAfter=16,
                                   keepWithNext=True, **common),
        'scene': ParagraphStyle('Scene', fontSize=14, leading=21, spaceBefore=18,
                                spaceAfter=8, keepWithNext=True, **common),
        'cover': ParagraphStyle('Cover', fontSize=29, leading=42, spaceAfter=24,
                                alignment=1, **common),
        'center': ParagraphStyle('Center', fontSize=13, leading=22, spaceAfter=16,
                                 alignment=1, **common),
        'toc': ParagraphStyle('ContentsEntry', fontSize=11, leading=24,
                              leftIndent=0, rightIndent=20, **common),
    }
    blocks = re.split(r'\n\s*\n', raw.strip())
    title = blocks[0].removeprefix('# ')
    version = blocks[1]
    first_episode = next(i for i, b in enumerate(blocks) if b.startswith('## '))
    story = [Spacer(1, 110), Paragraph(escape(title), styles['cover']),
             Paragraph(escape(version), styles['center']),
             Paragraph('导出日期：' + export_date, styles['center']), Spacer(1, 42)]
    for block in blocks[2:first_episode]:
        story.append(Paragraph(paragraph_text(block, 11), styles['body']))
    story += [PageBreak(), Paragraph('分集目录', styles['contents'])]
    toc = TableOfContents()
    toc.levelStyles = [styles['toc']]
    story += [toc]
    for block in blocks[first_episode:]:
        if block.startswith('## '):
            story += [PageBreak(), Paragraph(escape(block[3:]), styles['episode'])]
        elif block.startswith('### '):
            story.append(Paragraph(escape(block[4:]), styles['scene']))
        else:
            is_meta = block.startswith('预计正片') or '｜' in block
            story.append(Paragraph(paragraph_text(block, 9.5 if is_meta else 11),
                                   styles['meta' if is_meta else 'body']))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.partial.pdf')
    doc = ScriptDocument(str(temporary), pagesize=A4, leftMargin=55, rightMargin=55,
                         topMargin=48, bottomMargin=48,
                         title=title + ' · ' + version, author='李寄斩蛇 · 把灯带回家')

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('ScriptChinese', 9)
        canvas.setFillColor(colors.HexColor('#777777'))
        canvas.drawCentredString(A4[0] / 2, 26, str(document.page))
        canvas.restoreState()

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='script', frames=frame, onPage=footer))
    doc.multiBuild(story)
    if not temporary.read_bytes().startswith(b'%PDF-'):
        raise ValueError('Build did not produce a PDF')
    temporary.replace(output)
    print(json.dumps({'output': str(output), 'source': str(source),
                      'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--date', default=date.today().isoformat())
    args = parser.parse_args()
    build(args.source, args.output, args.font, args.date)
