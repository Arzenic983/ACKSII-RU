"""Read-only source snapshot and preservation baseline for chapter09."""
from pathlib import Path
import hashlib,json,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
OUT=ROOT/'contributions/09'
OUT.mkdir(parents=True,exist_ok=True)
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    units=[dict(x) for x in db.execute("SELECT * FROM bilingual WHERE chapter_id='09' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    assert len(units)==3179 and all(x['revision']==0 and not x['russian'] for x in units)
    fields=['id','chapter_id','pdf_page','printed_page','kind','english','russian','status','origin','revision','note','source_sha256']
    rows=[]
    for u in units:
        row={k:u[k] for k in fields}
        row.update(russian='',status='draft',origin='new_translation',note='',pdf_reference='ACKSII/Source/ACKSII Revised Rulebook.pdf#page='+str(u['pdf_page']))
        rows.append(row)
    snapshot=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)
    target=OUT/'source.jsonl'
    if target.exists():assert target.read_text('utf-8')==snapshot
    else:target.write_text(snapshot,'utf-8',newline='\n')
    baseline={'date':'2026-10-17','previous_commit':'cdf4081','all_bilingual_sha256':digest([tuple(x) for x in db.execute('SELECT * FROM bilingual ORDER BY id')]),'source_units_sha256':digest([tuple(x) for x in db.execute('SELECT * FROM units ORDER BY id')]),'source_tables_sha256':digest([tuple(x) for x in db.execute('SELECT * FROM source_tables ORDER BY id')]),'protected':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ACKSII/Перевод Markdown').glob('*.md')}}
    baseline_path=HERE/'baseline.json'
    if not baseline_path.exists():baseline_path.write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Chapter09:',len(units),'units; pages:',[(p,sum(x['pdf_page']==p for x in units)) for p in range(428,448)])
print('\n'.join(x['id']+' '+x['kind']+' '+x['english'] for x in units if x['pdf_page']<=430))
