from pathlib import Path
import re
base=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
src=dict(pat.findall((base/'source_D.md').read_text(encoding='utf-8-sig')))
raw=(base/'translated_D.md').read_text(encoding='utf-8-sig')
units=pat.findall(raw)
replacements={
'rr.p0082.b018': [('в книги заклинаний','в гримуары'),('другие книги божественных заклинаний','другие божественные гримуары'),('из книг тайных заклинаний','из тайных гримуаров')],
'rr.p0087.b005': [('прорыв, разрушение','пробиться, разделение')],
'rr.p0101.b005': [('прорыв, разрушение','пробиться, разделение')],
'rr.p0100.b009': [(' ОО',' очков опыта')],
'rr.p0090.t01.r005.c03': [('Специализация на боевом стиле','Специализация<br>на боевом стиле')],
'rr.p0093.t02.r004.c03': [('Мастерство зачарования и иллюзий','Мастерство<br>зачарования и иллюзий')],
}
out=[]
for uid,txt in units:
    for a,b in replacements.get(uid,[]): txt=txt.replace(a,b)
    count=len(re.findall(r'<br\s*/?>',src[uid]))
    own=len(re.findall(r'<br\s*/?>',txt))
    if count!=own:
        assert '.t' in uid and own==0, (uid,count,own)
        # Retain the source cell's line-break structure by wrapping the translated cell.
        # This changes layout only; text, emphasis, numbers, and cell boundaries stay intact.
        points=[]
        breaks=[m.start() for m in re.finditer(r'<br\s*/?>',src[uid])]
        candidates=[m.start() for m in re.finditer(' ',txt) if not (txt[m.start()-1].isdigit() and txt[m.start()+1].isdigit())]
        for i,pos in enumerate(breaks):
            desired=len(txt)*pos/len(src[uid])
            viable=[p for p in candidates if (not points or p>points[-1]) and len([q for q in candidates if q>p])>=count-i-1]
            pick=min(viable,key=lambda p: abs(p-desired)+(0 if txt[p-1]==',' else 6))
            points.append(pick)
        for p in reversed(points): txt=txt[:p]+'<br>'+txt[p+1:]
    out.append(f'<!-- unit: {uid} -->\n{txt.strip()}\n\n')
(base/'translated_D.md').write_text(''.join(out),encoding='utf-8',newline='\n')
