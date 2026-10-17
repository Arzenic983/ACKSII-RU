"""One-time integration of the nine reviewed audit records through the official CLI."""
from pathlib import Path
import json, sqlite3, subprocess, sys, hashlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
DATABASE=BASE/'acksii_translation.sqlite'

def main():
    assert not (HERE/'integration.json').exists(),'Already integrated'
    applied=json.loads((HERE/'applied.json').read_text('utf-8'))
    glossary_bytes=(BASE/'glossary.json').read_bytes()
    with sqlite3.connect(DATABASE) as db:
        before={r[0]:r for r in db.execute('SELECT * FROM bilingual')}
        tables=('units','pages','source_tables','sources','glossary','working_labels')
        immutable={t:list(db.execute('SELECT * FROM '+t+' ORDER BY 1')) for t in tables}
        with sqlite3.connect(HERE/'before_audit.sqlite.tmp') as backup:db.backup(backup)
    for chapter in applied['chapters']:
        r=subprocess.run([sys.executable,str(BASE/'database_tools.py'),'import-chapter',
            str(ROOT/'contributions/rr-completeness'/(chapter+'_corrections.jsonl')),
            '--chapter',chapter,'--reviewer','Codex'],capture_output=True,text=True,encoding='utf-8',check=True)
        print(chapter,r.stdout.strip())
    with sqlite3.connect(DATABASE) as db:
        after={r[0]:r for r in db.execute('SELECT * FROM bilingual')}
        assert set(before)==set(after)
        assert {uid for uid in before if before[uid]!=after[uid]}==set(applied['units'])
        for t,rows in immutable.items():assert list(db.execute('SELECT * FROM '+t+' ORDER BY 1'))==rows,t
        # The nine affected records were reviewed against the sources, without human approval.
        db.executemany("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id=?",[(ch,) for ch in applied['chapters']])
    for command in ('verify','export'):
        r=subprocess.run([sys.executable,str(BASE/'database_tools.py'),command],capture_output=True,text=True,encoding='utf-8',check=True)
        print(r.stdout.strip())
    assert (BASE/'glossary.json').read_bytes()==glossary_bytes,'Glossary changed'
    result={'date':'2026-10-18','changed_units':applied['units'],'text_corrections':applied['meaning_changes'],
        'unchanged_other_units':30624-len(applied['units']),'source_tables_unchanged':True,'official_import_used':True,'human_approval_assigned':False}
    (HERE/'integration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
