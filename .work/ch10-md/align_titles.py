"""Align two chapter-title references with the existing contents, revision 1→2."""
from pathlib import Path
import json,sqlite3,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'ACKSII/База перевода'
def main():
    out=ROOT/'contributions/10/title_alignment.jsonl'
    assert not out.exists(),'Already applied; do not repeat stale revision 1.'
    ids=('rr.p0449.b016','rr.p0450.b004')
    # Chapter 11 is already «Сражения» in front matter and chapters.title_ru.
    p=HERE/'translations.tsv';s=p.read_text('utf-8')
    lines=s.splitlines();changes=[]
    for i,line in enumerate(lines):
        uid,text=line.split('\t',1)
        if uid in ids:
            new=text.replace('«**Битвы.**»','«**Сражения.**»')
            assert new!=text
            lines[i]=uid+'\t'+new
            changes.append((uid,text,new))
    assert len(changes)==2
    source={u['id']:u for u in (json.loads(t) for t in (ROOT/'contributions/10/source.jsonl').read_text('utf-8').splitlines())}
    with sqlite3.connect((BASE/'acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        for uid,old,new in changes:
            ru,rev=db.execute('SELECT text_ru,revision FROM translations WHERE unit_id=?',(uid,)).fetchone()
            assert ru==old and rev==1
    rows=[]
    for uid,old,new in changes:
        row=dict(source[uid]);row.update(russian=new,status='reviewed',origin='new_translation',revision=1,note='Название главы 11 согласовано с оглавлением: «Сражения». Смысл правил не менялся.')
        rows.append(row)
    out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),'utf-8')
    subprocess.run([sys.executable,str(BASE/'database_tools.py'),'import-chapter',str(out),'--chapter','10','--reviewer','Codex'],check=True)
    p.write_text('\n'.join(lines)+'\n','utf-8')
    state=json.loads((HERE/'integration.json').read_text('utf-8'));state['revisions']={uid:2 for uid in ids};state['title_alignment']='Two references to chapter 11 aligned with existing contents, official revision 1→2.'
    (HERE/'integration.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
    with sqlite3.connect(BASE/'acksii_translation.sqlite') as db:db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='10'")
if __name__=='__main__':main()
