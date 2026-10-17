"""Seed only exact, already translated table phrases; list remaining phrases."""
from pathlib import Path
import json,re,sqlite3
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
source=[json.loads(s) for s in (ROOT/'contributions/12/source.jsonl').read_text('utf-8').splitlines()]
old=dict(s.split('\t',1) for s in (HERE.parent/'ch11-md/cell_terms.tsv').read_text('utf-8').splitlines() if s)
cells=list(dict.fromkeys(u['english'] for u in source if u['kind']=='table_cell'))
target=HERE/'cell_terms.tsv'
assert not target.read_text('utf-8')
target.write_text(''.join(en+'\t'+old[en]+'\n' for en in cells if en in old),'utf-8')
untranslated=[en for en in cells if en not in old and re.search('[A-Za-z]',re.sub(r'[dD](?=\d)','',en)) and not re.fullmatch(r'[\d,]+gp',en)]
print(json.dumps(untranslated,ensure_ascii=False,indent=2))
with sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    print('SOURCE CROSS-CHECKS')
    for row in db.execute("SELECT id,english,russian FROM bilingual WHERE chapter_id='04' AND (english LIKE '%Stone structures are even%' OR english LIKE '**Keep:**%' OR english LIKE '**Unit Capacity:**%' OR english LIKE '%Cauldron:%' OR english LIKE '%Light Catapult%' AND kind!='table_cell')"):
        print(json.dumps(row,ensure_ascii=False))
