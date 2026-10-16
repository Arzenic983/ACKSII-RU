"""Integrator entry point: backup, official atomic import, verify and export."""
from pathlib import Path
import json
import shutil
import sqlite3
import subprocess
import sys
from auto_units import HERE, ROOT

BASE=ROOT/'ACKSII/База перевода'
DB=BASE/'acksii_translation.sqlite'

def main():
    rows=[json.loads(line) for line in (ROOT/'contributions/04/translator.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==4566 and all(r['status']=='reviewed' and r['revision']==0 for r in rows)
    backup=HERE/'before_chapter04.sqlite.tmp'
    assert not backup.exists(),'A pre-import backup already exists; inspect state before repeating integration.'
    with sqlite3.connect(DB) as db,sqlite3.connect(backup) as saved:
        db.backup(saved)
    tool=BASE/'database_tools.py'
    subprocess.run([sys.executable,str(tool),'import-chapter',str(ROOT/'contributions/04/translator.jsonl'),'--chapter','04','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,str(tool),'verify'],check=True)
    # Completion metadata is assigned only after translation review and validation.
    with sqlite3.connect(DB) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='04' AND status='reviewed' AND russian IS NOT NULL").fetchone()[0]==4566
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='04'")
    exported=ROOT/'contributions/_export/ch04'
    subprocess.run([sys.executable,str(tool),'export','--out',str(exported)],check=True)
    # Avoid rewriting historical CSV packages outside this chapter.
    assert json.loads((exported/'glossary.json').read_text('utf-8'))==json.loads((BASE/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','04_review.csv'):
        shutil.copyfile(exported/name,BASE/name)
    print('Integrated chapter 04; preserved original revision-0 contribution and exported fresh revision-1 CSV.')

if __name__=='__main__':main()
