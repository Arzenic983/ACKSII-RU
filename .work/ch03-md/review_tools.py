"""Alignment and numeric audit, independent of Markdown rendering."""
from collections import Counter
from auto_units import HERE, ROOT, records
import hashlib
import json
import re

def strip_english(text):
    return re.sub(r' ?\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\]', '',text)

def get_text():
    values={}
    for path in [HERE/'automatic.md',HERE/'tables.md',*sorted(HERE.glob('translated_*.md'))]:
        part=records(path)
        overlap=set(part)&set(values)
        assert not overlap, (path,overlap)
        values.update(part)
    return values

def nums(text):
    text=re.sub(r'(?<=\d)[ ,\u00a0](?=\d{3}(?:\D|$))','',text)
    text=re.sub(r'(?<=\d),(?=\d)', '.',text)
    # A dash between positive numbers is a range, not a negative modifier.
    text=re.sub(r'(?<=\d)\s*[-–—]\s*(?=\d)', '~',text)
    return Counter(re.findall(r'\d+d\d+!?|[+\-]?\d+(?:\.\d+)?(?:%|\+)?',text))

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    text=get_text()
    assert set(text)=={u['id'] for u in units}, {'missing':sorted({u['id'] for u in units}-set(text)), 'extra':sorted(set(text)-{u['id'] for u in units})}
    errors=[]
    for u in units:
        a,b=nums(u['source_markup']),nums(strip_english(text[u['id']]))
        if a!=b:
            errors.append({'id':u['id'],'english':u['source_markup'],'russian':text[u['id']],'missing':dict(a-b),'extra':dict(b-a)})
    (HERE/'numeric_review.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf-8')
    for p in range(102,124):
        aligned='\n\n'.join(f'### {u["id"]}\n\n{u["source_markup"]}\n\n{ text[u["id"]] }' for u in units if u['pdf_page']==p)
        (HERE/f'review_{p}.md').write_text(aligned+'\n','utf-8')
    print('Coverage:',len(text),'/',len(units))
    print(json.dumps(errors,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
