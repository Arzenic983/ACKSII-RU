"""Read-only glossary consultation and exact cross-chapter source evidence."""
from pathlib import Path
import json,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
terms={'Judge','Henchmen','Mercenary','Sneaking','Hiding','Disordered','Faltering','Wavering','Military Strategy','Leadership','Siege Engineering','Engineering','Blast','Naturalism','Loremastery','extraordinary','Domain','Realm','SHP','Structural hit points','Huge','Gigantic','Colossal'}
gloss=json.loads((BASE/'glossary.json').read_text('utf-8'))
selected=[u for u in gloss if u['term_en'].casefold() in {s.casefold() for s in terms}]
(HERE/'glossary_check.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n','utf-8')
with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    refs=[dict(r) for r in db.execute("SELECT id,chapter_id,kind,english,russian FROM bilingual WHERE id IN ('rr.p0151.b006','rr.p0151.b008','rr.p0151.b011','rr.p0178.b018','rr.p0179.t01.r003.c01') OR chapter_id='05' AND english LIKE '%MIRE%' AND length(english)<150")]
(HERE/'cross_chapter_evidence.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'glossary_entries':len(selected),'cross_references':[r['id'] for r in refs],'spell_name_check':[r for r in refs if r['chapter_id']=='05']},ensure_ascii=False,indent=2))
