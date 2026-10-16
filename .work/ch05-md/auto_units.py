"""Presentation candidates only; no approval and no SQLite writes."""
from pathlib import Path
import json,re,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def records(path):
    ms=list(re.finditer(r'<!-- unit: (rr\.[^ ]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',path.read_text('utf-8'),re.S))
    assert len(ms)==len({m[1] for m in ms}),str(path)
    return {m[1]:m[2].strip() for m in ms}
def write_records(path,values):
    path.write_text('\n\n'.join(f'<!-- unit: {k} -->\n{v}' for k,v in values.items())+'\n','utf-8')
def terms():
    d=json.loads((HERE/'known_terms.json').read_text('utf-8'))
    for line in (HERE/'spell_terms.txt').read_text('utf-8').splitlines():
        if line and not line.startswith('#'):
            en,ru=line.split(' | ',1);d[en.lower()]=ru
    return d
def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'));names=terms()
    labels=json.loads((HERE/'table_terms.json').read_text('utf-8'))
    meta={'stationary concentration':'неподвижная концентрация [stationary concentration]',
          'per caster level':'за уровень заклинателя [caster level]','per level':'за уровень [level]',
          'instantaneous':'мгновенная [instantaneous]','indefinite':'неопределённая [indefinite]',
          'perpetual':'поддерживаемая [perpetual]','concentration':'концентрация [concentration]',
          'special':'особая [special]','touch':'касание [touch]','self':'на себя [self]',
          'ARCANE':'ТАЙНАЯ [ARCANE]','DIVINE':'БОЖЕСТВЕННАЯ [DIVINE]','Type:':'Тип [Type]:',
          'Range:':'Радиус действия [Range]:','Duration:':'Длительность [Duration]:',
          'transmogrification':'трансмогрификация [transmogrification]','necromancy':'некромантия [necromancy]',
          'enchantment':'очарование [enchantment]','detection':'обнаружение [detection]',
          'summoning':'призыв [summoning]','protection':'защита [protection]','elemental':'стихии [elemental]',
          'esoteric':'эзотерика [esoteric]','healing':'исцеление [healing]','illusion':'иллюзия [illusion]',
          'movement':'движение [movement]','blast':'взрыв [blast]','death':'смерть [death]','wall':'стена [wall]',
          'earth':'земля [earth]','water':'вода [water]','fire':'огонь [fire]','air':'воздух [air]','any':'любая [any]',
          'turns':'ходов [turns]','turn':'ход [turn]','rounds':'раундов [rounds]','round':'раунд [round]',
          'hours':'часов','hour':'час','days':'дней','day':'день','weeks':'недель','week':'неделя',
          'months':'месяцев','month':'месяц','level':'уровень [level]','until':'до','or':'или',
          'Sunrise':'восход солнца','Special':'особая [Special]','miles':'мил.',
          'conjuration':'вызов [conjuration]','summons':'призыв [summons]','calling':'зов [calling]',
          'call':'зов [call]','caster level':'уровень заклинателя [caster level]',
          'until it happens':'до исполнения предсказанного',
          'caster':'заклинатель [caster]','mile':'миля [mile]'}
    pattern=re.compile(r'(?<![A-Za-z])('+ '|'.join(re.escape(k) for k in sorted(meta,key=len,reverse=True))+r')(?![A-Za-z])')
    def tr(s):
        s=pattern.sub(lambda m:meta[m[0]],s)
        for a,b in {'3 ходов':'3 хода','2 ходов':'2 хода','3 раундов':'3 раунда','2 раундов':'2 раунда','24 часов':'24 часа','1 дней':'1 день'}.items():s=s.replace(a,b)
        return s
    sections=json.loads((HERE/'candidate_alignment.json').read_text('utf-8'))
    bodymeta={u['id']:u.get('metadata','') for s in sections for u in s['source']}
    candidates=json.loads((HERE/'candidates.json').read_text('utf-8'))
    overrides={}
    for p in sorted(HERE.glob('translated_*.md')):
        found=records(p);assert not set(overrides)&set(found);overrides.update(found)
    for p in sorted(HERE.glob('corrections_review_*.md')):overrides.update(records(p))
    values={};missing=[]
    spells=[s['name'] for s in sections]
    aliases={'Dominate Beast':'Dominate Beasts','Spellward Zone':'Spellwarded Zone','Conjure Supreme Elem.':'Conjure Supreme Elemental',
             'Sphere of Invulnerability, Grt.':'Sphere of Invulnerability, Greater','Sphere of Invulnerability, Grtr.':'Sphere of Invulnerability, Greater'}
    for u in units:
        id=u['id'];en=u['source_markup'];ru=None
        if u['kind']=='heading':continue
        if u['table_id']:
            if en in labels:ru=labels[en]
            elif not re.search('[A-Za-z]',en):ru=en
            else:
                for name in sorted(spells+list(aliases),key=len,reverse=True):
                    if en.lower().startswith(name.lower()):
                        key=aliases.get(name,name);ru=names[key.lower()]+' ['+key+']'+en[len(name):];break
        elif id in bodymeta:
            candidate=overrides.get(id,candidates.get(id,''))
            if candidate:ru=(tr(bodymeta[id])+' '+candidate).strip()
            elif not u.get('body'):ru=tr(bodymeta[id]) or None
        elif id in overrides:ru=overrides[id]
        elif re.match(r'^\*\*(ARCANE|DIVINE)\*\*',en) or en.startswith('**Type:**'):ru=tr(en)
        else:
            m=re.fullmatch(r'\*\*\*([^*]+)\*\*\*(?:\s*\\?\*)?\s*',en)
            if m:
                name=m[1].rstrip('\\');ru='***'+names[name.lower()]+'*** ['+name+']'+(' \\*' if '\\*' in en else '')
        if ru:values[id]=ru
        else:missing.append({'id':id,'english':en})
    write_records(HERE/'automatic.md',values)
    (HERE/'missing_units.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2),'utf-8')
    print('Prepared candidates',len(values),'missing non-heading units',len(missing))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
