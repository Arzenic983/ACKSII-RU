"""Read-only checkpoint validation; deliberately does not certify semantic review."""
from pathlib import Path
import hashlib,json,re,sqlite3

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def digest(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()

baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
source=[json.loads(s) for s in (ROOT/'contributions/C/source.jsonl').read_text('utf-8').splitlines()]
pure=json.loads((HERE/'partial.json').read_text('utf-8'))
issues=[]
pages={str(p):{'translated':0,'total':0} for p in range(518,532)}
for u in source:
    pages[str(u['pdf_page'])]['total']+=1
    if u['id'] not in pure:continue
    pages[str(u['pdf_page'])]['translated']+=1
    en=u['english'];ru=pure[u['id']]
    dice=lambda s:[x.lower() for x in re.findall(r'\b\d+[dD]\d+(?:[+-]\d+)?\b',s)]
    if dice(en)!=dice(ru):issues.append({'id':u['id'],'check':'dice'})
    feet_en=re.findall(r'(\d+)[’\u2032\x27]',en)
    feet_ru=re.findall(r'(\d+)\s+фут',ru)
    if feet_en!=feet_ru:issues.append({'id':u['id'],'check':'feet','en':feet_en,'ru':feet_ru})
    if 'Listening' in en and 'подслушивания' not in ru:
        issues.append({'id':u['id'],'check':'Listening glossary'})
    if 'NPC' in en and 'НИП' not in ru:
        issues.append({'id':u['id'],'check':'NPC glossary'})

with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    assert digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='C' ORDER BY id")])==baseline['other_chapters']
    for table,expected in baseline['immutable_tables'].items():
        assert digest([tuple(r) for r in db.execute('SELECT * FROM '+table+' ORDER BY 1')])==expected,table
    for u in source:
        row=db.execute('SELECT english,source_sha256,russian,revision FROM bilingual WHERE id=?',(u['id'],)).fetchone()
        assert row['english']==u['english'] and row['source_sha256']==u['source_sha256']
        assert row['russian'] is None and row['revision']==u['revision']==0
    for table in baseline['tables']:
        cells=[u for u in source if u['id'].startswith(table['id']+'.')]
        assert len(cells)==table['row_count']*table['column_count']==72,table['id']
        positions={tuple(r) for r in db.execute('SELECT row_index,column_index FROM bilingual WHERE id LIKE ?',(table['id']+'.%',))}
        assert positions=={(r,c) for r in range(9) for c in range(8)}
for relative,expected in baseline['protected_files'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
report={'date':'2026-10-17','translated_draft':len(pure),'pending':len(source)-len(pure),
        'translation_sha256':hashlib.sha256((HERE/'partial.json').read_bytes()).hexdigest(),
        'source_packet_sha256':hashlib.sha256((ROOT/'contributions/C/source.jsonl').read_bytes()).hexdigest(),
        'pages':pages,'issues':issues,'checks':['dice','feet','Listening and NPC glossary',
        'all original English and source hashes','revision 0 and no C import','other chapters',
        'immutable database tables','11 table geometries','protected Markdown hashes'],
        'semantic_review':False,'visual_review':False,'integrated':False}
(HERE/'partial_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(report,ensure_ascii=False))
assert not issues,issues
