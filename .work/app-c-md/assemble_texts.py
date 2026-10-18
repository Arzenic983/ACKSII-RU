"""Assemble all 827 manually translated units; no database mutation."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def read_tsv(p):
    pairs=[s.split('\t',1) for s in p.read_text('utf-8').splitlines() if s]
    assert len(dict(pairs))==len(pairs),p
    return dict(pairs)
def main():
    source=[json.loads(s) for s in (ROOT/'contributions/C/source.jsonl').read_text('utf-8').splitlines()]
    manual=read_tsv(HERE/'translations.tsv');cells=read_tsv(HERE/'cell_terms.tsv');pure={}
    assert set(manual).issubset({u['id'] for u in source})
    for u in source:
        en=u['english'];ru=manual.get(u['id'])
        if ru is None and u['kind']=='table_cell':
            ru=cells.get(en)
            if ru is None and not re.search('[A-Za-z]',re.sub('<[^>]*>','',en)):ru=en.replace(',',' ')
        assert ru and ru.strip(),u['id']
        pure[u['id']]=ru
    assert len(pure)==len(source)==827
    (HERE/'pure.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Assembled 827/827 units')
if __name__=='__main__':main()
