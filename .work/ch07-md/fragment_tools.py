"""Build the saved, incomplete chapter 07 fragment; never modify SQLite.

Run rebuild() after adding entries to styled.json. Source snapshots and original
revision values are retained. Only complete source tables are emitted.
"""
import csv
import html
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ACKSII/База перевода'
OUT = ROOT / 'contributions/07'
STYLE = Path(__file__).with_name('styled.json')
MD = ROOT / 'ACKSII/Перевод Markdown/07 Плавания.md'


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = {}
        self.table = self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table':
            assert self.table is None
            self.table = []
            self.tables[attrs['id']] = self.table
        elif tag == 'tr' and self.table is not None:
            self.row = []
            self.table.append(self.row)
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = {'attrs': attrs, 'anchors': []}
            self.row.append(self.cell)
        elif tag == 'a' and self.cell is not None:
            self.cell['anchors'].append(attrs['id'])

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.cell = None
        elif tag == 'tr':
            self.row = None
        elif tag == 'table':
            self.table = None


def plain(text):
    return re.sub(r' ?\[[^\[\]\n]*[A-Za-z#][^\[\]\n]*\]', '', text)


def numbers(text):
    text = re.sub(r'(?<=\d)[, \u00a0](?=\d{3}(?:\D|$))', '', text)
    return [v.replace(',', '.') for v in re.findall(r'\d+(?:[.,]\d+)?', text)]


def add_texts(additions):
    texts = json.loads(STYLE.read_text(encoding='utf-8'))
    assert not set(texts).intersection(additions), 'Existing translations must be reviewed explicitly'
    texts.update(additions)
    STYLE.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rebuild()


def rebuild(allow_revisions=()):
    source = [json.loads(line) for line in (OUT / 'source.jsonl').read_text(encoding='utf-8').splitlines()]
    texts = json.loads(STYLE.read_text(encoding='utf-8'))
    assert set(texts).issubset({u['id'] for u in source})
    assert [u['id'] for u in source[:len(texts)]] == list(texts), 'Fragment must be contiguous'
    rows = [dict(u) for u in source[:len(texts)]]
    metadata = {}
    notes_path = STYLE.with_name('notes.json')
    notes = json.loads(notes_path.read_text(encoding='utf-8')) if notes_path.exists() else {}
    figure_path = STYLE.with_name('figures.json')
    figures = json.loads(figure_path.read_text(encoding='utf-8')) if figure_path.exists() else {}
    old = {u['id']: u for u in (json.loads(line) for line in (OUT / 'translator.jsonl').read_text(encoding='utf-8').splitlines())}
    with sqlite3.connect((BASE / 'acksii_translation.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for u in rows:
            original = dict(db.execute('SELECT * FROM bilingual WHERE id=?', (u['id'],)).fetchone())
            metadata[u['id']] = original
            for key in ('id', 'chapter_id', 'pdf_page', 'printed_page', 'kind', 'english', 'source_sha256'):
                assert u[key] == original[key], (u['id'], key)
            integrated = STYLE.with_name('integration.json').exists()
            expected_revision = json.loads(STYLE.with_name('integration.json').read_text(encoding='utf-8')).get('revisions', {}).get(u['id'], u['revision'] + 1) if integrated else u['revision']
            assert original['revision'] == expected_revision, (u['id'], 'revision')
            if integrated:
                assert original['russian'] == plain(texts[u['id']]), (u['id'], 'integrated text')
            assert hashlib.sha256(u['english'].encode()).hexdigest() == u['source_sha256']
            russian = plain(texts[u['id']])
            assert numbers(u['english']) == numbers(russian), u['id']
            assert u['english'].count('*') == russian.count('*'), (u['id'], 'emphasis')
            assert u['english'].count('\\*') == russian.count('\\*'), (u['id'], 'author note')
            if u['id'] in old:
                assert russian == old[u['id']]['russian'] or u['id'] in allow_revisions, (u['id'], 'previous translation changed')
                u.update({key: old[u['id']][key] for key in ('russian', 'status', 'origin', 'note')})
                if u['id'] in allow_revisions:
                    u['russian'] = russian
                    u['note'] += ' Уточнена формулировка при сверке с оригиналом; см. отчёт главы.'
            else:
                u.update(russian=russian, status='draft', origin='new_translation', note='Продолжение фрагмента главы 7, 2026-10-16. Первичная сверка с английским текстом; новые термины рабочие. См. 07_review.md.')
    following = source[len(rows)]['id'] if len(rows) < len(source) else None
    complete = len(rows) == len(source)
    review_path = STYLE.with_name('semantic_review.json')
    reviewed = review_path.exists() and json.loads(review_path.read_text(encoding='utf-8'))['complete_semantic_review_by_Codex']
    if reviewed:
        assert complete
        for row in rows:
            row['status'] = 'reviewed'
            row['note'] = '\n\n'.join(plain(n) for n in ([notes[row['id']]] if row['id'] in notes else []))
    first_page, last_page = rows[0]['pdf_page'], rows[-1]['pdf_page']
    md = ['# Глава 7. Плавания', '', '<small>CHAPTER 7: VOYAGES</small>', '',
          f'Перевод Revised Rulebook от 16 октября 2026 года. Физические PDF-страницы {first_page}–{last_page}; {len(rows)} из 964 единиц. Статус — ' + ('проверено Codex' if reviewed else 'черновик') + ', без утверждения человеком. Английские подписи относятся к Markdown; пакет для базы содержит русский текст без них.', '']
    page = None
    tables = {}
    for u in rows:
        if u['kind'] == 'table_cell':
            tables.setdefault(metadata[u['id']]['table_id'], []).append(u)
    for table, cells in tables.items():
        assert {u['id'] for u in cells} == {u['id'] for u in source if u['id'].startswith(table + '.')}, (table, 'incomplete table')
    emitted = set()
    geometry = {}
    for u in rows:
        if page != u['pdf_page']:
            page = u['pdf_page']
            md += [f'<a id="pdf-page-{page:04}"></a>', '', f'## PDF-страница {page}' + (f' · печатная стр. {u["printed_page"]}' if u['printed_page'] is not None else ''), '', f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})', '']
        if u['kind'] == 'table_cell':
            table = metadata[u['id']]['table_id']
            if table in emitted:
                continue
            emitted.add(table)
            cells = tables[table]
            nrows = max(metadata[c['id']]['row_index'] + metadata[c['id']]['rowspan'] for c in cells)
            ncols = max(metadata[c['id']]['column_index'] + metadata[c['id']]['colspan'] for c in cells)
            starts, covered = {}, set()
            for cell in cells:
                meta = metadata[cell['id']]
                pos = (meta['row_index'], meta['column_index'])
                assert pos not in starts
                starts[pos] = cell
                for r in range(pos[0], pos[0] + meta['rowspan']):
                    for c in range(pos[1], pos[1] + meta['colspan']):
                        assert (r, c) not in covered, (table, r, c)
                        covered.add((r, c))
            md += [f'<table id="{table}">']
            for r in range(nrows):
                md.append('<tr>')
                for c in range(ncols):
                    cell = starts.get((r, c))
                    if cell is None:
                        if (r, c) not in covered:
                            md.append('<td></td>')
                        continue
                    meta = metadata[cell['id']]
                    is_header = r == 0 or meta['colspan'] == ncols or bool(re.search('[A-Za-z]', cell['english']) and cell['english'].isupper() and cell['english'] not in ('N/A',))
                    tag = 'th' if is_header else 'td'
                    attrs = ''.join(f' {k}="{meta[k]}"' for k in ('rowspan', 'colspan') if meta[k] > 1)
                    text = html.escape(texts[cell['id']]).replace('&lt;br&gt;', '<br>')
                    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
                    text = re.sub(r'(?<!\\)\*(.*?)(?<!\\)\*', r'<em>\1</em>', text)
                    text = text.replace('\\*', '*')
                    if is_header:
                        text = html.escape(plain(texts[cell['id']])).replace('&lt;br&gt;', '<br>')
                        english_header = html.escape(cell['english']).replace('&lt;br/&gt;', '<br>').replace('&lt;br&gt;', '<br>')
                        text += '<br><small>' + english_header + '</small>'
                    if cell['id'] in notes:
                        text += '<sup>*</sup>'
                    md.append(f'<{tag}{attrs}><!-- unit: {cell["id"]} --><a id="{cell["id"]}"></a>{text}</{tag}>')
                md.append('</tr>')
            md += ['</table>', '']
            for cell in cells:
                if cell['id'] in notes:
                    md += ['> \\* ' + notes[cell['id']], '']
            geometry[table] = {'rows': nrows, 'columns': ncols, 'source_cells': len(cells), 'missing_empty_positions': nrows * ncols - len(covered)}
            continue
        md += [f'<!-- unit: {u["id"]} -->', f'<a id="{u["id"]}"></a>', '']
        if u['kind'] == 'heading':
            level = metadata[u['id']]['heading_level'] or 3
            md += ['#' * level + ' ' + texts[u['id']], '', f'<small>{u["english"]}</small>', '']
        else:
            md += [texts[u['id']], '']
        if u['id'] in notes:
            md += ['> \\* ' + notes[u['id']], '']
        if u['id'] in figures:
            md += [figures[u['id']], '']
    if not complete:
        md += [f'> Перевод главы пока доведён до этого места. Следующий ID: `{following}`. Продолжение ещё не переведено.', '']
    rendered = '\n'.join(md)
    assert re.findall(r'<!-- unit: (.*?) -->', rendered) == [u['id'] for u in rows]
    anchors = re.findall(r'<a id="([^"]+)"', rendered)
    assert len(anchors) == len(set(anchors))
    headings = sum(u['kind'] == 'heading' for u in rows)
    header_cells = sum(metadata[u['id']]['row_index'] == 0 or metadata[u['id']]['colspan'] == geometry[metadata[u['id']]['table_id']]['columns'] or bool(re.search('[A-Za-z]', u['english']) and u['english'].isupper() and u['english'] not in ('N/A',)) for u in rows if u['kind'] == 'table_cell')
    assert rendered.count('<small>') == headings + header_cells + 1
    if tables:
        parsed = TableParser()
        parsed.feed(rendered)
        for table_id, cells in tables.items():
            node = parsed.tables[table_id]
            assert len(node) == geometry[table_id]['rows']
            assert [a for tr in node for td in tr for a in td['anchors']] == [c['id'] for c in cells]
            parsed_grid = set()
            for r, tr in enumerate(node):
                col = 0
                for td in tr:
                    while (r, col) in parsed_grid:
                        col += 1
                    rs, cs = int(td['attrs'].get('rowspan', 1)), int(td['attrs'].get('colspan', 1))
                    if td['anchors']:
                        assert len(td['anchors']) == 1
                        meta = metadata[td['anchors'][0]]
                        assert (r, col, rs, cs) == (meta['row_index'], meta['column_index'], meta['rowspan'], meta['colspan'])
                    for rr in range(r, r + rs):
                        for cc in range(col, col + cs):
                            assert (rr, cc) not in parsed_grid
                            parsed_grid.add((rr, cc))
                    col += cs
            assert len(parsed_grid) == geometry[table_id]['rows'] * geometry[table_id]['columns']
    for u in rows:
        assert plain(texts[u['id']]) == u['russian']
    with (OUT / 'translator.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    (OUT / 'translator.jsonl').write_text(''.join(json.dumps(u, ensure_ascii=False) + '\n' for u in rows), encoding='utf-8')
    MD.write_text(rendered, encoding='utf-8', newline='\n')
    with (OUT / 'translator.csv').open(encoding='utf-8-sig', newline='') as f:
        csv_rows = list(csv.DictReader(f, delimiter=';'))
    json_rows = [json.loads(line) for line in (OUT / 'translator.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(csv_rows) == len(json_rows) == len(rows)
    for a, b in zip(csv_rows, json_rows):
        assert all(a[k] == ('' if b[k] is None else str(b[k])) for k in b)
    result = {'date': '2026-10-16', 'chapter': '07', 'scope': f'PDF {first_page}–{last_page}; {rows[0]["id"]}–{rows[-1]["id"]}', 'translated_units': len(rows), 'chapter_units': 964, 'next_unit': following, 'status': 'reviewed_by_Codex' if reviewed else 'draft',
              'checks': {'source_fields_and_revision_match_readonly_database': True, 'source_sha256': True, 'numeric_tokens_normalizing_thousands_separators': True, 'emphasis_markers_match_source': True, 'author_note_markers_match_source': True, 'previous_translations_preserved': True, 'csv_jsonl_roundtrip': True, 'markdown_unit_order': True, 'unique_anchors': True, 'english_heading_lines': headings, 'markdown_and_package_text_match_without_english_labels': True},
              'database_changed': integrated, 'tables_in_fragment': len(tables), 'table_geometry': geometry, 'editor_notes': len(notes), 'chapter_complete': complete, 'pdf_visual_review': False, 'markdown_visual_review': False}
    if tables:
        result['checks']['table_coordinates_and_spans_after_html_parse'] = True
    visual_log = STYLE.with_name('visual_review.json')
    if visual_log.exists():
        result['pdf_visual_review'] = json.loads(visual_log.read_text(encoding='utf-8'))
    (BASE / '07_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    checkpoint = f'**Текущий сохранённый охват:** {len(rows)} единиц, PDF {first_page}–{last_page}, до `{rows[-1]["id"]}`. ' + ('Глава переведена полностью. ' if complete else f'Следующий ID — `{following}`. ') + 'Технические проверки последней сборки пройдены.\n\n'
    for path in (BASE / '07_review.md', OUT / 'README.md'):
        report = path.read_text(encoding='utf-8')
        report = re.sub(r'\*\*Текущий сохранённый охват:\*\*.*?\n\n', '', report, count=1)
        title, body = report.split('\n\n', 1)
        path.write_text(title + '\n\n' + checkpoint + body, encoding='utf-8', newline='\n')
    print(json.dumps({'translated_units': len(rows), 'last_unit': rows[-1]['id'], 'next_unit': following, 'checks': 'passed'}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    rebuild()
