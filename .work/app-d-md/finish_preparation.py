"""Record completed review and prepare the guarded one-time D integrator."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):(HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
def main():
    assert not (HERE/'semantic_review.json').exists() and not (HERE/'integration.json').exists(),'Historical one-time review record already exists'
    source=[json.loads(s) for s in (ROOT/'contributions/D/source.jsonl').read_text('utf-8').splitlines()]
    assert len(source)==163
    save('semantic_review.json',{
        'date':'2026-10-17','chapter':'D','pdf_pages':[532,537],'units':163,
        'complete_semantic_review_by_Codex':True,'human_approval':False,'reviewer':'Codex',
        'method':'Все 163 единицы сопоставлены с EN checked; вручную прочитаны 134 различных английских текста с русскими парами. Дополнительно просмотрены изображения исходных листов PDF 533–537. Проверены назначение полей, суммы и знаки формул, порядок атрибутов, категории спасбросков, скорость, нагрузка, единицы и пустые поля. Один Codex, без второго независимого редактора.',
        'distinct_english_texts':len({u['english'] for u in source}),
        'russian_units_sha256':sha(HERE/'pure.json'),
        'source_package_sha256':sha(ROOT/'contributions/D/source.jsonl'),
        'primary_source':'ACKSII/Source/ACKSII Revised Rulebook (EN checked).md',
        'all_checked_pages_equal_database':True,
        'crosschecks':[
            'rr.p0125: PP/EP/GP/SP/CP — платиновые, электрумовые, золотые, серебряные и медные монеты',
            'rr.p0344.b016: доход Домена и расчёт на семью независимого Владения',
            'rr.p0347.b004–rr.p0347.b007: Lord — сеньор; duties — обязанности',
            'glossary.json: Hireling — Спутник, Henchman — Приспешник; словарные категории спасбросков',
            'PDF 533, нижний колонтитул: 19th July 2024 вместо 18th July 2024 в дампе'
        ],
        'source_display_exceptions':'source_display_fixes.json',
        'editorial_notes':12,
        'limitations':[
            'Переведена структурированная текстовая версия бланков, а не их графическая геометрия или заполняемый PDF.',
            'Неоднозначная подпись Revenue per Family minus Expenses сохранена с примечанием.',
            'Новые рабочие термины и сокращения человеком не утверждены.'
        ]})
    glossary=json.loads((ROOT/'ACKSII/База перевода/glossary.json').read_text('utf-8'))
    wanted={'Attributes','Proficiencies','Hit Die','Hit Points','Armor Class','Stone','Domain','Realm','Hireling','Henchman','Cleave','Mortal Wounds','Listening','Paralysis','Death','Blast','Implements','Spells','Strength','Intelligence','Dexterity','Will','Constitution','Charisma'}
    matched=[{'english':u['term_en'],'russian':u['term_ru'],'category':u['category'],'status':u['status']} for u in glossary if u['term_en'] in wanted]
    save('glossary_review.json',{
        'date':'2026-10-17',
        'sources':{p:sha(ROOT/p) for p in ['ACKSII/Глоссарий.md','ACKSII/База перевода/glossary.json','ACKSII/База перевода/bilingual_terms.md']},
        'matched_project_entries':matched,
        'working_terms':{'Healing Rate':'Темп исцеления','Follower':'Последователь','Stronghold':'крепость (общее название)','Pouch':'Поясная сумка','ST':'СТ','SPD':'СКР','ENC':'НАГ'},
        'context_decisions':{'Morale':'мораль Домена; боевой дух в карточке существа','Domain / Realm':'Домен / Владение','PP / EP':'ПМ / ЭМ','#AT':'Число атак'},
        'glossary_database_unchanged':True,'human_approval':False
    })
    save('visual_review.json',{
        'date':'2026-10-17',
        'source_pages_inspected':[533,534,535,536,537],
        'source_detail_inspected':'PDF 533: увеличенный нижний колонтитул с датой 19th July 2024',
        'rendered_pages_inspected':[533,534,535,536,537],
        'rendered_tables_inspected':['rr.p0533.t01','rr.p0533.t02','rr.p0533.t03','rr.p0533.t04','rr.p0534.t01','rr.p0537.t01'],
        'metrics':'visual_metrics.json','viewport_width':1500,'content_width':1080,
        'result':'Все шесть таблиц прочитаны в рендеринге: 109 позиций, включая 17 пустых без ID, без горизонтального переполнения и обрезания. Подписи русских полей и отдельные английские подписи видны; формулы и единицы читаются.',
        'limitations':'Это проверка текстового Markdown и его HTML-рендеринга. Графическая PDF-вёрстка листов, повторяющиеся пустые карточки и заполняемые PDF-поля не создавались.'
    })
    s=(ROOT/'.work/app-c-md/integrate.py').read_text('utf-8')
    for a,b in [('appendix-C','appendix-D'),('contributions/C','contributions/D'),('827','163'),('before_appendixC','before_appendixD'),("chapter_id='C'","chapter_id='D'"),("id='C'","id='D'"),("'--chapter','C'","'--chapter','D'"),('30378','30541'),('appC','appD'),('C_review.csv','D_review.csv'),("'chapter':'C'","'chapter':'D'")]:
        assert a in s,a
        s=s.replace(a,b)
    s=s.replace("chapter_id!='C'", "chapter_id!='D'")
    (HERE/'integrate.py').write_text(s,'utf-8')
    print('Review records and guarded integrator prepared. No database changes.')
if __name__=='__main__':main()
