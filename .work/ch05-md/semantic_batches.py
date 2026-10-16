"""Bounded complete pairs for explicit semantic review; does not mark them reviewed."""
import json,sys
from auto_units import HERE
from review_tools import get_text,strip_english
def main():
    us={u['id']:u for u in json.loads((HERE/'source_units.json').read_text('utf-8'))};state=json.loads((HERE/'semantic_review.json').read_text('utf-8'));v=get_text()
    groups=[];current=[];length=0
    for id in state['remaining_reference_candidates_for_semantic_review']:
        size=len(us[id]['source_plain'])+len(strip_english(v[id]))+50
        if current and length+size>18000:groups.append(current);current=[];length=0
        current.append(id);length+=size
    if current:groups.append(current)
    saved=HERE/'semantic_batches.json'
    if saved.exists():groups=json.loads(saved.read_text('utf-8'))
    else:saved.write_text(json.dumps(groups,ensure_ascii=False,indent=2),'utf-8')
    if len(sys.argv)==1:print('Batches',len(groups));return
    n=int(sys.argv[1]);print('BATCH',n,'of',len(groups))
    for id in groups[n]:print(id+'\nEN: '+us[id]['source_plain']+'\nRU: '+strip_english(v[id])+'\n')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
