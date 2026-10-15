"""Update current text references and the chapter-3 term appendix."""
from auto_units import HERE, ROOT
import json
import re

def main():
    base=ROOT/'ACKSII/База перевода'
    catalog=base/'bilingual_terms.md'
    text=catalog.read_text('utf-8')
    marker='## Дополнение: глава 3'
    text=text.split(marker,1)[0].rstrip()
    text=text.replace('Рабочая карта для двуязычного оформления PDF-страниц 1–101.','Основная карта для двуязычного оформления PDF-страниц 1–101; дополнение главы 3 (PDF 102–123) приведено ниже.')
    working=json.loads((HERE/'working_terms.json').read_text('utf-8'))
    appendix='\n\n'+marker+' «Навыки», PDF 102–123\n\nОбновлено 16 октября 2026 года. Названия навыков сохранены по глоссарию и основной карте выше; английские подписи повторяются при каждом употреблении. Следующие формы остаются рабочими, включая встречавшиеся ранее названия заклинаний. Утверждение человеком не присваивалось.\n\n| Английское имя | Рабочая русская форма |\n| --- | --- |\n'
    appendix+='\n'.join(f'| {en} | {ru} |' for en,ru in working['terms'].items())+'\n'
    catalog.write_text(text+appendix,'utf-8')
    note_path=ROOT/'ACKSII/Перевод Markdown/Примечания редактора.md'
    old=note_path.read_text('utf-8')
    old=re.split(r'\n<!-- unit: rr\.p010[2-9]\.',old,maxsplit=1)[0].rstrip()
    notes=json.loads((HERE/'notes.json').read_text('utf-8'))
    units=json.loads((HERE/'source_units.json').read_text('utf-8'))
    addition='\n\n'+'\n\n'.join(f'<!-- unit: {u["id"]} -->\n'+'\n\n'.join(notes[u['id']]) for u in units if u['id'] in notes)+'\n'
    note_path.write_text(old+addition,'utf-8')

if __name__=='__main__':main()
