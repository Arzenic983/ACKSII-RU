from prepare import *

special = {
 'Starting Equipment':'Начальное снаряжение', 'Fighting Style Spec.':'Специализация на боевом стиле',
 'weapon & shield':'оружие и щит', 'weapon and shield':'оружие и щит', 'two-handed weapon':'двуручное оружие',
 'dual weapon':'два оружия', 'swords and daggers':'мечи и кинжалы', 'construction':'строительство',
 'disarm':'обезоруживание', 'force back':'оттеснение', 'knock down':'сбивание с ног', 'overrun':'Пробиться',
 'sunder':'Разделение', 'wrestling':'борьба', 'pole arms and spears':'древковое оружие и копья',
 'bows and crossbows':'луки и арбалеты', 'maces, flails, and hammers':'булавы, цепы и молоты',
 'maces and hammers':'булавы и молоты', 'trading':'торговля', 'merchant':'купец', 'acting':'актёрское искусство',
 'sailing':'Хождение под парусом', 'woodworking':'работа по дереву', 'armorer':'оружейник',
}
for r in db.execute('SELECT term_en,term_ru FROM glossary WHERE category LIKE ? OR category LIKE ?',('%Навыки%','%Особенности%')):
 special.setdefault(r[0],r[1])
special.update({'Key Attribute':'Ключевой атрибут','Requirements':'Требования','Hit Dice':'КЗ','Maximum Level':'Максимальный уровень','STR':'СИЛ','DEX':'ЛОВ','INT':'ИНТ','WIL':'ВОЛ','CON':'ТЕЛ','CHA':'ХАР','None':'Нет'})
classes={'FIGHTER':'Воина','EXPLORER':'Исследователя','THIEF':'Вора','MAGE':'Мага','CRUSADER':'Крестоносца','VENTURER':'Торговца'}
direct={'2 CLASSES':'2 Классы','CLASSES':'Классы','CORE CLASSES':'Основные классы','CHARACTER TEMPLATES AND INTELLECT':'Шаблоны персонажей и Интеллект','INTELLECT SCORES OF STUDIOUS SPELLCASTERS':'Интеллект учёных заклинателей',r'\* No adjustment from Constitution applies to this flat bonus.':r'\* К этому фиксированному бонусу не применяется модификатор Телосложения.'}
for en,ru in classes.items():
 direct[en+' LEVEL PROGRESSION']='Прогрессия '+ru.lower()+' по уровням'
 direct[en+' ATTACK AND SAVING THROWS']='Броски атаки и спасброски '+ru.lower()
 direct[en+' TEMPLATES']='Шаблоны '+ru.lower()
direct['EXPLORER (FIGHTER) ATTACK AND SAVING THROWS']='Броски атаки и спасброски исследователя (воина)'
def replace_terms(s):
 for k,v in sorted(special.items(),key=lambda kv:-len(kv[0])):
  s=re.sub(r'(?<![A-Za-z])'+re.escape(k)+r'(?![A-Za-z])',lambda m:v,s,flags=re.I)
 return s
data={}
for u in units:
 if not 24<=u['pdf_page']<=45 or u['id'] in auto:continue
 s=u['source_markup']; plain=u['source_plain']
 if s in direct:data[u['id']]=direct[s];continue
 if plain.upper() in direct:data[u['id']]=direct[plain.upper()];continue
 if s.startswith('♦ **'):
  t=replace_terms(s)
  if not re.search(r'[A-Za-ce-z]{2,}',t):data[u['id']]=t
 elif u['kind']=='table_cell' and ('<br>' in s or plain.lower() in {k.lower() for k in special}):
  t=replace_terms(s)
  if not re.search(r'[A-Za-z]{2,}',t.replace('<br>','')):data[u['id']]=t
 elif re.match(r'\*\*\w+ Proficiency List:',s):
  cls=re.match(r'\*\*(\w+) Proficiency List:',s)[1].upper()
  t=re.sub(r'^\*\*\w+ Proficiency List:', '**Список навыков '+classes[cls].lower()+':',s)
  t=replace_terms(t)
  if not re.search(r'[A-Za-z]{2,}',t):data[u['id']]=t
write_records(HERE/'generic_A.md',data)
done={**auto,**data}
write_records(HERE/'pending_A.md',{u['id']:u['source_markup'] for u in units if 24<=u['pdf_page']<=45 and u['id'] not in done})
print('GENERIC A',len(data),'PENDING',566-len(data))
