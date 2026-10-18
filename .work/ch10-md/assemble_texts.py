"""Join manually translated units and explicitly mapped table phrases."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def tsv(path):
    pairs=[s.split('\t',1) for s in path.read_text('utf-8').splitlines() if s]
    assert len({p[0] for p in pairs})==len(pairs),path
    return dict(pairs)
def main():
    explicit=tsv(HERE/'translations.tsv')
    cells=tsv(HERE/'cell_terms.tsv')
    source=[json.loads(s) for s in (ROOT/'contributions/10/source.jsonl').read_text('utf-8').splitlines()]
    result={};missing=[]
    for u in source:
        en=u['english']
        if u['id'] in explicit: ru=explicit[u['id']]
        elif en in cells: ru=cells[en]
        elif u['kind']=='table_cell' and re.fullmatch(r'[IVX]+|1D8',en): ru=en
        elif u['kind']=='table_cell' and not re.search('[A-Za-z]',en): ru=en
        elif u['kind']=='table_cell' and re.fullmatch(r'[\d,]+gp',en): ru=en.replace(',',' ').replace('gp',' зм')
        elif u['kind']=='table_cell' and all(s in cells for s in en.split('<br/>')):
            ru='<br/>'.join(cells[s] for s in en.split('<br/>'))
        else:
            missing.append((u['id'],en));continue
        result[u['id']]=ru
    assert set(explicit).issubset(result),'Unknown explicit IDs'
    (HERE/'pure.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Translated:',len(result),'of',len(source))
    if missing:
        print(json.dumps(missing,ensure_ascii=False,indent=2))
    assert not missing,'Translation gaps'
if __name__=='__main__':main()
