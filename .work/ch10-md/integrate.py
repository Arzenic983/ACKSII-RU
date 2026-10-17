"""One-time guarded integration through the official chapter importer."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
DB=BASE/'acksii_translation.sqlite'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def main():
    assert not (HERE/'integration.json').exists(),'Already integrated. Export new revisions for further edits.'
    assert json.loads((HERE/'semantic_review.json').read_text('utf-8'))['complete_semantic_review_by_Codex']
    subprocess.run([sys.executable,str(HERE/'validate.py')],check=True)
    baseline=json.loads((HERE/'baseline.json').read_text('utf-8'))
    rows=[json.loads(s) for s in (ROOT/'contributions/10/translator.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==521 and all(u['revision']==0 and u['status']=='reviewed' for u in rows)
    backup=HERE/'before_chapter10.sqlite.tmp'
    assert not backup.exists(),'Inspect existing backup before any repeat.'
    with sqlite3.connect(DB) as db,sqlite3.connect(backup) as saved:
        assert db.execute("SELECT count(*) FROM translations WHERE unit_id IN (SELECT id FROM units WHERE chapter_id='10')").fetchone()[0]==0
        db.backup(saved)
    tool=str(BASE/'database_tools.py')
    subprocess.run([sys.executable,tool,'import-chapter',str(ROOT/'contributions/10/translator.jsonl'),'--chapter','10','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,tool,'verify'],check=True)
    with sqlite3.connect(DB) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='10' AND revision=1 AND status='reviewed'").fetchone()[0]==521
        assert digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='10' ORDER BY id").fetchall())==baseline['other_chapters']
        for t,old in baseline['immutable_tables'].items():assert digest(db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall())==old,t
        assert db.execute('SELECT count(*) FROM translations').fetchone()[0]==27497
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='10'")
    export=ROOT/'contributions/_export/ch10'
    subprocess.run([sys.executable,tool,'export','--out',str(export)],check=True)
    assert json.loads((export/'glossary.json').read_text('utf-8'))==json.loads((BASE/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','10_review.csv'):shutil.copyfile(export/name,BASE/name)
    (HERE/'integration.json').write_text(json.dumps({'date':'2026-10-17','chapter':'10','units':521,'package_revision':0,'database_revision':1,'official_importer':'database_tools.py import-chapter','backup':'before_chapter10.sqlite.tmp','verify':'passed','other_chapters_and_sources_unchanged':True,'translated_total':27497},ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Integrated 521 reviewed units. Source, glossary and other chapters preserved.')
if __name__=='__main__':main()
