"""Collect the 283 manually translated units; reject gaps and unknown IDs."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    pairs=[s.split('\t',1) for s in (HERE/'translations.tsv').read_text('utf-8').splitlines() if s]
    pure=dict(pairs);assert len(pure)==len(pairs)==283
    source=[json.loads(s) for s in (ROOT/'contributions/B/source.jsonl').read_text('utf-8').splitlines()]
    assert set(pure)=={u['id'] for u in source}
    assert all(pure[u['id']].strip() for u in source)
    pure={u['id']:pure[u['id']] for u in source}
    (HERE/'pure.json').write_text(json.dumps(pure,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Translated:',len(pure))
if __name__=='__main__':main()
