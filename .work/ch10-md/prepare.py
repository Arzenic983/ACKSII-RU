"""Read-only baseline, terminology candidates, and local PDF inspection renders."""
from pathlib import Path
import collections, hashlib, json, sqlite3, xml.etree.ElementTree as ET, zipfile
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'ACKSII/База перевода'
def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()
with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro', uri=True) as db:
    db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='10' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    assert len(rows)==521 and all(r['revision']==0 and r['russian'] is None for r in rows)
    baseline={
        'date':'2026-10-17',
        'other_chapters':digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='10' ORDER BY id")]),
        'immutable_tables':{t:digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')]) for t in ('units','source_tables','pages','glossary','working_labels','sources')},
        'protected_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ACKSII/Перевод Markdown').glob('*.md')},
        'unit_kinds':dict(collections.Counter(r['kind'] for r in rows)),
        'tables':[dict(r) for r in db.execute("SELECT id,row_count,column_count FROM source_tables WHERE chapter_id='10'")],
        'first_id':rows[0]['id'],'last_id':rows[-1]['id']}
    path=HERE/'baseline.json'
    assert not path.exists(), 'Baseline already exists; do not reset it.'
    path.write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n','utf-8')
    glossary=json.loads((BASE/'glossary.json').read_text('utf-8'))
    source=' '.join(r['english'].lower() for r in rows)
    candidates=[g for g in glossary if g['term_en'].lower() in source]
    (HERE/'glossary_candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'metadata.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n','utf-8')
draft=ROOT/'ACKSII/ACKSII Revised Rulebook/CHAPTER 10_ Maneuvers (Елизавета).docx'
with zipfile.ZipFile(draft) as z:
    xml=ET.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paras=[''.join(p.itertext()) for p in []] # Text nodes below avoid duplicated runs.
    paras=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in xml.findall('.//w:p',ns)]
    (HERE/'contributor_draft.txt').write_text('\n'.join(paras),'utf-8')
print(json.dumps({k:v for k,v in baseline.items() if k not in ('protected_files','immutable_tables')},ensure_ascii=False,indent=2))
