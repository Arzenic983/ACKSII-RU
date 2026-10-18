"""Assemble only completed units and report gaps; no import or completion claim."""
from pathlib import Path
import hashlib,json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def read_tsv(path):
    pairs=[s.split('\t',1) for s in path.read_text('utf-8').splitlines() if s]
    assert len(dict(pairs))==len(pairs),path
    return dict(pairs)
def numeric(s,russian=False):
    s=re.sub('<[^>]*>','',s)
    s=re.sub(r'(?<=\d)'+(r'[ \u00a0]' if russian else r'[,\u00a0]')+r'(?=\d{3}(?:\D|$))','',s)
    return [n.replace(',','.') for n in re.findall(r'\d+(?:[.,]\d+)?',s)]
def main():
    source=[json.loads(s) for s in (ROOT/'contributions/C/source.jsonl').read_text('utf-8').splitlines()]
    manual=read_tsv(HERE/'translations.tsv');cells=read_tsv(HERE/'cell_terms.tsv')
    assert set(manual).issubset({u['id'] for u in source})
    pure={};pending=[];issues=[]
    for u in source:
        en=u['english'];ru=manual.get(u['id'])
        if ru is None and u['kind']=='table_cell':
            if en in cells:ru=cells[en]
            elif not re.search('[A-Za-z]',re.sub('<[^>]*>','',en)):ru=en.replace(',',' ')
        if ru is None:pending.append(u['id']);continue
        assert hashlib.sha256(en.encode()).hexdigest()==u['source_sha256']
        diffs={}
        if numeric(en)!=numeric(ru,True):diffs['numbers']=[numeric(en),numeric(ru,True)]
        if en.count('*')!=ru.count('*'):diffs['emphasis']=[en.count('*'),ru.count('*')]
        if en.count('<br>')!=ru.count('<br>'):diffs['breaks']=[en.count('<br>'),ru.count('<br>')]
        if re.findall(r'\d+%',en)!=re.findall(r'\d+%',ru):diffs['percentages']=[en,ru]
        if re.findall(r'(?<!\w)[+-]\d+(?:/\d+)?',en)!=re.findall(r'(?<!\w)[+-]\d+(?:/\d+)?',ru):diffs['signed_modifiers']=[en,ru]
        if diffs:issues.append({'id':u['id'],'differences':diffs})
        pure[u['id']]=ru
    (HERE/'partial.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2)+'\n','utf-8')
    report={'date':'2026-10-17','chapter':'C','translated_draft':len(pure),'total':len(source),'pending':len(pending),'pending_ids':pending,'mechanical_differences':issues,'reviewed':False,'integrated':False}
    (HERE/'partial_status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not issues,issues
    with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='C' AND russian IS NULL AND revision=0").fetchone()[0]==827
    print(json.dumps({k:v for k,v in report.items() if k!='pending_ids'},ensure_ascii=False))
if __name__=='__main__':main()
