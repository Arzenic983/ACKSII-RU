from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def read(name,default=None):
    p=HERE/name
    return json.loads(p.read_text('utf-8')) if p.exists() else default
def write(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')
def normalize(s,en=''):
    pairs={'партии':'группы','партию':'группу','партией':'группой','партия':'группа',
        'Судья':'Арбитр','судья':'Арбитр','судьи':'Арбитра','судье':'Арбитру','судью':'Арбитра','судьей':'Арбитром','судьёй':'Арбитром',
        'скоростью разведки':'скоростью исследования','скорости разведки':'скорости исследования','скорость разведки':'скорость исследования',
        'скоростью разведчика':'скоростью исследования','мастерство':'навык','на мастерство':'на навык'}
    for a,b in pairs.items():s=re.sub(r'\b'+re.escape(a)+r'\b',b,s,flags=re.I)
    for a,b in {'скалолазания':'Лазания','скалолазанию':'Лазанию','скалолазание':'Лазание','Выносливость':'Стойкость','Картографирования':'Картография','структурные хит-пойнты':'конструкционные ОЗ'}.items():s=re.sub(r'\b'+a+r'\b',b,s,flags=re.I)
    refs=re.findall(r'\bp\.\s*(\d+)',en)
    if s.count('XX XX')==len(refs):
        for page in refs:s=s.replace('XX XX',page,1)
    if '[mundane bludgeoning]' in en:
        s=s.replace('Bl урона','обычного дробящего урона')
        s=re.sub(r'(1d6|1)\s+(?:единиц\s+)?урона',r'\1 обычного дробящего урона',s)
    s=s.replace('[[Ancillary activities - Вспомогательное дело|вспомогательным действием]]','вспомогательной деятельностью').replace('[[Dedicated activities - Целенаправленное дело]]','целенаправленная деятельность')
    return s
def accept(pages,edits,notes=None):
    units=read('source_units.json');candidates=read('candidates.json');values=read('prose.json',{})
    edits={('rr.p0'+k if not k.startswith('rr.') else k):v for k,v in edits.items()}
    selected=[u for u in units if u['pdf_page'] in pages and not u['table_id'] and u['kind']!='heading']
    for u in selected:
        id=u['id'];value=edits.get(id,candidates.get(id))
        assert value,(id,'missing manual translation')
        values[id]=normalize(value,u['source_markup'])
    assert set(edits)<={u['id'] for u in selected}
    write('prose.json',values)
    reviewed=read('reviewed_pages.json',[]);write('reviewed_pages.json',sorted(set(reviewed)|set(pages)))
    allnotes=read('notes.json',{})
    for id,content in (notes or {}).items():allnotes['rr.p0'+id if not id.startswith('rr.') else id]=content
    write('notes.json',allnotes)
    print('Reviewed prose pages',pages,'units',len(selected),'total',len(values))
