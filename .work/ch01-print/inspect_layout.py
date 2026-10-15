import sys, pathlib, gzip, json, sqlite3, re, importlib.util
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.work/revised-rulebook-extraction'))
import build_text as bt
cache=WORK/'chapter_geometry.json'
if cache.exists(): pages=json.loads(cache.read_text(encoding='utf8'))
else:
    pages=[]
    with gzip.open(ROOT/'.work/revised-rulebook-extraction/pages-corrected.jsonl.gz','rt',encoding='utf8') as f:
        for line in f:
            p=json.loads(line)
            if 14<=p['page']<=23: pages.append(p)
            if p['page']>=23: break
    cache.write_text(json.dumps(pages,ensure_ascii=False),encoding='utf8')
db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
units=[dict(r) for r in db.execute('select u.*,t.text_ru as russian from units u join translations t on t.unit_id=u.id where u.chapter_id="01" order by pdf_page,block_order,row_index,column_index')]
norm=lambda s: ''.join(c.lower() for c in s if c.isalnum())
layouts={}
for p in pages:
    n=p['page'];mid=319.5 if n%2 else 292.5
    cs=[bt.prepare(c,n) for c in p['chars'] if bt.in_body(c,p)]
    cs=[c for c in cs if not any(bt.inside(c,t['bbox']) for t in p['tables'])]
    def make_stream(heading):
        streams=[]
        for side in [0,1]:
            sel=[c for c in cs if (bt.center(c)[0]>=mid)==bool(side) and (any(f in c['font'] for f in ['Trajan','Archeologicaps','Imperator']))==heading]
            string='';mapping=[]
            for l in bt.get_lines(sel):
                for text,c in l['tuples']:
                    if c is None:continue
                    t=norm(text);string+=t;mapping.extend([c]*len(t))
            streams.append((string,mapping))
        return ''.join(s[0] for s in streams),[c for s in streams for c in s[1]]
    prose=make_stream(False);heads=make_stream(True)
    print('PAGE',n)
    for u in units:
        if u['pdf_page']!=n or u['table_id']:continue
        string,mapping=heads if u['kind']=='heading' else prose
        en=norm(u['source_plain']);start=string.find(en);found=start>=0
        if not found:
            start=string.find(en[:min(35,len(en))]);end=string.find(en[-min(35,len(en)):],start)
            stop=end+min(35,len(en)) if end>=0 else start+len(en)
        else:stop=start+len(en)
        if start<0:
            print('MISS',u['id'],u['source_plain'][:60]);continue
        matched=mapping[start:stop]
        if not matched:continue
        chunks=[]
        for side in [0,1]:
            part=[c for c in matched if (bt.center(c)[0]>=mid)==bool(side)]
            if part:chunks.append({'side':side,'bbox':[min(c['x0'] for c in part),min(c['top'] for c in part),max(c['x1'] for c in part),max(c['bottom'] for c in part)],'chars':part})
        layouts[u['id']]={'matched_exactly':found,'chunks':chunks}
        print(u['id'].split('.')[-1],u['kind'],round(max(c['size'] for c in matched),1),[(x['side'],[round(v,1) for v in x['bbox']]) for x in chunks], 'exact',found)
(WORK/'unit_layout.json').write_text(json.dumps(layouts,ensure_ascii=False),encoding='utf8')
