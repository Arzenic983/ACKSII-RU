"""One-time official appendix-E import; never rerun over integrated revisions."""
from pathlib import Path
import hashlib,json,shutil,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
DB=BASE/'acksii_translation.sqlite'
def digest(rows):return hashlib.sha256(json.dumps(rows,ensure_ascii=False).encode()).hexdigest()
def main():
    assert not (HERE/'integration.json').exists(),'Already integrated: export fresh revisions for later changes'
    review=json.loads((HERE/'semantic_review.json').read_text('utf-8'))
    assert review['complete_semantic_review_by_Codex'] and not review['human_approval']
    assert hashlib.sha256((HERE/'pure.json').read_bytes()).hexdigest()==review['russian_units_sha256']
    subprocess.run([sys.executable,str(HERE/'validate.py')],check=True)
    rows=[json.loads(s) for s in (ROOT/'contributions/E/translator.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==83 and all(u['status']=='reviewed' and u['revision']==0 for u in rows)
    before=json.loads((HERE/'baseline.json').read_text('utf-8'))
    backup=HERE/'before_appendixE.sqlite.tmp'
    assert not backup.exists(),'Inspect an existing backup before repeating'
    with sqlite3.connect(DB) as db,sqlite3.connect(backup) as saved:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='E' AND revision=0").fetchone()[0]==83
        db.backup(saved)
    tool=str(BASE/'database_tools.py')
    subprocess.run([sys.executable,tool,'import-chapter',str(ROOT/'contributions/E/translator.jsonl'),'--chapter','E','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,tool,'verify'],check=True)
    with sqlite3.connect(DB) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='E' AND revision=1 AND status='reviewed'").fetchone()[0]==83
        assert digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='E' ORDER BY id").fetchall())==before['other_chapters']
        for t,h in before['immutable_tables'].items():assert digest(db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall())==h,t
        assert db.execute('SELECT count(*) FROM translations').fetchone()[0]==30624
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='E'")
    export=ROOT/'contributions/_export/appE'
    subprocess.run([sys.executable,tool,'export','--out',str(export)],check=True)
    assert json.loads((export/'glossary.json').read_text('utf-8'))==json.loads((BASE/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','E_review.csv'):shutil.copyfile(export/name,BASE/name)
    (HERE/'integration.json').write_text(json.dumps({'date':'2026-10-17','chapter':'E','units':83,'package_revision':0,'database_revision':1,'official_importer':'database_tools.py import-chapter','backup':'before_appendixE.sqlite.tmp','verify':'passed','other_chapters_and_sources_unchanged':True,'translated_total':30624},ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Integrated 83 units; source, glossary and other chapters unchanged.')
if __name__=='__main__':main()
