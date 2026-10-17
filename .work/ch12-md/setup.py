"""One-time chapter-12 baseline; export and adapt inspected chapter-11 tools."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def main():
    assert not (HERE/'baseline.json').exists(),'Baseline already exists'
    subprocess.run([sys.executable,str(ROOT/'tools/export_chapter.py'),'--chapter','12','--out',str(ROOT/'contributions/12/source.jsonl')],check=True)
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        units=[dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='12' ORDER BY pdf_page,block_order,row_index,column_index,id")]
        assert len(units)==809 and all(not u['russian'] and u['revision']==0 for u in units)
        checked=(ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md').read_text('utf-8')
        for p in range(474,488):
            part=checked.split(f'<a id="pdf-page-{p:04}"></a>',1)[1].split('<a id="pdf-page-',1)[0]
            body=part.split(f'[Original PDF page {p}](ACKSII%20Revised%20Rulebook.pdf#page={p})',1)[1].strip()
            body=re.sub(r'\n---\s*$','',body).strip()
            assert body==db.execute('SELECT source_markup FROM pages WHERE pdf_page=?',(p,)).fetchone()[0].strip(),p
        baseline={'date':'2026-10-17','previous_commit':'8509643f4633318744c5ce8978796062afb05e7a','other_chapters':digest([tuple(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id!='12' ORDER BY id")]),'immutable_tables':{t:digest([tuple(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1')]) for t in ('units','source_tables','pages','glossary','working_labels','sources')},'protected_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'ACKSII/Перевод Markdown').glob('*.md')},'unit_kinds':dict(Counter(u['kind'] for u in units)),'tables':[dict(r) for r in db.execute("SELECT id,row_count,column_count FROM source_tables WHERE chapter_id='12'")],'first_id':units[0]['id'],'last_id':units[-1]['id'],'all_checked_source_pages_equal_database':True}
    (HERE/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'metadata.json').write_text(json.dumps(units,ensure_ascii=False,indent=2)+'\n','utf-8')
    for name in ('assemble_texts.py','audit.py','labels.py','build_chapter.py','validate.py'):
        s=(HERE.parent/'ch11-md'/name).read_text('utf-8')
        for old,new in [('contributions/11','contributions/12'),("chapter_id='11'","chapter_id='12'"),("chapter_id!='11'","chapter_id!='12'"),('11 Сражения.md','12 Осады.md'),('Глава 11. Сражения','Глава 12. Осады'),('CHAPTER 11: BATTLES','CHAPTER 12: SIEGES'),('462–473','474–487'),('range(462,474)','range(474,488)'),('[462,473]','[474,487]'),('618','809'),('630','823'),("'chapter':'11'","'chapter':'12'"),("'11_validation.json'","'12_validation.json'"),('chapter 11','chapter 12'),('all_12_checked_dump','all_14_checked_dump'),('all 12','all 14')]:s=s.replace(old,new)
        s=s.replace("'headings':41",f"'headings':{baseline['unit_kinds']['heading']}").replace("'table_count':11",f"'table_count':{len(baseline['tables'])}")
        s=s.replace('==42+',f"=={baseline['unit_kinds']['heading']+1}+")
        (HERE/name).write_text(s,'utf-8')
    (HERE/'source_display_fixes.json').write_text('{}\n','utf-8')
    (HERE/'notes.json').write_text('{}\n','utf-8')
    (HERE/'translations.tsv').write_text('','utf-8')
    (HERE/'cell_terms.tsv').write_text('','utf-8')
    (HERE/'term_rules.tsv').write_text((HERE.parent/'ch11-md/term_rules.tsv').read_text('utf-8'),'utf-8')
    (HERE/'english-prose.txt').write_text('\n'.join(u['id']+'\t'+u['english'] for u in units if u['kind']!='table_cell')+'\n','utf-8')
    table_lines=[]
    for t in baseline['tables']:
        table_lines.append('\n'+str(t))
        for u in units:
            if u['table_id']==t['id']:table_lines.append(u['id']+'\t'+u['english'])
    (HERE/'english-tables.txt').write_text('\n'.join(table_lines)+'\n','utf-8')
    print(json.dumps({k:v for k,v in baseline.items() if k not in ('protected_files','immutable_tables','other_chapters')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
