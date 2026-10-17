"""Parse every leader-and-page index entry without changing source units."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    source=[json.loads(s) for s in (ROOT/'contributions/E/source.jsonl').read_text('utf-8').splitlines()]
    entries=[]
    fixes_path=HERE/'source_display_fixes.json'
    fixes=json.loads(fixes_path.read_text('utf-8')) if fixes_path.exists() else {}
    for u in source:
        if u['kind']!='paragraph' or u['pdf_page']<545:continue
        text=u['english'];pos=0;n=0
        if u['id'] in fixes:
            assert text==fixes[u['id']]['original']
            text=fixes[u['id']]['numeric_source']
        for m in re.finditer(r'(.*?)\.{1,}\s*(\d+(?:\s*[,–-]\s*\d+)*)',text):
            assert not text[pos:m.start()].strip(),(u['id'],text[pos:m.start()])
            label=m[1].strip();letters=[]
            while re.match(r'^\*\*[A-Z]\*\*\s*',label):
                lead=re.match(r'^\*\*([A-Z])\*\*\s*',label);letters.append(lead[1]);label=label[lead.end():]
            assert label,(u['id'],m[0])
            n+=1;entries.append({'unit':u['id'],'part':n,'english':label,'pages':m[2],'embedded_letters':letters,'source_fragment':m[0]})
            pos=m.end()
        assert pos and not text[pos:].strip(),(u['id'],text[pos:])
    (HERE/'index_entries.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n','utf-8')
    (HERE/'index_english.tsv').write_text(''.join(f"{e['unit']}\t{e['part']}\t{e['english']}\t{e['pages']}\n" for e in entries),'utf-8')
    print('Parsed',len(entries),'entries;',len({e['english'] for e in entries}),'distinct labels')
if __name__=='__main__':main()
