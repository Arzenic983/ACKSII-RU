from common import read
import sys
sys.stdout.reconfigure(encoding='utf-8')
pages={int(x) for x in sys.argv[1:] if x.isdigit()};ru='--ru' in sys.argv;cells='--cells' in sys.argv
values=read('prose.json',{});candidate=read('candidates.json',{})
seen=set()
for u in read('source_units.json'):
    if u['pdf_page'] not in pages:continue
    if bool(u['table_id'])!=cells:continue
    en=u['source_markup']
    if cells and en in seen:continue
    seen.add(en)
    if '--ruonly' not in sys.argv:print(u['id']+' | '+en)
    else:print(u['id'])
    if ru:print('RU: '+values.get(u['id'],candidate.get(u['id'],'[НЕТ]')))
    print()
