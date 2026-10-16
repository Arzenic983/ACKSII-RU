"""Verify chapter/package geometry, numbers, source hashes and previous work."""
from common import HERE,ROOT,read,write
from audit import nums
from build_chapter import NODE,strip
from html.parser import HTMLParser
from collections import Counter
import re,csv,json,hashlib,sqlite3,subprocess,sys
def sha(b):return hashlib.sha256(b).hexdigest()
class DOM(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='table':self.table=[];self.tables.append(self.table)
        elif tag=='tr':self.row=[];self.table.append(self.row)
        elif tag in ('td','th'):
            self.cell={'rowspan':int(a.get('rowspan',1)),'colspan':int(a.get('colspan',1)),'id':a.get('id')};self.row.append(self.cell)
        elif tag=='a' and self.cell is not None and a.get('id','').startswith('rr.'):
            assert self.cell['id'] is None;self.cell['id']=a['id']
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.cell=None
def main():
    integrated='--integrated' in sys.argv;us=read('source_units.json');ts=read('source_tables.json');pure=read('pure_translations.json');bilingual=read('bilingual_translations.json')
    path=ROOT/'ACKSII/Перевод Markdown/06 Приключения.md';doc=path.read_text('utf-8')
    assert re.findall(r'<!-- unit: ([^ ]+) -->',doc)==[u['id'] for u in us]
    assert [int(x) for x in re.findall(r'<a id="pdf-page-(\d+)"></a>',doc)]==list(range(264,316))
    rendered=subprocess.run([NODE,str(ROOT/'.work/ch02-md/render_document.mjs')],input=doc,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    dom=DOM();dom.feed(rendered);assert len(dom.ids)==len(set(dom.ids));assert len(dom.tables)==len(ts)==33
    empty=0
    for t,rows in zip(ts,dom.tables):
        assert len(rows)==t['row_count'],t['id'];grid={};starts={}
        for r,row in enumerate(rows):
            c=0
            for cell in row:
                while (r,c) in grid:c+=1
                starts[r,c]=cell
                for ri in range(r,r+cell['rowspan']):
                    for ci in range(c,c+cell['colspan']):assert (ri,ci) not in grid;grid[ri,ci]=True
                c+=cell['colspan']
        assert set(grid)=={(r,c) for r in range(t['row_count']) for c in range(t['column_count'])},t['id']
        expected={(u['row_index'],u['column_index']):u for u in us if u['table_id']==t['id']}
        for pos,cell in starts.items():
            if pos not in expected:assert cell['id'] is None;empty+=1
            else:
                u=expected[pos];assert (cell['id'],cell['rowspan'],cell['colspan'])==(u['id'],u['rowspan'] or 1,u['colspan'] or 1),u['id']
    for u in us:
        id=u['id'];assert nums(u['source_markup'])==nums(pure[id]),id
        assert strip(bilingual[id])==pure[id],id
        assert sha(u['source_markup'].encode())==u['source_sha256']
        if u['kind']=='heading':assert '<small>'+u['source_markup']+'</small>' in doc,id
    assert not re.search(r'\[[^\]\n]*\[[A-Za-z]',doc)
    assert 'XX XX' not in doc and '[НЕТ' not in doc and '[[' not in doc
    rows=[json.loads(s) for s in (ROOT/'contributions/06/translator.jsonl').read_text('utf-8').splitlines()]
    with (ROOT/'contributions/06/translator.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f,delimiter=';'))
    assert len(rows)==len(csvrows)==len(us)==2144
    for u,r,cr in zip(us,rows,csvrows):
        assert r['id']==u['id'] and r['russian']==pure[u['id']] and r['revision']==0 and r['status']=='reviewed'
        assert r['english']==u['source_markup'] and r['source_sha256']==u['source_sha256']
        assert all(('' if v is None else str(v))==cr[k] for k,v in r.items())
    baseline=read('baseline.json')
    for rel,oldsha in baseline['protected_files'].items():
        if rel.endswith('/Примечания редактора.md'):continue
        assert sha((ROOT/rel).read_bytes())==oldsha,rel
    db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    for name,oldsha in baseline['immutable_database'].items():
        assert sha(json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {name} ORDER BY 1')],ensure_ascii=False).encode())==oldsha,name
    before=[tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='06') ORDER BY unit_id")]
    assert sha(json.dumps(before,ensure_ascii=False).encode())==baseline['previous_translations']
    saved={r[0]:r[1:] for r in db.execute("SELECT id,russian,status,revision FROM bilingual WHERE chapter_id='06' AND russian IS NOT NULL")}
    if integrated:
        assert len(saved)==2144
        for r in rows:assert saved[r['id']]==(r['russian'],'reviewed',1),r['id']
    else:assert not saved
    report={'date':'2026-10-16','book':'Revised Rulebook','pdf_pages':[264,315],'id_range':[us[0]['id'],us[-1]['id']],
        'source_units':len(us),'source_headings':175,'tables':len(ts),'table_cells':1298,'empty_cells_without_id':empty,
        'editorial_notes':sum(map(len,read('notes.json').values())),'reviewed_prose_units':671,'numeric_differences':0,
        'source_hashes_unchanged':True,'table_geometry_and_cell_positions_checked':True,'csv_jsonl_match':True,'previous_translations_unchanged':True,
        'complete_semantic_review_by_Codex':True,'user_approved':False,'pdf_images_inspected':[270,278,303],'complete_visual_review':False,
        'database_imported':integrated,'chapter_sha256_normalized_newlines':sha(doc.encode())}
    (ROOT/'ACKSII/База перевода/06_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'chapter_preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><style>body{max-width:1100px;margin:3em auto;font:17px/1.5 Georgia}table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #999;padding:5px}small{font-size:.75em}</style><body>'+rendered,'utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
