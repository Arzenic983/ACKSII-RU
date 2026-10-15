"""English reading aids derived from the project glossary and aligned source units.

This decorates Markdown for reading. It never changes translations or English source.
"""
import collections, html, json, pathlib, re, sqlite3

RU=r'А-Яа-яЁё'
PLAIN_SKIP={'Notes','EXAMPLE','Example','Proficiency Progression','Combat Proficiencies','Combat Progression','Air','Earth','Water'}
SYSTEM_KEEP={'Judge','Class powers','Armor Class (AC)','Hit Dice','Hit Points','PC','NPC','Mercantile Ventures','Arcane power','Hex','Evasion','Reactions','Readied to Attack/combat action','initiative number','line of sight','Unholy, Holy','extraordinary (damage)','Resistance','enchanted','Spell-like','concentration','a second-rank combatant’s','Lance','Staff','Rod','Wand','Polearm','Full Round Actions','Movement Actions','Combat Actions','Ready Action','Mortal Wounds','permanent wound','Tampering with Mortality','nonlethal','lay on hands','Countercharge','proselytizing','Caster','Encumbrance','alignment','Hijinks'}
CLASS_KEEP={'Bladedancer','Crusader','Venturer','Warlock','Witch','Dwarven Vaultguard','Dwarven Craftpriest','Elven nightblade','Elven spellswords','Nobiran wonderworker','Zaharan ruinguard'}
STRONGHOLD_KEEP={'Vault','Lair','Fastness','Sanctum','Cloister','Medicine Lodge','Cottage','Guildhouse','Dark Fortress','Border Fort','Fortified Church'}

def fold(s):return s.lower().replace('ё','е')

def word_pattern(w):
    w=fold(w)
    irregular={'бой':r'бо(?:й|я|ю|ем|и|ев|ям|ями|ях)','бросок':r'брос(?:ок|к[а-я]*)','замок':r'зам(?:ок|к[а-я]*)','порядок':r'поряд(?:ок|к[а-я]*)','клинок':r'клин(?:ок|к[а-я]*)','торговец':r'торгов(?:ец|ц[а-я]*)','певец':r'пев(?:ец|ц[а-я]*)','чтец':r'чте(?:ц|ц[а-я]*)','руки':r'рук[а-я]*','рук':r'рук[а-я]*','путь':r'пут(?:ь|и|ем|ей|ям|ями|ях)'}
    if w in irregular:return irregular[w]
    if len(w)<=3:return re.escape(w)
    if w.endswith(('ение','ание','ствие','тие','ия')):stem=w[:-1]
    elif w.endswith('ость'):stem=w[:-1]
    elif len(w)>=5 and w.endswith(('ая','яя','ое','ее','ый','ий','ой','ые','ие','ую','юю','ых','их','ым','им','ом','ем','ей')):stem=w[:-2]
    elif w.endswith(('а','я','ь','ы','и','у','ю','е')):stem=w[:-1]
    else:stem=w
    if len(stem)<3:return re.escape(w)
    return re.escape(stem)+r'[а-я]{0,6}'

def ru_pattern(s):
    words=re.findall(r'[А-Яа-яЁё]+|[A-Za-z]+',s)
    if not words:return None
    sep=r'(?:\s|<br\s*/?>|[-–—/])+'
    return re.compile(r'(?<!['+RU+r'A-Za-z])'+sep.join(word_pattern(w) if re.search('['+RU+']',w) else re.escape(w) for w in words)+r'(?!['+RU+r'A-Za-z])',re.I)

def english_pattern(names):
    parts=[]
    for name in names:
        name=name.strip(' ()*.,;:')
        words=re.findall(r"[A-Za-z]+(?:[’'][a-z]+)?",name.replace('&',' and '))
        if not words:continue
        p=[]
        for w in words:
            v=re.escape(w)
            if w.lower().endswith('ies'):v=re.escape(w[:-3])+r'(?:y|ies)'
            elif w.lower().endswith('s') and len(w)>3:v=re.escape(w[:-1])+r's?'
            elif len(w)>3:v+=r'(?:s|es)?'
            p.append(v)
        parts.append(r'\b'+r'[\s/&,–—-]+'.join(p)+r'\b')
    return re.compile('|'.join(parts),re.I) if parts else re.compile(r'(?!x)x')

def italic_pairs(en,ru):
    def extract(t):
        t=re.sub(r'(?<!\*)\*(?!\*)\s*(?:<br\s*/?>)?\s*(?<!\*)\*(?!\*)',' ',t)
        return [x.strip(' .,;:()«»') for x in re.findall(r'(?<!\*)\*([^*\n]+)\*(?!\*)',t)]
    e,v=extract(en),extract(ru)
    if len(e)!=len(v):return []
    out=[]
    for a,b in zip(e,v):
        aa=re.split(r',\s*',a);bb=re.split(r',\s*',b)
        if len(aa)==len(bb):out.extend(zip(aa,bb))
        else:out.append((a,b))
    return [(a.strip(),re.sub(r'<br\s*/?>',' ',b).strip()) for a,b in out if a and a[0].islower() and 1<len(a)<65 and len(a.split())<=7 and re.search('[A-Za-z]',a) and not re.search('['+RU+']',a) and re.search('['+RU+']',b)]

class Annotator:
    def __init__(self,db_path,units,text):
        db=sqlite3.connect(pathlib.Path(db_path).as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        entries={}
        def add(ru,en,aliases=(),origin='project_glossary',global_match=False):
            ru=ru.strip(' ?«»');en=en.strip(' .:()')
            if not ru or not en or fold(ru)==fold(en):return
            key=(fold(ru),en.casefold())
            if key not in entries:entries[key]={'ru':ru,'en':en,'aliases':set(aliases)|{en},'origins':set(),'global':global_match}
            entries[key]['aliases'].update(aliases);entries[key]['origins'].add(origin)
        for g in db.execute('SELECT * FROM glossary ORDER BY id'):
            en,ru,cat=g['term_en'],g['term_ru'],g['category']
            keep=('Навыки' in cat or 'Состояния' in cat or cat in {'Особенности','Места','НПС','Типы (активности) деятельности','Авантюрные предприятия','Наёмники и прочие типы','Saving throw - Спасбросок'})
            if cat.startswith('Class Power'):keep=en!='Avoid surprise'
            if cat.startswith('Системные'):keep=en in SYSTEM_KEEP and en!='Staff'
            if cat=='Классы':keep=en in CLASS_KEEP
            if cat=='Крепости':keep=en in STRONGHOLD_KEEP
            if not keep:continue
            aliases=[r[0] for r in db.execute('SELECT alias FROM glossary_aliases WHERE term_id=?',(g['id'],))]
            if en=='Armor Class (AC)':en='Armor Class';aliases+=['AC']
            if en=='Hit Dice':aliases+=['Hit Die','HD']
            if en=='Hit Points':aliases+=['hp']
            if en=='extraordinary (damage)':en='extraordinary';aliases+=['extraordinary damage']
            if en=='Readied to Attack/combat action':en='Readied to Attack';aliases+=['readied combat action']
            if en=='Unholy, Holy':continue
            if en=='Elven spellswords':en='Elven Spellsword'
            add(ru,en,aliases)
        for row in db.execute("SELECT * FROM working_labels WHERE note LIKE '%главы 2%'"):
            add(row['term_ru'],row['term_en'],origin='working_label')
        header_kinds={}
        class_names={r[0].casefold() for r in db.execute("SELECT term_en FROM glossary WHERE category='Классы'")}
        for u in units:
            if u['chapter_id']=='02' and u['table_id'] and u['row_index']==0 and u['source_plain'].strip().upper() in {'TITLE','TEMPLATE','CASTE'}:
                header_kinds[(u['table_id'],u['column_index'])]=u['source_plain'].strip().lower()
        for u in units:
            if u['table_id'] and u['row_index']>0 and (u['table_id'],u['column_index']) in header_kinds:
                en=re.sub(r',?\s*\d+(?:st|nd|rd|th)\s+(?:lvl|level)\.?\s*$','',u['source_plain']).strip()
                ru=re.sub(r',?\s*\d+-[йгом]+\s+(?:ур\.|уровень)\s*$','',text[u['id']]).strip()
                if en.casefold() not in class_names and re.search('[A-Za-z]',en):add(ru,en,origin='aligned_'+header_kinds[(u['table_id'],u['column_index'])])
        # The same table heading can have a different sense from a save category.
        for u in units:
            if u['chapter_id']!='02':continue
            if u['kind']=='paragraph':
                a=re.match(r'^\*\*([^*]+):\*\*',u['source_markup']);b=re.match(r'^\*\*([^*]+):\*\*',text[u['id']])
                if a and b:
                    en=re.sub(r'\s*\([^)]*\)\s*$','',a[1]).strip();ru=re.sub(r'\s*\([^)]*\)\s*$','',b[1]).strip()
                    if en not in PLAIN_SKIP and 'Proficiency List' not in en and len(en)<70:add(ru,en,origin='aligned_class_power')
            for en,ru in italic_pairs(u['source_markup'],text[u['id']]) if u['kind']!='verse' else []:
                if en not in {'restored to life','resurrected','bewitched','forest enchantments'}:add(ru,en,origin='aligned_spell')
        custom=[
            ('Мифография','Loremastery',['lore mastery']),
            ('дальнобойное оружие','missile weapons',['missile weapon']),
            ('метательное оружие','missile weapons',['missile weapon']),
            ('дальнобойные атаки','missile attacks',['missile attack']),
            ('рукопашное оружие','melee weapons',['melee weapon']),
            ('спасбросок','saving throw',['saving throws','save','saves']),
            ('бросок атаки','attack throw',['attack throws']),
            ('классовая способность','class power',['class powers']),
            ('классовый навык','class proficiency',['class proficiencies']),
            ('общий навык','general proficiency',['general proficiencies']),
            ('воровское умение','thief skill',['thief skills']),
            ('учёный заклинатель','studious spellcaster',['studious spellcasters']),
            ('спонтанный заклинатель','spontaneous spellcaster',['spontaneous spellcasters']),
            ('тайная магия','arcane magic',['arcane casting']),('божественная магия','divine magic',['divine casting']),
            ('тайное заклинание','arcane spell',['arcane spells']),('божественное заклинание','divine spell',['divine spells']),
            ('ритуальное заклинание','ritual spell',['ritual spells']),
            ('репертуар заклинаний','spell repertoire',['spell repertoires']),('репертуар','repertoire',['repertoires']),
            ('гримуар','spellbook',['spellbooks']),('рассечение','cleave',['cleaving']),
            ('гримуар','grimoire',['grimoires']),
            ('боевые владения','Combat Proficiencies',[]),
            ('боевое развитие','Combat Progression',[]),
            ('развитие навыков','Proficiency Progression',[]),
            ('владение оружием','weapon proficiency',['weapon proficiencies']),
            ('владение доспехами','armor proficiency',['armor proficiencies']),
            ('начальный репертуар заклинаний','Starting Spell Repertoires',[]),
            ('уровень заклинателя','caster level',['caster levels']),
            ('дальнобойный','missile',[]),('рукопашный','melee',[]),
            ('близкий бой','melee combat',[]),('раунд внезапности','surprise round',[]),
            ('бросок внезапности','surprise roll',['surprise rolls']),
            ('исследовательская скорость','exploration speed',[]),('скорость исследования','exploration speed',[]),
            ('боевая скорость','combat speed',[]),('скорость бега','running speed',[]),
            ('приспешник','henchman',['henchmen']),('наёмник','mercenary',['mercenaries']),
            ('наёмник','sell-sword',['sell-swords']),('наёмник','man-at-arms',['men-at-arms']),
            ('пассивное вложение','passive investment',['passive investments']),('влияние на рынок','market impact',[]),
            ('Порядок','Law',['Order']),('порядочный','lawful',[]),('Хаос','Chaos',[]),('хаотичный','chaotic',[]),
            ('боевой дух','morale',[]),('верность','loyalty',[]),('ключевой атрибут','key attribute',['key attributes']),
            ('КБ','AC',['Armor Class']),('КЗ','HD',['Hit Die','Hit Dice']),('ОЗ','hp',['hit points']),
            ('проверка навыка','proficiency throw',['proficiency throws']),
            ('шаблон','template',['templates']),
            ('ночной клинок','Elven Nightblade',['nightblade','elven nightblade']),
            ('страж убежищ','Dwarven Vaultguard',['vaultguard','dwarven vaultguard']),
            ('мастер-жрец','Dwarven Craftpriest',['craftpriest','dwarven craftpriest']),
            ('мечник-чародей','Elven Spellsword',['spellsword','elven spellsword']),
            ('чудотворцец','Nobiran Wonderworker',['wonderworker','Nobiran wonderworker']),
            ('страж руин','Zaharan Ruinguard',['ruinguard','Zaharan ruinguard']),
            ('Одно оружие','Single Weapon',[]),('Парное оружие','Dual Weapon',[]),
            ('Двуручное оружие','Two-Handed Weapon',[]),('Оружие и щит','Weapon and Shield',[]),
        ]
        for ru,en,aliases in custom:add(ru,en,aliases,origin='source_terminology')
        self.entries=[]
        for e in entries.values():
            p=ru_pattern(e['ru'])
            if p is not None:
                e['pattern']=p;e['en_pattern']=english_pattern(e['aliases']);self.entries.append(e)
        self.entries.sort(key=lambda e:(-len(e['ru']),e['en']))
        self.stats=collections.Counter();self.by_unit=collections.defaultdict(list);self.db=db

    def annotate(self,id,ru,en,track=True):
        # Damage icon descriptions already use square brackets in the translation.
        # Keep those intact and place the English icon name beside the whole tag.
        damages=re.findall(r'\[(?:mundane|extraordinary) [a-z]+\]',en)
        ru_damage=list(re.finditer(r'\[[^\]\n]*['+RU+r'][^\]\n]*\]',ru))
        if damages and len(damages)==len(ru_damage):
            for m,label in reversed(list(zip(ru_damage,damages))):
                if not ru[m.end():].lstrip().startswith(label):ru=ru[:m.end()]+' '+label+ru[m.end():]
        elif len(damages)==1 and len(ru)<80 and not ru_damage:
            if not ru.rstrip().endswith(damages[0]):ru+=' '+damages[0]
        folded=fold(ru)
        protected=[(m.start(),m.end()) for m in re.finditer(r'\[[^\]\n]*\]|`[^`]*`|<[^>]+>',ru)]
        candidates=[]
        for e in self.entries:
            if not e['en_pattern'].search(en.replace('&',' and ')):continue
            for m in e['pattern'].finditer(folded):
                a,b=m.span()
                if any(a<q and b>p for p,q in protected):continue
                tail=re.sub(r'^\*+','',ru[b:])
                if re.match(r'\s*\['+re.escape(e['en'])+r'\]',tail,re.I):continue
                # A full name plus its Russian abbreviation is one reading aid.
                if e['en'] in {'Armor Class','Hit Dice','Hit Points'}:
                    extra=re.match(r'\s*\((?:КБ|КЗ|ОЗ)\)',ru[b:],re.I)
                    if extra:b+=extra.end()
                candidates.append((a,b,e))
        selected=[]
        for a,b,e in sorted(candidates,key=lambda v:(-(v[1]-v[0]),v[0],v[2]['en'])):
            if not any(a<y and b>x for x,y,_ in selected):selected.append((a,b,e))
        for a,b,e in sorted(selected,reverse=True,key=lambda v:v[0]):
            # Put annotations after closing emphasis, not inside a word or tag.
            end=b
            while end<len(ru) and ru[end]=='*':end+=1
            ru=ru[:end]+' ['+e['en']+']'+ru[end:]
            if track:self.stats[(e['ru'],e['en'])]+=1;self.by_unit[id].append(e['en'])
        for _,_,e in selected:
            ru=re.sub(r'(\['+re.escape(e['en'])+r'\])([»”\"]?)\s*\('+re.escape(e['en'])+r'\)',r'\1\2',ru,flags=re.I)
        return ru

    def decorate(self,units,text):
        decorated={}
        for u in units:
            id=u['id'];ru=text[id]
            is_header=u['kind']=='heading' or is_subheading(u) or (u['table_id'] and u['row_index']==0)
            decorated[id]=ru if is_header else self.annotate(id,ru,u['source_plain'])
        return decorated

    def write_catalog(self,path):
        out=['# Английские подписи терминов','','Рабочая карта для двуязычного оформления PDF-страниц 1–101. Английское имя выбирается по исходной единице; помета повторяется при каждом соответствующем употреблении. Это оформление для чтения, а не новая редакция утверждённого глоссария.','','| Русская форма | Английское имя | Употреблений с подписью |','| --- | --- | ---: |']
        for (ru,en),n in sorted(self.stats.items(),key=lambda v:(v[0][0].lower(),v[0][1])):out.append(f'| {ru} | {en} | {n} |')
        pathlib.Path(path).write_text('\n'.join(out)+'\n','utf-8')

def english_subtitle(u):
    return '<small>'+html.escape(re.sub(r'\s+',' ',u['source_plain']).strip())+'</small>'

def is_subheading(u):
    return bool(not u['table_id'] and u['kind']!='heading' and re.fullmatch(r'\*\*\*[^*\n]{2,80}\*\*\*',u['source_markup'].strip()))
