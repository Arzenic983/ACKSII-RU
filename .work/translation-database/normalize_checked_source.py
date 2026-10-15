import collections,hashlib,json,pathlib,re,subprocess,sys
sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
ROOT=WORK.parents[1]
source=ROOT/'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md'
text=source.read_text(encoding='utf8');old=text
patches=json.loads((WORK/'source_normalizations.json').read_text(encoding='utf8'))
applied=0
for patch in patches:
    n=patch['page'];start=text.index(f'<a id="pdf-page-{n:04d}">')
    end=text.find('<a id="pdf-page-',start+10)
    if end<0:end=len(text)
    page=text[start:end];a,b=patch['before']
    if a in page and '\n\n'+b in page:
        page=page.replace(a,patch['after'],1).replace('\n\n'+b,'',1)
        text=text[:start]+page+text[end:];applied+=1
assert collections.Counter(c for c in text if c.isalnum())==collections.Counter(c for c in old if c.isalnum())
source.write_text(text,encoding='utf8')
before_units={u['id']:u['source_sha256'] for u in json.loads((WORK/'all_units.json').read_text(encoding='utf8'))}
r=subprocess.run([sys.executable,str(WORK/'prepare_units.py')],capture_output=True,encoding='utf8')
assert r.returncode==0,r.stdout+r.stderr
after_units={u['id']:u['source_sha256'] for u in json.loads((WORK/'all_units.json').read_text(encoding='utf8'))}
assert before_units==after_units,'Unit identity changed after source paragraph normalization'
manifest=ROOT/'.work/revised-rulebook-extraction/final-validation.json'
validation=json.loads(manifest.read_text(encoding='utf8'));validation['transcription_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
validation.setdefault('followup_corrections',[])
if applied:validation['followup_corrections'].append({'kind':'paragraph_continuity','pages':sorted({x['page'] for x in patches}),'joins':applied,'source_payload_unchanged':True,'date':'2026-10-14'})
manifest.write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
if applied:
    with (ROOT/'ACKSII/Source/ACKSII Revised Rulebook — проверка извлечения.md').open('a',encoding='utf8') as out:
        out.write('\nТакже объединены семь разорванных абзацев на PDF 4, 10, 16, 18 и 21. Содержание сохранено; идентификаторы и контрольные суммы записей базы до и после объединения совпадают.\n')
print('Paragraph joins applied:',applied,'; all',len(after_units),'unit IDs and hashes retained.')
