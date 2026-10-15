import collections
import hashlib
import html
import json
import pathlib
import re
import sqlite3
import sys
from zipfile import ZipFile
from lxml import etree
from pypdf import PdfReader

sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
ROOT=WORK.parents[1]
FILE=ROOT/'ACKSII'/'Сборки для чтения'/'ACKSII Введение и глава 1 с пометками.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
baseline=json.loads((WORK/'input_hashes.json').read_text(encoding='utf8'))
changed=[rel for rel,sha in baseline.items() if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=sha]
assert not changed,changed
db=sqlite3.connect((ROOT/'ACKSII'/'База перевода'/'acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
units=[dict(r) for r in db.execute('SELECT * FROM bilingual WHERE pdf_page<=23')]
def plain(s):
    s=re.sub(r'<br\s*/?>',' ',s)
    s=re.sub(r'<[^>]+>','',s)
    s=html.unescape(s).replace('\\|','|').replace('\\*','*').replace('\\_','_')
    return re.sub(r'\*{1,3}','',s)
expected=collections.Counter(ch for u in units for ch in plain(u['russian']) if ch.isalnum())
annotations=json.loads((WORK/'annotations.json').read_text(encoding='utf8'))
with ZipFile(FILE) as z:
    root=etree.fromstring(z.read('word/document.xml'))
    body=root.find('w:body',NS)
    captured=[];begun=False
    for p in body.xpath('.//w:p',namespaces=NS):
        bookmarks=p.xpath('.//w:bookmarkStart[starts-with(@w:name,"u_")]',namespaces=NS)
        begun=begun or bool(bookmarks)
        if not begun or p.xpath('./w:pPr/w:pStyle[@w:val="Source"]',namespaces=NS):continue
        for run in p.xpath('./w:r',namespaces=NS):
            text=''.join(run.xpath('.//w:t/text()',namespaces=NS))
            if re.fullmatch(r'\*\d+',text):continue
            captured.append(text)
    actual=collections.Counter(ch for ch in ''.join(captured) if ch.isalnum())
    missing=dict(expected-actual);added=dict(actual-expected)
    assert not missing and not added,{'missing':missing,'added':added}
    names=root.xpath('//w:bookmarkStart[starts-with(@w:name,"u_")]/@w:name',namespaces=NS)
    expected_names={'u_'+u['id'].replace('.','_') for u in units}
    assert len(names)==1689 and set(names)==expected_names
    comments=etree.fromstring(z.read('word/comments.xml'))
    ids=comments.xpath('//w:comment/@w:id',namespaces=NS)
    for tag in ('commentRangeStart','commentRangeEnd','commentReference'):
        assert collections.Counter(ids)==collections.Counter(root.xpath('//w:'+tag+'/@w:id',namespaces=NS))
    assert len(ids)==37
    actual_comments={}
    for c in comments:
        text=''.join(c.xpath('.//w:t/text()',namespaces=NS))
        number=int(re.match(r'^\*(\d+)\s',text).group(1))
        assert number not in actual_comments
        actual_comments[number]=text
    for a in annotations:
        text=actual_comments[a['number']]
        assert text.startswith('*'+str(a['number'])+' ')
        assert a['text'] in text
    assert b'relationships/comments' in z.read('word/_rels/document.xml.rels')
    assert b'/word/comments.xml' in z.read('[Content_Types].xml')
    # The title rule was removed; all presentation changes remain local.
    styles=etree.fromstring(z.read('word/styles.xml'))
    assert not styles.xpath('//w:style[@w:styleId="Title"]//w:pBdr',namespaces=NS)
    assert len(body.xpath('./w:tbl',namespaces=NS))==15
    settings=etree.fromstring(z.read('word/settings.xml'))
    # Word can omit the default on values when it saves the document.
    # Reject an explicit off value; actual visibility is also checked below
    # against the PDF exported by Word with all margin comments.
    assert not settings.xpath('//w:revisionView[@w:comments="0" or @w:comments="false" or @w:comments="off"]',namespaces=NS)
word=json.loads((WORK/'native_render'/'word_render.json').read_text(encoding='utf-8-sig'))
assert word['comment_count']==37
body_pdf=PdfReader(WORK/'native_render'/'body.pdf')
markup_pdf=PdfReader(WORK/'native_render'/'with_comments.pdf')
assert len(body_pdf.pages)==len(markup_pdf.pages)==word['pages']
markup_text='\n'.join(page.extract_text() for page in markup_pdf.pages)
for a in annotations:
    assert ('*'+str(a['number'])+' ') in markup_text or ('*'+str(a['number'])+'\n') in markup_text,a['number']
result={'protected_files_checked':len(baseline),'protected_files_changed':changed,
        'translation_units':1689,'table_count':15,'comments':37,'pages':word['pages'],
        'translation_letters_and_numbers_preserved':True,'all_units_bookmarked':True,
        'comment_anchors_valid':True,'all_comments_present_in_margin_pdf':True,
        'sha256':hashlib.sha256(FILE.read_bytes()).hexdigest()}
(WORK/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
db.close()
print(json.dumps(result,ensure_ascii=False,indent=2))
