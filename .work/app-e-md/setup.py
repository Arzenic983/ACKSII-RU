"""One-time read-only source export and preservation baseline for appendix E."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
assert not (HERE/'baseline.json').exists(),'Baseline already exists'
subprocess.run([sys.executable,str(ROOT/'tools/export_chapter.py'),'--chapter','E','--out',str(ROOT/'contributions/E/source.jsonl')],check=True)
with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    units=[dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='E' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    assert len(units)==83 and all(not u['russian'] and u['revision']==0 for u in units)
    checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
    for p in range(538,551):
        part=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
        body=part.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip()
        body=re.sub(r'\n---\s*$','',body).strip()
        assert body==db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip(),p
    baseline={'date':'2026-10-17','previous_commit':'53e77ae2f17c56392b18f0e0d0a06ee3075c5c40','other_chapters':digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='E' ORDER BY id")]),'immutable_tables':{t:digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')]) for t in ('units','source_tables','pages','glossary','working_labels','sources')},'protected_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ACKSII/Перевод Markdown').glob('*.md')},'unit_kinds':dict(Counter(u['kind'] for u in units)),'tables':[dict(r) for r in db.execute("SELECT id,row_count,column_count FROM source_tables WHERE chapter_id='E'")],'first_id':units[0]['id'],'last_id':units[-1]['id'],'units_per_page':dict(Counter(u['pdf_page'] for u in units)),'all_checked_source_pages_equal_database':True}
(HERE/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'metadata.json').write_text(json.dumps(units,ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'english.txt').write_text('\n'.join(u['id']+'\t'+u['english'] for u in units)+'\n','utf-8')
(HERE/'translations.tsv').write_text('','utf-8')
print(json.dumps({k:v for k,v in baseline.items() if k not in ('protected_files','immutable_tables','other_chapters')},ensure_ascii=False,indent=2))
