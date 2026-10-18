"""Combine isolated translation ranges without changing the source snapshot."""
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=[json.loads(s) for s in (ROOT/'contributions/08/source.jsonl').read_text('utf-8').splitlines()]
initial=HERE/'initial_fragment.json'
if not initial.exists():
    old=json.loads((HERE/'styled.json').read_text('utf-8'))
    assert len(old)==275
    initial.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'initial_notes.json').write_text((HERE/'notes.json').read_text('utf-8'),'utf-8')
texts=json.loads(initial.read_text('utf-8'))
notes=json.loads((HERE/'initial_notes.json').read_text('utf-8'))
parts=[('p339_360',339,354,1398),('p355_360',355,360,315),('p361_385',361,385,1357),('p386_407',386,407,831),('p408_427',408,427,730)]
for folder,start,end,count in parts:
    path=HERE/'parts'/folder
    part=json.loads((path/'translations.json').read_text('utf-8'))
    expected={u['id'] for u in source if start<=u['pdf_page']<=end}
    assert len(part)==len(expected)==count and set(part)==expected,(folder,'coverage')
    assert not set(part)&set(texts)
    texts.update(part)
    addnotes=json.loads((path/'notes.json').read_text('utf-8'))
    assert set(addnotes)<=expected and not set(addnotes)&set(notes)
    notes.update(addnotes)
# Approved glossary correction in the previously saved fragment.
for k in list(texts):
    if k in json.loads(initial.read_text('utf-8')):
        texts[k]=texts[k].replace('соратников [companions]','компаньонов [companions]').replace('соратника [companion]','компаньона [companion]')
texts['rr.p0336.t01.r011.c04']=texts['rr.p0336.t01.r011.c04'].replace('в пограничье [outlands]','на окраинных землях [outlands]')
for k in ('rr.p0336.t01.r005.c04','rr.p0336.t01.r006.c04','rr.p0336.t01.r017.c04'):
    texts[k]=texts[k].replace('Последователи [followers] получают +4 к боевому духу [morale] и верности [loyalty]','Боевой дух [morale] и верность [loyalty] Последователей [followers]: +4')
notes['rr.p0336.t01.r017.c03']='Разночтение оригинала: таблица даёт Шаманов-Последователей 1–3-го уровней, а описание класса `rr.p0073.b011` — только 1-го. Оба английских места проверены; исходные уровни не унифицированы.'
notes['rr.p0336.t01.r017.c04']='Разночтение оригинала: таблица и описание Шамана `rr.p0073.b011` дают боевой дух и верность +4. Однако общий абзац `rr.p0337.b004` назначает +4 только Последователям Крестоносца и Девы клинков, а всем остальным классам — начальную верность +2 и обычный боевой дух с +1. Все английские места сверены; таблица и общее правило сохранены.'
for k,v in notes.items():
    # Every technical reference must be removable from the compact reader.
    v=re.sub(r'^\*\s*`'+re.escape(k)+r'`:\s*','',v)
    v=re.sub(r'(?<![`\w])rr\.p\d{4}(?:\.t\d{2}\.r\d{3}\.c\d{2}|\.b\d{3})(?![`\w])',lambda m:'`'+m[0]+'`',v)
    notes[k]=v
assert set(texts)=={u['id'] for u in source}
texts={u['id']:texts[u['id']] for u in source}
notes={u['id']:notes[u['id']] for u in source if u['id'] in notes}
(HERE/'styled.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2)+'\n','utf-8')
(HERE/'notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n','utf-8')
changes={k:{'before':v,'after':texts[k],'reason':'Независимая вычитка: термины глоссария; outlands; начальный показатель +4 вместо неоднозначного бонуса.'} for k,v in json.loads(initial.read_text('utf-8')).items() if v!=texts[k]}
(HERE/'initial_fragment_corrections.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n','utf-8')
print('Merged',len(texts),'units;',len(notes),'notes; corrected initial IDs:',list(changes))
