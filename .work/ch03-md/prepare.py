"""Read-only source preparation and baseline for chapter 3."""
from pathlib import Path
import collections
import hashlib
import json
import sqlite3

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'ACKSII/База перевода'

def digest(value):
    return hashlib.sha256(value).hexdigest()

def main():
    db = sqlite3.connect((BASE / 'acksii_translation.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    units = [dict(r) for r in db.execute("SELECT * FROM units WHERE chapter_id='03' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    tables = [dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='03' ORDER BY pdf_page,block_order")]
    (HERE / 'source_units.json').write_text(json.dumps(units, ensure_ascii=False, indent=2), 'utf-8')
    (HERE / 'source_tables.json').write_text(json.dumps(tables, ensure_ascii=False, indent=2), 'utf-8')
    for page in range(102,124):
        selected = [u for u in units if u['pdf_page']==page]
        body = '\n\n'.join(f'<!-- unit: {u["id"]} -->\n{u["source_markup"]}' for u in selected)
        (HERE / f'source_{page}.md').write_text(body+'\n', 'utf-8')
        print(page, dict(collections.Counter(u['kind'] for u in selected)))
    protected = {}
    for p in (ROOT / 'ACKSII').rglob('*'):
        if p.is_file() and (p.suffix.lower() in ('.pdf','.docx') or 'Source' in p.parts or p.name in ('00 Начало.md','01 Персонажи.md','02 Классы.md','Глоссарий.md','glossary.json')):
            protected[p.relative_to(ROOT).as_posix()] = digest(p.read_bytes())
    baseline = {
        'date': '2026-10-15',
        'protected_files': protected,
        'immutable_database': {name: digest(json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {name} ORDER BY 1')],ensure_ascii=False).encode()) for name in ('units','source_tables','pages','glossary','glossary_aliases')},
        'previous_translations': digest(json.dumps([tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='03') ORDER BY unit_id")],ensure_ascii=False).encode()),
        'previous_reader_sha256': digest((ROOT / 'ACKSII/Перевод Markdown/ACKS II — Начало и главы 1–2.md').read_bytes()),
    }
    baseline_path = HERE / 'baseline.json'
    with baseline_path.open('x', encoding='utf-8') as out:
        json.dump(baseline,out,ensure_ascii=False,indent=2)
    print('tables',len(tables),'units',len(units),'words',sum(len(u['source_plain'].split()) for u in units))
    print('headings',[(u['id'],u['source_plain']) for u in units if u['kind']=='heading'])

if __name__ == '__main__':
    main()
