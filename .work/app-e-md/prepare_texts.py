"""Freeze reviewed chapter-name correspondences and assemble E, without import."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    assert not (HERE/'label_translations.tsv').exists(),'Already frozen; edit the reviewed mapping explicitly'
    candidates=json.loads((HERE/'candidate_labels.json').read_text('utf-8'))
    overrides=dict(s.split('\t',1) for s in (HERE/'manual_labels.tsv').read_text('utf-8').splitlines() if s)
    labels={e['english']:e['candidate']['russian'] for e in candidates if e['candidate']}
    labels.update(overrides)
    assert set(labels)=={e['english'] for e in candidates}
    for en,ru in labels.items():
        if ru.isupper():ru=ru.capitalize()
        ru=ru.replace('чудотворцеца','чудотворца')
        labels[en]=ru[0].upper()+ru[1:]
    (HERE/'label_translations.tsv').write_text(''.join(en+'\t'+labels[en]+'\n' for en in dict.fromkeys(e['english'] for e in candidates)),'utf-8',newline='\n')
    headings={'E INDEX':'E. Предметный указатель','ACKS II BACKER MEMORIAL':'Памятный список спонсоров ACKS II','AUTARCHS SUPREME':'Верховные автархи','AUTARCHS':'Автархи','COSMARCHS':'Космархи','ARBITERS OF WORLDS':'Арбитры миров','PATRON DEITIES':'Боги-покровители','DEMIGODS':'Полубоги','EMPERORS':'Императоры','KINGS':'Короли','CONQUERORS':'Завоеватели','ADVENTURERS':'Искатели приключений','INDEXES':'Указатели','GENERAL INDEX':'Общий указатель','SPELL INDEX':'Указатель заклинаний','REVERSED SPELL':'обратных заклинаний','INDEX':'Указатель','TABLE INDEX':'Указатель таблиц'}
    source=[json.loads(s) for s in (ROOT/'contributions/E/source.jsonl').read_text('utf-8').splitlines()]
    plain={}
    for u in source:
        if u['kind']=='heading':plain[u['id']]=headings.get(u['english'],u['english'])
        elif u['pdf_page']<545:plain[u['id']]=u['english']
    plain['rr.p0539.b002']='***Имперское издание системы ACKS II*** стало возможным благодаря поддержке 1 972 спонсоров Kickstarter и 114 спонсоров, присоединившихся позднее. Да будут их имена увековечены нетленной славой в летописях Ауранской империи.'
    # Index units are assembled from the frozen names by assemble_texts.py.
    (HERE/'translations.tsv').write_text(''.join(u['id']+'\t'+plain[u['id']]+'\n' for u in source if u['id'] in plain),'utf-8',newline='\n')
    print('Frozen',len(labels),'names;',len(plain),'non-index units prepared')
if __name__=='__main__':main()
