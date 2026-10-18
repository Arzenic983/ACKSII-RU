"""Integrator: back up, atomic import via database_tools, verify, export chapter 6."""
from common import HERE,ROOT,read
import json,sqlite3,subprocess,shutil,sys
def main():
    assert read('semantic_review.json')['complete_semantic_review_by_Codex']
    base=ROOT/'ACKSII/База перевода';dbpath=base/'acksii_translation.sqlite';backup=HERE/'before_chapter06.sqlite.tmp'
    assert not backup.exists(),'Inspect the previous import before attempting integration again.'
    rows=[json.loads(s) for s in (ROOT/'contributions/06/translator.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==2144 and all(r['status']=='reviewed' and r['revision']==0 for r in rows)
    with sqlite3.connect(dbpath) as db,sqlite3.connect(backup) as saved:db.backup(saved)
    tool=base/'database_tools.py'
    subprocess.run([sys.executable,str(tool),'import-chapter',str(ROOT/'contributions/06/translator.jsonl'),'--chapter','06','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,str(tool),'verify'],check=True)
    with sqlite3.connect(dbpath) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='06' AND status='reviewed' AND revision=1").fetchone()[0]==2144
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='06'")
    exported=ROOT/'contributions/_export/ch06'
    subprocess.run([sys.executable,str(tool),'export','--out',str(exported)],check=True)
    assert json.loads((exported/'glossary.json').read_text('utf-8'))==json.loads((base/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','06_review.csv'):shutil.copyfile(exported/name,base/name)
    print('Integrated chapter 6; original revision-0 package preserved, fresh export has revision 1.')
if __name__=='__main__':main()
