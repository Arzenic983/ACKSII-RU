"""Assemble all 83 units, including 862 indexed labels and original references."""
from pathlib import Path
import json
from collections import defaultdict
from parse_index import main as parse
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    parse()
    source=[json.loads(s) for s in (ROOT/'contributions/E/source.jsonl').read_text('utf-8').splitlines()]
    entries=json.loads((HERE/'index_entries.json').read_text('utf-8'))
    labels=dict(s.split('\t',1) for s in (HERE/'label_translations.tsv').read_text('utf-8').splitlines() if s)
    pairs=[s.split('\t',1) for s in (HERE/'translations.tsv').read_text('utf-8').splitlines() if s]
    pure=dict(pairs);assert len(pure)==len(pairs)
    blocks=defaultdict(list)
    for e in entries:
        e['russian']=labels[e['english']]
        prefix=''.join('**'+letter+'**\n' for letter in e['embedded_letters'])
        blocks[e['unit']].append(prefix+e['russian']+' — '+e['pages'])
    assert not set(blocks)&set(pure)
    pure.update({uid:'\n'.join(lines) for uid,lines in blocks.items()})
    assert set(pure)=={u['id'] for u in source} and len(pure)==83 and all(s.strip() for s in pure.values())
    pure={u['id']:pure[u['id']] for u in source}
    for name,value in [('pure.json',pure),('styled_entries.json',entries)]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8',newline='\n')
    print('Assembled 83/83 units, 862 index entries')
if __name__=='__main__':main()
