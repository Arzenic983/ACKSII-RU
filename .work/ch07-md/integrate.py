"""Integrator: SQLite backup, official atomic import, verify, selective export."""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'ACKSII/База перевода'
DB = BASE / 'acksii_translation.sqlite'


def digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()


def main():
    assert json.loads((HERE / 'semantic_review.json').read_text(encoding='utf-8'))['complete_semantic_review_by_Codex']
    rows = [json.loads(s) for s in (ROOT / 'contributions/07/translator.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 964 and all(u['status'] == 'reviewed' and u['revision'] == 0 for u in rows)
    backup = HERE / 'before_chapter07.sqlite.tmp'
    assert not backup.exists(), 'Inspect the previous import before repeating integration.'
    with sqlite3.connect(DB) as db, sqlite3.connect(backup) as saved:
        before = digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='07' ORDER BY id").fetchall())
        english = digest(db.execute('SELECT id,english,source_sha256,rowspan,colspan FROM bilingual ORDER BY id').fetchall())
        db.backup(saved)
    tool = str(BASE / 'database_tools.py')
    subprocess.run([sys.executable, tool, 'import-chapter', str(ROOT / 'contributions/07/translator.jsonl'), '--chapter', '07', '--reviewer', 'Codex'], check=True)
    subprocess.run([sys.executable, tool, 'verify'], check=True)
    with sqlite3.connect(DB) as db:
        assert db.execute("SELECT count(*) FROM bilingual WHERE chapter_id='07' AND status='reviewed' AND revision=1").fetchone()[0] == 964
        assert digest(db.execute("SELECT * FROM bilingual WHERE chapter_id!='07' ORDER BY id").fetchall()) == before
        assert digest(db.execute('SELECT id,english,source_sha256,rowspan,colspan FROM bilingual ORDER BY id').fetchall()) == english
        db.execute("UPDATE chapters SET review_state='reviewed_by_Codex' WHERE id='07'")
    export = ROOT / 'contributions/_export/ch07'
    subprocess.run([sys.executable, tool, 'export', '--out', str(export)], check=True)
    assert json.loads((export / 'glossary.json').read_text(encoding='utf-8')) == json.loads((BASE / 'glossary.json').read_text(encoding='utf-8'))
    for name in ('units.jsonl', 'progress.json', '07_review.csv'):
        shutil.copyfile(export / name, BASE / name)
    (HERE / 'integration.json').write_text(json.dumps({'chapter': '07', 'units': 964, 'package_revision': 0, 'database_revision': 1, 'other_chapters_unchanged': True, 'english_and_geometry_unchanged': True, 'backup': str(backup), 'verify': 'passed'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Integrated chapter 07; all other chapters and English source fields preserved.')


if __name__ == '__main__':
    main()
