from pathlib import Path
from collections import Counter
import hashlib, json, re, sqlite3, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'ACKSII/База перевода'
HERE = Path(__file__).resolve().parent
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def main():
    db = sqlite3.connect((BASE/'acksii_translation.sqlite').as_uri()+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    units = [dict(r) for r in db.execute('SELECT * FROM bilingual ORDER BY pdf_page,block_order,row_index,column_index,id')]
    result = {'units': len(units), 'status': dict(Counter(u['status'] for u in units)),
              'issues': [dict(r) for r in db.execute('SELECT * FROM issues')],
              'no_cyrillic': [u for u in units if re.search('[A-Za-z]{3}', u['russian'] or '') and not re.search('[А-Яа-яЁё]', u['russian'] or '')],
              'docx': []}
    for path in sorted((ROOT/'ACKSII').rglob('*.docx')):
        if path.parts[-2] in ('ACKSII Monstrous Manual', 'ACKSII Judges Journal', 'ACKSII Treasure Tome'):
            continue
        entry = {'path': str(path.relative_to(ROOT)), 'comments': [], 'tracked': {}}
        try:
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    if re.fullmatch(r'word/comments\d*\.xml', name):
                        for c in ET.fromstring(z.read(name)).iter(W+'comment'):
                            entry['comments'].append({'id': c.get(W+'id'), 'author': c.get(W+'author'),
                                'text': ''.join(c.itertext())})
                if 'word/document.xml' in z.namelist():
                    doc = ET.fromstring(z.read('word/document.xml'))
                    entry['tracked'] = {k: sum(1 for _ in doc.iter(W+k)) for k in ('ins','del','moveFrom','moveTo')}
        except zipfile.BadZipFile:
            entry['unavailable'] = True
        result['docx'].append(entry)
    result['protected'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT/'ACKSII').rglob('*') if p.is_file() and (p.suffix in ('.sqlite','.pdf','.docx') or p.name in ('glossary.json','Глоссарий.md','bilingual_terms.md') or p.parent.name=='Source')}
    (HERE/'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n','utf-8')
    print(json.dumps({'units': result['units'], 'status': result['status'],
        'issues': result['issues'], 'non_cyrillic': len(result['no_cyrillic']),
        'long_non_cyrillic': [{k:u[k] for k in ('id','english','russian')} for u in result['no_cyrillic'] if len(u['russian'])>45],
        'docx': [{**d,'comments':d['comments']} for d in result['docx'] if d['comments'] or any(d['tracked'].values())],
        'docx_count':len(result['docx'])}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
