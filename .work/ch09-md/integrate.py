"""Back up SQLite, import chapter09 officially, prove source and other chapters unchanged."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
DB=BASE/'acksii_translation.sqlite'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def main():
    assert json.loads((HERE/'semantic_review.json').read_text('utf-8'))['complete_semantic_review_by_Codex']
    rows=[json.loads(s) for s in (ROOT/'contributions/09/translator.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==3179 and all(u['status']=='reviewed' and u['revision']==0 for u in rows)
    backup=HERE/'before_chapter09.sqlite.tmp'
    assert not backup.exists(),'Inspect existing backup/import before repeating.'
    with sqlite3.connect(DB) as db,sqlite3.connect(backup) as saved:
        before=digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='09' ORDER BY id").fetchall())
        source=digest(db.execute('SELECT * FROM units ORDER BY id').fetchall())
        tables=digest(db.execute('SELECT * FROM source_tables ORDER BY id').fetchall())
        db.backup(saved)
    tool=str(BASE/'database_tools.py')
    subprocess.run([sys.executable,tool,'import-chapter',str(ROOT/'contributions/09/translator.jsonl'),'--chapter','09','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,tool,'verify'],check=True)
    with sqlite3.connect(DB) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='09' AND status='reviewed' AND revision=1").fetchone()[0]==3179
        assert digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='09' ORDER BY id").fetchall())==before
        assert digest(db.execute('SELECT * FROM units ORDER BY id').fetchall())==source
        assert digest(db.execute('SELECT * FROM source_tables ORDER BY id').fetchall())==tables
        assert db.execute('SELECT count(*) FROM translations').fetchone()[0]==26976
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='09'")
    export=ROOT/'contributions/_export/ch09'
    subprocess.run([sys.executable,tool,'export','--out',str(export)],check=True)
    assert json.loads((export/'glossary.json').read_text('utf-8'))==json.loads((BASE/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','09_review.csv'):shutil.copyfile(export/name,BASE/name)
    (HERE/'integration.json').write_text(json.dumps({'chapter':'09','units':3179,'package_revision':0,'database_revision':1,'other_chapters_unchanged':True,'english_and_geometry_unchanged':True,'backup':str(backup),'verify':'passed'},ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Integrated chapter09; other chapters, immutable units and geometry preserved.')
if __name__=='__main__':main()
