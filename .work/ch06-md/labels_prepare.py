from common import HERE,ROOT,read,write
from collections import defaultdict
import re,sqlite3
db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
known=defaultdict(set)
for en,ru in db.execute('SELECT u.source_markup,t.text_ru FROM units u JOIN translations t ON t.unit_id=u.id'):
    known[en].add(ru)
values={};unknown={}
for u in read('source_units.json'):
    if not u['table_id'] and u['kind']!='heading':continue
    en=u['source_markup']
    if not re.search('[A-Za-z]',re.sub(r'\d+d\d+','',en)):values[u['id']]=en
    elif len(known[en])==1:values[u['id']]=next(iter(known[en]))
    else:unknown.setdefault(en,u['id'])
write('automatic_labels.json',values)
(HERE/'labels_needed.txt').write_text('\n'.join(id+' | '+en for en,id in unknown.items()),'utf-8')
print('automatic',len(values),'unique labels to translate',len(unknown))
print((HERE/'labels_needed.txt').read_text('utf-8'))
