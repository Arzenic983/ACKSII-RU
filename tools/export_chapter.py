"""Export one chapter from the translation database as an editable CSV or JSONL.

Uses the standard library. The database is opened read-only; existing output
files are never overwritten. Run from any directory.
"""
import argparse
import csv
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / 'ACKSII' / 'База перевода' / 'acksii_translation.sqlite'
FIELDS = ['id', 'chapter_id', 'pdf_page', 'printed_page', 'kind', 'english',
          'russian', 'status', 'origin', 'revision', 'note', 'source_sha256',
          'pdf_reference']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapter', required=True, help='front_matter, 01, 02, 03, ..., A, ...')
    parser.add_argument('--out', required=True, type=Path, help='New .csv or .jsonl file')
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    if args.out.suffix.lower() not in ('.csv', '.jsonl'):
        parser.error('--out must end with .csv or .jsonl')
    with sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        if not db.execute('SELECT 1 FROM chapters WHERE id=?', (args.chapter,)).fetchone():
            parser.error('Unknown chapter: ' + args.chapter)
        rows = db.execute('''SELECT * FROM bilingual WHERE chapter_id=?
            ORDER BY pdf_page,block_order,row_index,column_index,id''', (args.chapter,)).fetchall()
    records = []
    for row in rows:
        item = {field: row[field] for field in FIELDS if field != 'pdf_reference'}
        if item['status'] == 'pending':
            item['status'] = 'draft'
        item['pdf_reference'] = 'ACKSII/Source/ACKSII Revised Rulebook.pdf#page=' + str(row['pdf_page'])
        records.append(item)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.suffix.lower() == '.csv':
        with args.out.open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter=';')
            writer.writeheader()
            writer.writerows(records)
    else:
        with args.out.open('x', encoding='utf-8', newline='\n') as stream:
            for item in records:
                stream.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f'Exported chapter {args.chapter}: {len(records)} units -> {args.out}')


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (OSError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
