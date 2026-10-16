"""Prepare candidate paragraph alignment for human review; preserve contributor drafts."""
import json,re,sys
from pathlib import Path
from align_drafts import HERE
def main():
    rows=json.loads((HERE/'aligned_sections.json').read_text('utf-8'))
    out=[];problems=[]
    for sec in rows:
        def grade(v):
            if not v:return 1000000
            return sum(len(re.findall('[A-Za-z]',s)) for s in v if not re.search('[А-Яа-яЁё]',s) and not re.match(r'#?(Arcane|Divine)',s)) + (0 if len(v)>1 else 100000)
        # Prefer the more complete spell collection; compare the other draft during review.
        ref=next(((k,v) for k,v in sec['variants'].items() if k.endswith('LIST ALL') and v),None)
        if ref is None:ref=min(sec['variants'].items(),key=lambda kv:grade(kv[1]),default=('',[]))
        if grade(ref[1])>100:
            alternatives=[(k,v) for k,v in sec['variants'].items() if v and sum(map(len,v))>sum(len(u['source_plain']) for u in sec['source'])*.65]
            if alternatives:ref=min(alternatives,key=lambda kv:grade(kv[1]))
        paras=ref[1]
        # The first contributor paragraph is always the English statistics line.
        if paras and re.match(r'#?(Arcane|Divine)',paras[0],re.I):paras=paras[1:]
        source=[]
        for u in sec['source'][1:]:
            if u['table_id'] or u['kind']=='heading':continue
            en=u['source_markup']
            if re.match(r'^\*\*(ARCANE|DIVINE)\*\*',en) or en.startswith('**Type:**'):continue
            if en.startswith('**Range:**'):
                m=re.search(r'\b(This |The |On |By |If |Upon |When |With |A |An |Each |For |At |To |It |All |Any |While |One |As )',en)
                if m:u=dict(u,metadata=en[:m.start()].strip(),body=en[m.start():])
                else:u=dict(u,metadata=en,body='')
            else:u=dict(u,metadata='',body=en)
            source.append(u)
        body=[u for u in source if u['body']]
        item={'name':sec['name'],'reference':ref[0],'source':source,'candidate_paragraphs':paras}
        out.append(item)
        if len(body)!=len(paras):problems.append((sec['name'],len(body),len(paras)))
    (HERE/'candidate_alignment.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
    print('Aligned counts',len(out)-len(problems),'of',len(out))
    print('Count differences',problems)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
