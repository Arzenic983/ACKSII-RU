from pathlib import Path
import re, json, sqlite3
from collections import Counter
base=Path(__file__).resolve().parent
pat=re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)',re.S)
src=pat.findall((base/'source_D.md').read_text(encoding='utf-8-sig'))
dst=pat.findall((base/'translated_D.md').read_text(encoding='utf-8-sig'))
s,t=dict(src),dict(dst)
def nums(v):
    v=re.sub(r'(?<=\d)[ ,\u00a0\u202f](?=\d{3}(?:\D|$))','',v).replace('−','-')
    return Counter(re.findall(r'\d+',v))
num=[{'id':u,'source':dict(nums(v)),'target':dict(nums(t[u]))} for u,v in src if u in t and nums(v)!=nums(t[u])]
fmt=[{'id':u,'source_br':len(re.findall(r'<br\s*/?>',v)),'target_br':len(re.findall(r'<br\s*/?>',t[u])),'source_bold':v.count('**'),'target_bold':t[u].count('**')} for u,v in src if u in t and (len(re.findall(r'<br\s*/?>',v))!=len(re.findall(r'<br\s*/?>',t[u])) or v.count('**')!=t[u].count('**'))]
result={'source_count':len(src),'target_count':len(dst),'ids_and_order_equal':[u for u,v in src]==[u for u,v in dst],'missing_ids':sorted(set(s)-set(t)),'unexpected_ids':sorted(set(t)-set(s)),'duplicate_ids':[u for u,c in Counter(u for u,v in dst).items() if c>1],'empty_ids':[u for u,v in dst if not v.strip()],'numeric_mismatches':num,'formatting_mismatches':fmt}
(base/'validation_D.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
conn=sqlite3.connect('file:ACKSII/База перевода/acksii_translation.sqlite?mode=ro',uri=True)
print(conn.execute('PRAGMA table_info(bilingual)').fetchall())
