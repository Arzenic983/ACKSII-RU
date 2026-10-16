"""Create bilingual presentation without changing the pure Russian translation."""
from common import read,write,ROOT,HERE
from collections import Counter
import json,re
def stem(w):
    for ending in ('ение','ание','ость','его','ому','ыми','ими','ого','ая','яя','ое','ее','ые','ие','ий','ый','ой','а','я','ь','о','е','ы','и'):
        if w.lower().endswith(ending) and len(w)-len(ending)>=4:return re.escape(w[:-len(ending)])+r'[а-яё]*'
    return re.escape(w)+r'[а-яё]*' if len(w)>=5 else re.escape(w)
def pat(ru):return r'\s+'.join(stem(w) for w in ru.split())
rules=[]
def add(pattern,en,gate=True):rules.append((pattern,en,gate))
generic=[
(r'действи[а-яё]* полного раунда','full-round action'),(r'действи[а-яё]* движени[а-яё]*','movement action'),
(r'боев[а-яё]* действи[а-яё]*','combat action'),(r'подготовленн[а-яё]* действи[а-яё]*','readied action'),
(r'действи[а-яё]* вместо перемещени[а-яё]*','action in lieu of movement'),(r'действи[а-яё]* вместо атак[а-яё]*','action in lieu of attacking'),
(r'боев[а-яё]* скорост[а-яё]*','combat speed'),(r'скорост[а-яё]* исследовани[а-яё]*','exploration speed'),
(r'скорост[а-яё]* бега','running speed'),(r'экспедиционн[а-яё]* скорост[а-яё]*','expedition speed'),
(r'лини[а-яё]* видимост[а-яё]*','line of sight'),(r'пол[а-яё]* зрени[а-яё]*','field of view'),
(r'номер[а-яё]* инициатив[а-яё]*','initiative number'),(r'сегмент[а-яё]* инициатив[а-яё]*','initiative segment'),
(r'боев[а-яё]* дух[а-яё]*','morale'),(r'брос[а-яё]* реакци[а-яё]*','reaction roll'),
(r'брос[а-яё]* внезапност[а-яё]*','surprise roll'),(r'брос(?:ок|ка|ки|ков|кам|ками|ке) атак[а-яё]*','attack throw'),
(r'спасброс[а-яё]*','saving throw'),(r'инициатив[а-яё]*','initiative'),(r'раунд[а-яё]*','round'),
(r'ход(?:а|ов|ами|ам|ах|ом|е|у|ы)?','turn'),(r'Арбитр[а-яё]*','Judge'),
(r'КБ','AC'),(r'КЗ','HD'),(r'ОЗ','hp'),(r'КОЗ','shp'),(r'СИЛ','STR'),(r'ЛОВ','DEX'),(r'ТЕЛ','CON'),(r'ИНТ','INT'),(r'ХАР','CHA'),(r'ВОЛ','WIL'),
(r'кост[а-яё]* здоров[а-яё]*','Hit Dice'),(r'очк[а-яё]* здоров[а-яё]*','hit points'),
(r'очк[а-яё]* опыт[а-яё]*','experience points'),(r'опыт(?:а|у|ом|е)?','XP'),(r'нагрузк[а-яё]*','encumbrance'),
(r'навык[а-яё]*','proficiency'),(r'заклинател[а-яё]*','caster'),(r'репертуар[а-яё]*','repertoire'),
(r'целенаправленн[а-яё]* деятельност[а-яё]*','dedicated activity'),(r'вспомогательн[а-яё]* деятельност[а-яё]*','ancillary activity'),
(r'необратим[а-яё]* ран[а-яё]*','permanent wound'),(r'смертельн[а-яё]* ран[а-яё]*','Mortal Wounds'),
(r'игр[а-яё]* со смертью','Tampering with Mortality'),(r'особ[а-яё]* урон[а-яё]*','extraordinary damage'),
(r'нелетальн[а-яё]* урон[а-яё]*','nonlethal damage'),(r'точк[а-яё]* попадани[а-яё]*','impact point'),
(r'ударн[а-яё]* урон[а-яё]*','impact damage'),(r'дальнобойн[а-яё]* оружи[а-яё]*','missile weapon'),
(r'дальнобойн[а-яё]* атак[а-яё]*','missile attack'),(r'ближн[а-яё]* атак[а-яё]*','melee attack'),
(r'концентрац[а-яё]*','concentration'),(r'стоун[а-яё]*','stone'),
]
for a,b in generic:add(a,b,False)
for a,b in [(r'НИП','NPC'),(r'ПИ','PC')]:add(a,b,False)
for a,b in [(r'маг(?:и|ом|а|ам|ами|ах|е|ов)?','Mage'),(r'вор(?:ы|а|у|ом|е|ов|ам|ами|ах)?','Thief'),(r'бард[а-яё]*','Bard'),(r'воин[а-яё]*','Fighter'),(r'всадник[а-яё]*','rider'),(r'пассажир[а-яё]*','passenger'),(r'носител[а-яё]*','transporter'),(r'возниц[а-яё]*','driver'),(r'последовательност[а-яё]* атак[а-яё]*','attack sequence'),(r'ударн[а-яё]* оружи[а-яё]*','impact weapon')]:add(a,b)
for a,b in [(r'протискивани[а-яё]*','Squeezing'),(r'Уменьшени[а-яё]*','shrinking'),(r'представител[а-яё]*','face'),(r'Вол(?:я|и|ю|ей|е)','WIL')]:add(a,b)
add(r'вылазк[а-яё]*','delve',False)
add(r'экспедици[а-яё]*','expedition',False)
add(r'плавани[а-яё]*','voyage')
for a,b in [(r'ошараш[а-яё]*','surprised'),(r'запыхавш[а-яё]*','winded'),(r'бессознател[а-яё]*','unconscious'),(r'крадущ[а-яё]*','sneaking'),(r'трясущ[а-яё]*','cowering'),(r'дремлющ[а-яё]*','slumbering'),(r'кара[bб]кающ[а-яё]*','clambering')]:add(a,b,False)
for a,b in [(r'устойчив[а-яё]*','resistant'),(r'неуязвим[а-яё]*','immune'),(r'обычн[а-яё]* урон[а-яё]*','mundane damage'),(r'Скизостан[а-яё]*','Skysostan'),(r'лют[а-яё]* волк[а-яё]*','dire wolf'),(r'ламмасу','lammasu'),(r'кхепри','khepri'),(r'арбалест[а-яё]*','arbalest'),(r'стрелк[а-яё]*','darts'),(r'дротик[а-яё]*','javelins'),(r'умертви[а-яё]*','wights'),(r'обессилива[а-яё]*','enervate'),(r'вестник[а-яё]* рока','doombringer'),(r'опеленск[а-яё]*','Opelenean')]:add(a,b)
for ru,en in [('Вплотную','engaged'),('В беспорядке','disordered'),('Запыхавшийся','winded'),('Опрокинутый','prone'),('Уязвимый','vulnerable'),('Ошарашенный','surprised'),('Нерешительный','faltering'),('Устрашённый','frightened'),('Трясущийся','cowering'),('Голодный','hungry'),('Недокормленный','underfed'),('Оголодавший','starving'),('Обезвоженный','dehydrated'),('Переохлаждённый','hypothermic'),('Истощённый','fatigued'),('Недееспособный','incapacitated'),('Бессознательный','unconscious'),('Схваченный','grabbed'),('Скованный','restrained'),('Скрученный','wrestled'),('Застрявший','stuck'),('Крадущийся','sneaking'),('Дремлющий','slumbering'),('Ослеплённый','blinded'),('Карабкающийся','clambering'),('Фланкированный','flanked'),('Нижестоящий','subjacent'),('Спрятанный','hidden')]:
    add(pat(ru),en,False)
for a,en in [(r'проламывани[а-яё]*','Dungeonbashing'),(r'прятани[а-яё]*','Hiding'),(r'поиск[а-яё]*','Searching'),(r'подслушивани[а-яё]*','Listening'),(r'обезвреживани[а-яё]* ловуш[а-яё]*','Trapbreaking'),(r'прорывани[а-яё]*','Traversing'),(r'собирательств[а-яё]*','Foraging'),(r'форсированн[а-яё]* марш[а-яё]*','forced march'),(r'предварительн[а-яё]* сведени[а-яё]*','foreknowledge')]:add(a,en)
for ru,en in [('обычный дробящий','mundane bludgeoning'),('обычный огненный','mundane fire'),('обычный колющий','mundane piercing'),('особый некротический','extraordinary necrotic'),('особый урон излучением','extraordinary luminous')]:add(pat(ru),en)
# Reuse established glossary and working terms only in an English unit that mentions them.
pairs=[]
for g in json.loads((ROOT/'ACKSII/База перевода/glossary.json').read_text('utf-8')):
    ru=g['term_ru'];en=g['term_en']
    if re.fullmatch(r'[А-Яа-яЁё -]+',ru) and len(ru)>3:pairs.append((ru,en))
for line in (ROOT/'ACKSII/База перевода/bilingual_terms.md').read_text('utf-8').splitlines():
    cols=[s.strip() for s in line.strip('|').split('|')]
    if len(cols)>=2 and re.fullmatch(r'[А-Яа-яЁё -]+',cols[0]) and re.search('[A-Za-z]',cols[1]):pairs.append((cols[0],cols[1]))
    elif len(cols)>=2 and re.fullmatch(r'[А-Яа-яЁё -]+',cols[1]) and re.search('[A-Za-z]',cols[0]):pairs.append((cols[1],cols[0]))
for line in (ROOT/'.work/ch05-md/spell_terms.txt').read_text('utf-8').splitlines():
    if ' | ' in line:
        en,ru=line.split(' | ',1);pairs.append((ru,en))
for ru,en in pairs:
    if len(ru)>3 and re.fullmatch(r'[А-Яа-яЁё -]+',ru):add(pat(ru),en)
special={'thief':r'thie(?:f|ves)','henchman':r'henchm[ae]n','hit dice':r'hit di(?:ce|e)','saving throw':r'saving throws?'}
gates={}
def gate(en,source):
    if en not in gates:
        root=en[:-1] if en.lower().endswith('s') and not en.lower().endswith(('ss','ness')) else en
        p=special.get(en.lower(),re.escape(root)+r'(?:s|es)?')
        p=p.replace(r'\ and\ ',r'\ (?:and|&)\ ')
        gates[en]=re.compile(r'(?<![A-Za-z])'+p+r'(?![A-Za-z])',re.I)
    return gates[en].search(source) is not None
counts=Counter();units=read('source_units.json');pure=read('pure_translations.json')
def annotate(s,source):
    if not re.search('[А-Яа-яЁё]',s):return s
    active={}
    for pattern,en,gated in rules:
        if not gated or gate(en,source):active.setdefault(pattern,en)
    # Prefer multiword matches; a label replaces no Russian text.
    order=sorted(active,key=lambda p:(p.count(' ')+p.count(r'\s+'),len(p)),reverse=True)
    combined=re.compile(r'(?<![А-Яа-яЁёA-Za-z])(?:'+'|'.join('(?P<r'+str(i)+'>'+p+')' for i,p in enumerate(order))+r')(?![А-Яа-яЁёA-Za-z])',re.I)
    def sub(m):
        en=active[order[int(m.lastgroup[1:])]];counts[en]+=1
        return m[0]+' ['+en+']'
    result=combined.sub(sub,s)
    return re.sub(r'\[([^\[\]\n]+) \[([A-Za-z][^\[\]\n]*)\]\]',r'[\1] [\2]',result)
values={u['id']:annotate(pure[u['id']],u['source_plain']) if u['kind']!='heading' else pure[u['id']] for u in units}
write('bilingual_translations.json',values)
notes=read('notes.json')
bn={}
for id,ns in notes.items():
    source=next(u['source_plain'] for u in units if u['id']==id)
    bn[id]=[]
    for s in ns:
        # Preserve deliberately contextual English labels already written in notes.
        parts=re.split(r'(\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\])',s)
        out=[]
        for i,p in enumerate(parts):
            if i%2:out.append(p);continue
            linked=annotate(p,source)
            if i+1<len(parts):linked=re.sub(r' \[[^\]]+\](\s*)$',r'\1',linked)
            out.append(linked)
        bn[id].append(''.join(out))
write('bilingual_notes.json',bn)
write('annotation_counts.json',dict(counts))
print('Annotations',sum(counts.values()),'different terms',len(counts))
