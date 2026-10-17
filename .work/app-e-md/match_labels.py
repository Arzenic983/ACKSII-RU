"""Find index names in already reviewed translations; candidates require review."""
from pathlib import Path
from collections import defaultdict,Counter
import html,json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def strip(s):return html.unescape(re.sub(r'<[^>]+>',' ',s)).replace('\\','').replace('*','').replace('_','').strip().rstrip(':')
def norm(s):return re.sub(r'\s+',' ',strip(s)).casefold().replace('’',"'").replace('–','-')
def main():
    entries=json.loads((HERE/'index_entries.json').read_text('utf-8'));candidates=defaultdict(list)
    with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        for uid,page,kind,en,ru in db.execute("SELECT id,printed_page,kind,english,russian FROM bilingual WHERE chapter_id!='E' AND russian IS NOT NULL"):
            pairs=[]
            if len(en)<220 and len(ru)<350:pairs.append((strip(en),strip(ru),'whole'))
            a=re.match(r'^\s*(\*{1,3})(.+?)\1',en);b=re.match(r'^\s*(\*{1,3})(.+?)\1',ru)
            if a and b and len(a[2])<160:pairs.append((strip(a[2]),strip(b[2]),'leading_emphasis'))
            a=re.match(r'^([^:]{2,100}):',en);b=re.match(r'^([^:]{2,160}):',ru)
            if a and b:pairs.append((strip(a[1]),strip(b[1]),'leading_label'))
            a=list(re.finditer(r'(\*{1,3})(.+?)\1',en));b=list(re.finditer(r'(\*{1,3})(.+?)\1',ru))
            if len(a)==len(b):
                pairs.extend((strip(x[2]),strip(y[2]),'paired_emphasis') for x,y in zip(a,b) if len(x[2])<150 and len(y[2])<200)
            for name,russian,method in pairs:
                variants=[(name,russian)]
                if re.search(r'\s*\([^()]+\)$',name) and re.search(r'\s*\([^()]+\)$',russian):
                    variants.append((re.sub(r'\s*\([^()]+\)$','',name),re.sub(r'\s*\([^()]+\)$','',russian)))
                for name,russian in variants:
                    candidates[norm(name)].append({'russian':russian,'source_id':uid,'printed_page':page,'kind':kind,'method':method})
    result=[]
    for e in entries:
        choices=candidates.get(norm(e['english']),[]);pages={int(s) for s in re.findall(r'\d+',e['pages'])}
        choices=sorted(choices,key=lambda c:((c['printed_page'] in pages)*100+(c['kind']=='heading')*20+(c['method']=='whole')*10),reverse=True)
        result.append({**e,'candidate':choices[0] if choices else None,'alternatives':choices[:6]})
    (HERE/'candidate_labels.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    unique={e['english']:e for e in result}
    (HERE/'candidate_review.tsv').write_text(''.join(f"{name}\t{e['candidate']['russian'] if e['candidate'] else '???'}\t{e['candidate']['source_id'] if e['candidate'] else ''}\n" for name,e in unique.items()),'utf-8')
    missing=[e for e in unique.values() if not e['candidate']]
    print('Matched:',len(unique)-len(missing),'Unmatched:',len(missing))
    for e in missing:print(e['english'],e['pages'])
if __name__=='__main__':main()
