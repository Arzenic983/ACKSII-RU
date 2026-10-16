"""Read-only preparation for chapter 5; record immutable source and review baseline."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sqlite3
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    db=sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    units=[dict(r) for r in db.execute("SELECT * FROM units WHERE chapter_id='05' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    tables=[dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='05' ORDER BY pdf_page,block_order")]
    (HERE/'source_units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),'utf-8')
    (HERE/'source_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),'utf-8')
    for page in range(180,264):
        chosen=[u for u in units if u['pdf_page']==page]
        body='\n\n'.join(f'<!-- unit: {u["id"]} -->\n{u["source_markup"]}' for u in chosen)
        (HERE/f'source_{page}.md').write_text(body+'\n','utf-8')
        print(page,dict(Counter(u['kind'] for u in chosen)))
    protected={}
    for p in (ROOT/'ACKSII').rglob('*'):
        if p.is_file() and (p.suffix.lower() in ('.pdf','.docx') or 'Source' in p.parts or p.name in ('00 Начало.md','01 Персонажи.md','02 Классы.md','03 Навыки.md','04 Снаряжение.md','Глоссарий.md','glossary.json')):
            protected[p.relative_to(ROOT).as_posix()]=digest(p.read_bytes())
    reader=ROOT/'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–4.md'
    baseline={
        'date':'2026-10-16','protected_files':protected,
        'immutable_database':{name:digest(json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {name} ORDER BY 1')],ensure_ascii=False).encode()) for name in ('units','source_tables','pages','glossary','glossary_aliases')},
        'previous_translations':digest(json.dumps([tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='05') ORDER BY unit_id")],ensure_ascii=False).encode()),
        'previous_reader_sha256_normalized_newlines':digest(reader.read_text('utf-8').encode()),
    }
    with (HERE/'baseline.json').open('x',encoding='utf-8') as f:json.dump(baseline,f,ensure_ascii=False,indent=2)
    print('units',len(units),'tables',len(tables),'words',sum(len(u['source_plain'].split()) for u in units))
    print('draft links',db.execute("SELECT count(*) FROM unit_drafts d JOIN units u ON u.id=d.unit_id WHERE u.chapter_id='05'").fetchone()[0])
    print('source headings')
    print('\n'.join(u['id']+' | '+u['source_plain'] for u in units if u['kind']=='heading'))
    drafts=[dict(r) for r in db.execute("SELECT DISTINCT f.* FROM draft_fragments f JOIN unit_drafts d ON d.draft_id=f.id JOIN units u ON u.id=d.unit_id WHERE u.chapter_id='05' ORDER BY f.id")]
    (HERE/'draft_fragments.json').write_text(json.dumps(drafts,ensure_ascii=False,indent=2),'utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
