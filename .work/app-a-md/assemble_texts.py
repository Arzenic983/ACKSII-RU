"""Read manual translations, table rows and visually reconstructed language trees."""
from pathlib import Path
import json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    pairs=[s.split('\t',1) for s in (HERE/'translations.tsv').read_text('utf-8').splitlines() if s]
    assert len(dict(pairs))==len(pairs)
    translated=dict(pairs)
    source=[json.loads(s) for s in (ROOT/'contributions/A/source.jsonl').read_text('utf-8').splitlines()]
    with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        meta={r['id']:dict(r) for r in db.execute("SELECT * FROM bilingual WHERE chapter_id='A'")}
    tables=json.loads((HERE/'table_rows.json').read_text('utf-8'))
    for u in source:
        m=meta[u['id']]
        if u['kind']=='table_cell':
            assert u['id'] not in translated
            translated[u['id']]=tables[m['table_id']][m['row_index']][m['column_index']]
    nodes=[s.split('\t') for s in (HERE/'language_nodes.tsv').read_text('utf-8').splitlines() if s]
    en={u['id']:u['english'] for u in source}
    assert ' '.join(n[1] for n in nodes)==en['rr.p0507.b003']
    counterparts=re.findall(r'\[[^]]+\]',en['rr.p0507.b005'])
    assert len(nodes)==len(counterparts)==58
    previous=0
    for n,english in zip(nodes,counterparts):
        depth=int(n[0]);assert depth<=previous+1;previous=depth
        n.append(english)
    translated['rr.p0507.b003']=' '.join(n[2] for n in nodes)
    translated['rr.p0507.b005']=' '.join('['+n[3]+']' for n in nodes)
    assert set(translated)==set(en),(set(en)-set(translated),set(translated)-set(en))
    translated={u['id']:translated[u['id']] for u in source}
    (HERE/'pure.json').write_text(json.dumps(translated,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'language_nodes.json').write_text(json.dumps(nodes,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Translated:',len(translated),'units; language nodes:',len(nodes))
if __name__=='__main__':main()
