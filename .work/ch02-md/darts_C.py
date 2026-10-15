from pathlib import Path
p=Path('.work/ch02-md/translated_C.md')
s=p.read_text(encoding='utf-8').replace('дротиками для метания','метательными стрелками').replace('дротиков для метания','метательных стрелок')
p.write_text(s,encoding='utf-8')
