"""Combine chapter terms with prior terms, retaining phrase precedence."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
rules=[];seen=set()
for path in (HERE/'chapter_terms.tsv',HERE.parent/'ch11-md/term_rules.tsv'):
    for line in path.read_text('utf-8').splitlines():
        if not line:continue
        pattern,en,ru=line.split('\t')
        if pattern not in seen:rules.append((pattern,en,ru));seen.add(pattern)
(HERE/'term_rules.tsv').write_text(''.join('\t'.join(r)+'\n' for r in rules),'utf-8')
(HERE/'term_map.json').write_text(json.dumps([{'russian_pattern':p,'english':e,'working_russian':r} for p,e,r in rules],ensure_ascii=False,indent=2)+'\n','utf-8')
p=HERE/'translations.tsv'
s=p.read_text('utf-8').replace('**«Разграбление Доменов»**','**«Разграбление** **Доменов»**')
s=s.replace('восстанавливается 50% урона','устраняется 50% урона')
p.write_text(s,'utf-8')
p=HERE/'cell_terms.tsv'
s=p.read_text('utf-8').replace('[особого холодом] урона','[особого урона холодом]').replace('[особого электричеством] урона','[особого урона электричеством]')
p.write_text(s,'utf-8')
