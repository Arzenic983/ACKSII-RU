"""Context-checked glossary corrections before Markdown annotations; no DB writes."""
import json,re
from auto_units import HERE,records,write_records
def main():
    source={u['id']:u['source_plain'] for u in json.loads((HERE/'source_units.json').read_text('utf-8'))}
    values=records(HERE/'automatic.md');changed=[]
    for id,text in values.items():
        before=text;en=source[id]
        def outside(fn,s):
            return ''.join(p if i%2 else fn(p) for i,p in enumerate(re.split(r'(\[[^\[\]\n]*\])',s)))
        def clean(p):
            p=re.sub(r'хит[- ]?дайс(?:ов|ы|а)?','Кости Здоровья',p,flags=re.I)
            p=re.sub(r'хит[- ]?пойнт(?:ов|ы|а)?','ОЗ',p,flags=re.I)
            p=re.sub(r'\bхп\b','ОЗ',p,flags=re.I)

            for a,b in {'завладевшего':'одержимого','завладевшему':'одержимому','завладевшем':'одержимом','завладевшим':'одержимым','завладевшее':'одержимое','завладевшей':'одержимой'}.items():p=re.sub(r'\b'+a+r'\b',b,p,flags=re.I)
            if re.search(r'\bdeafened\b',en,re.I) and not re.search(r'\bstunn',en,re.I):
                for a,b in {'оглушенное':'глухое','оглушенному':'глухому','оглушенного':'глухого','оглушенным':'глухим','оглушено':'оглохло','оглушается':'глохнет'}.items():p=re.sub(r'\b'+a+r'\b',b,p,flags=re.I)
            if re.search(r'\bfrightened\b',en,re.I):p=re.sub(r'(?:напуганн|испуганн)', 'устрашённ',p,flags=re.I)
            if re.search(r'\bsanctums?\b',en,re.I):
                for a,b in {'святилища':'Санктума','святилище':'Санктуме','святилищ':'Санктумов','убежища':'Санктума','убежище':'Санктуме','убежищ':'Санктумов'}.items():p=re.sub(r'\b'+a+r'\b',b,p,flags=re.I)
            if re.search(r'\bNaturalism\b',en):p=re.sub('Натурализм[а-яё]*','Природоведение [Naturalism]',p,flags=re.I)
            if re.search(r'\bMapping\b',en):p=re.sub('Картографировани[а-яё]*','Картография [Mapping]',p,flags=re.I)
            p=re.sub(r'\bAС\b','КБ [AC]',p)
            p=p.replace('услугу или услугу','одолжение или услугу').replace('или или','или').replace('спас брос','спасброс')
            p=p.replace('Ослеплённый (Ослепленный)','Ослеплённый').replace('Slumbering (Дремлющий) существо','Дремлющее [Slumbering] существо').replace('Mute (Немой)','Немой [Mute]')
            return p
        text=outside(clean,text)
        # These are explicit glossary labels, so their meaning is unambiguous.
        for a,b in {
          'Скрытностью [Sneaking]':'Подкрадыванием [Sneaking]', 'Скрытность [Sneaking]':'Подкрадывание [Sneaking]',
          'Обездвиженным [restrained]':'Скованным [restrained]', 'Увязшим [stuck]':'Застрявшим [stuck]',
          'Захваченным в борьбе [wrestled]':'Скрученным [wrestled]',
          'Истощён [enervated]':'Обессилен [enervated]',
          'Укрощения [rebuked]':'Изгнания нежити [rebuked]', 'Укротил [rebuked]':'Изгнал [rebuked]',
          'Подчинил [dominated]':'Задоминировал [dominated]',
          'Невосприимчивым [immune]':'Неуязвимым [immune]', 'Невосприимчивых [immune]':'Неуязвимых [immune]',
          'Прислушивание [Listening]':'Подслушивание [Listening]',
        }.items():text=text.replace(a,b)
        if text!=before:changed.append(id)
        values[id]=text
    write_records(HERE/'automatic.md',values)
    (HERE/'glossary_corrections.json').write_text(json.dumps(changed,ensure_ascii=False,indent=2),'utf-8')
    print('Glossary and wording corrections',len(changed))
if __name__=='__main__':main()
