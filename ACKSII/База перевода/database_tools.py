"""Portable SQLite translation store: search, export, atomic chapter import.

Uses only Python's standard library. Run --help for commands.
"""
import argparse
import csv
import datetime
import json
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_DB = HERE / 'acksii_translation.sqlite'
CSV_FIELDS = ['id', 'chapter_id', 'pdf_page', 'printed_page', 'kind', 'english',
              'russian', 'status', 'origin', 'revision', 'note', 'source_sha256', 'pdf_reference']

def connect(path):
    if not pathlib.Path(path).is_file():
        raise ValueError('Database does not exist: ' + str(path))
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

def export(db, folder):
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'units.jsonl').open('w', encoding='utf-8', newline='\n') as out:
        for row in db.execute('SELECT * FROM bilingual ORDER BY pdf_page,block_order,row_index,column_index,id'):
            out.write(json.dumps(dict(row), ensure_ascii=False) + '\n')
    glossary = []
    for row in db.execute('SELECT * FROM glossary ORDER BY id'):
        item = dict(row)
        item['variants'] = json.loads(item.pop('variants_json'))
        item['aliases'] = [x[0] for x in db.execute('SELECT alias FROM glossary_aliases WHERE term_id=? ORDER BY alias', (row['id'],))]
        glossary.append(item)
    (folder / 'glossary.json').write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding='utf-8')
    progress = [dict(row) for row in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page')]
    (folder / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')
    for chapter in db.execute('SELECT * FROM chapter_progress WHERE translated_units>0 ORDER BY first_pdf_page'):
        path = folder / (chapter['id'] + '_review.csv')
        with path.open('w', encoding='utf-8-sig', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=CSV_FIELDS, delimiter=';')
            writer.writeheader()
            for row in db.execute('SELECT * FROM bilingual WHERE chapter_id=? ORDER BY pdf_page,block_order,row_index,column_index,id', (chapter['id'],)):
                item = {key: row[key] for key in CSV_FIELDS if key != 'pdf_reference'}
                item['pdf_reference'] = 'ACKSII/Source/ACKSII Revised Rulebook.pdf#page=' + str(row['pdf_page'])
                writer.writerow(item)

def read_import(path):
    path = pathlib.Path(path)
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream, delimiter=';'))
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]

def import_chapter(db, path, chapter_id, reviewer):
    with db:
        db.execute('BEGIN IMMEDIATE')
        return _import_chapter_locked(db, path, chapter_id, reviewer)

def _import_chapter_locked(db, path, chapter_id, reviewer):
    records = read_import(path)
    seen, changes = set(), []
    # All validation precedes all writes; one bad row rejects the entire import.
    for item in records:
        unit_id = item['id']
        if unit_id in seen:
            raise ValueError('Duplicate unit: ' + unit_id)
        seen.add(unit_id)
        row = db.execute('SELECT * FROM bilingual WHERE id=?', (unit_id,)).fetchone()
        if row is None or row['chapter_id'] != chapter_id:
            raise ValueError('Unknown unit or wrong chapter: ' + unit_id)
        if item.get('chapter_id', chapter_id) != chapter_id:
            raise ValueError('Chapter in file does not match: ' + unit_id)
        if item.get('source_sha256') != row['source_sha256']:
            raise ValueError('English source hash conflict: ' + unit_id)
        if 'english' in item and item['english'] != row['english']:
            raise ValueError('English text is immutable in this import: ' + unit_id)
        if int(item.get('revision', -1)) != row['revision']:
            raise ValueError('Revision conflict: ' + unit_id)
        text_ru = item.get('russian')
        if text_ru is None or not text_ru.strip():
            continue  # An empty draft never deletes an existing translation.
        status = item.get('status') or 'draft'
        if status not in ('draft', 'reviewed', 'user_approved'):
            raise ValueError('Unsupported translation status: ' + status)
        note = item.get('note') or ''
        if (text_ru, status, note) == (row['russian'], row['status'], row['note'] or ''):
            continue
        changes.append((row, text_ru, status, note))
    at = timestamp()
    with db:
        for row, text_ru, status, note in changes:
            revision = row['revision'] + 1
            origin = 'manual_edit' if row['revision'] else 'new_translation'
            args = (row['id'], text_ru, status, origin, reviewer, revision, note, at)
            db.execute('''INSERT INTO translations VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(unit_id) DO UPDATE SET text_ru=excluded.text_ru,status=excluded.status,
              origin=excluded.origin,reviewer=excluded.reviewer,revision=excluded.revision,
              note=excluded.note,updated_at=excluded.updated_at''', args)
            db.execute('INSERT INTO translation_revisions VALUES(?,?,?,?,?,?,?,?)',
                       (row['id'], revision, text_ru, status, origin, reviewer, note, at))
        if changes:
            db.execute("UPDATE chapters SET review_state='in_progress' WHERE id=?", (chapter_id,))
    return len(changes)

def verify(db):
    integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
    foreign_keys = list(db.execute('PRAGMA foreign_key_check'))
    history_errors = db.execute('''SELECT count(*) FROM translations t
      LEFT JOIN translation_revisions r ON r.unit_id=t.unit_id AND r.revision=t.revision
      WHERE r.unit_id IS NULL OR r.text_ru!=t.text_ru OR r.status!=t.status''').fetchone()[0]
    search_errors = db.execute('''SELECT count(*) FROM units u
      LEFT JOIN unit_search s ON s.rowid=u.rowid LEFT JOIN translations t ON t.unit_id=u.id
      WHERE s.unit_id IS NULL OR s.unit_id!=u.id OR s.english!=u.source_plain OR s.russian!=coalesce(t.text_ru,'')''').fetchone()[0]
    import hashlib
    hash_errors = sum(hashlib.sha256(row['source_markup'].encode()).hexdigest() != row['source_sha256']
                      for row in db.execute('SELECT source_markup,source_sha256 FROM units'))
    result = {'integrity': integrity, 'foreign_key_errors': len(foreign_keys),
              'history_errors': history_errors, 'search_errors': search_errors,
              'english_hash_errors': hash_errors,
              'units': db.execute('SELECT count(*) FROM units').fetchone()[0],
              'translations': db.execute('SELECT count(*) FROM translations').fetchone()[0]}
    if integrity != 'ok' or any(result[key] for key in ('foreign_key_errors','history_errors','search_errors','english_hash_errors')):
        raise ValueError('Validation failed: ' + json.dumps(result))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=pathlib.Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    sub.add_parser('progress')
    search = sub.add_parser('search')
    search.add_argument('query', help='SQLite FTS5 query; Russian and English supported')
    search.add_argument('--limit', type=int, default=20)
    exp = sub.add_parser('export')
    exp.add_argument('--out', type=pathlib.Path, default=HERE)
    imp = sub.add_parser('import-chapter')
    imp.add_argument('file', type=pathlib.Path)
    imp.add_argument('--chapter', required=True, help='front_matter, 01, 02, ...')
    imp.add_argument('--reviewer', required=True)
    args = parser.parse_args()
    with connect(args.db) as db:
        if args.command == 'verify':
            print(json.dumps(verify(db), ensure_ascii=False, indent=2))
        elif args.command == 'progress':
            for row in db.execute('SELECT * FROM chapter_progress ORDER BY first_pdf_page'):
                print(row['id'], row['title_ru'], str(row['translated_units'])+'/'+str(row['source_units']), row['review_state'])
        elif args.command == 'search':
            for row in db.execute('''SELECT b.* FROM unit_search s JOIN bilingual b ON b.id=s.unit_id
              WHERE unit_search MATCH ? ORDER BY rank LIMIT ?''', (args.query, args.limit)):
                print(json.dumps(dict(row), ensure_ascii=False))
        elif args.command == 'export':
            export(db, args.out)
            print('Exported to', args.out)
        elif args.command == 'import-chapter':
            print('Updated units:', import_chapter(db, args.file, args.chapter, args.reviewer))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError, KeyError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
