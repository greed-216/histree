"""Recover Ming History table coordinates from the unchanged selected EPUB."""
import argparse
from collections import defaultdict, deque
import gzip
import importlib.util
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
from build_shiji_layout_loader import load_layout_builder

M = load_layout_builder()
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'apps/api/src/data/mingshi-reading-layout.json'
AUDIT = ROOT / 'content/books/mingshi/vol-109/table-first/structure-review.json'
ERA = {'洪武':1368,'建文':1399,'永樂':1403,'洪熙':1425,'宣德':1426,
       '正統':1436,'景泰':1450,'天順':1457,'成化':1465,'弘治':1488,'正德':1506}
ERA_REFERENCE = 'https://dict.revised.moe.edu.tw/appendix.jsp?ID=43&la=0&page=5&powerMode=0'


def number(text):
    if text == '元':return 1
    return next(n for n in range(1,100) if M.EPUB.chinese(n)==text)


def build():
    directory=ROOT/'resources/derived/history-library/mingshi'
    index=json.loads((directory/'index.json').read_text())
    manifest=json.loads((ROOT/'resources/derived/epub-txt/24明史/manifest.json').read_text())
    text=(ROOT/manifest['txt_file']).read_text()
    assert M.sha(text.encode())==manifest['txt_sha256']
    assert M.sha((ROOT/manifest['epub_file']).read_bytes())==manifest['epub_sha256']
    with gzip.open(directory/'paragraphs.jsonl.gz','rt') as f:
        ps=[p for line in f if (p:=json.loads(line)).get('volume_candidate')==109]
    source_rows=[p for p in ps if p['kind']=='table_row']
    tables={};layouts={};audit_tables=[];by_row=defaultdict(list)
    with zipfile.ZipFile(ROOT/manifest['epub_file']) as z:
        member=ps[0]['locator']['epub_member'];raw=z.read(member)
        assert M.sha(raw)==ps[0]['locator']['member_sha256']
        body=ET.fromstring(raw).find('h:body',M.EPUB.NS);paths=M.elements(body)
        lookup=defaultdict(deque)
        for row in M.EPUB.extract(raw,capture_layout=True)[1]:
            if row['kind']=='table_row':lookup[(tuple(row['element_paths']),row['text'])].append(row)
        for p in source_rows:
            loc=p['locator'];original=text[loc['char_start']:loc['char_end']]
            assert M.sha(original.encode())==loc['raw_excerpt_sha256']
            key=(tuple(loc['element_paths']),original);assert lookup[key],p['id']
            row=lookup[key].popleft()
            trpaths={re.match(r'(.*/tr\[\d+\])',f['path']).group(1) for f in row['cell_fragments']}
            assert len(trpaths)==1
            trpath=next(iter(trpaths));tablepath=trpath.rsplit('/table[',1)[0]+'/table['+trpath.rsplit('/table[',1)[1].split(']')[0]+']'
            tid='mingshi-'+M.sha((member+'\0'+tablepath).encode())[:16]
            if tid not in tables:
                elements=[(path,e) for path,e in paths.items() if M.tag(e)=='tr' and path.startswith(tablepath+'/') and '/table[' not in path[len(tablepath):]]
                rows,positions,width=M.grid(elements)
                tables[tid]={'id':tid,'section_id':p['section_id'],'caption':'宰輔年表一 · '+('洪武中書省' if width==5 else '入閣與拜免'),
                             'columns':width,'column_labels':['紀年','左、右丞相','平章政事','左、右丞','參知政事'] if width==5 else ['紀年','宰輔入閣與拜免'],'epub_member':member,'source_table_path':tablepath,
                             'rows':rows,'header_paragraph_ids':[], '_positions':positions,'_elements':elements}
            table=tables[tid];fragments=[];covered=set();ri=None
            for f in row['cell_fragments']:
                row_index,ci=table['_positions'][f['path']]
                assert ri is None or ri==row_index
                ri=row_index;fragments.append([ci,f['start'],f['end']]);covered.update(range(f['start'],f['end']))
            assert all(i in covered or c.isspace() for i,c in enumerate(original))
            layouts[p['id']]={'content_sha256':loc['raw_excerpt_sha256'],'table_id':tid,'row_index':ri,'fragments':fragments}
            by_row[(tid,ri)].append(p)
        assert len(tables)==2
        years=[];issues=[]
        for tid,table in tables.items():
            era='洪武' if table['columns']==5 else '建文'
            year_context=None;year_origin=None;owners={}
            for ri,(trpath,tr) in enumerate(table['_elements']):
                cells=[e for e in tr if M.tag(e) in ('td','th')]
                row_p=by_row[(tid,ri)]
                assert row_p
                cell_text=[' '.join(''.join(c.itertext()).split()) for c in cells]
                first_at=table['rows'][ri][0][0]
                role='entry'
                if table['columns']==5 and ri==0:
                    role='header';table['header_paragraph_ids']=[p['id'] for p in row_p]
                    for cell in table['rows'][ri]:cell[3]=True
                    assert cell_text==['紀年','宰輔拜免']
                elif table['columns']==5 and ri==2:
                    role='office_header'
                    assert cell_text==['左、右丞相','平章政事','左、右丞','參知政事']
                    for cell in table['rows'][ri]:cell[3]=True
                elif first_at==0:
                    heading=cell_text[0]
                    match=re.match(r'^(?:太祖)?(?:(洪武|建文|永樂|洪熙|宣德|正統|景泰|天順|成化|弘治|正德))?([元一二三四五六七八九十]+)年([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥末])',heading)
                    assert match,(ri,heading)
                    if match[1]:era=match[1]
                    n=number(match[2]);year=ERA[era]+n-1
                    stems='甲乙丙丁戊己庚辛壬癸';branches='子丑寅卯辰巳午未申酉戌亥'
                    expected=stems[(year-4)%10]+branches[(year-4)%12]
                    year_context={'era':era,'regnal_year':n,'year':year,'source_heading':heading,
                                  'source_paragraph_id':row_p[0]['id'],'ganzhi':match[3],'expected_ganzhi':expected}
                    if match[3]!=expected:
                        issues.append({'kind':'source_ganzhi_variant','paragraph_id':row_p[0]['id'],'source':match[3],'expected':expected,'year':year,'action':'retain_source_and_flag'})
                    if '改天順元年' in heading:era='天順'
                    year_origin={'paragraph_id':row_p[0]['id'],'cell_index':0,'row_index':ri,'rowspan':int(cells[0].get('rowspan','1'))}
                for ci,(cell,position) in enumerate(zip(cells,table['rows'][ri])):
                    at,colspan,rowspan,_=position
                    owners[(ri,ci)]={'row_index':ri,'cell_index':ci,'column':at,'colspan':colspan,'rowspan':rowspan,
                                    'paragraph_id':row_p[0]['id']}
                context=[]
                for owner in owners.values():
                    if owner['row_index']<ri<owner['row_index']+owner['rowspan']:
                        if owner['column']!=0:continue
                        layout=layouts[owner['paragraph_id']]
                        ranges=[f for f in layout['fragments'] if f[0]==owner['cell_index']]
                        for _,a,b in ranges:
                            context.append({'column':owner['column'],'colspan':owner['colspan'],
                                            'rowspan':owner['row_index']+owner['rowspan']-ri,
                                            'paragraph_id':owner['paragraph_id'],'start':a,'end':b})
                for p in row_p:
                    if context:layouts[p['id']]['context_cells']=context
                    if year_context:
                        layouts[p['id']]['calendar_year']=year_context['year']
                        if year_context['ganzhi']!=year_context['expected_ganzhi']:
                            layouts[p['id']]['calendar_note']='原栏干支作'+year_context['ganzhi']+'，按年号换算应为'+year_context['expected_ganzhi']+'；原字保留。'
                if role!='header':
                    assert year_context is not None
                    assert ri<year_origin['row_index']+year_origin['rowspan'],(ri,'Expired year rowspan')
                years.append({'table_id':tid,'row_index':ri,'paragraph_ids':[p['id'] for p in row_p],
                              'role':role,'year_context':dict(year_context) if year_context else None,
                              'physical_cells':len(cells),'column_positions':table['rows'][ri]})
            audit_tables.append({'table_id':tid,'columns':table['columns'],'rows':len(table['rows']),
                                 'column_labels':['紀年','左、右丞相','平章政事','左、右丞','參知政事'] if table['columns']==5 else ['紀年','宰輔入閣與拜免'],
                                 'source_table_path':table['source_table_path']})
            table.pop('_positions');table.pop('_elements')
    assert len(layouts)==549
    groups={y['year_context']['year'] for y in years if y['role']!='header'}
    assert groups==set(range(1368,1381))|set(range(1402,1522))
    audit={'format_version':1,'book_key':'mingshi','volume':109,'source_version':index['source_version'],
           'epub_sha256':manifest['epub_sha256'],'txt_sha256':manifest['txt_sha256'],'source_member_sha256':M.sha(raw),
           'status':'source_structure_reviewed_facts_pending','tables':audit_tables,'rows':years,'issues':issues,
           'calendar_anchor_reference':ERA_REFERENCE,'calendar_anchor_last_page':'https://dict.revised.moe.edu.tw/appendix.jsp?ID=43&la=0&page=6&powerMode=0',
           'era_first_years':ERA,'covered_calendar_years':len(groups),
           'scope_note':'洪武十三年罢中书省后，本表跳至建文四年；1381—1401不补造空年行。年栏是格位时间背景，不自动等于每个追叙行动的发生年。'}
    data={'format_version':1,'book_key':'mingshi','source_version':index['source_version'],
          'source_sha256':manifest['txt_sha256'],'epub_sha256':manifest['epub_sha256'],'offset_unit':'unicode-codepoints',
          'divisions':[],'chapters':[],'tables':tables,'paragraphs':layouts,
          'annotations':{},'calendar_groups':{},'calendar_paragraphs':{}}
    return data,audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data,audit=build()
    for path,value in [(OUTPUT,data),(AUDIT,audit)]:
        raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
        if args.check:assert path.read_bytes()==raw
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(json.dumps({'tables':len(data['tables']),'table_rows':len(data['paragraphs']),'covered_years':audit['covered_calendar_years'],'issues':audit['issues']},ensure_ascii=False))
