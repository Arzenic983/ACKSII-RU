"""Extract a read-only textual reference from the existing contributor DOCX."""
from pathlib import Path
from zipfile import ZipFile
import json
import re
import xml.etree.ElementTree as ET
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def main():
    path=ROOT/'ACKSII/ACKSII Revised Rulebook/Chapter 4_ Equipment (Justluck, Faylow).docx'
    with ZipFile(path) as z:doc=ET.fromstring(z.read('word/document.xml'))
    parts=[]
    for p in doc.iter(W+'p'):
        text=''.join(e.text or '' for e in p.iter(W+'t'))
        if text.strip():parts.append(text)
    (HERE/'contributor_draft.txt').write_text('\n\n'.join(parts),'utf-8')
    print('paragraphs',len(parts),'Cyrillic letters',len(re.findall('[А-Яа-яЁё]',''.join(parts))))
    print('\n\n'.join(parts[:35]))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
