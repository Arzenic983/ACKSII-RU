from pathlib import Path
import re, json
from collections import Counter

root = Path(__file__).resolve().parent
pattern = re.compile(r'<!-- unit: ([\w.]+) -->\s*\n(.*?)(?=\n<!-- unit: |\Z)', re.S)
source = [(uid, txt.strip()) for uid, txt in pattern.findall((root/'pending_A.md').read_text(encoding='utf-8')) if 42 <= int(uid[4:8]) <= 45]
target = [(uid, txt.strip()) for uid, txt in pattern.findall((root/'translated_A_42_45.md').read_text(encoding='utf-8'))]
sid, tid = [a for a,b in source], [a for a,b in target]
s, t = dict(source), dict(target)
num = re.compile(r'(?<![A-Za-z0-9])[-+]?\d+(?:,\d{3})*(?:d\d+)?(?:/\d+)?')
numbers, formatting, latin = [], [], []
for uid in sid:
    if uid not in t: continue
    a, b = s[uid], t[uid]
    na, nb = Counter(num.findall(a)), Counter(num.findall(b))
    if na != nb: numbers.append({'id':uid, 'source':dict(na), 'target':dict(nb)})
    if a.count('*') != b.count('*') or Counter(re.findall(r'<br\s*/?>', a)) != Counter(re.findall(r'<br\s*/?>', b)):
        formatting.append(uid)
    eng = re.findall(r'[A-Za-z]+', re.sub(r'<br\s*/?>', '', b))
    eng = [v for v in eng if v not in {'d', 'I','II','III','IV','V','VI'}]
    if eng: latin.append({'id':uid,'words':eng})
result = {
    'source_count':len(source), 'target_count':len(target), 'ids_and_order_equal':sid==tid,
    'duplicate_ids':[u for u,c in Counter(tid).items() if c>1],
    'missing_ids':sorted(set(sid)-set(tid)), 'unexpected_ids':sorted(set(tid)-set(sid)),
    'numeric_token_mismatches':numbers, 'formatting_mismatches':formatting,
    'untranslated_latin_tokens':latin, 'empty_translations':[u for u,v in target if not v],
}
(root/'validation_A_42_45_B.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
