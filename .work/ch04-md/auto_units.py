"""Translate invariant table cells and reviewed terminology, retaining all source IDs."""
from pathlib import Path
import json
import re
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def records(path):
    matches=list(re.finditer(r'<!-- unit: (rr\.[^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',path.read_text('utf-8'),re.S))
    assert len(matches)==len({m[1] for m in matches}),str(path)
    return {m[1]:m[2].strip() for m in matches}

def write_records(path,values):
    path.write_text('\n\n'.join(f'<!-- unit: {k} -->\n{v}' for k,v in values.items())+'\n','utf-8')

def terms():
    values={}
    for line in (HERE/'terms.txt').read_text('utf-8').splitlines():
        if not line.strip() or line.startswith('#'):continue
        en,ru=line.split(' | ',1)
        assert en not in values or values[en]==ru,en
        values[en]=ru
    return values

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    previous=json.loads((HERE/'previous_exact.json').read_text('utf-8'))
    names=terms()
    prefixes=dict(line.split(' | ',1) for line in (HERE/'prefixes.txt').read_text('utf-8').splitlines() if line.strip())
    replacements={'gp':'зм','sp':'см','cp':'мм','ep':'эм','pp':'пм',
        'STR mod':'мод. СИЛ [STR]','Cleave':'Рассечение [Cleave]',
        'Handy':'Одноручное [Handy]','Slow':'Медленное [Slow]','Thrown':'Метательное [Thrown]',
        'Impact':'Ударное [Impact]','Long':'Длинное [Long]','Mounted':'Всадническое [Mounted]',
        'Silver':'Серебряное [Silver]','Entangling':'Опутывающее [Entangling]',
        'Incapacitating':'Оглушающее [Incapacitating]','Flexible':'Гибкое [Flexible]',
        'turns':'ходов [turns]','turn':'ход [turn]','rounds':'раундов [rounds]','round':'раунд [round]',
        'hours':'часов','hour':'час','days':'дней','day':'день','weeks':'недель','week':'неделя',
        'damage':'урона','Paralysis':'Паралич [Paralysis]','Incapacitation':'Недееспособность [Incapacitation]',
        'or less':'или меньше','or more':'или больше','value':'стоимости',
        'mundane piercing':'обычного колющего','mundane slashing':'обычного рубящего',
        'mundane bludgeoning':'обычного дробящего','mundane fire':'обычного огненного',
        'mundane poisonous':'обычного ядовитого',
        'extraordinary piercing':'особого колющего','extraordinary bludgeoning':'особого дробящего',
        'mundane seismic':'обычного сейсмического',
        'injury':'через рану','ingestion':'при проглатывании',
        'Madness':'Безумие [Madness]','madness':'безумие [madness]',
        'paralysis':'паралич [paralysis]','queasy':'тошнота [queasy]',
        'Death':'Смерть [Death]','Instant':'Мгновенно [Instant]',
        'month':'месяц','page':'страница','day/patient':'день/пациент',
        'st':'стоунов','lbs':'фунт.','lb':'фунт.','tons':'тонн',
        'shp':'КОЗ [shp]','cf':'куб. фут','f':'фут [f]',
        'fire':'огненного урона [fire]','radius':'радиус','diameter':'диаметр',
        'line':'линия','grapple':'захват [grapple]',
        'Crew':'членов расчёта [Crew]','Wood':'Дерево [Wood]','Stone':'Камень [Stone]',
        'or':'или','vessel':'стоимости судна [vessel]','in':'в','x':'×',
    }
    def mechanical(en):
        s=en
        for a,b in sorted(replacements.items(),key=lambda x:-len(x[0])):
            s=re.sub(r'(?<![A-Za-z])'+re.escape(a)+r'(?![A-Za-z])',lambda m:b,s)
        s=re.sub(r'(?<=\d)(?=(?:зм|см|мм|эм|пм))',' ',s)
        s=re.sub(r'(?<=\d)(?=[А-Яа-яЁё])',' ',s)
        # Already-added English annotations do not count as untranslated prose.
        left=re.sub(r'\[[^\]]*\]','',s)
        left=re.sub(r'<br\s*/?>','',left)
        left=re.sub(r'\d+d\d+!?','',left)
        left=re.sub(r'\b[IVX]+\b','',left)
        if re.search('[A-Za-z]',left):return None
        # Preserve original damage bracket and give its exact English name beside it.
        for en_damage in ('mundane piercing','mundane slashing','mundane bludgeoning','mundane fire','mundane poisonous','extraordinary piercing','extraordinary bludgeoning','mundane seismic'):
            ru_damage=replacements[en_damage]
            s=s.replace('['+ru_damage+']','['+ru_damage+'] ['+en_damage+']')
        return s
    dimensions={'long':'в длину','wide':'в ширину','high':'в высоту','tall':'в высоту','thick':'толщиной',
        'deep':'в глубину','diameter':'диаметром','square feet':'кв. футов','square':'по стороне',
        'mile':'миля','tons':'тонн','lbs':'фунтов','lb':'фунт','st':'стоунов',
        'one flight':'один пролёт','in adit':'в штольне','crenellated parapets':'зубчатый парапет',
        'gatehouse':'надвратное укрепление','small towers':'малые башни','drawbridge':'подъёмный мост',
        'basement':'подвал','hot pool':'горячий бассейн','tepid pool':'тёплый бассейн',
        'cold pool':'холодный бассейн','sauna':'сауна','stage':'сцена','and':'и',
        'heavy horses':'тяжёлые лошади','heavy horse':'тяжёлая лошадь','light horses':'лёгкие лошади',
        'medium horses':'средние лошади','mules':'мула','mule':'мул',
        'colossal creature':'колоссальное существо','gigantic creature':'гигантское существо',
        'huge creature':'огромное существо','gallon':'галлонов'}
    def compose(en):
        for prefix,ru in sorted(prefixes.items(),key=lambda x:-len(x[0])):
            if not en.startswith(prefix+' ('):continue
            tail=en[len(prefix):]
            for a,b in sorted(dimensions.items(),key=lambda x:-len(x[0])):
                tail=re.sub(r'(?<![A-Za-z])'+re.escape(a)+r'(?![A-Za-z])',lambda m:b,tail)
            if re.search('[A-Za-z]',tail.replace('x','×')):return None
            return ru+' ['+prefix+']'+tail.replace('x','×')
        return None
    values={};missing=[]
    for u in units:
        if not u['table_id']:continue
        en=u['source_markup'];ru=None
        if en in names:
            ru=names[en]
            if u['row_index']!=0 and re.search('[A-Za-z]',en) and len(en)<150 and not re.search(r'\[[^\]]*[A-Za-z]',ru):
                ru+=' ['+re.sub(r'<br\s*/?>',' ',en)+']'
        elif en in previous and len(en)<100:
            ru=mechanical(en)
            if ru is None:
                ru=previous[en]
                if u['row_index']!=0 and re.search('[A-Za-z]',en) and not re.search(r'\[[^\]]*[A-Za-z]',ru) and not re.fullmatch(r'[\d\s.,+×*/%–—-]+|[IVX]+|\d+d\d+.*',en):
                    ru+=' ['+re.sub(r'<br\s*/?>',' ',en)+']'
        if ru is None:ru=compose(en)
        if ru is None:ru=mechanical(en)
        if ru is None:missing.append((u['id'],en))
        else:values[u['id']]=ru
    write_records(HERE/'automatic.md',values)
    unknown={}
    for id,en in missing:unknown.setdefault(en,[]).append(id)
    (HERE/'missing_table_terms.json').write_text(json.dumps(unknown,ensure_ascii=False,indent=2),'utf-8')
    print('Translated table units:',len(values),'/',sum(u['table_id'] is not None for u in units),'distinct remaining:',len(unknown))
    print('\n'.join(unknown)[:2000])

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
