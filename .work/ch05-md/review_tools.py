"""Read-only alignment and numeric audit; partial coverage is reported explicitly."""
from collections import Counter
from pathlib import Path
import csv
import json
import re
from auto_units import HERE, ROOT, records, write_records

def strip_english(text):
    return re.sub(r' ?\[[^\[\]\n]*[A-Za-z][^\[\]\n]*\]', '',text)

def get_text():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    headings=dict(line.split(' | ',1) for line in (HERE/'headings.txt').read_text('utf-8').splitlines() if line.strip())
    values={u['id']:headings[u['source_markup']] for u in units if u['kind']=='heading'}
    part=records(HERE/'automatic.md')
    assert not set(part)&set(values)
    values.update(part)
    return values

def nums(text):
    text=text.replace('−','-')
    text=re.sub(r'(?<=\d)-in-(?=\d)', '~', text)
    text=re.sub(r'(?<=\d)\s+(?=%)', '', text)
    text=text.replace('¾','3/4').replace('½','1/2').replace('¼','1/4')
    text=re.sub(r'(?<=\d)[ ,\u00a0](?=\d{3}(?:\D|$))','',text)
    text=re.sub(r'(?<=\d),(?=\d)', '.',text)
    # Preserve signed dice modifiers before normalizing ordinary numeric ranges.
    dice=[]
    def take_dice(m):
        dice.append(re.sub(r'\s+','',m[0]));return ' DICE '
    text=re.sub(r'\d+d\d+(?:\s*[+\-]\s*\d+)?!?',take_dice,text)
    text=re.sub(r'(?<=\d)([’”\'\"]?)\s*[-–—]\s*(?=\d)',r'\1~',text)
    text=re.sub(r'(Divine|Arcane)-(?=\d)',r'\1~',text)
    return Counter(dice+re.findall(r'[+\-]?\d+(?:\.\d+)?(?:%|\+)?',text))

def main():
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    text=get_text();source={u['id']:u for u in units}
    assert not set(text)-set(source)
    errors=[];missing=[u['id'] for u in units if u['id'] not in text]
    for id,value in text.items():
        en=source[id]['source_markup'];a,b=nums(en),nums(strip_english(value))
        if a!=b:errors.append({'id':id,'english':en,'russian':value,'missing':dict(a-b),'extra':dict(b-a)})
    result={'complete':not missing,'translated_units':len(text),'source_units':len(units),'untranslated_units':missing,
        'numeric_differences':errors,'source_words_translated':sum(len(u['source_plain'].split()) for u in units if u['id'] in text),
        'source_words_total':sum(len(u['source_plain'].split()) for u in units)}
    (HERE/'numeric_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    for p in range(180,264):
        chosen=[u for u in units if u['pdf_page']==p and u['id'] in text]
        (HERE/f'review_{p}.md').write_text('\n\n'.join(f'### {u["id"]}\n\n{u["source_markup"]}\n\n{text[u["id"]]}' for u in chosen)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('untranslated_units','numeric_differences')},ensure_ascii=False))
    print(json.dumps([{k:v for k,v in e.items() if k not in ('english','russian')} for e in errors],ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
