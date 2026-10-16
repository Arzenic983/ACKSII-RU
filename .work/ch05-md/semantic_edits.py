"""Explicit edits found during reading of complete English/Russian pairs."""
import json,re
from auto_units import HERE,records,write_records
def main():
    values=json.loads((HERE/'candidates.json').read_text('utf-8'))
    for p in sorted(HERE.glob('translated_*.md')):values.update(records(p))
    for p in sorted(HERE.glob('corrections_review_*.md')):
        if p.name!='corrections_review_90.md':values.update(records(p))
    instructions=json.loads((HERE/'semantic_edits.json').read_text('utf-8'));result={}
    for id,edits in instructions['edits'].items():
        text=values[id]
        for old,new in {'кастер':'заклинатель','кастера':'заклинателя','кастеру':'заклинателю','кастером':'заклинателем'}.items():
            text=re.sub(r'\b'+old+r'\b',new,text,flags=re.I)
        for old,new in edits:
            assert old in text,(id,old);text=text.replace(old,new)
        result[id]=text
    write_records(HERE/'corrections_review_90.md',result)
if __name__=='__main__':main()
