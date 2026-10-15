"""Compress reproducible extraction caches, verifying them before any cleanup."""
import gzip
import hashlib
import json
import pathlib
import shutil
import sys

sys.stdout.reconfigure(encoding='utf8')
WORK=pathlib.Path(__file__).resolve().parent
geometry=WORK/'geometry.jsonl.gz'
number=0
with (WORK/'pages.jsonl').open(encoding='utf8') as source,gzip.open(geometry,'wt',encoding='utf8',compresslevel=4) as out:
    for line in source:
        rec=json.loads(line)
        out.write(json.dumps({k:v for k,v in rec.items() if k!='chars'},ensure_ascii=False)+'\n')
        number+=1
assert number==550
with gzip.open(geometry,'rt',encoding='utf8') as source:
    assert [json.loads(line)['page'] for line in source]==list(range(1,551))
print('Geometry cache: 550 pages verified',flush=True)
raw=WORK/'pages-corrected.jsonl'
packed=WORK/'pages-corrected.jsonl.gz'
with raw.open('rb') as source,gzip.open(packed,'wb',compresslevel=4) as out:
    shutil.copyfileobj(source,out,1024*1024)
with raw.open('rb') as source:original_hash=hashlib.file_digest(source,'sha256').hexdigest()
with gzip.open(packed,'rb') as source:packed_hash=hashlib.file_digest(source,'sha256').hexdigest()
assert original_hash==packed_hash
metadata={'geometry_pages':550,'corrected_cache_uncompressed_sha256':original_hash,'corrected_cache_raw_bytes':raw.stat().st_size,'corrected_cache_gzip_bytes':packed.stat().st_size,'geometry_gzip_bytes':geometry.stat().st_size,'verified':True}
(WORK/'packaging-checks.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
print(json.dumps(metadata,indent=2))
