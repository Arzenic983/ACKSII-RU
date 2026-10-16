"""Build the compact reading copy from the complete bilingual chapter files."""
from collections import Counter
from html import escape
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'ACKSII/Перевод Markdown'
TARGET = OUT / 'ACKS II — Начало и главы 1–4.md'
INPUTS = [OUT / name for name in ('00 Начало.md', '01 Персонажи.md', '02 Классы.md', '03 Навыки.md', '04 Снаряжение.md')]
LAST_PAGE = 179
EXPECTED_NOTES = 156
EXPECTED_TABLES = 151
NODE = os.environ.get('ACKS_NODE') or shutil.which('node') or 'node'
RENDER = ROOT / '.work/ch02-md/render_document.mjs'

PAGE = re.compile(
    r'<a id="pdf-page-(\d{4})"></a>\s*'
    r'## PDF-страница (\d+)(?: · печатная стр\. (\d+))?\s*'
    r'\[Английский оригинал: PDF-страница \d+\]\([^\n]+\)\s*'
)
REDUNDANT_HEADINGS = {
    9: ('Введение', 'INTRODUCTION'),
    15: ('Персонажи', 'CHARACTERS'),
    25: ('Классы', 'CLASSES'),
    103: ('Навыки', 'PROFICIENCIES'),
    125: ('Снаряжение', 'EQUIPMENT'),
}


def clean(text):
    # Remove extraction metadata, retaining every substantive editorial comment.
    text = re.sub(r'<!-- (?:unit:|table:)[^>]*-->\s*', '', text)
    text = re.sub(r'<a id="rr\.[^"]+"></a>\s*', '', text)
    text = re.sub(r' id="rr\.[^"]+"', '', text)
    text = re.sub(r'`rr\.p\d{4}\.t\d{2}\.r\d{3}\.c\d{2}` — ', '', text)
    text = re.sub(r'`rr\.p(\d{4})[^`]*`', lambda m: 'PDF ' + str(int(m[1])), text)
    text = text.replace('<!-- Original page contains illustration only; no source translation units. -->', '')
    text = text.replace('<!-- На этой странице нет текстовых единиц подготовленного исходника. -->', '')
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def notes(text):
    return [clean(line) for line in text.splitlines() if line.startswith('> ')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.pages = []
        self.pdf_links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'p' and attrs.get('id', '').startswith('pdf-page-'):
            assert attrs.get('align') == 'right'
            self.pages.append(int(attrs['id'].removeprefix('pdf-page-')))
        if tag == 'a' and '#page=' in attrs.get('href', ''):
            self.pdf_links.append(int(attrs['href'].split('#page=')[1]))
        if tag == 'table':
            self.table = []
            self.tables.append(self.table)
        if tag == 'tr':
            self.row = []
            self.table.append(self.row)
        if tag in ('td', 'th'):
            self.row.append((int(attrs.get('rowspan', 1)), int(attrs.get('colspan', 1))))


def main():
    protected = {str(p.relative_to(ROOT)): sha(p) for p in INPUTS}
    for p in (ROOT / 'ACKSII').rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.sqlite', '.docx', '.pdf'):
            protected[str(p.relative_to(ROOT))] = sha(p)
    sources = [p.read_text('utf-8') for p in INPUTS]
    source = '\n\n'.join(sources)
    all_notes = notes(source)
    matches = list(PAGE.finditer(source))
    assert [int(m[1]) for m in matches] == list(range(1, LAST_PAGE + 1))
    cover_note = next(line for line in all_notes if 'На обложке оригинала указано 18 классов' in line)
    parts = ['# ACKS II — Начало и главы 1–4\n\n<small>ACKS II — FRONT MATTER AND CHAPTERS 1–4</small>']
    expected_bodies = []
    original_headings = []
    retained_subtitles = []
    for index, match in enumerate(matches):
        page = int(match[1])
        if page < 5:
            continue  # Covers, advertising, price, credits and publishing details.
        body = source[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(source)]
        # Synthetic chapter wrappers sit at the end of the preceding PDF page.
        body = re.split(r'\n# Глава [1234]\. ', body, maxsplit=1)[0]
        body = re.sub(r'\n---\s*$', '', body)
        body = clean(body)
        if page in REDUNDANT_HEADINGS:
            russian, english = REDUNDANT_HEADINGS[page]
            repeated = f'### {russian}\n\n<small>{english}</small>'
            assert repeated in body
            body = body.replace(repeated, '', 1).strip()
        expected_bodies.append(body)
        original_headings.extend(re.findall(r'^#{1,6} (.*)$', body, re.M))
        retained_subtitles.extend(re.findall(r'<small>(.*?)</small>', body, re.S))
        body = re.sub(r'^(#{3,6}) ', lambda m: m[1][1:] + ' ', body, flags=re.M)
        for russian, english, new_russian, new_english in (
            ('Введение', 'INTRODUCTION', 'Введение', 'INTRODUCTION'),
            ('1 Персонажи', '1 CHARACTERS', 'Глава 1. Персонажи', 'CHAPTER 1: CHARACTERS'),
            ('2 Классы', '2 CLASSES', 'Глава 2. Классы', 'CHAPTER 2: CLASSES'),
            ('3 Навыки', '3 PROFICIENCIES', 'Глава 3. Навыки', 'CHAPTER 3: PROFICIENCIES'),
            ('4. Снаряжение', '4 EQUIPMENT', 'Глава 4. Снаряжение', 'CHAPTER 4: EQUIPMENT'),
        ):
            old = f'## {russian}\n\n<small>{english}</small>'
            if page in (8, 14, 24, 102, 124) and old in body:
                body = body.replace(old, f'# {new_russian}\n\n<small>{new_english}</small>', 1)
        if page == 25:
            paragraph = re.search(r'^В \*\*\*Adventurer Conqueror King System\*\*\*[^\n]+', body, re.M)
            assert paragraph
            at = paragraph.end()
            body = body[:at] + '<sup>*</sup>\n\n' + cover_note + body[at:]
        title = f'Страница PDF {page}'
        if match[3]:
            title += f' · печатная стр. {match[3]}'
        marker = (
            f'<p align="right" id="pdf-page-{page:04d}"><small>'
            f'<a href="../Source/ACKSII%20Revised%20Rulebook.pdf#page={page}" '
            f'title="{escape(title)}">страница {page}</a></small></p>'
        )
        parts.append(marker + ('\n\n' + body if body else ''))
    result = parts[0] + '\n\n' + '\n\n---\n\n'.join(parts[1:]) + '\n'
    expected = '\n\n'.join(expected_bodies)
    # Explicitly prove preservation of all notes, tables and bilingual content.
    assert Counter(notes(result)) == Counter(all_notes), 'Editorial note lost or changed'
    assert len(all_notes) == EXPECTED_NOTES
    # Markdown tables and HTML tables are compared individually, including their full cell text.
    html_tables = lambda text: re.findall(r'<table(?: [^>]*)?>.*?</table>', text, re.S)
    md_tables = lambda text: re.findall(r'^\|[^\n]*(?:\n\|[^\n]*)*', text, re.M)
    assert html_tables(result) == html_tables(expected)
    assert md_tables(result) == md_tables(expected)
    assert result.count('<sup>') == expected.count('<sup>') + 1
    assert len(html_tables(result)) + len(md_tables(result)) == EXPECTED_TABLES
    heading_text = re.findall(r'^#{1,6} (.*)$', result, re.M)[1:]
    expected_headings = [
        {'1 Персонажи': 'Глава 1. Персонажи', '2 Классы': 'Глава 2. Классы', '3 Навыки': 'Глава 3. Навыки', '4. Снаряжение': 'Глава 4. Снаряжение'}.get(h, h)
        for h in original_headings
    ]
    assert heading_text == expected_headings
    expected_small = Counter(retained_subtitles)
    for old, new in (('1 CHARACTERS', 'CHAPTER 1: CHARACTERS'), ('2 CLASSES', 'CHAPTER 2: CLASSES'), ('3 PROFICIENCIES', 'CHAPTER 3: PROFICIENCIES'), ('4 EQUIPMENT', 'CHAPTER 4: EQUIPMENT')):
        expected_small[old] -= 1
        expected_small[new] += 1
    actual_small = Counter(re.findall(r'<small>(.*?)</small>', result, re.S))
    actual_small['ACKS II — FRONT MATTER AND CHAPTERS 1–4'] -= 1
    for page in range(5, LAST_PAGE + 1):
        link = re.search(rf'<small>(<a href="[^\n]+#page={page}"[^\n]+</a>)</small>', result)
        assert link
        actual_small[link[1]] -= 1
    assert +actual_small == +expected_small
    # Compare the remaining prose in order, independently of heading formatting.
    prose_result = result.split('</small>', 1)[1]
    prose_result = re.sub(r'<p align="right"[^\n]+</p>', '', prose_result)
    prose_result = prose_result.replace(cover_note, '', 1)
    prose_result = re.sub(
        r'(^В \*\*\*Adventurer Conqueror King System\*\*\*[^\n]+)<sup>\*</sup>',
        r'\1', prose_result, count=1, flags=re.M,
    )
    def prose(text):
        text = re.sub(r'^#{1,6} [^\n]+\n\n<small>[^\n]+</small>', '', text, flags=re.M)
        text = re.sub(r'^---\s*$', '', text, flags=re.M)
        return re.sub(r'\s+', ' ', text).strip()
    assert prose(prose_result) == prose(expected), 'Rule text changed'
    assert not re.search(r'<!-- (?:unit:|table:)|`rr\.|## PDF-страница|Рекомендованная розничная цена|SKU:|ISBN:', result)
    rendered = subprocess.run([str(NODE), str(RENDER)], input=result, text=True, encoding='utf-8', capture_output=True, check=True).stdout
    before_rendered = subprocess.run([str(NODE), str(RENDER)], input=expected, text=True, encoding='utf-8', capture_output=True, check=True).stdout
    audit, before = Structure(), Structure()
    audit.feed(rendered)
    before.feed(before_rendered)
    assert audit.tables == before.tables
    assert len(audit.tables) == EXPECTED_TABLES
    assert audit.pages == audit.pdf_links == list(range(5, LAST_PAGE + 1))
    assert len(audit.ids) == len(set(audit.ids)) == LAST_PAGE - 4
    for path, old_hash in protected.items():
        assert sha(ROOT / path) == old_hash, 'Protected file changed: ' + path
    TARGET.write_text(result, 'utf-8')
    previous = OUT / 'ACKS II — Начало и главы 1–2.md'
    previous_coverage_unchanged = None
    previous_section = result.split('<p align="right" id="pdf-page-0102">', 1)[0]
    previous_section = re.sub(r'\n---\s*$', '', previous_section).rstrip() + '\n'
    previous_section = previous_section.replace('Начало и главы 1–4', 'Начало и главы 1–2', 1)
    previous_section = previous_section.replace('FRONT MATTER AND CHAPTERS 1–4', 'FRONT MATTER AND CHAPTERS 1–2', 1)
    # Reference is the original compact reader before this chapter was appended.
    # Compare LF-normalized text across Windows CRLF and Unix LF checkouts.
    assert hashlib.sha256(previous_section.encode()).hexdigest() == '4dcc3bae1b13b97eaf6a9f7d58e6297b9aacaf664f766a25960f0da145154cb7'
    previous_coverage_unchanged = True
    if previous.exists():
        old = previous.read_text('utf-8').split('</small>', 1)[1].strip()
        new = result.split('</small>', 1)[1].split('<p align="right" id="pdf-page-0102">', 1)[0]
        new = re.sub(r'\n---\s*$', '', new).strip()
        assert old == new, 'Previously completed reader content changed'
        previous_coverage_unchanged = True
    previous3 = result.split('<p align="right" id="pdf-page-0124">', 1)[0]
    previous3 = re.sub(r'\n---\s*$', '', previous3).rstrip() + '\n'
    previous3 = previous3.replace('Начало и главы 1–4', 'Начало и главы 1–3', 1).replace('FRONT MATTER AND CHAPTERS 1–4', 'FRONT MATTER AND CHAPTERS 1–3', 1)
    baseline = json.loads((ROOT/'.work/ch04-md/baseline.json').read_text('utf-8'))
    assert hashlib.sha256(previous3.encode()).hexdigest() == baseline['previous_reader_sha256_normalized_newlines']
    css = 'body{font:17px Georgia,serif;max-width:1080px;margin:32px auto;padding:0 24px;line-height:1.5}h1,h2,h3{line-height:1.2;margin-bottom:.25em}h1+ p:has(small),h2+ p:has(small),h3+ p:has(small){margin-top:0;color:#666}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bbb;padding:5px}th{background:#f3f3f3}blockquote{border-left:3px solid #bbb;margin-left:0;padding-left:12px;color:#555;font-size:15px}hr{border:0;border-top:1px solid #ccc;margin:28px 0 4px}p[align=right]{margin:4px 0 18px;font-size:13px}p[align=right] a{color:#777;text-decoration:none}small{font-size:.75em}'
    (HERE / 'preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><base href="../../ACKSII/Перевод%20Markdown/"><title>ACKS II — главы 1–4</title><style>' + css + '</style><body>' + rendered + '</body></html>', 'utf-8')
    report = {
        'date': '2026-10-16', 'target': str(TARGET.relative_to(ROOT)),
        'pdf_pages': [5, LAST_PAGE], 'compact_page_markers': LAST_PAGE - 4,
        'all_editorial_notes_preserved': len(all_notes),
        'cover_note_relocated_to_pdf_page': 25,
        'tables_preserved_verbatim_after_metadata_removal': EXPECTED_TABLES,
        'rendered_table_geometry_preserved': True,
        'bilingual_headings_and_table_subtitles_preserved': True,
        'rule_text_preserved_in_order': True,
        'protected_files_unchanged': True,
        'previous_reader_pages_5_101_unchanged': previous_coverage_unchanged,
        'previous_reader_pages_5_123_unchanged': True,
        'previous_reader_1_3_sha256_normalized_newlines': hashlib.sha256(previous3.encode()).hexdigest(),
        'previous_reader_sha256_normalized_newlines': hashlib.sha256(previous_section.encode()).hexdigest(),
        'bytes': TARGET.stat().st_size, 'sha256': sha(TARGET),
    }
    (HERE / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    (ROOT / 'ACKSII/База перевода/reading_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
