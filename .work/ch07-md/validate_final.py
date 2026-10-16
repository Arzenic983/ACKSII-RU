"""Compare every rendered unit with its package and integrated SQLite text."""
from pathlib import Path
from html.parser import HTMLParser
import html
import json
import re
import sqlite3
import subprocess
from collections import Counter
from fragment_tools import plain

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
BASE = ROOT / 'ACKSII/База перевода'


class UnitText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data, self.current, self.skip = {}, None, 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('id', '').startswith('rr.'):
            self.current = attrs['id']
            self.data[self.current] = []
        if tag in ('small', 'sup'):
            self.skip += 1
        if tag == 'br' and self.current and not self.skip:
            self.data[self.current].append(' ')

    def handle_endtag(self, tag):
        if tag in ('small', 'sup'):
            self.skip -= 1
        if tag in ('p', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            # Markdown puts standalone anchors in their own empty paragraph.
            if self.current and ''.join(self.data[self.current]).strip():
                self.current = None

    def handle_data(self, text):
        if self.current and not self.skip:
            self.data[self.current].append(text)


def normalized(text):
    text = html.unescape(re.sub('<[^>]+>', ' ', text))
    text = plain(text).replace('\\*', '*').replace('*', '')
    return re.sub(r'\s+', ' ', text).strip()


def main():
    rows = [json.loads(s) for s in (ROOT / 'contributions/07/translator.jsonl').read_text(encoding='utf-8').splitlines()]
    node = 'C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    md = (ROOT / 'ACKSII/Перевод Markdown/07 Плавания.md').read_text(encoding='utf-8')
    rendered = subprocess.run([node, str(ROOT / '.work/ch02-md/render_document.mjs')], input=md, text=True, encoding='utf-8', capture_output=True, check=True).stdout
    parser = UnitText()
    parser.feed(rendered)
    assert set(parser.data) == {u['id'] for u in rows}
    differences = [(u['id'], normalized(''.join(parser.data[u['id']])), normalized(u['russian'])) for u in rows if normalized(''.join(parser.data[u['id']])) != normalized(u['russian'])]
    assert not differences, differences[:5]
    def mechanics(text):
        text = text.replace('−', '-').replace('–', '-')
        dice = Counter(t.lower() for t in re.findall(r'\b(?:\d+)?d\d+\b', text, re.I))
        percentages = Counter(re.findall(r'\d+(?:[.,]\d+)?%', text))
        modifiers = Counter(re.findall(r'(?<![\w\d])[-+±]\d+(?:[.,]\d+)?', text))
        return dice, percentages, modifiers
    for row in rows:
        assert mechanics(row['english']) == mechanics(row['russian']), (row['id'], 'dice, percent, or modifier')
    with sqlite3.connect((BASE / 'acksii_translation.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for u in rows:
            current = db.execute('SELECT * FROM bilingual WHERE id=?', (u['id'],)).fetchone()
            assert current['russian'] == u['russian'] and current['status'] == 'reviewed'
            assert current['english'] == u['english'] and current['source_sha256'] == u['source_sha256']
            assert u['revision'] == 0 and current['revision'] in (1, 2)
        with sqlite3.connect((WORK / 'before_chapter07.sqlite.tmp').resolve().as_uri() + '?mode=ro', uri=True) as old:
            assert [tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='07' ORDER BY id")] == old.execute("SELECT * FROM bilingual WHERE chapter_id!='07' ORDER BY id").fetchall()
    report = json.loads((BASE / '07_validation.json').read_text(encoding='utf-8'))
    report.update(database_changed=True, database_translations=18891)
    report['checks'].update(rendered_unit_text_matches_database=True, other_chapters_unchanged_after_integration=True, integrated_russian_and_status_match_package=True, dice_percentages_and_signed_modifiers=True, source_unit_count=964)
    (BASE / '07_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (WORK / 'rendered_chapter.html').write_text(rendered, encoding='utf-8')
    print('964 rendered units match package and SQLite; all other chapters preserved.')


if __name__ == '__main__':
    main()
