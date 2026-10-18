"""Build chapter 08 and a revision-safe exchange package; SQLite is read-only."""
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
from collections import Counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'ACKSII/База перевода'
OUT = ROOT / 'contributions/08'
MD = ROOT / 'ACKSII/Перевод Markdown/08 Кампании.md'


def plain(s):
    s = re.sub(r'(?:<br\s*/?>\s*)?<small>.*?</small>', '', s, flags=re.S)
    # A Russian damage bracket can contain an original <br>; its tag name
    # must not make the bracket look like an English formatting label.
    return re.sub(r' ?\[([^\[\]\n]*)\]',
                  lambda m: '' if re.search(r'[A-Za-z#]',re.sub('<[^>]*>','',m[1])) else m[0],s).strip()


def numbers(s):
    s = re.sub(r'<[^>]*>', '', s)
    s = re.sub(r'(?<=\d)[, \u00a0](?=\d{3}(?:\D|$))', '', s)
    return [n.replace(',', '.') for n in re.findall(r'\d+(?:[.,]\d+)?', s)]


def inline(s):
    s = html.escape(s)
    s = re.sub(r'&lt;br\s*/?&gt;', '<br>', s)
    s = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', s)
    s = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\\)\*(.*?)(?<!\\)\*', r'<em>\1</em>', s)
    return s.replace('\\*', '*')


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = {}
        self.table = self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table':
            self.table = []
            self.tables[attrs['id']] = self.table
        elif tag == 'tr':
            self.row = []
            self.table.append(self.row)
        elif tag in ('td', 'th'):
            self.cell = {'attrs': attrs, 'ids': []}
            self.row.append(self.cell)
        elif tag == 'a' and self.cell is not None:
            self.cell['ids'].append(attrs['id'])

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.cell = None
        elif tag == 'table':
            self.table = None


def rebuild():
    source = [json.loads(s) for s in (OUT/'source.jsonl').read_text('utf-8').splitlines()]
    texts = json.loads((HERE/'styled.json').read_text('utf-8'))
    notes = json.loads((HERE/'notes.json').read_text('utf-8'))
    assert len(source) == len(texts) == 4906
    assert list(texts) == [u['id'] for u in source]
    assert set(notes) <= set(texts)
    review = HERE/'semantic_review.json'
    reviewed = review.exists() and json.loads(review.read_text('utf-8'))['complete_semantic_review_by_Codex']
    integrated = (HERE/'integration.json').exists()
    exceptions_file = HERE/'mechanical_exceptions.json'
    exceptions = json.loads(exceptions_file.read_text('utf-8')) if exceptions_file.exists() else {}
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        meta = {r['id']: dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='08'")}
    rows, checks = [], []
    for u in source:
        m = meta[u['id']]
        assert all(u[k] == m[k] for k in ('id','chapter_id','pdf_page','printed_page','kind','english','source_sha256'))
        assert m['revision'] == u['revision'] + int(integrated)
        assert hashlib.sha256(u['english'].encode()).hexdigest() == u['source_sha256']
        ru = plain(texts[u['id']])
        assert ru.strip(), (u['id'], 'empty translation')
        numeric_ok = Counter(numbers(u['english'])) == Counter(numbers(ru))
        stars_ok = u['english'].count('*') == ru.count('*')
        if not numeric_ok or not stars_ok:
            checks.append({'id':u['id'],'numeric':numeric_ok,'emphasis':stars_ok,'english':u['english'],'russian':ru})
            assert u['id'] in exceptions, (u['id'], 'mechanical difference', checks[-1])
        row = dict(u)
        row.update(russian=ru,status='reviewed' if reviewed else 'draft',origin='new_translation',note=plain(notes.get(u['id'], '')))
        assert row['revision'] == 0
        if integrated:
            assert m['russian'] == ru and m['status'] == row['status']
        rows.append(row)
    groups = {}
    for u in rows:
        if u['kind']=='table_cell':
            groups.setdefault(meta[u['id']]['table_id'],[]).append(u)
    md = ['# Глава 8. Кампании','','<small>CHAPTER 8: CAMPAIGNS</small>','',
          'Перевод Revised Rulebook от 17 октября 2026 года. Физические PDF-страницы 334–427; 4 906 из 4 906 единиц. Статус — '+('проверено Codex' if reviewed else 'черновик')+', без утверждения человеком. Английские подписи относятся к Markdown; пакет для базы содержит русский текст без них.','']
    english_overrides = {'rr.p0425.b001':'EARNING EXPERIENCE FROM CAMPAIGNS','rr.p0425.b003':'MONTHLY XP THRESHOLD'}
    emitted, geometry, page, heading_count, header_count = set(), {}, None, 0, 0
    for u in rows:
        if page != u['pdf_page']:
            page=u['pdf_page']
            md += [f'<a id="pdf-page-{page:04}"></a>','',f'## PDF-страница {page}'+(f' · печатная стр. {u["printed_page"]}' if u['printed_page'] is not None else ''),'',f'[Английский оригинал: PDF-страница {page}](../Source/ACKSII%20Revised%20Rulebook.pdf#page={page})','']
        if u['kind']=='table_cell':
            table=meta[u['id']]['table_id']
            if table in emitted:
                continue
            emitted.add(table)
            cells=groups[table]
            nr=max(meta[c['id']]['row_index']+meta[c['id']]['rowspan'] for c in cells)
            nc=max(meta[c['id']]['column_index']+meta[c['id']]['colspan'] for c in cells)
            starts, covered={},set()
            for cell in cells:
                m=meta[cell['id']]
                starts[(m['row_index'],m['column_index'])]=cell
                for r in range(m['row_index'],m['row_index']+m['rowspan']):
                    for c in range(m['column_index'],m['column_index']+m['colspan']):
                        assert (r,c) not in covered
                        covered.add((r,c))
            md += [f'<table id="{table}">']
            for r in range(nr):
                md += ['<tr>']
                for c in range(nc):
                    cell=starts.get((r,c))
                    if not cell:
                        if (r,c) not in covered:
                            md += ['<td></td>']
                        continue
                    m=meta[cell['id']]
                    header=r==0 or m['colspan']==nc or bool(re.search('[A-Za-z]',cell['english']) and cell['english'].isupper() and cell['english']!='N/A')
                    tag='th' if header else 'td'
                    attrs=''.join(f' {k}="{m[k]}"' for k in ('rowspan','colspan') if m[k]>1)
                    text=inline(plain(texts[cell['id']]) if header else texts[cell['id']])
                    if header:
                        header_count+=1
                        en='TITLE' if cell['id']=='rr.p0345.t02.r001.c01' else cell['english']
                        text += '<br><small>'+inline(en)+'</small>'
                    if cell['id'] in notes:
                        text += '<sup>*</sup>'
                    md += [f'<{tag}{attrs}><!-- unit: {cell["id"]} --><a id="{cell["id"]}"></a>{text}</{tag}>']
                md += ['</tr>']
            md += ['</table>','']
            for cell in cells:
                if cell['id'] in notes:
                    md += ['> \\* '+notes[cell['id']],'']
            geometry[table]={'rows':nr,'columns':nc,'source_cells':len(cells),'missing_empty_positions':nr*nc-len(covered)}
            continue
        if u['id']=='rr.p0353.b013':
            continue  # Its text and anchor are in the verified joined heading.
        if u['id']=='rr.p0353.b011':
            heading_count+=2  # Two immutable source heading units, one display.
            md += [f'<!-- unit: {u["id"]} -->',
                   '### <a id="rr.p0353.b011"></a>'+texts[u['id']]+' <!-- unit: rr.p0353.b013 --><a id="rr.p0353.b013"></a>'+texts['rr.p0353.b013'],
                   '', '<small>FOUNDING SETTLEMENTS</small>', '']
            if u['id'] in notes:md += ['> \\* '+notes[u['id']],'']
            continue
        md += [f'<!-- unit: {u["id"]} -->',f'<a id="{u["id"]}"></a>','']
        if u['kind']=='heading':
            heading_count+=1
            md += ['#'*(meta[u['id']]['heading_level'] or 3)+' '+texts[u['id']],'','<small>'+english_overrides.get(u['id'],u['english'])+'</small>','']
        else:
            md += [texts[u['id']],'']
        if u['id'] in notes:
            md += ['> \\* '+notes[u['id']],'']
    document='\n'.join(md)
    display_order=[u['id'] for u in rows]
    at=display_order.index('rr.p0353.b011')
    assert display_order[at:at+3]==['rr.p0353.b011','rr.p0353.b012','rr.p0353.b013']
    display_order[at:at+3]=['rr.p0353.b011','rr.p0353.b013','rr.p0353.b012']
    assert re.findall(r'<!-- unit: (.*?) -->',document)==display_order
    anchors=re.findall(r'<a id="([^"]+)"',document)
    assert len(anchors)==len(set(anchors))==4906+94
    assert document.count('<small>')==heading_count-1+header_count+1
    parsed=Tables();parsed.feed(document)
    for table,cells in groups.items():
        node=parsed.tables[table]
        assert len(node)==geometry[table]['rows']
        assert [a for tr in node for td in tr for a in td['ids']]==[c['id'] for c in cells]
        grid=set()
        for r,tr in enumerate(node):
            c=0
            for td in tr:
                while (r,c) in grid:c+=1
                rs,cs=int(td['attrs'].get('rowspan',1)),int(td['attrs'].get('colspan',1))
                if td['ids']:
                    assert len(td['ids'])==1
                    m=meta[td['ids'][0]]
                    assert (r,c,rs,cs)==(m['row_index'],m['column_index'],m['rowspan'],m['colspan'])
                for rr in range(r,r+rs):
                    for cc in range(c,c+cs):
                        assert (rr,cc) not in grid
                        grid.add((rr,cc))
                c+=cs
        assert len(grid)==geometry[table]['rows']*geometry[table]['columns']
    with (OUT/'translator.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');writer.writeheader();writer.writerows(rows)
    (OUT/'translator.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf-8')
    with (OUT/'translator.csv').open(encoding='utf-8-sig',newline='') as f:
        reread=list(csv.DictReader(f,delimiter=';'))
    assert len(reread)==len(rows)
    assert all(all(a[k]==('' if b[k] is None else str(b[k])) for k in b) for a,b in zip(reread,rows))
    MD.write_text(document,'utf-8',newline='\n')
    report={'date':'2026-10-17','chapter':'08','pdf_pages':[334,427],'id_first':rows[0]['id'],'id_last':rows[-1]['id'],'translated_units':4906,'chapter_complete':True,'status':'reviewed_by_Codex' if reviewed else 'draft','user_approved':False,'database_changed':integrated,'editor_notes':len(notes),'headings':heading_count,'bilingual_header_cells':header_count,'tables':len(groups),'table_geometry':geometry,'mechanical_exceptions':checks,'checks':{'immutable_english_sha_and_original_revision':True,'numeric_multisets':True,'emphasis_with_documented_exceptions':True,'table_spans_after_independent_html_parse':True,'all_ids_in_order_and_unique':True,'csv_jsonl_roundtrip':True,'russian_package_without_english_labels':True},'pdf_visual_review':'См. semantic_review.json и отчёты диапазонов; полная визуальная проверка не заявляется.','markdown_visual_review':False}
    (BASE/'08_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:report[k] for k in ('translated_units','tables','headings','editor_notes','status')},ensure_ascii=False))
    return report


if __name__=='__main__':
    rebuild()
