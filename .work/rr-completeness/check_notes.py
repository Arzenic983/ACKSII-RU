"""Compare the summary with all inline notes, accounting for historical grouping."""
from pathlib import Path
from collections import Counter
import importlib.util,json,re

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'ACKSII/База перевода'
spec=importlib.util.spec_from_file_location('reader',ROOT/'tools/build_rr_reader.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)

def normalize(s):
    s=re.split(r'\n#{1,6} ',s,maxsplit=1)[0]
    # Compare the historical summary with the original full-chapter notes;
    # reader-only wording is checked separately by the explicit projection.
    s=reader.clean(s,project_notes=False)
    s=re.sub(r'<!--[^>]*-->','',s)
    s=re.sub(r'^#{1,6} [^\n]*','',s,flags=re.M)
    s=re.sub(r'<small>.*?</small>','',s,flags=re.S)
    s=re.sub(r'^> \\?\*\s*','',s)
    s=re.sub(r'^\d+\s+','',s)
    s=re.sub(r'^(?:PDF \d+\s*[:—]\s*)+','',s)
    s=re.sub(r'\[[^\[\]А-Яа-яЁё]*[A-Za-z][^\[\]А-Яа-яЁё]*\]','',s)
    return ''.join(re.findall('[А-Яа-яЁёA-Za-z0-9]',s)).lower()

def main():
    source=(reader.OUT/'Примечания редактора.md').read_text('utf-8')
    records=re.split(r'<!-- unit: [^ ]+ -->\s*',source)[1:]
    inline=[]
    for ch in json.loads((BASE/'progress.json').read_text('utf-8')):
        path=reader.OUT/('00 Начало.md' if ch['id']=='front_matter' else ch['id']+' '+ch['title_ru']+'.md')
        inline.extend(line for line in path.read_text('utf-8').splitlines() if line.startswith('> '))
    available=Counter(normalize(s) for s in inline);combined=[]
    for text in records:
        n=normalize(text)
        if available[n]:available[n]-=1;continue
        pairs=[(first,n[len(first):]) for first,count in available.items() if count and n.startswith(first) and available[n[len(first):]]]
        assert len(pairs)==1,('Unmatched summary note',text[:160])
        a,b=pairs[0];available[a]-=1;available[b]-=1
        combined.append(text[:150])
    left=list((+available).elements())
    assert len(left)==1 and left[0].startswith('греблянамалойскорости'),left
    result={'date':'2026-10-18','inline_notes':len(inline),'editorial_summary_records':len(records),
        'summary_records_combining_two_notes':len(combined),'all_summary_notes_present_inline':True,
        'all_editorial_notes_present_in_summary':True,'author_footnotes_outside_editorial_summary':1,
        'author_footnote':'rr.p0335.b036: гребля и сменная работа команды',
        'reader_notes_equal_full_chapters':Counter(reader.notes(reader.HUMAN.read_text('utf-8')))==Counter(reader.notes('\n'.join(inline)))}
    assert result['reader_notes_equal_full_chapters']
    (BASE/'RR_notes_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8');main()
