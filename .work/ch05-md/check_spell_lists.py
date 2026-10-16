"""Compare the English lists against English descriptions; never repair source values."""
import json,re
from auto_units import HERE
def main():
    us=json.loads((HERE/'source_units.json').read_text('utf-8'));sections=json.loads((HERE/'aligned_sections.json').read_text('utf-8'))
    descriptions={s['name']:next(u for u in s['source'] if re.match(r'^\*\*(ARCANE|DIVINE)\*\*',u['source_markup'])) for s in sections}
    aliases={'Dominate Beast':'Dominate Beasts','Spellward Zone':'Spellwarded Zone','Conjure Supreme Elem.':'Conjure Supreme Elemental',
             'Sphere of Invulnerability, Grt.':'Sphere of Invulnerability, Greater','Sphere of Invulnerability, Grtr.':'Sphere of Invulnerability, Greater',
             'Repair Disfigurement & Dis.':'Repair Disfigurement and Disability'}
    levels={'FIRST':1,'SECOND':2,'THIRD':3,'FOURTH':4,'FIFTH':5,'SIXTH':6}
    codes={'bst':'blast','dth':'death','det':'detection','enc':'enchantment','eso':'esoteric','hea':'healing',
           'ill':'illusion','mov':'movement','nec':'necromancy','pro':'protection','sum':'summoning','trn':'transmogrification','wal':'wall'}
    headers={};diff=[]
    for u in us:
        if not u['table_id'] or not 188<=u['pdf_page']<=193:continue
        m=re.fullmatch(r'(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH) LEVEL (ARCANE|DIVINE) SPELLS',u['source_markup'])
        if m:headers[u['table_id'],u['column_index']]=(m[2],levels[m[1]]);continue
        spell=next((s for s in sorted(list(descriptions)+list(aliases),key=len,reverse=True) if u['source_markup'].lower().startswith(s.lower())),None)
        if not spell:continue
        magic,level=headers[u['table_id'],u['column_index']];name=aliases.get(spell,spell);meta=descriptions[name]
        stated=re.findall(r'\*\*(ARCANE|DIVINE)\*\* (\d)',meta['source_markup'])
        listtypes=set(codes[c] for c in re.findall(r'\b(?:bst|dth|det|enc|eso|hea|ill|mov|nec|pro|sum|trn|wal)\b',u['source_markup'][len(spell):]))
        if 'elm' in u['source_markup'][len(spell):]:listtypes.add('elemental')
        metatext=meta['source_plain']
        if 'Type:' not in metatext:
            metatext+=' '+next(u['source_plain'] for u in sections[[s['name'] for s in sections].index(name)]['source'] if u['source_markup'].startswith('**Type:**'))
        mtypes=metatext.split('Type:',1)[1].strip();descriptiontypes={c for c in set(codes.values())|{'elemental'} if re.search(r'\b'+c+r'\b',mtypes)}
        # A necromancy label is formally a death subtype, but compare printed names as written.
        mismatch=[]
        if (magic,str(level)) not in stated:mismatch.append('level_or_magic_type')
        if listtypes!=descriptiontypes:mismatch.append('spell_types')
        if mismatch:diff.append({'id':u['id'],'spell':name,'list_magic':magic,'list_level':level,'list_types':sorted(listtypes),
                               'description_id':meta['id'],'description':meta['source_plain'],'differences':mismatch})
    (HERE/'english_list_differences.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2),'utf-8')
    print('English list/description differences',len(diff))
    for d in diff:print(d['id'],d['spell'],d['list_types'],'vs',d['description'])
if __name__=='__main__':main()
