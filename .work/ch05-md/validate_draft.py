"""Technical validation only. Success never implies completed semantic review."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import csv,hashlib,json,re,sqlite3,subprocess,sys
from auto_units import HERE,ROOT
from review_tools import get_text,nums,strip_english
class DOM(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.tables=[];self.table=None;self.row=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='table':self.table=[];self.tables.append(self.table)
        elif tag=='tr':self.row=[];self.table.append(self.row)
        elif tag in ('td','th'):self.row.append((int(a.get('rowspan',1)),int(a.get('colspan',1))))
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
    reviewed='--reviewed' in sys.argv;integrated='--integrated' in sys.argv
    us=json.loads((HERE/'source_units.json').read_text('utf-8'));tables=json.loads((HERE/'source_tables.json').read_text('utf-8'));v=get_text()
    path=ROOT/('ACKSII/Перевод Markdown/05 Заклинания.md' if reviewed else 'contributions/05/Черновик главы 5.md');doc=path.read_text('utf-8')
    assert re.findall(r'<!-- unit: ([^ ]+) -->',doc)==[u['id'] for u in us]
    assert [int(x) for x in re.findall(r'<a id="pdf-page-(\d+)"></a>',doc)]==list(range(180,264))
    rendered=subprocess.run(['node',str(ROOT/'.work/ch02-md/render_document.mjs')],input=doc,text=True,encoding='utf-8',capture_output=True,check=True).stdout
    parsed=DOM();parsed.feed(rendered)
    assert len(parsed.ids)==len(set(parsed.ids))
    assert len(parsed.tables)==len(tables)==24
    for source,got in zip(tables,parsed.tables):
        assert len(got)==source['row_count'];grid={}
        for r,row in enumerate(got):
            c=0
            for rs,cs in row:
                while (r,c) in grid:c+=1
                for ri in range(r,r+rs):
                    for ci in range(c,c+cs):
                        assert (ri,ci) not in grid;grid[ri,ci]=True
                c+=cs
        assert set(grid)=={(r,c) for r in range(source['row_count']) for c in range(source['column_count'])},source['id']
    for u in us:
        assert nums(strip_english(v[u['id']]))==nums(u['source_markup']),u['id']
        assert digest(u['source_markup'].encode())==u['source_sha256']
        if u['kind']=='heading':assert '<small>'+u['source_markup']+'</small>' in doc,u['id']
        spell=re.fullmatch(r'\*\*\*([^*]+)\*\*\*(?:\s*\\?\*)?\s*',u['source_markup'])
        if spell:assert '<small>'+spell[1].rstrip('\\')+'</small>' in doc,u['id']
    assert '[[' not in doc and 'XX XX' not in doc
    assert not re.search(r'\[[^\]\n]*\[[A-Za-z]',doc)
    rows=[json.loads(s) for s in (ROOT/'contributions/05/translator.jsonl').read_text('utf-8').splitlines()]
    with (ROOT/'contributions/05/translator.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f,delimiter=';'))
    for u,row,cr in zip(us,rows,csvrows):
        assert row['id']==u['id'] and row['russian']==strip_english(v[u['id']])
        assert row['revision']==0 and row['status']==('reviewed' if reviewed else 'draft')
        assert all(('' if val is None else str(val))==cr[key] for key,val in row.items())
    assert len(rows)==len(csvrows)==len(us)==2861
    base=json.loads((HERE/'baseline.json').read_text('utf-8'))
    for rel,sha in base['protected_files'].items():assert digest((ROOT/rel).read_bytes())==sha,rel
    db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    for name,sha in base['immutable_database'].items():
        assert digest(json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {name} ORDER BY 1')],ensure_ascii=False).encode())==sha,name
    old_rows=[tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='05') ORDER BY unit_id")]
    assert digest(json.dumps(old_rows,ensure_ascii=False).encode())==base['previous_translations']
    if integrated:
        saved={r[0]:r[1:] for r in db.execute("SELECT id,russian,status,revision FROM bilingual WHERE chapter_id='05'")}
        assert len(saved)==2861
        for row in rows:assert saved[row['id']]==(row['russian'],'reviewed',1),row['id']
    else:assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='05' AND russian IS NOT NULL").fetchone()[0]==0
    reader=ROOT/'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–4.md'
    if reader.exists():assert digest(reader.read_text('utf-8').encode())==base['previous_reader_sha256_normalized_newlines']
    else:
        previous=(ROOT/'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–5.md').read_text('utf-8').split('<p align="right" id="pdf-page-0180">',1)[0]
        previous=re.sub(r'\n---\s*$','',previous).rstrip()+'\n'
        previous=previous.replace('Начало и главы 1–5','Начало и главы 1–4',1).replace('FRONT MATTER AND CHAPTERS 1–5','FRONT MATTER AND CHAPTERS 1–4',1)
        assert digest(previous.encode())==base['previous_reader_sha256_normalized_newlines']
    gate=json.loads((HERE/'semantic_review.json').read_text('utf-8'))
    if reviewed:assert gate['complete_semantic_review']
    result={'date':'2026-10-16','state':'reviewed_by_Codex' if reviewed else 'draft','pdf_pages':[180,263],'source_units':len(us),'tables':len(tables),
       'source_headings':49,'spell_headings':317,'numeric_digit_dice_and_formula_differences':0,
       'csv_jsonl_match':True,'table_geometry_checked':True,'source_unchanged':True,'database_imported':integrated,'previous_translations_unchanged':True,
       'reader_1_4_unchanged':True,'complete_semantic_review':gate['complete_semantic_review'],'complete_visual_review':False,
       'sha256_normalized_newlines':digest(doc.encode())}
    (ROOT/'ACKSII/База перевода/05_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    (HERE/'chapter_preview.html').write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><style>body{max-width:1100px;margin:3em auto;font:17px/1.5 Georgia}table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #999;padding:5px}small{font-size:.75em}h4{font-size:24px}</style><body>'+rendered,'utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
