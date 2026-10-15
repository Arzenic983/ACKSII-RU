"""Independent coverage, alignment, rendering, and immutable-source checks."""
from collections import Counter
from html.parser import HTMLParser
import hashlib
import csv
import json
import re
import sqlite3
import subprocess
import sys
from auto_units import HERE, ROOT, records
from build_chapter import NODE, CORRECTED_HEADERS, MAX_LEVELS
from review_tools import get_text, nums, strip_english

BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'ACKSII/Перевод Markdown'

def digest(data):return hashlib.sha256(data).hexdigest()

class DOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[];self.tables=[];self.table=None;self.cell=None;self.row=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='table':
            self.table=[];self.tables.append(self.table)
        elif tag=='tr':
            self.row=[];self.table.append(self.row)
        elif tag in ('td','th'):
            self.cell={'id':a.get('id'),'rowspan':int(a.get('rowspan',1)),'colspan':int(a.get('colspan',1)),'text':''}
            self.row.append(self.cell)
    def handle_data(self,data):
        if self.cell is not None:self.cell['text']+=data
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.cell=None
        elif tag=='table':self.table=None

def render(value):
    return subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=value,text=True,encoding='utf-8',capture_output=True,check=True).stdout

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    tables=json.loads((HERE/'source_tables.json').read_text('utf-8'))
    text=get_text()
    pure={id:strip_english(t) for id,t in text.items()}
    document=(OUT/'03 Навыки.md').read_text('utf-8')
    rendered=render(document)
    audit=DOM();audit.feed(rendered)
    expected=[u['id'] for u in units]
    assert re.findall(r'<!-- unit: ([^ ]+) -->',document)==expected
    assert [id for id in audit.ids if id.startswith('rr.') and re.search(r'\.(?:b\d{3}|t\d{2}\.r\d{3}\.c\d{2})$',id)]==expected
    assert len(audit.ids)==len(set(audit.ids))
    assert re.findall(r'<a id="pdf-page-(\d{4})"></a>',document)==[f'{p:04d}' for p in range(102,124)]
    assert len(audit.tables)==len(tables)==10
    # Validate the rendered grid, including all originally empty cells.
    for table,got in zip(tables,audit.tables):
        assert len(got)==table['row_count'],table['id']
        grid={}
        for r,row in enumerate(got):
            c=0
            for cell in row:
                while (r,c) in grid:c+=1
                for ri in range(r,r+cell['rowspan']):
                    for ci in range(c,c+cell['colspan']):
                        assert (ri,ci) not in grid,(table['id'],ri,ci)
                        grid[ri,ci]=cell
                c+=cell['colspan']
        assert set(grid)=={(r,c) for r in range(table['row_count']) for c in range(table['column_count'])},table['id']
        cells=[u for u in units if u['table_id']==table['id']]
        for u in cells:
            cell=grid[u['row_index'],u['column_index']]
            assert cell['rowspan']==(u['rowspan'] or 1) and cell['colspan']==(u['colspan'] or 1),u['id']
            if cell['id']:assert cell['id']==u['id']
            # Term annotations and subtitles can add English but not alter numeric content.
            assert nums(strip_english(text[u['id']]))==nums(u['source_markup']),u['id']
        if table['id']=='rr.p0104.t01':
            for r in range(1,22):
                for level in range(1,15):
                    unavailable=r in MAX_LEVELS and level>MAX_LEVELS[r]
                    assert (grid[r,level]['text'].strip()=='-')==unavailable,(r,level)
    for u in units:
        assert nums(pure[u['id']])==nums(u['source_markup']),u['id']
        dice=lambda s:Counter(re.findall(r'\d+d\d+!?(?:[+-]\d+)?',s))
        assert dice(pure[u['id']])==dice(u['source_markup']),u['id']
        assert hashlib.sha256(u['source_markup'].encode()).hexdigest()==u['source_sha256']
        if u['kind']=='heading':assert '<small>'+u['source_markup']+'</small>' in document
    headings=sum(u['kind']=='heading' for u in units)
    table_headers=sum(u['table_id'] is not None and u['row_index']==0 and bool(re.search('[A-Za-z]',u['source_markup'])) for u in units)
    assert not re.search(r'\[[^\]\n]*\[[^\]\n]*\]',document),'Nested square brackets'
    # Every occurrence of the two expressly approved names carries its English name.
    bodies='\n'.join(text[u['id']] for u in units if u['kind']!='heading')
    for root,en in (('Мифограф','Loremastery'),('Природоведен','Naturalism')):
        for m in re.finditer(root+r'[а-яё]*',bodies,re.I):
            assert re.match(r' \['+en+r'\]',bodies[m.end():]),m.group()
    for id,value in pure.items():
        # C/G and the book title ACKS II MM are original notation.
        assert not re.search(r'\[[^\]]*[A-Za-z]',value),id
    package=[json.loads(line) for line in (ROOT/'contributions/03/translator.jsonl').read_text('utf-8').splitlines()]
    csv_path=ROOT/'contributions/03/translator.csv'
    assert csv_path.read_bytes().startswith(b'\xef\xbb\xbf')
    with csv_path.open(encoding='utf-8-sig',newline='') as f:
        csv_rows=list(csv.DictReader(f,delimiter=';'))
    assert csv_rows==[{k:'' if v is None else str(v) for k,v in r.items()} for r in package]
    assert [r['id'] for r in package]==expected
    for u,row in zip(units,package):
        assert row['revision']==0 and row['english']==u['source_markup'] and row['source_sha256']==u['source_sha256']
        assert row['russian']==pure[row['id']]
        assert row['status'] in ('draft','reviewed')
    db=sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    for rel,sha in baseline['protected_files'].items():
        assert digest((ROOT/rel).read_bytes())==sha,'Protected file changed: '+rel
    for name,sha in baseline['immutable_database'].items():
        data=json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {name} ORDER BY 1')],ensure_ascii=False).encode()
        assert digest(data)==sha,name
    before=json.dumps([tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='03') ORDER BY unit_id")],ensure_ascii=False).encode()
    assert digest(before)==baseline['previous_translations']
    translated=db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='03' AND russian IS NOT NULL").fetchone()[0]
    if translated:
        assert translated==704
        for id,ru,status in db.execute("SELECT id,russian,status FROM bilingual WHERE chapter_id='03'"):
            assert ru==pure[id] and status=='reviewed',id
        with (BASE/'03_review.csv').open(encoding='utf-8-sig',newline='') as f:
            current_rows=list(csv.DictReader(f,delimiter=';'))
        assert [r['id'] for r in current_rows]==expected
        assert all(r['revision']=='1' and r['status']=='reviewed' and r['russian']==pure[r['id']] for r in current_rows)
        exported=[json.loads(line) for line in (BASE/'units.jsonl').read_text('utf-8').splitlines()]
        assert len(exported)==30624
        assert {r['id']:r['russian'] for r in exported if r['chapter_id']=='03'}==pure
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    report={
        'date':'2026-10-16','chapter_id':'03','book':'Revised Rulebook','pdf_pages':[102,123],
        'first_id':expected[0],'last_id':expected[-1],
        'source_units':len(units),'translated_units':len(text),'pending_units':0,
        'table_count':len(tables),'nonempty_source_table_cells':sum(u['table_id'] is not None for u in units),
        'rendered_table_cells_including_original_blanks':sum(len(row) for t in audit.tables for row in t),
        'headings_with_english_subtitles':headings,'table_headers_with_english_subtitles':table_headers,
        'editorial_notes':sum(map(len,notes.values())),
        'unit_order_anchors_and_coverage':'passed','numeric_values_dice_modifiers_percentages':'passed',
        'rendered_table_geometry_and_blank_cell_positions':'passed',
        'original_units_pages_tables_glossary_unchanged':True,
        'previous_translations_unchanged':True,'protected_source_and_docx_files_unchanged':len(baseline['protected_files']),
        'exchange_package_revision':0,'database_chapter_translations':translated,
        'csv_jsonl_content_equal':True,'csv_encoding':'UTF-8 BOM','csv_delimiter':';',
        'reviewer':'Codex','user_approved':False,
        'pdf_images_inspected':[104,107,113,118,119,122],
        'markdown_sha256_normalized_newlines':digest(document.encode()),
    }
    (BASE/'03_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'chapter_preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><style>body{font:17px Georgia,serif;max-width:1200px;margin:30px auto;padding:20px;line-height:1.5}h1,h2,h3,h4{line-height:1.2;margin-bottom:.25em}small{font-size:.75em}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bbb;padding:5px}th{background:#f4f0eb}blockquote{border-left:3px solid #bbb;padding-left:12px;color:#555}</style><body>'+rendered+'</body></html>','utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
