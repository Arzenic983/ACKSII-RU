"""Translate invariant cells and glossary lists; no database writes."""
from pathlib import Path
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def records(path):
    text=path.read_text('utf-8')
    found=list(re.finditer(r'<!-- unit: (rr\.[^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',text,re.S))
    assert len(found)==len({m[1] for m in found}), str(path)
    return {m[1]:m[2].strip() for m in found}

def write_records(path,values):
    path.write_text('\n\n'.join(f'<!-- unit: {k} -->\n{v}' for k,v in values.items())+'\n','utf-8')

def labels():
    gs=json.loads((ROOT/'ACKSII/База перевода/glossary.json').read_text('utf-8'))
    names={}
    for g in gs:
        if g['category']=='Классы' or 'Навыки' in g['category']:
            names[g['term_en'].casefold()]=g['term_ru'].strip(' ?')
    names.update({k.casefold():v for k,v in {
        'Witch':'Ведьма','Elven Spellsword':'Эльфийский мечник-чародей',
        'Nobiran Wonderworker':'Нобирийский чудотворцец','Zaharan Ruinguard':'Захарийский страж руин',
        'Art':'Искусство','Craft':'Ремесло','Fighting Style':'Боевой стиль',
        'Fighting Style Specialization':'Специализация на боевом стиле',
        'Kin- Slaying':'Убийца родичей','Passing without Trace':'Проход без следа',
    }.items()})
    return names

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    names=labels()
    headings={
        '3 PROFICIENCIES':'3 Навыки','PROFICIENCIES':'Навыки',
        'THE BASICS OF PROFICIENCIES':'Основы навыков','STARTING PROFICIENCIES':'Начальные навыки',
        'GAINING PROFICIENCIES':'Получение навыков',
        'GAINING PROFICIENCIES BY TIME AND TRAINING (OPTIONAL)':'Получение навыков со временем и через обучение (опциональное правило)',
        'RETRAINING PROFICIENCIES (OPTIONAL)':'Переобучение навыкам (опциональное правило)',
        'PROFICIENCIES GAINED PER LEVEL':'Навыки, получаемые по уровням',
        'PROFICIENCIES OF NORMAL HUMANS AND DEMI-HUMANS':'Навыки обычных людей и полулюдей',
        'PROFICIENCY LISTS':'Списки навыков','PROFICIENCY DESCRIPTIONS':'Описания навыков',
        'FIGHTING STYLE SPECIALIZATIONS':'Специализации на боевом стиле',
    }
    progression={'ANIMAL HUSBANDRY':'Уход за животными','ANIMAL TRAINING':'Дрессировка','ART/CRAFT':'Искусство/Ремесло','HEALING':'Целительство','KNOWLEDGE':'Знания','PERFORMANCE':'Выступление','PROFESSION':'Профессия'}
    headings.update({k+' PROFICIENCY PROGRESSION':'Развитие навыка «'+v+'»' for k,v in progression.items()})
    tricks={'disarm':'обезоруживание [disarm]','incapacitate':'выведение из строя [incapacitate]','force back':'оттеснение [force back]','knock down':'сбивание с ног [knock down]','overrun':'Пробиться [Overrun]','wrestling':'борьба [wrestling]','sunder':'Разделение [Sunder]','judge':'судья [judge]'}
    def term(s):
        m=re.fullmatch(r'(.+?)(?: \(([^)]+)\))?',s.strip())
        name,sub=m.groups()
        en=name.replace('Kin- Slaying','Kin-Slaying')
        ru=names[name.casefold()]+f' [{en}]'
        if sub:ru+=' ('+', '.join(tricks[x] for x in sub.split(', '))+')'
        return ru
    values={}
    missing=[]
    for u in units:
        en=u['source_markup'];id=u['id']
        if u['kind']=='heading':
            if en in headings:values[id]=headings[en]
            else:
                key=re.sub(r' \(G\)$','',en).casefold()
                values[id]=names[key]+(' (G)' if en.endswith(' (G)') else '')
        elif 'Proficiency List:**' in en:
            title,body=en.split(':** ',1)
            cname=title.removeprefix('**').removesuffix(' Proficiency List')
            title_ru='Общий список навыков' if cname=='General' else 'Список навыков: '+names[cname.casefold()]+f' [{cname}]'
            items=re.split(r', (?![^()]*\))',body)
            values[id]='**'+title_ru+':** '+', '.join(term(x) for x in items)
        elif u['table_id']:
            if not re.search('[A-Za-z]',u['source_plain']):values[id]=en
            elif re.fullmatch(r'\d+gp',en):values[id]=en[:-2]+' зм'
            elif en in ('C','G','C + G'):values[id]=en
            elif en.casefold() in names:values[id]=term(en)
            else:missing.append((id,en))
    write_records(HERE/'automatic.md',values)
    print('Automatic units:',len(values))
    print('\n'.join(id+' | '+en for id,en in missing))

if __name__=='__main__':main()
