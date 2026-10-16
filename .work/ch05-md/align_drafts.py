"""Read-only alignment of contributor reference texts; never imports or approves text."""
from pathlib import Path
import json,re,sys
HERE=Path(__file__).resolve().parent
def canon(s):return re.sub('[^a-z0-9]','',s.lower())
def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    title=re.compile(r'^\*\*\*([^*]+)\*\*\*(?:\s*\\?\*)?\s*$')
    starts=[i for i,u in enumerate(units) if title.fullmatch(u['source_markup'])]
    sections={title.fullmatch(units[a]['source_markup'])[1].rstrip('\\'):units[a:b] for a,b in zip(starts,starts[1:]+[len(units)])}
    spell_names=sorted(sections,key=len,reverse=True)
    refs={}
    for p in HERE.glob('CHAPTER*.txt'):
        paragraphs=p.read_text('utf-8').split('\n\n');ref={};current=None
        for para in paragraphs:
            prefix=re.split('[А-Яа-яЁё✪]',para,1)[0]
            prefix=prefix.replace('Summon Wrathful Herald','Summon Winged Herald')
            matched=next((s for s in spell_names if len(para)<160 and canon(prefix)==canon(s)),None)
            if matched:
                current=matched;ref[current]=[]
            elif current:ref[current].append(para)
        refs[p.stem]=ref
    rows=[]
    for name,source in sections.items():
        variants={k:v[name] for k,v in refs.items() if name in v}
        rows.append({'name':name,'source':source,'variants':variants})
    (HERE/'aligned_sections.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf-8')
    print('Sections',len(rows),'missing all drafts',[r['name'] for r in rows if not r['variants']])
    for r in rows:
        variants=r['variants'];best=min(variants.values(),key=lambda v:sum(len(re.findall('[A-Za-z]',s)) for s in v if not re.search('[А-Яа-яЁё]',s)),default=[])
        english=[s for s in best if len(re.findall('[A-Za-z]',s))>100 and not re.search('[А-Яа-яЁё]',s)]
        if english:print(r['name'],len(english),sum(len(s.split()) for s in english),'English words')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
