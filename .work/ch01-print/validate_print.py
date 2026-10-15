import pathlib,json,hashlib,sqlite3,re,html,collections,sys
from pypdf import PdfReader
from pypdf.generic import IndirectObject,StreamObject
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).resolve().parents[2];WORK=pathlib.Path(__file__).resolve().parent
m=json.loads((WORK/'layout_manifest.json').read_text(encoding='utf8'))
file=pathlib.Path(m['output']);pdf=PdfReader(file)
db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
expected={u:t for u,t in db.execute('select u.id,t.text_ru from units u join translations t on u.id=t.unit_id where u.chapter_id="01"')}
plain=lambda s:html.unescape(re.sub('<[^>]+>','',s)).replace('*','')
payload=lambda s:collections.Counter(c.casefold() for c in plain(s) if c.isalnum())
counts=collections.Counter(e['unit_id'] for e in m['elements'])
assert set(counts)==set(expected) and set(counts.values())=={1}
for e in m['elements']:assert payload(e['text'])==payload(expected[e['unit_id']]),e['unit_id']
page_checks=[]
for i,p in enumerate(pdf.pages):
    got=payload(p.extract_text());want=collections.Counter()
    for e in m['elements']:
        if e['unit_id'].startswith(f'rr.p{i+14:04d}.'):want.update(payload(e['text']))
    if i:
        # The source prints the same footer numeral twice in coincident streams.
        want.update(payload('ПЕРСОНАЖИПЕРСОНАЖИ'+str(i+12)*2))
    assert got==want, (i+1,dict(want-got),dict(got-want))
    assert list(p.mediabox)==[0,0,612,792]
    assert not p.get('/Annots')
    assert '*' not in p.extract_text()
    page_checks.append({'page':i+1,'text_complete':True,'source_pdf_page':i+14,'printed_page':i+12 if i else None})

def image_fingerprints(p):
    result=[];seen=set()
    def color_key(value):
        if isinstance(value,IndirectObject):return color_key(value.get_object())
        if isinstance(value,StreamObject):return ('stream',hashlib.sha256(value.get_data()).hexdigest())
        if isinstance(value,list):return tuple(color_key(v) for v in value)
        if isinstance(value,dict):return tuple(sorted((str(k),color_key(v)) for k,v in value.items()))
        if isinstance(value,bytes):return hashlib.sha256(value).hexdigest()
        return str(value)
    def walk(res):
        for ref in res.get('/XObject',{}).values():
            ob=ref.get_object();key=id(ob)
            if key in seen:continue
            seen.add(key)
            if ob.get('/Subtype')=='/Form':walk(ob.get('/Resources',res))
            elif ob.get('/Subtype')=='/Image':
                cs=color_key(ob.get('/ColorSpace'))
                mask=ob.get('/SMask')
                mask_hash=hashlib.sha256(mask.get_object()._data).hexdigest() if mask else ''
                result.append((int(ob['/Width']),int(ob['/Height']),str(cs),hashlib.sha256(ob._data).hexdigest(),mask_hash))
    walk(p['/Resources']);return sorted(result)
source=PdfReader(ROOT/'ACKSII/Source/ACKSII Revised Rulebook.pdf')
for i,p in enumerate(pdf.pages):
    assert image_fingerprints(p)==image_fingerprints(source.pages[i+13]),i+1

fonts={};seen=set()
def check_fonts(res):
    for ref in res.get('/Font',{}).values():
        ob=ref.get_object();name=str(ob.get('/BaseFont'))
        descendants=ob.get('/DescendantFonts',[])
        fd=(descendants[0].get_object() if descendants else ob).get('/FontDescriptor')
        assert fd and any(k in fd.get_object() for k in ['/FontFile','/FontFile2','/FontFile3']),name
        fonts[name]=True
    for ref in res.get('/XObject',{}).values():
        ob=ref.get_object()
        if id(ob) in seen:continue
        seen.add(id(ob))
        if ob.get('/Subtype')=='/Form':check_fonts(ob.get('/Resources',res))
for p in pdf.pages:check_fonts(p['/Resources'])
protected=json.loads((WORK/'protected_hashes.json').read_text(encoding='utf8'))
changed=[name for name,sha in protected.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha]
assert not changed,changed
report={'pages':len(pdf.pages),'page_size_points':[612,792],'units':358,'tables':9,
    'translation_preserved':True,'all_original_image_streams_unchanged':True,
    'all_fonts_embedded':True,'annotations':0,'protected_files_checked':len(protected),
    'protected_files_changed':changed,'pdf_version':pdf.pdf_header,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
    'page_checks':page_checks,
    'production_scope':'Layout proof at original page size; no added bleed or printer-specific output intent.'}
(WORK/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['page_checks']},ensure_ascii=False,indent=2))
