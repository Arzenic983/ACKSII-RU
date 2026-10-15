import json,pathlib,re,sys
sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
data=json.loads((WORK/'readme.json').read_text(encoding='utf8'))
terms=[];lookup={};category=''
for item in data['items']:
    if item['kind']!='paragraph':continue
    if (item.get('style') or '').startswith('Heading'):
        category=item['text'];continue
    text=item['text']
    for line in re.split(r'\n|(?<=[А-Яа-яё?])(?=[A-Z][a-z])',text):
        m=re.match(r'^\s*([A-Za-z][A-Za-z0-9 /(),&.’\'-]+?)\s+-\s*(.+)',line)
        if not m or not re.search(r'[А-Яа-я]',m.group(2)):continue
        en,raw=m.groups();preferred=raw.split('(')[0].split(' - ')[0].strip().rstrip('?.').strip()
        if en.strip()=='Hit Points':preferred='Очки Здоровья'
        # Slash-separated alternatives are retained, but the first is used in
        # the working translation unless context explicitly requires another.
        variants=[x.strip().rstrip('?') for x in re.split(r'\s*/\s*',preferred)]
        if en.strip().startswith('Art/Craft') or en.strip() in ('party formation/ marching','Readied to Attack/combat action','Blessed/Inspired','Choking / Vomiting'):
            variants=[preferred]
        preferred=variants[0]
        en=re.sub(r'\s*\([GOО]\)\s*','',en).strip()
        abbreviation=re.search(r'\(([А-ЯЁ]{2,4})\)',raw)
        term={'en':en,'ru':preferred,'ru_abbreviation':abbreviation.group(1) if abbreviation else None,'raw_entry':line,'source_locator':item['locator'],'category':category,'status':'user_confirmed' if en in ('Naturalism','Loremastery','extraordinary (damage)') else 'project_glossary','variants':variants[1:]}
        terms.append(term)
        for alias in [en,*[a.strip() for a in en.split(',')]]:lookup.setdefault(alias.lower(),preferred)
for en,ru in [('Naturalism','Природоведение'),('Loremastery','Мифография'),('extraordinary (damage)','Особый')]:
    assert lookup[en.lower()]==ru,(en,lookup.get(en.lower()))
(WORK/'glossary_import.json').write_text(json.dumps(terms,ensure_ascii=False,indent=2),encoding='utf8')
(WORK/'glossary_lookup.json').write_text(json.dumps(lookup,ensure_ascii=False,indent=2),encoding='utf8')
labels=json.loads((WORK/'scope_labels.json').read_text(encoding='utf8'))
remaining=[]
for text in labels:
    key=re.sub(r'\s*\(G\)','',text).lower()
    if key not in lookup:remaining.append(text)
(WORK/'labels_to_translate.txt').write_text('\n'.join(remaining),encoding='utf8')
print('GLOSSARY',len(terms),'missing labels',len(remaining))
for text in remaining:print(text)
