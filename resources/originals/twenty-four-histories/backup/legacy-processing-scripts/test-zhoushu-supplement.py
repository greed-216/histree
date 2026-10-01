"""Verify PDF supplement conservation, ordered joins, old IDs and export locators."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'resources/derived/supplements/zhoushu-volume-04'
LIBRARY = ROOT/'resources/derived/history-library'
manifest = json.loads((BASE/'manifest.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
norm = lambda t: re.sub(r'\s','',t)
for f,h in [('source_file','source_sha256'),('mapped_source_file','mapped_source_sha256'),
            ('source_map_file','source_map_sha256'),('raw_pages_file','raw_pages_sha256'),
            ('original_txt_file','original_txt_sha256'),('combined_file','combined_sha256'),
            ('combined_map_file','combined_map_sha256'),('excluded_file','excluded_sha256')]:
    assert sha(ROOT/manifest[f]) == manifest[h]
source = (ROOT/manifest['mapped_source_file']).read_bytes().decode('utf-8')
pages = [json.loads(row) for row in (ROOT/manifest['raw_pages_file']).read_text().splitlines()]
assert [row['pdf_page'] for row in pages] == list(range(80,97))
expected = ''.join(norm(line) for row in pages for line in row['text'].splitlines()
                   if norm(line)!='周书' and not re.fullmatch(r'\d+/1466',norm(line)))
assert norm(source) == expected and len(expected)==manifest['non_whitespace_characters']
assert source.startswith('帝纪第四\n\n明帝\n\n') and source.rstrip().endswith('享年不永。惜哉！')
assert '世宗明皇帝讳毓，小名统万突，太祖长子也。' in source
assert len(re.findall('^\u3000\u3000',source,re.M))==manifest['paragraphs']==19
for anomaly in manifest['source_anomalies_preserved']:
    assert anomaly['text'] in source
mapping = [json.loads(row) for row in (ROOT/manifest['source_map_file']).read_text().splitlines()]
previous = 0
for row in mapping:
    a,b = row['char_start'],row['char_end']
    assert a>=previous and not source[previous:a].strip()
    assert source[a:b] == row['text']
    previous = b
assert not source[previous:].strip()
combined = (ROOT/manifest['combined_file']).read_bytes().decode('utf-8')
cursor, slices = 0, []
for part in json.loads((ROOT/manifest['combined_map_file']).read_text()):
    assert part['char_start']==cursor
    if part.get('kind')=='editorial_heading_prefix':
        assert part['text']==manifest['combined_editorial_heading']['prefix']=='周书卷四  '
        piece=part['text']
    else:
        assert sha(ROOT/part['source_file'])==part['source_sha256']
        effective = (ROOT/part['source_file']).read_bytes().decode('utf-8')
        piece = effective[part['source_char_start']:part['source_char_end']]
    assert combined[part['char_start']:part['char_end']] == piece
    slices.append(piece);cursor=part['char_end']
assert ''.join(slices)==combined and cursor==len(combined)
assert combined.index('周书卷三') < combined.index('帝纪第四\n\n明帝') < combined.index('周书卷五')
assert len(re.findall(r'^周书卷四  帝纪第四$',combined,re.M))==1
book = json.loads((LIBRARY/'zhoushu/index.json').read_text())
sections = json.loads((ROOT/book['sections_file']).read_text())
volumes = [s['volume_candidate'] for s in sections if s['kind']=='section' and s['volume_candidate']]
assert volumes[:6]==[1,2,3,4,5,6]
records = [json.loads(line) for line in (ROOT/book['paragraph_file']).read_text().splitlines()]
supplement = [r for r in records if 'local_pdf_supplement' in r['flags']]
assert len(supplement)==21 and sum(r['kind']=='body' for r in supplement)==19
assert all(r['volume_candidate']==4 and r['volume_verified'] for r in supplement)
assert norm(''.join(r['text'] for r in supplement)) == expected
assert min(r['locator']['pdf_page_start'] for r in supplement)==80
assert max(r['locator']['pdf_page_end'] for r in supplement)==96
cli=ROOT/'scripts/search-history-library.py'
query=json.loads(subprocess.check_output([sys.executable,str(cli),'世宗明皇帝讳毓','--book','周书','--volume','4']))
assert query['returned']==1 and query['results'][0]['locator']['pdf_page_start']==80
with tempfile.TemporaryDirectory(prefix='histree-zhoushu-export-') as tmp:
    record = next(r for r in supplement if r['kind']=='body')
    subprocess.check_output([sys.executable,str(cli),'--id',record['id'],'--export',tmp])
    exported=json.loads((Path(tmp)/'manifest.json').read_text())
    assert exported['upstream_locator']['pdf_page_start']==80
    assert exported['sha256']==sha(Path(tmp)/'source.txt')
    assert norm((Path(tmp)/'source.txt').read_text())==norm(record['text'])
# The previous book version remains readable with its original source offsets.
archives=list((LIBRARY/'zhoushu/versions').glob('*/paragraphs.jsonl'))
assert archives
old=json.loads(archives[0].read_text().splitlines()[0])
old_result=json.loads(subprocess.check_output([sys.executable,str(cli),'--id',old['id']]))
assert old_result==old
replacement_file=BASE/'replacement.json'
if replacement_file.exists():
    replacement=json.loads(replacement_file.read_text())
    assert sha(ROOT/replacement['target_file'])==replacement['target_sha256']==manifest['combined_sha256']
    assert sha(ROOT/replacement['backup_file'])==replacement['backup_sha256']
    assert (ROOT/replacement['target_file']).read_bytes()==(ROOT/manifest['combined_file']).read_bytes()
    assert len(re.findall(r'^周书卷四  帝纪第四$',(ROOT/replacement['target_file']).read_text(),re.M))==1
    with tempfile.TemporaryDirectory(prefix='histree-old-source-') as tmp:
        subprocess.check_output([sys.executable,str(cli),'--id',old['id'],'--export',tmp])
        exported=json.loads((Path(tmp)/'manifest.json').read_text())
        assert exported['resolved_original_file']==replacement['backup_file']
        assert exported['resolved_source_file']==replacement['decoded_backup_file']
result={'status':'verified','pdf_pages':[80,96],'characters':len(expected),'body_paragraphs':19,
        'headings':2,'checks':['PDF body character conservation','exact page/line maps',
                              'original TXT preserved','volume 3/4/5 join order','search and PDF citation export',
                              'previous version paragraph IDs still readable']}
(BASE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
