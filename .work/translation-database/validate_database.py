"""Verify content, export round trips and safe revision imports on a COPY."""
import collections
import csv
import importlib.util
import json
import pathlib
import re
import sqlite3
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
ROOT=WORK.parents[1]
OUT=ROOT/'ACKSII'/'База перевода'
spec=importlib.util.spec_from_file_location('dbtools',OUT/'database_tools.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
result={}
with m.connect(OUT/'acksii_translation.sqlite') as db:
    result['database']=m.verify(db)
    rows={r['id']:dict(r) for r in db.execute('SELECT * FROM bilingual')}
    for row in rows.values():
        assert (row['russian'] is not None)==(row['pdf_page']<=23),row['id']
    result['scope_complete']=True
    result['later_chapters_untranslated']=True
    source={u['id']:u for u in json.loads((WORK/'all_units.json').read_text(encoding='utf8'))}
    assert set(rows)==set(source)
    assert all(rows[k]['english']==source[k]['source'] and rows[k]['source_sha256']==source[k]['source_sha256'] for k in rows)
    result['english_source_unchanged']=True
    occupied={}
    dims={r['id']:(r['row_count'],r['column_count']) for r in db.execute('SELECT * FROM source_tables')}
    for row in rows.values():
        if not row['table_id']:continue
        nr,nc=dims[row['table_id']]
        assert 0<=row['row_index']<nr and 0<=row['column_index']<nc
        assert row['row_index']+row['rowspan']<=nr and row['column_index']+row['colspan']<=nc
        for ri in range(row['row_index'],row['row_index']+row['rowspan']):
            for ci in range(row['column_index'],row['column_index']+row['colspan']):
                key=(row['table_id'],ri,ci);assert key not in occupied;occupied[key]=row['id']
    result['table_geometry_valid']=True
    exported=[json.loads(line) for line in (OUT/'units.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(exported)==len(rows) and {r['id']:r for r in exported}==rows
    result['jsonl_roundtrip']=True
    for cid in ('front_matter','01'):
        with (OUT/(cid+'_review.csv')).open(encoding='utf-8-sig',newline='') as stream:
            csv_rows=list(csv.DictReader(stream,delimiter=';'))
        expected=[r for r in rows.values() if r['chapter_id']==cid]
        assert len(csv_rows)==len(expected)
        for r in csv_rows:
            original=rows[r['id']]
            assert all(r[key]==str(original[key] if original[key] is not None else '') for key in m.CSV_FIELDS if key!='pdf_reference'),r['id']
    result['csv_roundtrip']=True
    numeric_errors=[]
    for row in rows.values():
        if row['kind']!='table_cell' or row['pdf_page']>23:continue
        en=source[row['id']]['plain']
        ru=row['russian'].replace('1 000','1,000')
        if collections.Counter(re.findall(r'\d+(?:[.,]\d+)*',en))!=collections.Counter(re.findall(r'\d+(?:[.,]\d+)*',ru)):
            numeric_errors.append(row['id'])
    assert not numeric_errors,numeric_errors
    result['all_translated_table_numbers_match']=True
    obsolete=re.compile(r'\b(?:судья|конституция|хиты|хитдайс|хитпойнт|чернокнижник|танцующ\w* с клинк\w*)\b',re.I)
    assert not any(obsolete.search(r['russian'] or '') for r in rows.values())
    result['obsolete_draft_terms_removed']=True
    assert db.execute("SELECT term_ru FROM glossary WHERE term_en='Naturalism'").fetchone()[0]=='Природоведение'
    assert db.execute("SELECT term_ru FROM glossary WHERE term_en='Loremastery'").fetchone()[0]=='Мифография'
    assert db.execute("SELECT term_ru FROM glossary WHERE term_en='extraordinary (damage)'").fetchone()[0]=='Особый'
    result['user_confirmed_terms_match']=True
    assert rows['rr.p0006.t01.r066.c01']['russian']=='Заклинания'
    assert rows['rr.p0006.t01.r050.c01']['russian']=='Приспешники'
    assert rows['rr.p0007.t01.r158.c01']['russian']=='Скизийцы'
    result['glossary_context_checked']=True
    # A disposable copy ensures importer tests do not touch the deliverable.
    with tempfile.TemporaryDirectory(prefix='acksii_db_check_') as temp:
        folder=pathlib.Path(temp);copy=folder/'copy.sqlite'
        destination=sqlite3.connect(copy);db.backup(destination);destination.close()
        with m.connect(copy) as test:
            before={r['id']:dict(r) for r in test.execute('SELECT * FROM bilingual')}
            sample=dict(before['rr.p0015.b003'])
            def attempt(record,chapter='01',must_fail=False):
                file=folder/'edit.jsonl';file.write_text(json.dumps(record,ensure_ascii=False)+'\n',encoding='utf8')
                try:n=m.import_chapter(test,file,chapter,'test')
                except ValueError:
                    assert must_fail
                    return
                assert not must_fail
                return n
            wrong=dict(sample);wrong['source_sha256']='wrong'
            attempt(wrong,must_fail=True)
            wrong=dict(sample);wrong['revision']=0
            attempt(wrong,must_fail=True)
            attempt(sample,chapter='02',must_fail=True)
            wrong=dict(sample);wrong['english']='CHANGED SOURCE'
            attempt(wrong,must_fail=True)
            wrong=dict(sample);wrong['russian']=''
            assert attempt(wrong)==0
            assert attempt(sample)==0
            edited=dict(sample);edited['russian']=sample['russian']+' Проверочный маркер.'
            assert attempt(edited)==1
            after={r['id']:dict(r) for r in test.execute('SELECT * FROM bilingual')}
            assert after[sample['id']]['revision']==2
            assert after[sample['id']]['russian']==edited['russian']
            assert test.execute('SELECT count(*) FROM translation_revisions WHERE unit_id=?',(sample['id'],)).fetchone()[0]==2
            assert all(before[k]==after[k] for k in before if k!=sample['id'])
            attempt(edited,must_fail=True)
            m.verify(test)
            # First translation in a pending chapter appends history and updates search.
            pending=dict(before['rr.p0024.b001']);pending['russian']='Проверочная запись';pending['status']='draft'
            assert attempt(pending,chapter='02')==1
            assert test.execute("SELECT revision FROM translations WHERE unit_id='rr.p0024.b001'").fetchone()[0]==1
            m.verify(test)
            # If any row fails, even a valid earlier edit is rolled back.
            edited=dict(after[sample['id']]);edited['russian']+=' Ещё маркер.'
            bad=dict(edited);bad['id']='missing'
            file=folder/'bad_batch.jsonl';file.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in (edited,bad))+'\n',encoding='utf8')
            try:m.import_chapter(test,file,'01','test')
            except ValueError:pass
            else:raise AssertionError('Invalid batch accepted')
            assert test.execute('SELECT revision FROM translations WHERE unit_id=?',(sample['id'],)).fetchone()[0]==2
        test.close()
        result['import_tests']=['source_hash_conflict_rejected','stale_revision_rejected','wrong_chapter_rejected','english_edit_rejected','empty_ru_does_not_delete','unchanged_import_no_op','revision_history_appended','other_units_untouched','fts_refreshed','pending_chapter_import','invalid_batch_atomic_rollback']
db.close()
(OUT/'workflow_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
