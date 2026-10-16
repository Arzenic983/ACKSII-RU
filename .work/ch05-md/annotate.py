"""Repeat bilingual rule terms in chapter 5 only; keep a separate pure-Russian package."""
import json,re
from auto_units import HERE,records,write_records,terms
def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'));source={u['id']:u for u in units}
    names=terms();values=records(HERE/'automatic.md');count=0
    spell_rules=[]
    for line in (HERE/'spell_terms.txt').read_text('utf-8').splitlines():
        if not line or line.startswith('#'):continue
        eng,rus=line.split(' | ',1);words=rus.split()
        if len(words)==1 and len(rus)<7:continue
        pats=[]
        for word in words:
            stem=re.sub(r'(?:ение|ание|ость|ые|ая|ое|ий|ый|ой|его|ее|ие|а|я|ь|о|е)$','',word,flags=re.I)
            pats.append(re.escape(stem)+r'[а-яё]*' if len(stem)>=4 else re.escape(word))
        spell_rules.append((eng,re.compile(r'(?<![А-Яа-яЁё])'+r'\s+'.join(pats)+r'(?![А-Яа-яЁё])',re.I)))
    rules=[
    (r'заклинател[а-яё]*','caster'),(r'Арбитр[а-яё]*','Judge'),(r'репертуар[а-яё]*','repertoire'),
    (r'спасброс[а-яё]*','saving throw'),(r'брос(?:ок|ка|ки|ков|кам|ками|ке) атак[а-яё]*','attack throw'),
    (r'концентрац[а-яё]*','concentration'),(r'инициатив[а-яё]*','initiative'),
    (r'раунд[а-яё]*','round'),(r'ход(?:а|ов|ами|ам|ах|ом|е|у|ы)?','turn'),
    (r'навык[а-яё]*','proficiency'),(r'КБ','AC'),(r'КЗ','HD'),(r'ОЗ','hp'),(r'КОЗ','shp'),
    (r'СИЛ','STR'),(r'ЛОВ','DEX'),(r'ТЕЛ','CON'),(r'ИНТ','INT'),(r'ХАР','CHA'),(r'ВОЛ','WIL'),
    (r'нежит[а-яё]*','undead'),(r'гуманоид[а-яё]*','humanoid'),(r'приспешник[а-яё]*','henchman'),
    (r'спутник[а-яё]*','hireling'),(r'боев(?:ая|ой|ую|ые|ых|ом|ому|ым|ыми) скорост[а-яё]*','combat speed'),
    (r'скорост[а-яё]* исследовани[а-яё]*','exploration speed'),(r'экспедиционн[а-яё]* скорост[а-яё]*','expedition speed'),
    (r'нагрузк[а-яё]*','encumbrance'),(r'лини[а-яё]* видимост[а-яё]*','line of sight'),
    (r'радиус[а-яё]* действи[а-яё]*','range'),(r'област[а-яё]* действи[а-яё]*','area of effect'),
    (r'мировоззрени[а-яё]*','alignment'),(r'класс[а-яё]* брони','Armor Class'),
    (r'кост[а-яё]* здоров[а-яё]*','Hit Dice'),(r'очк[а-яё]* здоров[а-яё]*','hit points'),
    (r'парализован[а-яё]*','paralyzed'),(r'беспомощн[а-яё]*','helpless'),(r'разъяр[а-яё]*','infuriated'),
    (r'околдован[а-яё]*','bewitched'),(r'зачарован[а-яё]*','enchanted'),(r'ослепл[а-яё]*','blinded'),
    (r'устраш[а-яё]*','frightened'),(r'нерешительн[а-яё]*','faltering'),(r'безумн[а-яё]*','mad'),
    (r'спрятан[а-яё]*','hidden'),(r'опрокинут[а-яё]*','prone'),(r'дремл[а-яё]*','slumbering'),
    (r'маг(?:и|ом|а|ам|ами|ах|е|ов)?','Mage'),(r'воин[а-яё]*','Fighter'),
    (r'Маскировк[а-яё]*','Disguise'),(r'Мореплавани[а-яё]*','Seafaring'),
    (r'получател[а-яё]*','recipient'),(r'цел(?:ь|и|ью|ей|ям|ями|ях)','target'),
    (r'иллюзи[а-яё]*','illusion'),(r'уров[а-яё]* заклинател[а-яё]*','caster level'),
    (r'загруженност[а-яё]*','encumbrance'),(r'брос[а-яё]* внезапност[а-яё]*','surprise roll'),
    (r'укрыти[а-яё]*','concealment'),(r'предмет[а-яё]* маги[а-яё]*','magic item'),
    (r'глух(?:ой|ое|ие|ого|ому|им|их|ими|ом|ую|ая)','deafened'),
    (r'неуязвим[а-яё]*','immune'),(r'устойчив[а-яё]*','resistant'),
    (r'опутан[а-яё]*','webbed'),(r'схвачен[а-яё]*','grabbed'),(r'скован[а-яё]*','restrained'),
    (r'Плавани[а-яё]*','Swimming'),(r'Трансмогрификаци[а-яё]*','Transmogrification'),
    (r'Элементализм[а-яё]*','Elementalism'),(r'Рассечени[а-яё]*','Cleave'),
    ]
    combined=re.compile(r'(?<![А-Яа-яЁёA-Za-z])(?:'+'|'.join('(?P<t'+str(i)+'>'+pat+')' for i,(pat,en) in enumerate(rules))+r')(?![А-Яа-яЁёA-Za-z])',re.I)
    raw={'HD':'КЗ [HD]','Hit Dice':'Кости Здоровья [Hit Dice]','AC':'КБ [AC]','CON':'ТЕЛ [CON]','КОН':'ТЕЛ [CON]',
         'DEX':'ЛОВ [DEX]','STR':'СИЛ [STR]','INT':'ИНТ [INT]','CHA':'ХАР [CHA]','WIL':'ВОЛ [WIL]',
         'hp':'ОЗ [hp]','HP':'ОЗ [HP]','shp':'КОЗ [shp]','sHP':'КОЗ [shp]','NPC':'НИП [NPC]',
         'Mystic Aura':'Мистическая аура [Mystic Aura]','gp':'зм','sp':'см','cp':'мм'}
    raw.update({'permanent':'постоянная [permanent]','self':'на себя [self]','touch':'касание [touch]',
        'Spells':'Заклинания [Spells]','Blinded':'Ослеплённый [Blinded]','bewitch':'Околдованный [bewitched]',
        'faltering':'Нерешительный [faltering]','Climbing':'Лазание [Climbing]'})
    raw.update({'Dominated':'Задоминированный [Dominated]','Prone':'Опрокинутый [Prone]',
        'Enslaved':'Порабощённый [Enslaved]','Forgetful':'Забывчивый [Forgetful]',
        'Flanked':'Фланкированный [Flanked]','bewitchments':'околдования [bewitchments]',
        'Contortionism':'Гибкость [Contortionism]','Black Lore of Zahar':'Темные знания Захарийцев [Black Lore of Zahar]',
        'Tampering with Mortality':'Игра со смертью [Tampering with Mortality]',
        'Savage Mortal Wounds':'Жестокие смертельные раны [Savage Mortal Wounds]',
        'Permanent Wounds Suffered':'Полученные постоянные раны [Permanent Wounds Suffered]',
        'magic research throw':'бросок магических исследований [magic research throw]',
        'curse':'проклятие [curse]','Listening':'Подслушивание [Listening]',
        'anti-magic sphere':'Антимагическая сфера [anti-magic sphere]','SHP':'КОЗ [shp]',
        'weakness of mind':'Слабость разума [weakness of mind]','Dungeonbashing':'Проламывание [Dungeonbashing]'})
    rawpattern=re.compile(r'(?<![A-Za-z])('+ '|'.join(re.escape(k) for k in sorted(raw,key=len,reverse=True))+r')(?![A-Za-z])')
    for id,text in values.items():
        en=source[id]['source_plain']
        def link(m):
            inner=m[1].split('/')[-1].strip();latin=re.match(r'([A-Za-z][A-Za-z ,’\-]+)',inner)
            key=latin[1].strip() if latin else ''
            if key.lower() in names:return names[key.lower()]+' ['+key+']'
            states={'helpless':'Беспомощный','searching':'Поиск','land surveying':'Геодезия','faltering':'Нерешительный'}
            if key.lower() in states:return states[key.lower()]+' ['+key+']'
            named=re.fullmatch(r'([^()]+)\s*\(([^()]+)\)',inner)
            if named and re.search('[A-Za-z]',named[1]):return named[2].strip()+' ['+named[1].strip()+']'
            return inner.replace('✪','').strip()
        text=re.sub(r'\[\[([^\]]+)\]\]',link,text)
        # Match established Russian spell names only when this English unit
        # actually mentions that spell; labels already present are protected.
        for eng,pat in spell_rules:
            if not re.search(r'(?<![A-Za-z])'+re.escape(eng)+r'(?![A-Za-z])',en,re.I):continue
            ps=re.split(r'(\[[^\[\]\n]*\])',text)
            for j,p in enumerate(ps):
                if j%2:continue
                def spell_add(m):
                    if j+1<len(ps) and re.fullmatch(r'[\s*»”"]*',p[m.end():]):return m[0]
                    return m[0]+' ['+eng+']'
                ps[j]=pat.sub(spell_add,p)
            text=''.join(ps)
        # Correct unambiguous legacy names for the acting caster and the Judge.
        substitutions={'кастер':'заклинатель','кастера':'заклинателя','кастеру':'заклинателю','кастером':'заклинателем','кастеры':'заклинатели','кастеров':'заклинателей',
                       'судья':'Арбитр','судьи':'Арбитра','судье':'Арбитру','судью':'Арбитра','судьей':'Арбитром','судьёй':'Арбитром'}
        if re.search(r'\b(?:his familiar|has a familiar|familiar’s)\b',en,re.I):
            substitutions.update({'знакомый':'Фамильяр','знакомого':'Фамильяра','знакомому':'Фамильяру','знакомым':'Фамильяром','знакомые':'Фамильяры'})
        if re.search(r'\bcaster\b',en,re.I) and not re.search(r'\bmaster\b',en,re.I):
            substitutions.update({'мастер':'заклинатель','мастера':'заклинателя','мастеру':'заклинателю','мастером':'заклинателем'})
        if re.search(r'\bcaster\b',en,re.I) and not re.search(r'\bmages?\b',en,re.I):
            substitutions.update({'маг':'заклинатель','мага':'заклинателя','магу':'заклинателю','магом':'заклинателем','маги':'заклинатели','магов':'заклинателей'})
        # Operate outside existing English labels; avoid doubled annotations.
        parts=re.split(r'(\[[^\[\]\n]*\])',text)
        result=[]
        for i,part in enumerate(parts):
            if i%2:result.append(part);continue
            for a,b in substitutions.items():part=re.sub(r'\b'+a+r'\b',b,part,flags=re.I)
            part=rawpattern.sub(lambda m:raw[m[0]],part)
            # Labels just inserted above must also be protected from scanning.
            def add(m):
                nonlocal count
                tail=part[m.end():]
                existing=(i+1<len(parts) and re.search('[A-Za-z]',parts[i+1]) and re.fullmatch(r'[\s*»”\"]*',tail) is not None)
                if existing or re.match(r'[\s*»”\"]*\[[^\]]*[A-Za-z]',tail):return m[0]
                label=rules[int(m.lastgroup[1:])][1]
                if label=='hireling' and not re.search(r'\bhirelings?\b',en,re.I):return m[0]
                if label=='henchman' and not re.search(r'\bhenchm[ae]n\b',en,re.I):return m[0]
                if label=='Mage' and not re.search(r'\bmages?\b',en,re.I):return m[0]
                if label=='Fighter' and not re.search(r'\bfighters?\b',en,re.I):return m[0]
                if label in ('immune','resistant','concealment') and not re.search(r'\b'+label+r'\b',en,re.I):return m[0]
                count+=1
                return m[0]+' ['+label+']'
            subparts=re.split(r'(\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\])',part)
            # Scan the original part only where a match does not fall in a label.
            protected=[(m.start(),m.end()) for m in re.finditer(r'\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\]',part)]
            def safeadd(m):
                if any(a<=m.start()<b for a,b in protected):return m[0]
                return add(m)
            part=combined.sub(safeadd,part)
            result.append(part)
        text=''.join(result)
        text=text.replace('XX XX','[неуточнённая ссылка]')
        assert '[[' not in text,id
        values[id]=text
    write_records(HERE/'automatic.md',values)
    print('Additional repeated annotations',count)
if __name__=='__main__':main()
