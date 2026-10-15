PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
  id TEXT PRIMARY KEY, path TEXT NOT NULL, kind TEXT NOT NULL,
  sha256 TEXT NOT NULL, snapshot TEXT, note TEXT
);
CREATE TABLE chapters (
  id TEXT PRIMARY KEY, title_en TEXT NOT NULL, title_ru TEXT NOT NULL,
  first_pdf_page INTEGER NOT NULL, last_pdf_page INTEGER NOT NULL,
  review_state TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE pages (
  pdf_page INTEGER PRIMARY KEY, printed_page INTEGER,
  chapter_id TEXT NOT NULL REFERENCES chapters(id),
  anchor TEXT NOT NULL UNIQUE, source_markup TEXT NOT NULL
);
CREATE TABLE source_tables (
  id TEXT PRIMARY KEY, pdf_page INTEGER NOT NULL REFERENCES pages(pdf_page),
  chapter_id TEXT NOT NULL REFERENCES chapters(id), block_order INTEGER NOT NULL,
  row_count INTEGER NOT NULL, column_count INTEGER NOT NULL, source_markup TEXT NOT NULL
);
CREATE TABLE units (
  id TEXT PRIMARY KEY, chapter_id TEXT NOT NULL REFERENCES chapters(id),
  pdf_page INTEGER NOT NULL REFERENCES pages(pdf_page), block_order INTEGER NOT NULL,
  kind TEXT NOT NULL, source_markup TEXT NOT NULL, source_plain TEXT NOT NULL,
  source_sha256 TEXT NOT NULL, invariant INTEGER NOT NULL CHECK(invariant IN (0,1)),
  table_id TEXT REFERENCES source_tables(id), row_index INTEGER, column_index INTEGER,
  rowspan INTEGER, colspan INTEGER, heading_level INTEGER, damage_icons_json TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX units_location ON units(chapter_id, pdf_page, block_order, row_index, column_index);
CREATE TABLE draft_fragments (
  id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id),
  locator TEXT NOT NULL, kind TEXT NOT NULL, raw_text TEXT NOT NULL, metadata_json TEXT NOT NULL,
  UNIQUE(source_id, locator)
);
CREATE TABLE unit_drafts (
  unit_id TEXT NOT NULL REFERENCES units(id), draft_id INTEGER NOT NULL REFERENCES draft_fragments(id),
  relation TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', PRIMARY KEY(unit_id, draft_id)
);
CREATE TABLE glossary (
  id INTEGER PRIMARY KEY, term_en TEXT NOT NULL, term_ru TEXT NOT NULL,
  abbreviation_ru TEXT, category TEXT NOT NULL, status TEXT NOT NULL,
  raw_entry TEXT NOT NULL, variants_json TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(id), source_locator TEXT NOT NULL
);
CREATE INDEX glossary_english ON glossary(term_en COLLATE NOCASE);
CREATE TABLE glossary_aliases (
  term_id INTEGER NOT NULL REFERENCES glossary(id), alias TEXT NOT NULL,
  PRIMARY KEY(term_id, alias)
);
CREATE TABLE working_labels (
  term_en TEXT PRIMARY KEY, term_ru TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'working', note TEXT NOT NULL
);
CREATE TABLE unit_terms (
  unit_id TEXT NOT NULL REFERENCES units(id), term_id INTEGER NOT NULL REFERENCES glossary(id),
  match_status TEXT NOT NULL DEFAULT 'candidate',
  PRIMARY KEY(unit_id, term_id)
);
CREATE TABLE translations (
  unit_id TEXT PRIMARY KEY REFERENCES units(id), text_ru TEXT NOT NULL CHECK(length(trim(text_ru))>0),
  status TEXT NOT NULL, origin TEXT NOT NULL, reviewer TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK(revision>0), note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE TABLE translation_revisions (
  unit_id TEXT NOT NULL REFERENCES units(id), revision INTEGER NOT NULL,
  text_ru TEXT NOT NULL, status TEXT NOT NULL, origin TEXT NOT NULL, reviewer TEXT NOT NULL,
  note TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(unit_id, revision)
);
CREATE TABLE issues (
  id INTEGER PRIMARY KEY, unit_id TEXT REFERENCES units(id), category TEXT NOT NULL,
  state TEXT NOT NULL, detail TEXT NOT NULL, resolution TEXT NOT NULL
);
CREATE VIRTUAL TABLE unit_search USING fts5(unit_id UNINDEXED, english, russian, tokenize='unicode61');
CREATE TRIGGER translations_insert AFTER INSERT ON translations BEGIN
  UPDATE unit_search SET russian=new.text_ru WHERE rowid=(SELECT rowid FROM units WHERE id=new.unit_id);
END;
CREATE TRIGGER translations_update AFTER UPDATE OF text_ru ON translations BEGIN
  UPDATE unit_search SET russian=new.text_ru WHERE rowid=(SELECT rowid FROM units WHERE id=new.unit_id);
END;
CREATE VIEW chapter_progress AS
  SELECT c.id,c.title_en,c.title_ru,c.first_pdf_page,c.last_pdf_page,c.review_state,
    count(u.id) AS source_units,count(t.unit_id) AS translated_units,
    sum(CASE WHEN u.id IS NOT NULL AND t.unit_id IS NULL THEN 1 ELSE 0 END) AS pending_units
  FROM chapters c LEFT JOIN units u ON u.chapter_id=c.id
  LEFT JOIN translations t ON t.unit_id=u.id GROUP BY c.id;
CREATE VIEW bilingual AS
  SELECT u.id,u.chapter_id,u.pdf_page,p.printed_page,u.block_order,u.kind,u.table_id,
    u.row_index,u.column_index,u.rowspan,u.colspan,u.heading_level,u.source_markup AS english,
    t.text_ru AS russian,coalesce(t.status,'pending') AS status,t.origin,t.reviewer,
    coalesce(t.revision,0) AS revision,t.note,u.source_sha256,u.damage_icons_json
  FROM units u JOIN pages p ON p.pdf_page=u.pdf_page
  LEFT JOIN translations t ON t.unit_id=u.id;
