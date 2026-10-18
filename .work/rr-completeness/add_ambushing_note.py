"""One-time follow-up: preserve the remaining glossary proposal beside the skill."""
from pathlib import Path
import csv,json,re,sqlite3,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
UID='rr.p0107.b023'
NOTE='В отслеживаемых правках прежнего словаря для Засады [Ambushing] предложены «внезапный удар» или «удар исподтишка»: автор замечания считает название «Засада» неточным для описанной способности. Действующая словарная форма сохранена; предложение передано главному переводчику и не считается утверждённой заменой.'

def main():
    marker=HERE/'ambushing_note_integration.json'
    assert not marker.exists(),'Already applied'
    with sqlite3.connect(BASE/'acksii_translation.sqlite') as db:
        db.row_factory=sqlite3.Row
        u=dict(db.execute('SELECT * FROM bilingual WHERE id=?',(UID,)).fetchone())
        before={r['id']:tuple(r) for r in db.execute('SELECT * FROM bilingual')}
        with sqlite3.connect(HERE/'before_ambushing_note.sqlite.tmp') as backup:db.backup(backup)
    row={k:u[k] for k in ('id','chapter_id','pdf_page','printed_page','kind','english','russian','status','revision','note','source_sha256')}
    row['note']=((u['note'] or '')+'\n\n'+NOTE).strip()
    packet=ROOT/'contributions/rr-completeness/03_ambushing_note.jsonl'
    packet.write_text(json.dumps(row,ensure_ascii=False)+'\n','utf-8')
    with packet.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(row),delimiter=';');w.writeheader();w.writerow(row)
    p=ROOT/'ACKSII/Перевод Markdown/03 Навыки.md';s=p.read_text('utf-8')
    start=s.index('<!-- unit: '+UID+' -->');end=s.index('<!-- unit:',start+20)
    block=s[start:end];assert NOTE not in s
    block=re.sub(r'^(#{1,6} [^\n]+)',r'\1<sup>*</sup>',block,count=1,flags=re.M).rstrip()+'\n\n> \\* '+NOTE+'\n\n'
    p.write_text(s[:start]+block+s[end:],'utf-8')
    p=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md'
    p.write_text(p.read_text('utf-8').rstrip()+'\n\n<!-- unit: '+UID+' -->\n'+NOTE+'\n','utf-8')
    subprocess.run([sys.executable,str(BASE/'database_tools.py'),'import-chapter',str(packet),'--chapter','03','--reviewer','Codex'],check=True)
    with sqlite3.connect(BASE/'acksii_translation.sqlite') as db:
        db.row_factory=sqlite3.Row
        after={r['id']:tuple(r) for r in db.execute('SELECT * FROM bilingual')}
        assert {uid for uid in before if before[uid]!=after[uid]}=={UID}
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='03'")
    subprocess.run([sys.executable,str(BASE/'database_tools.py'),'verify'],check=True)
    subprocess.run([sys.executable,str(BASE/'database_tools.py'),'export'],check=True)
    marker.write_text(json.dumps({'id':UID,'source_revision':u['revision'],'result_revision':u['revision']+1,'russian_text_unchanged':True,'note':NOTE},ensure_ascii=False,indent=2)+'\n','utf-8')
    p=HERE/'integration.json';data=json.loads(p.read_text('utf-8'))
    data['changed_units'].append(UID);data['unchanged_other_units']=30624-len(data['changed_units']);data['followup_note']=UID
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')

if __name__=='__main__':main()
