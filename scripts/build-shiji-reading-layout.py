"""Derive reading-only table coordinates from the unchanged EPUB and TXT edition.

No canonical text, paragraph ID, ingestion ledger, MySQL row or evidence is changed.
The generated file contains layout and hashes, never a second copy of table prose.
"""
import argparse
from collections import Counter, defaultdict, deque
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'apps/api/src/data/shiji-reading-layout.json'
spec = importlib.util.spec_from_file_location('epub_conversion', ROOT/'scripts/prepare-history-epubs.py')
EPUB = importlib.util.module_from_spec(spec);spec.loader.exec_module(EPUB)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def tag(element):return element.tag.rsplit('}',1)[-1]


def elements(body):
    result={}
    def visit(e,path):
        result[path]=e;counts=Counter()
        for child in e:
            counts[tag(child)]+=1;visit(child,path+'/'+tag(child)+'['+str(counts[tag(child)])+']')
    visit(body,'body');return result


def grid(rows):
    """Use explicit cells/spans; absent text never shifts a column left."""
    result=[];occupied={};positions={};width=0
    for index,(path,tr) in enumerate(rows):
        column=0;cells=[]
        for suffix,cell in elements(tr).items():
            if suffix=='body' or '/' in suffix[len('body/'):]:continue
            if tag(cell) not in ('td','th'):continue
            colspan=int(cell.get('colspan','1'));rowspan=int(cell.get('rowspan','1'))
            assert 1<=colspan<=100 and 1<=rowspan<=len(rows)-index, 'Invalid source span'
            while occupied.get(column,-1)>=index:column+=1
            assert all(occupied.get(c,-1)<index for c in range(column,column+colspan)), 'Overlapping source spans'
            position=len(cells);positions[path+suffix[len('body'):]]=(index,position)
            cells.append([column,colspan,rowspan,tag(cell)=='th'])
            for c in range(column,column+colspan):occupied[c]=index+rowspan-1
            column+=colspan;width=max(width,column)
        result.append(cells)
    return result,positions,width


DIVISIONS=[('benji','十二本纪',1,12),('biao','十表',13,22),('shu','八书',23,30),('shijia','三十世家',31,60),('liezhuan','七十列传',61,130)]


def chapter_title(text,volume):
    numbers={EPUB.chinese(volume),''.join('零一二三四五六七八九'[int(n)] for n in str(volume))}
    if 110<=volume<=119:numbers.add('一百一'+EPUB.chinese(volume-100))
    title=re.sub(r'^史[記记][卷巻](?:'+'|'.join(sorted(numbers,key=len,reverse=True))+r')\s*','',text)
    title=re.sub(r'^太史公書','',title)
    title=re.sub(r'作者[：:].*$','',title).strip()
    title=re.sub(r'\s*(?:第[一二三四五六七八九十百]+|〈第[一二三四五六七八九十百]+〉)$','',title).strip()
    assert title and title!=text or text=='太史公自序', (volume,text)
    assert not re.match(r'^史[記记][卷巻]',title), (volume,title)
    return title


def build(root=ROOT):
    conversion=root/'resources/derived/epub-txt/01史记';manifest=json.loads((conversion/'manifest.json').read_text())
    rawpath=root/manifest['txt_file'];epubpath=root/manifest['epub_file'];raw=rawpath.read_bytes()
    assert sha(raw)==manifest['txt_sha256'] and sha(epubpath.read_bytes())==manifest['epub_sha256']
    txt=raw.decode('utf-8');directory=root/'resources/derived/history-library/shiji';index=json.loads((directory/'index.json').read_text())
    with gzip.open(directory/'paragraphs.jsonl.gz','rt',encoding='utf-8') as stream:paragraphs=[json.loads(line) for line in stream]
    sections=json.loads((directory/'sections.json').read_text());chapters=[]
    for section in sections:
        v=section.get('volume_candidate')
        if v is None:continue
        candidates=[p for p in paragraphs if p['section_id']==section['id'] and p['kind']=='heading' and 'editorial_navigation_heading' not in p.get('flags',[]) and p['text'][:2]!='史记']
        assert candidates,(v,'No source heading')
        p=candidates[0];original=txt[p['locator']['char_start']:p['locator']['char_end']]
        group=next(d for d in DIVISIONS if d[2]<=v<=d[3])
        chapters.append(dict(section_id=section['id'],volume=v,title=chapter_title(original,v),division=group[0],source_heading_id=p['id'],source_heading_sha256=sha(original.encode())))
    assert [c['volume'] for c in chapters]==list(range(1,131))
    wanted=[p for p in paragraphs if p.get('volume_candidate') in range(13,23) and p['kind']=='table_row']
    by_member=defaultdict(list)
    for p in wanted:by_member[p['locator']['epub_member']].append(p)
    tables={};layouts={}
    with zipfile.ZipFile(epubpath) as archive:
        for member,ps in by_member.items():
            source=archive.read(member);assert all(sha(source)==p['locator']['member_sha256'] for p in ps)
            body=ET.fromstring(source).find('h:body',EPUB.NS);paths=elements(body)
            extracted=EPUB.extract(source,capture_layout=True)[1];lookup=defaultdict(deque)
            for row in extracted:
                if row['kind']=='table_row':lookup[(tuple(row['element_paths']),row['text'])].append(row)
            for p in ps:
                loc=p['locator'];text=txt[loc['char_start']:loc['char_end']]
                assert sha(text.encode())==loc['raw_excerpt_sha256']
                key=(tuple(loc['element_paths']),text);assert lookup[key],p['id'];row=lookup[key].popleft()
                source_rows={re.match(r'(.*/tr\[\d+\])',f['path']).group(1) for f in row['cell_fragments']}
                assert len(source_rows)==1,(p['id'],source_rows)
                trpath=next(iter(source_rows));tablepath=trpath.rsplit('/table[',1)[0]+'/table['+trpath.rsplit('/table[',1)[1].split(']')[0]+']'
                tid='shiji-'+sha((member+'\0'+tablepath).encode())[:16]
                if tid not in tables:
                    row_elements=[(path,e) for path,e in paths.items() if tag(e)=='tr' and path.startswith(tablepath+'/') and '/table[' not in path[len(tablepath):]]
                    rows,positions,width=grid(row_elements)
                    title=next(c['title'] for c in chapters if c['section_id']==p['section_id'])
                    tables[tid]=dict(id=tid,section_id=p['section_id'],caption=title,columns=width,epub_member=member,source_table_path=tablepath,rows=rows,header_paragraph_ids=[])
                    tables[tid]['_positions']=positions
                table=tables[tid];fragments=[];covered=set();row_index=None
                for f in row['cell_fragments']:
                    ri,ci=table['_positions'][f['path']];assert row_index is None or row_index==ri
                    row_index=ri;fragments.append([ci,f['start'],f['end']]);covered.update(range(f['start'],f['end']))
                assert all(i in covered or char.isspace() for i,char in enumerate(text)),(p['id'],'Unmapped original text')
                layouts[p['id']]=dict(content_sha256=loc['raw_excerpt_sha256'],table_id=tid,row_index=row_index,fragments=fragments)
                if table['rows'][row_index] and all(c[3] for c in table['rows'][row_index]):table['header_paragraph_ids'].append(p['id'])
    for table in tables.values():table.pop('_positions')
    assert set(layouts)=={p['id'] for p in wanted}
    return dict(format_version=1,book_key='shiji',source_version=index['source_version'],source_sha256=manifest['txt_sha256'],epub_sha256=manifest['epub_sha256'],offset_unit='unicode-codepoints',divisions=[dict(id=k,title=t,start_volume=a,end_volume=b) for k,t,a,b in DIVISIONS],chapters=chapters,tables=tables,paragraphs=layouts)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args()
    value=build();raw=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    if args.check:assert args.output.read_bytes()==raw,'Reading layout is stale'
    else:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(raw)
    print(json.dumps(dict(chapters=len(value['chapters']),tables=len(value['tables']),table_paragraphs=len(value['paragraphs']),bytes=len(raw),canonical_text_changed=False)))


if __name__=='__main__':main()
