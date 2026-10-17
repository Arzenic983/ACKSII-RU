"""Explicit corrections recorded during second source/terminology review."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
def main():
    p=HERE/'translations.tsv';s=p.read_text('utf-8')
    changes={
        'галереи, подъёмники, буравы':'передвижные галереи, подъёмники, буры',
        'Баала Ужасного':'Баала Грозного',
        'побережья Келдореи':'побережья Келдории',
        'Каждый погибший, выбывший из строя или пленный':'Каждый воин, учтённый в потерях, или пленный',
        'Происки убийства, кутежа':'Происки заказного убийства, кутежа',
        'во вражескую армии до поимки':'во вражеской армии до поимки',
        'ни адвокаты, ни защитники ему недоступны':'ему недоступны ни адвокаты, ни заступничество',
    }
    applied=[]
    for old,new in changes.items():
        assert old in s or new in s,old
        if old in s:s=s.replace(old,new)
        applied.append({'before':old,'after':new})
    p.write_text(s,'utf-8')
    (HERE/'corrections.json').write_text(json.dumps(applied,ensure_ascii=False,indent=2)+'\n','utf-8')
if __name__=='__main__':main()
