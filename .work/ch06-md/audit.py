from common import read,write,HERE
from collections import Counter
import re,sys
def nums(text):
    text=re.sub(r'<[^>]*>','',text).replace('−','-')
    text=text.replace('¾','3/4').replace('½','1/2').replace('¼','1/4')
    text=re.sub(r'(?<=\d)\s+(?=%)','',text)
    text=re.sub(r'(?<=\d)[ ,\u00a0](?=\d{3}(?:\D|$))','',text)
    text=re.sub(r'(?<=\d),(?=\d)', '.',text)
    dice=[]
    def take(m):dice.append(re.sub(r'\s+','',m[0]));return ' DICE '
    text=re.sub(r'\d+d\d+(?:\s*[+\-]\s*\d+)?!?',take,text)
    text=re.sub(r'(?<=\d)([’”\'\"]?)\s*[-–—]\s*(?=\d)',r'\1~',text)
    return Counter(dice+re.findall(r'[+\-]?\d+(?:\.\d+)?(?:%|\+)?',text))
def main():
    vals=read('pure_translations.json');diff=[]
    for u in read('source_units.json'):
        a,b=nums(u['source_markup']),nums(vals[u['id']])
        if a!=b:diff.append({'id':u['id'],'missing':dict(a-b),'extra':dict(b-a),'english':u['source_markup'],'russian':vals[u['id']]})
    write('numeric_differences.json',diff)
    print('Numeric differences',len(diff))
    for e in diff:print(e['id'],'missing',e['missing'],'extra',e['extra'])
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
