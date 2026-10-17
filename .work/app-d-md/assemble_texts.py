"""Assemble all 163 manually translated resource units without importing."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    pairs=[s.split('\t',1) for s in (HERE/'translations.tsv').read_text('utf-8').splitlines() if s]
    pure=dict(pairs)
    source=[json.loads(s) for s in (ROOT/'contributions/D/source.jsonl').read_text('utf-8').splitlines()]
    assert len(pairs)==len(pure)==len(source)==163
    assert set(pure)=={u['id'] for u in source} and all(v.strip() for v in pure.values())
    pure={u['id']:pure[u['id']] for u in source}
    (HERE/'pure.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2)+'\n','utf-8',newline='\n')
    print('Assembled 163/163 units')
if __name__=='__main__':main()
