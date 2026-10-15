import collections,json,pathlib,re,sys
sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
units=json.loads((WORK/'scope_units.json').read_text(encoding='utf8'))
glossary=json.loads((WORK/'glossary_import.json').read_text(encoding='utf8'))
lookup=json.loads((WORK/'glossary_lookup.json').read_text(encoding='utf8'))
for term in glossary:
    bare=re.sub(r'\s*\([A-Z]{2,4}\)$','',term['en'])
    lookup.setdefault(bare.lower(),term['ru'])
lookup['elven spellsword']=lookup['elven spellswords']
labels={}
for line in (WORK/'labels_ru.txt').read_text(encoding='utf8').splitlines():
    if ' = ' in line:
        en,ru=line.split(' = ',1);labels[en.lower()]=ru
custom={}
for file in ('front_ru.txt','chapter01_ru.txt'):
    text=(WORK/file).read_text(encoding='utf8')
    for block in text.split('@@ ')[1:]:
        head,body=block.split('\n',1);parts=[x.strip() for x in head.split('|')]
        assert parts[0] not in custom
        custom[parts[0]]={'ru':body.strip(),'draft_locators':[s.strip() for s in parts[1].split(',')] if len(parts)>1 and 'body.' in parts[1] else [],'explicit_reuse':len(parts)>2 and parts[2]=='reuse'}
trans=[];missing=[];term_conflicts=[]
damage_names={'acidic':'Кислота','arcane':'Мистический','bludgeoning':'Дробящий','cold':'Холод','electric':'Электричество','fire':'Огонь','luminous':'Излучения','necrotic':'Некротический','piercing':'Колющий','poisonous':'Яд','seismic':'Сейсмический','slashing':'Рубящий','varies by weapon':'Зависит от оружия'}
for u in units:
    key=u['plain'].lower();base=re.sub(r'\s*\(g\)','',key)
    c=custom.get(u['id']);record={'id':u['id'],'status':'reviewed','reviewer':'Codex','draft_locators':[]}
    if c:
        record.update(c);record['origin']='existing_reused' if c['explicit_reuse'] else 'existing_revised' if c['draft_locators'] else 'new_translation'
    elif key in lookup or base in lookup:
        record['ru']=lookup.get(key,lookup.get(base));record['origin']='project_glossary'
        if base!=key:record['ru']+=' (О)'
    elif key in labels:
        record['ru']=labels[key];record['origin']='new_translation'
    elif u['invariant']:
        record['ru']=u['source'];record['origin']='invariant'
    elif re.fullmatch(r'\[(mundane|extraordinary) [^\]]+\]',u['plain']):
        m=re.fullmatch(r'\[(mundane|extraordinary) ([^\]]+)\]',u['plain']);kind,typ=m.groups()
        record['ru']=f"[{'Обычный' if kind=='mundane' else 'Особый'} урон: {damage_names[typ]}]";record['origin']='damage_symbol'
    else:
        missing.append({'id':u['id'],'kind':u['kind'],'source':u['source']});continue
    if not c and key in labels and (key in lookup or base in lookup):
        g=lookup.get(key,lookup.get(base))
        if labels[key].lower()!=g.lower():term_conflicts.append({'source':u['plain'],'label_file':labels[key],'glossary':g})
    record['source_sha256']=u['source_sha256'];trans.append(record)
(WORK/'translations_scope.json').write_text(json.dumps(trans,ensure_ascii=False,indent=2),encoding='utf8')
(WORK/'missing_translations.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),encoding='utf8')
(WORK/'term_label_conflicts.json').write_text(json.dumps(term_conflicts,ensure_ascii=False,indent=2),encoding='utf8')
print('TRANSLATED',len(trans),'MISSING',len(missing),'COUNTS',collections.Counter(x['origin'] for x in trans))
for m in missing:print(m['id'],m['kind'],m['source'])
print('LABEL VARIANTS RESOLVED TO GLOSSARY',term_conflicts[:20])
