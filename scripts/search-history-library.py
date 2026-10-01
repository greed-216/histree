"""Read-only local search and traceable excerpt export for the history library."""
import argparse
import hashlib
import json
import sqlite3
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'resources/derived/history-library'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_record(value):
    return json.loads(zlib.decompress(value) if isinstance(value, bytes) else value)


def resolve_source(filename, checksum):
    path=ROOT/filename
    if path.exists() and digest(path)==checksum:return path
    aliases=ROOT/'resources/catalog/source-replacements.json'
    if aliases.exists():
        for item in json.loads(aliases.read_text())['aliases']:
            if item['file']==filename and item['sha256']==checksum:
                backup=ROOT/item['backup_file']
                assert digest(backup)==checksum, 'Archived source changed'
                return backup
    raise AssertionError('Source changed without a matching archived snapshot; rebuild before export')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',nargs='?',help='literal substring; two-character Chinese terms are supported')
    parser.add_argument('--book',help='Chinese title or stable book key')
    parser.add_argument('--section',help='literal substring in section title')
    parser.add_argument('--volume',type=int,help='numbered EPUB volume; textual review is separate')
    parser.add_argument('--include-notes',action='store_true')
    parser.add_argument('--all-kinds',action='store_true',help='include headings, directories and navigation')
    parser.add_argument('--id',help='retrieve a complete paragraph record')
    parser.add_argument('--export',type=Path,help='export --id as exact source excerpt plus audit manifest')
    parser.add_argument('--limit',type=int,default=20)
    args = parser.parse_args()
    if not (BASE/'search.sqlite').exists():
        parser.error('检索缓存未建立。请先运行 python3 scripts/build-history-library.py --rebuild-search')
    db = sqlite3.connect('file:'+str(BASE/'search.sqlite')+'?mode=ro',uri=True)
    if db.execute('SELECT value FROM metadata WHERE key=?',('catalog_sha256',)).fetchone()[0] != digest(BASE/'catalog.json'):
        parser.error('检索缓存已过期。请运行 python3 scripts/build-history-library.py --rebuild-search')
    if args.id:
        row = db.execute('SELECT record_json FROM paragraphs WHERE id=?',(args.id,)).fetchone()
        if not row: parser.error('paragraph ID not found in this source version')
        record = decode_record(row[0])
        if args.export:
            loc = record['locator']
            source = resolve_source(loc['source_file'],loc['source_sha256'])
            original = resolve_source(loc['original_file'],loc['original_sha256'])
            if loc.get('source_map_file'):
                assert digest(ROOT/loc['source_map_file']) == loc['source_map_sha256']
            text = source.read_bytes().decode('utf-8')[loc['char_start']:loc['char_end']]
            assert hashlib.sha256(text.encode()).hexdigest() == loc['raw_excerpt_sha256']
            args.export.mkdir(parents=True,exist_ok=True)
            target = args.export/'source.txt'
            target.write_text(text,encoding='utf-8')
            (args.export/'paragraph.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
            manifest = {'status':'draft_source_snapshot_not_published','paragraph_id':record['id'],
                        'file':'source.txt','sha256':digest(target),'upstream_locator':loc,
                        'resolved_source_file':str(source.relative_to(ROOT)),
                        'resolved_original_file':str(original.relative_to(ROOT)),
                        'citation':record['citation'],'notes':[
                            '逐字保存有效底本中的片段，包含原换行；不是人工校勘完成的引文。',
                            '发布时仍需独立source、校核说明和固定提交链接。']}
            (args.export/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(record,ensure_ascii=False,indent=2))
        return
    if args.export: parser.error('--export requires --id')
    if not args.query or not args.query.strip(): parser.error('provide a search term or --id')
    query = args.query.strip()
    conditions, params = [], []
    if len(query) >= 3:
        conditions.append('p.rowid IN (SELECT rowid FROM search WHERE search MATCH ?)')
        params.append('"'+query.replace('"','""')+'"')
    # Literal check makes punctuation and case semantics independent of FTS.
    conditions.append('instr(p.text,?)>0')
    params.append(query)
    if args.book:
        conditions.append('(p.book=? OR p.book_key=?)')
        params.extend([args.book,args.book])
    if args.section:
        conditions.append('instr(p.section_title,?)>0')
        params.append(args.section)
    if args.volume is not None:
        conditions.append('p.volume=?')
        params.append(args.volume)
    if not args.all_kinds:
        conditions.append("p.kind IN ('body','table_row','annotation')" if args.include_notes else "p.kind IN ('body','table_row')")
    rows = db.execute('SELECT p.record_json FROM paragraphs p WHERE '+' AND '.join(conditions)+' ORDER BY p.book_key,p.rowid LIMIT ?',params+[max(1,min(args.limit,100))])
    results = []
    for row in rows:
        record = decode_record(row[0])
        pos = record['text'].find(query)
        record['snippet'] = record['text'][max(0,pos-80):pos+len(query)+180]
        record.pop('text')
        results.append(record)
    print(json.dumps({'query':query,'returned':len(results),'limit':max(1,min(args.limit,100)),
                      'results':results},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
