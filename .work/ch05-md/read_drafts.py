"""Read contributor DOCX references; retain prose stored inside Word tables."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re
from auto_units import HERE,ROOT
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def main():
    for path in (ROOT/'ACKSII/ACKSII Revised Rulebook').glob('CHAPTER 5*.docx'):
        with ZipFile(path) as z:doc=ET.fromstring(z.read('word/document.xml'))
        parts=[]
        for node in doc.find(W+'body'):
            if node.tag==W+'p':
                paras=[node]
            elif node.tag==W+'tbl':
                paras=[p for p in node.iter(W+'p') if len(''.join(t.text or '' for t in p.iter(W+'t')))>100 and re.search('[А-Яа-яЁё]',''.join(t.text or '' for t in p.iter(W+'t')))]
            else:continue
            for p in paras:
                text=''.join(t.text or '' for t in p.iter(W+'t'))
                if text.strip():parts.append(text)
        (HERE/(path.stem+'.txt')).write_text('\n\n'.join(parts),'utf-8')
        print(path.name,len(parts))
if __name__=='__main__':main()
