"""Print complete source/translation pairs for a bounded semantic review."""
import json,sys
from auto_units import HERE
from review_tools import get_text,strip_english
def main():
    start,end=map(int,sys.argv[1:3]);u=json.loads((HERE/'source_units.json').read_text('utf-8'));v=get_text()
    for x in u:
        if not start<=x['pdf_page']<=end or x['table_id'] or x['kind']=='heading':continue
        if x['source_markup'].startswith(('**ARCANE**','**DIVINE**')):continue
        print(x['id']+'\nEN: '+x['source_plain']+'\nRU: '+strip_english(v[x['id']])+'\n')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
