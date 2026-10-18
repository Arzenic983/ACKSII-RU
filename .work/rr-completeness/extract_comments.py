from pathlib import Path
import json, zipfile, re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def text(e):
    return ''.join(n.text or '' for n in e.iter() if n.tag in (W+'t',W+'delText'))

def main():
    inventory=json.loads((HERE/'inventory.json').read_text('utf-8'))
    result=[]; changes=[]
    for d in inventory['docx']:
        if not d['comments'] and not any(d['tracked'].values()):continue
        with zipfile.ZipFile(ROOT/d['path']) as z:
            doc=ET.fromstring(z.read('word/document.xml'))
            contexts={}; anchors={}; active=set()
            for p in doc.iter(W+'p'):
                for n in p.iter():
                    if n.tag==W+'commentRangeStart':
                        cid=n.get(W+'id');active.add(cid);contexts.setdefault(cid,[]).append(text(p));anchors.setdefault(cid,[])
                    elif n.tag==W+'commentRangeEnd':active.discard(n.get(W+'id'))
                    elif n.tag==W+'t':
                        for cid in active:anchors[cid].append(n.text or '')
                for kind in ('ins','del','moveFrom','moveTo'):
                    for n in p.iter(W+kind):
                        changes.append({'path':d['path'],'kind':kind,'text':text(n),'context':text(p)})
            for c in d['comments']:
                result.append({'key':str(len(result)+1),'path':d['path'],**c,
                    'anchor':''.join(anchors.get(c['id'],[])), 'context':' '.join(dict.fromkeys(contexts.get(c['id'],[])))})
    (HERE/'legacy_comments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'tracked_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Comments:',len(result),'Tracked changes:',len(changes))
    for c in result[:66]:
        print(c['key'],Path(c['path']).name,'#'+c['id'],json.dumps(c['text'],ensure_ascii=False),'ANCHOR:',c['anchor'][:350], 'CONTEXT:',c['context'][:350] if not c['anchor'] else '')

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
