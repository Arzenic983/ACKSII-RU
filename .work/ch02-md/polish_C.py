from pathlib import Path
import re
p=Path('.work/ch02-md/translated_C.md')
s=p.read_text(encoding='utf-8')
s=re.sub(r'\bст(?=[);<\n])', 'ст.', s)
s=s.replace('вызов демонического отродья','вызов исчадия')
s=s.replace('2 фунта бенедикта','2 фунта кардобенедикта')
s=s.replace('человеку или полулюдю','человеку или полулюдям')
s=s.replace('КЗд','__HIT_DICE_C__').replace('КЗ','КБ').replace('__HIT_DICE_C__','КЗ')
p.write_text(s, encoding='utf-8')
