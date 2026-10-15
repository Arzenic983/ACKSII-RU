import sqlite3, pathlib, re, collections, json, hashlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'ACKSII' / 'База перевода'
HERE = pathlib.Path(__file__).resolve().parent
db = sqlite3.connect(BASE / 'acksii_translation.sqlite')
db.row_factory = sqlite3.Row
units = [dict(r) for r in db.execute("SELECT * FROM units WHERE chapter_id='02' ORDER BY pdf_page,block_order,row_index,column_index,id")]

def records(path):
    if not path.exists(): return {}
    text = path.read_text('utf-8')
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'<!-- unit: (rr\.[^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)', text, re.S)}

def write_records(path, data):
    path.write_text('\n\n'.join('<!-- unit: '+k+' -->\n'+v for k,v in data.items())+'\n', 'utf-8')

memory = collections.defaultdict(set)
for r in db.execute("SELECT u.source_markup,t.text_ru FROM units u JOIN translations t ON t.unit_id=u.id WHERE u.pdf_page<=23"):
    memory[r[0]].add(r[1])
gloss = collections.defaultdict(set)
for r in db.execute('SELECT term_en,term_ru FROM glossary'):
    gloss[r[0].casefold()].add(r[1])
for r in db.execute('SELECT a.alias,g.term_ru FROM glossary_aliases a JOIN glossary g ON g.id=a.term_id'):
    gloss[r[0].casefold()].add(r[1])
simple = {'Level':'Уровень', 'Title':'Звание', 'Experience':'Опыт', 'XP':'Опыт', 'Lvl':'Ур.', 'Attack Throw':'Бросок атаки', 'Saving Throws':'Спасброски', 'Class Proficiencies':'Классовые навыки', 'Combat Characteristics':'Боевые характеристики', 'Starting Class Powers':'Начальные классовые способности', 'Additional Class Powers':'Дополнительные классовые способности', 'Proficiencies':'Навыки', 'Equipment':'Снаряжение', 'Template':'Шаблон', '3d6 Roll':'Бросок 3d6', 'None':'Нет', 'Hit Dice':'КЗ', 'Damage Bonus':'Бонус урона', 'Paralysis':'От паралича', 'Death':'От смерти', 'Blast':'От разрушений', 'Implements':'От артефактов', 'Spells':'От заклинаний'}
auto={}
for u in units:
    s=u['source_markup']; plain=u['source_plain']
    if u['invariant']:
        auto[u['id']]=s
    elif s in memory and len(memory[s])==1:
        auto[u['id']]=next(iter(memory[s]))
    elif plain.casefold() in gloss and len(gloss[plain.casefold()])==1 and len(plain)<100:
        auto[u['id']]=next(iter(gloss[plain.casefold()]))
    elif plain.casefold() in {k.casefold() for k in simple}:
        auto[u['id']]=next(v for k,v in simple.items() if k.casefold()==plain.casefold())
write_records(HERE/'automatic.md',auto)
ranges={'A':(24,45),'B':(46,61),'C':(62,81),'D':(82,101)}
for part,(first,last) in ranges.items():
    todo=[u for u in units if first<=u['pdf_page']<=last and u['id'] not in auto]
    with (HERE/f'source_{part}.md').open('w',encoding='utf-8') as f:
        for u in todo:
            f.write(f"<!-- unit: {u['id']} -->\n{u['source_markup']}\n\n")
    print(part,first,last,'pending',len(todo),'chars',sum(len(u['source_markup']) for u in todo))
with (HERE/'glossary_compact.md').open('w',encoding='utf-8') as f:
    for r in db.execute('SELECT term_en,term_ru,category FROM glossary'):
        f.write(f'{r[0]} | {r[1]} | {r[2]}\n')
print('automatic',len(auto))
