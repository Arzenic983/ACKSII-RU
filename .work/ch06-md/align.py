"""Sequence alignment creates unreviewed candidates only, never translations in DB."""
from pathlib import Path
from collections import Counter
import json,re,math,sys
HERE=Path(__file__).resolve().parent
def nums(s):return Counter(re.findall(r'\d+(?:[.,/]\d+)?',s.replace(',000','000')))
def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    source=[u for u in units if not u['table_id'] and u['kind']!='heading']
    draft=json.loads(next(HERE.glob('CHAPTER*.json')).read_text('utf-8'))
    ru=[(i,s) for i,s in enumerate(draft) if len(s)>45 and re.search('[А-Яа-яЁё]',s)]
    en=[u['source_plain'] for u in source]
    def cost(a,b):
        x,y=nums(a),nums(b)
        missing=sum((x-y).values());extra=sum((y-x).values())
        ratio=abs(math.log(max(20,len(b))/max(20,len(a)*1.14)))
        return ratio*1.8+(missing+extra)*0.65-0.3*sum((x&y).values())
    n,m=len(en),len(ru)
    d=[[1e8]*(m+1) for _ in range(n+1)];back={};d[0][0]=0
    for i in range(n+1):
        for j in range(m+1):
            now=d[i][j]
            opts=[]
            if i<n:opts.append((i+1,j,now+1.6,'skip_en'))
            if j<m:opts.append((i,j+1,now+1.6,'skip_ru'))
            if i<n and j<m:opts.append((i+1,j+1,now+cost(en[i],ru[j][1]),'match'))
            if i<n and j+1<m:opts.append((i+1,j+2,now+cost(en[i],ru[j][1]+' '+ru[j+1][1])+0.5,'two_ru'))
            for a,b,v,op in opts:
                if v<d[a][b]:d[a][b]=v;back[a,b]=(i,j,op)
    i,j=n,m;rows=[];mapping={}
    while i or j:
        a,b,op=back[i,j]
        if op in ('match','two_ru'):
            s=' '.join(ru[k][1] for k in range(b,j))
            mapping[source[a]['id']]=s
            rows.append({'id':source[a]['id'],'draft_indices':[ru[k][0] for k in range(b,j)],'cost':cost(en[a],s)})
        i,j=a,b
    (HERE/'candidates.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),'utf-8')
    (HERE/'alignment.json').write_text(json.dumps(rows[::-1],ensure_ascii=False,indent=2),'utf-8')
    print('source prose',n,'draft prose',m,'candidates',len(mapping),'source words',sum(len(u['source_plain'].split()) for u in source))
    for p in range(264,316):
        chosen=[u for u in source if u['pdf_page']==p]
        body='\n\n'.join(f'### {u["id"]}\n\nEN: {u["source_markup"]}\n\nRU: {mapping.get(u["id"],"[НЕТ ПЕРЕВОДА]")}' for u in chosen)
        (HERE/f'candidate_{p}.md').write_text(body,'utf-8')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
