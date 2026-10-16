"""Restore formal damage categories at the matching original dice expressions."""
import json,re
from collections import defaultdict
from auto_units import HERE,records,write_records
TYPES={'bludgeoning':'дробящего','piercing':'колющего','slashing':'рубящего','fire':'огненного','cold':'холодового','electric':'электрического',
       'luminous':'излучающего','necrotic':'некротического','seismic':'сейсмического','acidic':'кислотного','poisonous':'ядовитого','arcane':'мистического'}
def main():
    values=records(HERE/'automatic.md');us=json.loads((HERE/'source_units.json').read_text('utf-8'));changed=[]
    for u in us:
        if u['table_id'] or u['id'] not in values:continue
        pairs=defaultdict(dict)
        for m in re.finditer(r'(\d+d\d+(?:[+-]\d+)?(?:/\d+)?)(?:\s+points\s+of)?\s*((?:\[(?:mundane|extraordinary) [a-z]+\]\s*)+)',u['source_markup']):
            pairs[m[1]][m.start()]=re.findall(r'\[((?:mundane|extraordinary) [a-z]+)\]',m[2])
        text=values[u['id']];original=text
        for dice,positions in pairs.items():
            pattern=r'(?<![\dA-Za-z])'+re.escape(dice)+r'(?![\dA-Za-z+/-])'
            sequences=[positions.get(m.start()) for m in re.finditer(pattern,u['source_markup'])]
            if len(list(re.finditer(pattern,text)))!=len(sequences):continue
            at=0
            def add(m):
                nonlocal at
                seq=sequences[at];at+=1
                if seq is None:return m[0]
                tail=text[m.end():]
                if re.match(r'\s*\[',tail):return m[0]
                labels=[]
                for term in seq:
                    grade,typ=term.split();ru=('обычного' if grade=='mundane' else 'особого')+' '+TYPES[typ]
                    labels.append('['+ru+'] ['+term+']')
                return m[0]+' '+' '.join(labels)
            text=re.sub(pattern,add,text)
        if text!=original:changed.append(u['id'])
        values[u['id']]=text
    write_records(HERE/'automatic.md',values)
    (HERE/'damage_label_audit.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),'utf-8')
    print('Formal damage labels restored in',len(changed),'units')
if __name__=='__main__':main()
