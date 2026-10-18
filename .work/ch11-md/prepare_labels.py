"""Combine explicitly reviewed chapter-11 term rules with existing display rules."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
    p=HERE/'translations.tsv';s=p.read_text('utf-8')
    changes={
        'которое продаётся отдельно':'которое доступно отдельно',
        'арбалестами':'арбалетами с воротом',
        ' ОО':' Опыта',
    }
    for old,new in changes.items():s=s.replace(old,new)
    def xp_points(m):
        n=int(m[1].replace(' ',''));last=n%100
        word='очко' if last%10==1 and last!=11 else 'очка' if last%10 in (2,3,4) and last not in (12,13,14) else 'очков'
        return m[1]+' '+word+' Опыта'
    s=re.sub(r'(\d(?:[\d ]*\d)?) Опыта',xp_points,s)
    p.write_text(s,'utf-8')
    extra=(HERE/'chapter_terms.tsv').read_text('utf-8')
    prior=(HERE.parent/'ch10-md/term_rules.tsv').read_text('utf-8')
    # Exclude rules that would incorrectly label generic battle uses as other
    # chapter mechanics (Hiding/Hideout, for example, is not cover in battle).
    prior='\n'.join(line for line in prior.splitlines() if not any(t in line for t in ('Hideout','(?-i:Наблюдени','\tbur\t')))
    (HERE/'term_rules.tsv').write_text(extra.rstrip()+'\n'+prior+'\n','utf-8')
    glossary=json.loads((ROOT/'ACKSII/База перевода/glossary.json').read_text('utf-8'))
    relevant=('Judge','Hit Dice','Hit Points','Fighter','Bladedancer','Paladin','Thief','Henchmen','Longbowman','Proficiencies','Mortal Wounds','permanent wound','Blessed/Inspired','Disordered','Incapacitated','Hungry','Charisma','Constitution','Stone','Domain','Realm','Military Strategy')
    chosen=[{'en':g['term_en'],'ru':g['term_ru'],'status':g['status']} for g in glossary if g['term_en'] in relevant]
    (HERE/'glossary_check.json').write_text(json.dumps(chosen,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(chosen,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
