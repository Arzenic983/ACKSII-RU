import pathlib,sqlite3,re,subprocess,json,collections,hashlib
from html.parser import HTMLParser

P=pathlib.Path(__file__).resolve().parent
ROOT=P.parents[1]
OUT=ROOT/'ACKSII/Перевод Markdown'
NODE='C:/Users/Arsik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
class Audit(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.tables=[];self.current=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='table':self.current=[];self.tables.append(self.current)
        if tag=='tr':self.row=[];self.current.append(self.row)
        if tag in ('td','th'):
            self.cell={'id':a.get('id'),'rowspan':int(a.get('rowspan',1)),'colspan':int(a.get('colspan',1))};self.row.append(self.cell)
        if tag=='a' and self.cell is not None and 'id' in a:self.cell['id']=a['id']
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.cell=None
        if tag=='table':self.current=None

s=(OUT/'ACKS II — Начало и главы 1–2.md').read_text('utf-8')
render=subprocess.run([NODE,str(P/'render_document.mjs')],input=s,text=True,encoding='utf-8',capture_output=True,check=True).stdout
(P/'preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><style>body{font:17px Georgia;max-width:1200px;margin:40px auto;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #bbb;padding:6px}th{background:#eee}blockquote{border-left:3px solid #bbb;padding-left:12px;color:#555}</style><body>'+render+'</body></html>','utf-8')
a=Audit();a.feed(render)
db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
units=[dict(r) for r in db.execute('SELECT * FROM units WHERE pdf_page<=101 ORDER BY pdf_page,block_order,row_index,column_index,id')]
tables=list(db.execute('SELECT * FROM source_tables WHERE pdf_page<=101 ORDER BY pdf_page,block_order,id'))
assert len(a.tables)==len(tables),(len(a.tables),len(tables))
assert len(a.ids)==len(set(a.ids)), 'Duplicate rendered anchors'
assert {u['id'] for u in units}<=set(a.ids),'Missing rendered unit anchors'
assert {f'pdf-page-{p:04d}' for p in range(1,102)}<=set(a.ids),'Missing pages'
errors=[]
for actual,t in zip(a.tables,tables):
    cells=[u for u in units if u['table_id']==t['id']]
    if len(actual)!=t['row_count']:errors.append(t['id']+' row count')
    actual_cells=[c for row in actual for c in row]
    if len(actual_cells)!=len(cells):errors.append(t['id']+' cell count')
    for ac,expected in zip(actual_cells,cells):
        if ac!={'id':expected['id'],'rowspan':expected['rowspan'] or 1,'colspan':expected['colspan'] or 1}:errors.append(expected['id']+' geometry')
assert not errors,errors
assert not re.search(r'^> \\\\[*]',s,re.M),'Double escaped footnote'
assert not re.search(r'КЗд|направление взгляда|сотворение отродья|камнем для пращи|Большие магические исследования',s),'Unapplied review fixes'
result={'rendered_tables':len(a.tables),'rendered_unit_anchors':len(units),'rendered_pdf_page_anchors':101,'rendered_duplicate_anchors':0,'rendered_table_row_column_spans':'passed','markdown_notes_escaping':'passed','known_review_fixes':'passed','content_sha256':hashlib.sha256(s.encode()).hexdigest()}
(P/'rendered_markdown_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
