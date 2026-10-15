"""Read-only comparison of the English class lists in chapters 2 and 3."""
from auto_units import HERE, ROOT
import json
import re
import sqlite3

def lists(db,chapter):
    result={}
    rows=list(db.execute('SELECT id,source_markup FROM units WHERE chapter_id=? ORDER BY pdf_page,block_order,row_index,column_index,id',(chapter,)))
    for index,(id,en) in enumerate(rows):
        m=re.match(r'^\*\*(.+?) Proficiency List:\*\* (.*)',en,re.S)
        if m:
            body=m[2]
            next_index=index+1
            while body.rstrip().endswith(',') and next_index<len(rows):
                body+=' '+rows[next_index][1]
                next_index+=1
            result[m[1]]=(id,[re.sub(r'\s+',' ',s).strip() for s in re.split(r', (?![^()]*\))',body)])
    return result

def main():
    db=sqlite3.connect((ROOT/'ACKSII/База перевода/acksii_translation.sqlite').as_uri()+'?mode=ro',uri=True)
    a,b=lists(db,'02'),lists(db,'03')
    diffs=[]
    for cls,(id,items) in b.items():
        if cls not in a:continue
        before=set(a[cls][1]);after=set(items)
        if before!=after:diffs.append({'class':cls,'chapter_2_id':a[cls][0],'chapter_3_id':id,'only_chapter_2':sorted(before-after),'only_chapter_3':sorted(after-before)})
    (HERE/'class_list_differences.json').write_text(json.dumps(diffs,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(diffs,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
