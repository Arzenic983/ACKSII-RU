"""Capture chapter 11's baseline and adapt the inspected chapter-10 builders."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def main():
    assert not (HERE/'baseline.json').exists(),'Do not replace the initial baseline.'
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        units=[dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='11' ORDER BY pdf_page,block_order,row_index,column_index,id")]
        assert len(units)==618 and all(not u['russian'] and u['revision']==0 for u in units)
        checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
        for p in range(462,474):
            part=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
            body=part.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip()
            body=re.sub(r'\n---\s*$','',body).strip()
            assert body==db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip(),p
        baseline={'date':'2026-10-17','previous_commit':'cbe6af74fa680816f322deb3d6404b1c469a3be8','other_chapters':digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='11' ORDER BY id")]),'immutable_tables':{t:digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')]) for t in ('units','source_tables','pages','glossary','working_labels','sources')},'protected_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ACKSII/Перевод Markdown').glob('*.md')},'unit_kinds':dict(Counter(u['kind'] for u in units)),'tables':[dict(r) for r in db.execute("SELECT id,row_count,column_count FROM source_tables WHERE chapter_id='11'")],'first_id':units[0]['id'],'last_id':units[-1]['id'],'all_checked_source_pages_equal_database':True}
    (HERE/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'metadata.json').write_text(json.dumps(units,ensure_ascii=False,indent=2)+'\n','utf-8')
    for name in ('assemble_texts.py','audit.py','labels.py','build_chapter.py','validate.py'):
        s=(HERE.parent/'ch10-md'/name).read_text('utf-8')
        s=s.replace('contributions/10','contributions/11').replace("chapter_id='10'","chapter_id='11'").replace("chapter_id!='10'","chapter_id!='11'")
        s=s.replace('10 Манёвры.md','11 Сражения.md').replace('Глава 10. Манёвры','Глава 11. Сражения').replace('CHAPTER 10: MANEUVERS','CHAPTER 11: BATTLES')
        s=s.replace('448–461','462–473').replace('range(448,462)','range(462,474)').replace('[448,461]','[462,473]').replace('521','618').replace('535','630')
        s=s.replace("'chapter':'10'","'chapter':'11'").replace("'10_validation.json'","'11_validation.json'")
        s=s.replace("'headings':43",f"'headings':{baseline['unit_kinds']['heading']}")
        s=s.replace("'table_count':14",f"'table_count':{len(baseline['tables'])}")
        s=s.replace("==44+",f"=={baseline['unit_kinds']['heading']+1}+")
        s=s.replace('all_14_checked_dump','all_12_checked_dump').replace('all 14','all 12').replace('chapter 10','chapter 11')
        start=s.find('def header(u):')
        if start>=0:
            end=s.index('def main():',start)
            s=s[:start]+'''def header(u):
    if u['table_id']=='rr.p0465.t02':return True
    return u['row_index']==0 or (u['table_id'] in ('rr.p0463.t01','rr.p0463.t02','rr.p0463.t03') and u['row_index']==1) or (u['english'].isupper() and len(re.findall('[A-Z]',u['english']))>4)
'''+s[end:]
        (HERE/name).write_text(s,'utf-8')
    print(json.dumps({k:v for k,v in baseline.items() if k not in ('protected_files','immutable_tables','other_chapters')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
