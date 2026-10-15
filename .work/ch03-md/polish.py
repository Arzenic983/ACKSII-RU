"""Recorded corrections found during the author's second reading."""
from auto_units import HERE

REPLACEMENTS={
 'translated_110_111.md':{
  'Прорыв [Overrun], Разрушение оружия [Sunder]':'Пробиться [Overrun], Разделение [Sunder]',
 },
 'translated_114_115.md':{
  'Встретив такую опасность, Арбитр [Judge] тайно выполняет за него бросок Геодезии [Land Surveying].':'Когда персонаж встречает такую опасность, Арбитр [Judge] тайно выполняет за него бросок Геодезии [Land Surveying].',
 },
}

def main():
    for name,changes in REPLACEMENTS.items():
        path=HERE/name
        text=path.read_text('utf-8')
        for old,new in changes.items():
            assert old in text or new in text,(name,old)
            text=text.replace(old,new)
        path.write_text(text,'utf-8')

if __name__=='__main__':main()
