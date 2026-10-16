"""Build unapproved working candidates from aligned contributor paragraphs, with audit."""
from collections import Counter
from pathlib import Path
import json,re,sys
from align_drafts import HERE
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.work/ch04-md'))
from review_tools import nums
def terms():
    d=json.loads((HERE/'known_terms.json').read_text('utf-8'))
    for line in (HERE/'spell_terms.txt').read_text('utf-8').splitlines():
        if not line or line.startswith('#'):continue
        en,ru=line.split(' | ',1);d[en.lower()]=ru
    return d
def partition(source,paras):
    if len(source)==len(paras):return paras
    text=' '.join(paras);words=list(re.finditer(r'\S+',text));n=len(words)
    if not n:return ['']*len(source)
    positions=[0]+[m.end() for m in words]
    total=sum(len(s) for s in source);cum=0;states={0:(0,[])}
    for i,en in enumerate(source):
        cum+=len(en);want=round(n*cum/total);new={}
        ends=[n] if i==len(source)-1 else range(max(1,want-65),min(n,want+65)+1)
        for end in ends:
            choices=[]
            for start,(score,cuts) in states.items():
                if start>=end:continue
                val=text[positions[start]:positions[end]].strip();a,b=nums(en),nums(val)
                error=sum((a-b).values())+sum((b-a).values())
                penalty=error*50+abs((end-start)/n-len(en)/total)*40
                if i<len(source)-1 and not re.search(r'[.!?;:]\W*$',val):penalty+=.3
                choices.append((score+penalty,cuts+[val]))
            if choices:new[end]=min(choices,key=lambda x:x[0])
        states=dict(sorted(new.items(),key=lambda kv:kv[1][0])[:45])
    return states[n][1]
def main():
    sections=json.loads((HERE/'candidate_alignment.json').read_text('utf-8'))
    candidates={};audit=[]
    for s in sections:
        body=[u for u in s['source'] if u['body']]
        paras=s['candidate_paragraphs']
        # Inline table transcription in this contributor file duplicates the real source table.
        if s['name']=='Sling Stone':paras=paras[:2]
        if not paras:continue
        values=partition([u['body'] for u in body],paras)
        for u,value in zip(body,values):candidates[u['id']]=value
        en=' '.join(u['body'] for u in body);ru=' '.join(values)
        a,b=nums(en),nums(ru)
        english=[u['id'] for u,v in zip(body,values) if len(re.findall('[A-Za-z]',v))>50 and not re.search('[А-Яа-яЁё]',v)]
        audit.append({'name':s['name'],'source_ids':[u['id'] for u in body],'candidate_reference':s['reference'],
                      'paragraph_count_changed':len(body)!=len(paras),'numeric_missing':dict(a-b),'numeric_extra':dict(b-a),'english_body_ids':english,'reviewed':False})
    (HERE/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2),'utf-8')
    (HERE/'candidate_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),'utf-8')
    print('Candidate bodies',len(candidates),'of',sum(len([u for u in s['source'] if u['body']]) for s in sections))
    print('Sections with numeric differences',sum(bool(a['numeric_missing'] or a['numeric_extra']) for a in audit))
    print('English body units',sum(len(a['english_body_ids']) for a in audit))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
