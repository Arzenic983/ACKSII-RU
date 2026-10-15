"""Segment the checked source into stable, page-addressable translation units."""
import collections
import hashlib
import html
import json
import pathlib
import re
import sys
from lxml import etree

sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
ROOT=WORK.parents[1]
SOURCE=ROOT/'ACKSII'/'Source'/'ACKSII Revised Rulebook (EN checked).md'
BOOK='rr'
BOUNDARIES=[('front_matter',1,13,'Front matter'),('01',14,23,'Characters'),('02',24,101,'Classes'),('03',102,123,'Proficiencies'),('04',124,179,'Equipment'),('05',180,263,'Spells'),('06',264,315,'Adventures'),('07',316,333,'Voyages'),('08',334,427,'Campaigns'),('09',428,447,'Armies'),('10',448,461,'Maneuvers'),('11',462,473,'Battles'),('12',474,487,'Sieges'),('A',488,507,'Setting'),('B',508,517,'Conditions'),('C',518,531,'Wounds'),('D',532,537,'Resources'),('E',538,550,'Index')]

def plain(s):
    s=re.sub(r'<br\s*/?>',' ',s)
    s=re.sub(r'<[^>]+>','',s)
    s=html.unescape(s)
    s=re.sub(r'(?<!\\)\*{1,3}','',s).replace('\\*','*').replace('\\_','_').replace('\\|','|')
    return re.sub(r'\s+',' ',s).strip()

def split_cells(line):
    return [x.strip().replace('\\|','|') for x in re.split(r'(?<!\\)\|',line.strip())[1:-1]]

def invariant(text):
    stripped=re.sub(r'\b\d*d\d+!?\b','',text)
    return not any(ch.isalpha() for ch in stripped)

pages=[];units=[];tables=[];normalizations=[]
s=SOURCE.read_text(encoding='utf8')
pieces=re.split(r'<a id="pdf-page-(\d{4})"></a>\s*',s)
for i in range(1,len(pieces),2):
    number=int(pieces[i]);body=pieces[i+1]
    m=re.search(r'^## PDF page \d+(?: printed page (\S+))?\s*$',body,re.M)
    printed=int(m.group(1)) if m and m.group(1) and m.group(1).isdigit() else None
    body=re.sub(r'^## PDF page.*\n\s*','',body,count=1)
    body=re.sub(r'^\[Original PDF page.*\n\s*','',body,count=1)
    chapter=next(c[0] for c in BOUNDARIES if c[1]<=number<=c[2])
    blocks=[];current=[];table_mode=None
    for line in body.splitlines():
        if line.startswith('<table>'):
            if current:blocks.append('\n'.join(current));current=[]
            table_mode='html';current=[line]
        elif table_mode=='html':
            current.append(line)
            if line.startswith('</table>'):blocks.append('\n'.join(current));current=[];table_mode=None
        elif line.strip():current.append(line)
        elif current:blocks.append('\n'.join(current));current=[]
    if current:blocks.append('\n'.join(current))
    # Repair paragraph continuity before translation; table order remains stored
    # independently. Each join is explicit and checked against the same PDF.
    if number in (16,18,21):
        joins={16:[('**Strength (STR):','damage rolls in melee'),('If a character’s key attribute','attribute has on experience')],18:[('At 1st level, you roll','4. Add your Constitution')],21:[('At each stage, progressively','attribute adjustments appropriate'),('**EXAMPLE:** Marcus has','70. He succeeds')]}.get(number,[])
        for a,b in joins:
            ai=next((j for j,x in enumerate(blocks) if x.startswith(a)),None);bi=next((j for j,x in enumerate(blocks) if x.startswith(b)),None)
            if ai is None or bi is None:continue
            before=[blocks[ai],blocks[bi]]
            blocks[ai]+=' '+blocks[bi];blocks.pop(bi)
            normalizations.append({'page':number,'kind':'paragraph_join','before':before,'after':blocks[ai]})
    if number==4:
        ai=next((j for j,x in enumerate(blocks) if x.startswith('***Adventurer') and '©2024' in x),None)
        bi=next((j for j,x in enumerate(blocks) if x.startswith('places, or events')),None)
        if ai is not None and bi is not None:
            before=[blocks[ai],blocks[bi]];blocks[ai]+=' '+blocks[bi];blocks.pop(bi)
            normalizations.append({'page':number,'kind':'paragraph_join','before':before,'after':blocks[ai]})
    if number==10:
        ai=next((j for j,x in enumerate(blocks) if x.startswith('If an adventurer is not slain')),None)
        bi=next((j for j,x in enumerate(blocks) if x.startswith('multiple domains')),None)
        if ai is not None and bi is not None:
            before=[blocks[ai],blocks[bi]];blocks[ai]+=' '+blocks[bi];blocks.pop(bi)
            normalizations.append({'page':number,'kind':'paragraph_join','before':before,'after':blocks[ai]})
    pages.append({'page':number,'printed_page':printed,'chapter':chapter,'source_markup':body,'anchor':f'pdf-page-{number:04d}'})
    ti=0
    for order,block in enumerate(blocks,1):
        if block.startswith('<!--'):continue
        base=f'{BOOK}.p{number:04d}.b{order:03d}'
        if block.startswith('<table>') or block.startswith('|'):
            ti+=1;tid=f'{BOOK}.p{number:04d}.t{ti:02d}';cells=[];nr=0;nc=0
            if block.startswith('<table>'):
                tree=etree.fromstring(block.replace('<br>','<br/>').encode('utf8'));occupied=set()
                for rn,tr in enumerate(tree.findall('tr')):
                    ci=0
                    for td in tr:
                        while (rn,ci) in occupied:ci+=1
                        rs,cs=int(td.get('rowspan','1')),int(td.get('colspan','1'))
                        text=''.join(td.itertext())
                        markup=(td.text or '')+''.join(etree.tostring(child,encoding='unicode') for child in td)
                        for rr in range(rn,rn+rs):
                            for cc in range(ci,ci+cs):occupied.add((rr,cc))
                        cells.append((rn,ci,rs,cs,markup));ci+=cs;nc=max(nc,ci)
                    nr=rn+1
            else:
                rows=[split_cells(line) for line in block.splitlines() if line.startswith('|')]
                rows=[row for row in rows if not all(re.fullmatch(r':?-+:?',c.replace(' ','')) for c in row)]
                nr=len(rows);nc=len(rows[0])
                assert all(len(row)==nc for row in rows),(number,tid)
                cells=[(rn,ci,1,1,value) for rn,row in enumerate(rows) for ci,value in enumerate(row)]
            tables.append({'id':tid,'page':number,'chapter':chapter,'block_order':order,'rows':nr,'columns':nc,'source_markup':block})
            for rn,ci,rs,cs,value in cells:
                if not plain(value):continue
                units.append({'id':f'{tid}.r{rn+1:03d}.c{ci+1:02d}','chapter':chapter,'page':number,'printed_page':printed,'order':order,'kind':'table_cell','table_id':tid,'row':rn,'column':ci,'rowspan':rs,'colspan':cs,'source':value,'plain':plain(value),'invariant':invariant(plain(value))})
        else:
            hm=re.match(r'^(#{3,6}) (.+)',block,re.S)
            kind='heading' if hm else 'list_item' if re.match(r'^(?:♦|◇|\d+\.)\s',block) else 'verse' if block.startswith('*') and not block.startswith('**') and block.endswith('*') and len(block)<100 else 'paragraph'
            value=hm.group(2) if hm else block
            units.append({'id':base,'chapter':chapter,'page':number,'printed_page':printed,'order':order,'kind':kind,'heading_level':len(hm.group(1)) if hm else None,'source':value,'plain':plain(value),'invariant':False})
assert len(pages)==550
for u in units:u['source_sha256']=hashlib.sha256(u['source'].encode('utf8')).hexdigest()
(WORK/'all_units.json').write_text(json.dumps(units,ensure_ascii=False),encoding='utf8')
(WORK/'all_tables.json').write_text(json.dumps(tables,ensure_ascii=False),encoding='utf8')
(WORK/'all_pages.json').write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
if normalizations or not (WORK/'source_normalizations.json').exists():
    (WORK/'source_normalizations.json').write_text(json.dumps(normalizations,ensure_ascii=False,indent=2),encoding='utf8')
scope=[u for u in units if u['page']<=23]
(WORK/'scope_units.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf8')
for name,sel in [('front', [u for u in scope if u['page']<=13]),('chapter01',[u for u in scope if u['page']>=14])]:
    out=[]
    for u in sel:
        if u['kind']!='table_cell':out.append(f"[{u['id']}] {u['kind']}\n{u['source']}\n")
    (WORK/(name+'_prose.txt')).write_text('\n'.join(out),encoding='utf8')
labels=collections.OrderedDict()
for u in scope:
    if u['kind']=='table_cell' and not u['invariant']:labels.setdefault(u['plain'],[]).append(u['id'])
(WORK/'scope_labels.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'all_units':len(units),'all_tables':len(tables),'scope_units':len(scope),'scope_noninvariant':sum(not u['invariant'] for u in scope),'scope_prose':sum(u['kind']!='table_cell' for u in scope),'unique_scope_cell_texts':len(labels),'normalizations':len(normalizations),'scope_by_page':dict(collections.Counter(u['page'] for u in scope))},indent=2))
