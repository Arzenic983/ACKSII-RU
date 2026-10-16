"""Import the final terminology corrections with their actual current revisions."""
from pathlib import Path
import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from auto_units import HERE,ROOT

BASE=ROOT/'ACKSII/База перевода'
def main():
    desired=[json.loads(s) for s in (ROOT/'contributions/04/translator.jsonl').read_text('utf-8').splitlines()]
    with sqlite3.connect(BASE/'acksii_translation.sqlite') as db:
        db.row_factory=sqlite3.Row
        current={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='04'")}
        changes=[]
        for row in desired:
            if row['russian']==current[row['id']]['russian']:continue
            assert current[row['id']]['revision']==1,row['id']
            row=dict(row);row['revision']=current[row['id']]['revision'];changes.append(row)
        assert changes,'No terminology corrections to import'
        backup=HERE/'before_chapter04_corrections.sqlite.tmp'
        assert not backup.exists(),'Review existing correction backup before repeating'
        with sqlite3.connect(backup) as saved:db.backup(saved)
    package=ROOT/'contributions/04/corrections_01.jsonl'
    package.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in changes),'utf-8')
    with package.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(changes[0]),delimiter=';');w.writeheader();w.writerows(changes)
    tool=BASE/'database_tools.py'
    subprocess.run([sys.executable,str(tool),'import-chapter',str(package),'--chapter','04','--reviewer','Codex'],check=True)
    subprocess.run([sys.executable,str(tool),'verify'],check=True)
    with sqlite3.connect(BASE/'acksii_translation.sqlite') as db:
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='04'")
    export=ROOT/'contributions/_export/ch04_final'
    subprocess.run([sys.executable,str(tool),'export','--out',str(export)],check=True)
    assert json.loads((export/'glossary.json').read_text('utf-8'))==json.loads((BASE/'glossary.json').read_text('utf-8'))
    for name in ('units.jsonl','progress.json','04_review.csv'):shutil.copyfile(export/name,BASE/name)
    print('Corrected units:',len(changes))
if __name__=='__main__':main()
