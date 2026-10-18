"""Prepare chapter 6 read-only sources and immutable baselines; do not import."""
from pathlib import Path
from collections import Counter
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import hashlib,json,sqlite3,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    assert not (HERE/'baseline.json').exists()
    db=sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    units=[dict(r) for r in db.execute("SELECT * FROM units WHERE chapter_id='06' ORDER BY pdf_page,block_order,row_index,column_index,id")]
    tables=[dict(r) for r in db.execute("SELECT * FROM source_tables WHERE chapter_id='06' ORDER BY pdf_page,block_order")]
    for name,data in [('source_units',units),('source_tables',tables)]:
        (HERE/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
    for page in range(264,316):
        (HERE/f'source_{page}.md').write_text('\n\n'.join(f'<!-- unit: {u["id"]} -->\n{u["source_markup"]}' for u in units if u['pdf_page']==page)+'\n','utf-8')
    protected={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in (ROOT/'ACKSII').rglob('*') if p.is_file() and (p.suffix.lower() in ('.pdf','.docx') or 'Source' in p.parts or p.name in ('Глоссарий.md','glossary.json') or p.parent.name=='Перевод Markdown')}
    baseline={'date':'2026-10-16','protected_files':protected,
        'immutable_database':{n:sha(json.dumps([tuple(r) for r in db.execute(f'SELECT * FROM {n} ORDER BY 1')],ensure_ascii=False).encode()) for n in ('units','source_tables','pages','glossary','glossary_aliases')},
        'previous_translations':sha(json.dumps([tuple(r) for r in db.execute("SELECT * FROM translations WHERE unit_id NOT IN (SELECT id FROM units WHERE chapter_id='06') ORDER BY unit_id")],ensure_ascii=False).encode())}
    (HERE/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),'utf-8')
    w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paths=list((ROOT/'ACKSII/ACKSII Revised Rulebook').glob('CHAPTER 6*.docx'))+list((ROOT/'ACKSII/ACKSII Revised Rulebook/CHAPTER 6_ Adventures (MOCHET)').glob('*.docx'))
    for path in paths:
        with ZipFile(path) as z:doc=ET.fromstring(z.read('word/document.xml'))
        parts=[]
        for p in doc.iter(w+'p'):
            text=''.join(t.text or '' for t in p.iter(w+'t')).strip()
            if text:parts.append(text)
        (HERE/(path.stem+'.json')).write_text(json.dumps(parts,ensure_ascii=False,indent=2),'utf-8')
        (HERE/(path.stem+'.txt')).write_text('\n\n'.join(f'{i}: {s}' for i,s in enumerate(parts)),'utf-8')
        print(path.name,len(parts))
    print('units',len(units),'tables',len(tables),'words',sum(len(u['source_plain'].split()) for u in units))
    print('kinds',Counter(u['kind'] for u in units))
    print('range',units[0]['id'],units[-1]['id'])
    print('\n'.join(u['id']+' | '+u['source_plain'] for u in units if u['kind']=='heading'))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
