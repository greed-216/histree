"""Extract the missing Zhou Shu volume from the local PDF with page/line maps.

Requires pypdf and pdfplumber. Preserves printed characters and indentation
paragraphs; does not overwrite the original TXT or mix different sources silently.
"""
import hashlib
import json
from pathlib import Path
import re
import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'resources/derived/supplements/zhoushu-volume-04'
PDF = ROOT/'resources/originals/twenty-four-histories/12周书.pdf'
TXT = ROOT/'resources/originals/twenty-four-histories/12周书.TXT'
DECODED = ROOT/'resources/derived/readable-txt/12周书/decoded-source.txt'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s):
    return re.sub(r'\s','',s)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    replacement_file=OUT/'replacement.json'
    replacement=json.loads(replacement_file.read_text()) if replacement_file.exists() else None
    txt_source=ROOT/replacement['backup_file'] if replacement else TXT
    decoded_source=ROOT/replacement['decoded_backup_file'] if replacement else DECODED
    if replacement:
        assert sha(TXT)==replacement['target_sha256'], 'Canonical TXT changed; review replacement again'
    reviewed = json.loads((ROOT/'resources/derived/coverage-review/zhoushu-volume-04/finding.json').read_text())
    assert sha(PDF)==reviewed['pdf_sha256'], 'PDF changed; review pages and volume boundaries again'
    reference = PdfReader(PDF)
    raw_pages, removed, groups = [], [], []
    with pdfplumber.open(PDF) as pdf:
        for page_number in range(80,97):
            page = pdf.pages[page_number-1]
            raw = reference.pages[page_number-1].extract_text() or ''
            raw_pages.append({'pdf_page':page_number,'text':raw})
            kept = []
            for i,row in enumerate(page.extract_text_lines(),1):
                text = norm(row['text'])
                if text == '周书' or re.fullmatch(r'\d+/1466',text):
                    removed.append({'pdf_page':page_number,'line':i,'text':row['text'],'reason':'page_header_or_footer'})
                    continue
                if not text: continue
                item = {'pdf_page':page_number,'pdf_line':i,'text':text,
                        'bbox':[round(row[n],3) for n in ('x0','top','x1','bottom')]}
                kept.append(text)
                heading = page_number == 80 and text in ('帝纪第四','明帝')
                new_paragraph = heading or row['x0'] > 40
                if new_paragraph or not groups:
                    groups.append({'kind':'heading' if heading else 'paragraph','lines':[]})
                groups[-1]['lines'].append(item)
            expected = ''.join(norm(line) for line in raw.splitlines()
                               if norm(line) != '周书' and not re.fullmatch(r'\d+/1466',norm(line)))
            # Independent PDF extractors must agree on every printed character.
            assert ''.join(kept) == expected, f'PDF extractor discrepancy on page {page_number}'
    assert [g['lines'][0]['text'] for g in groups[:2]] == ['帝纪第四','明帝']
    parts, mapping, position = [], [], 0
    for group in groups:
        indent = '' if group['kind']=='heading' else '\u3000\u3000'
        parts.append(indent)
        position += len(indent)
        for line in group['lines']:
            value = line['text']
            mapping.append({**line,'kind':group['kind'],'char_start':position,'char_end':position+len(value)})
            parts.append(value)
            position += len(value)
        parts.append('\n\n')
        position += 2
    text = ''.join(parts)
    assert norm(text) == ''.join(line['text'] for group in groups for line in group['lines'])
    source = OUT/'source.txt'; source.write_text(text,encoding='utf-8')
    pages = OUT/'pdf-pages.jsonl'; pages.write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in raw_pages))
    page_map = OUT/'source-map.jsonl'; page_map.write_text(''.join(json.dumps(m,ensure_ascii=False)+'\n' for m in mapping))
    excluded = OUT/'excluded.json'; excluded.write_text(json.dumps(removed,ensure_ascii=False,indent=2)+'\n')
    original = txt_source.read_bytes().decode('gb18030')
    decoded = decoded_source.read_bytes().decode('utf-8')
    assert decoded == original
    boundary = re.search(r'(?m)^[ \t\u3000]*周书卷五[ \t\u3000]+帝纪第五',decoded)
    assert boundary and '世宗明皇帝讳毓，小名统万突，太祖长子也。' not in norm(decoded)
    at = boundary.start()
    navigation = '周书卷四  '
    combined = OUT/'combined-reading.txt'
    combined.write_text(decoded[:at]+navigation+text+decoded[at:],encoding='utf-8')
    joined_map = OUT/'combined-map.json'
    joined_map.write_text(json.dumps([
        {'char_start':0,'char_end':at,'source_file':str(decoded_source.relative_to(ROOT)),
         'source_sha256':sha(decoded_source),'source_char_start':0,'source_char_end':at},
        {'char_start':at,'char_end':at+len(navigation),'kind':'editorial_heading_prefix',
         'text':navigation,'note':'全文导航所加书名和卷号，非PDF原文；后接原有帝纪第四标题'},
        {'char_start':at+len(navigation),'char_end':at+len(navigation)+len(text),'source_file':str(source.relative_to(ROOT)),
         'source_sha256':sha(source),'source_char_start':0,'source_char_end':len(text)},
        {'char_start':at+len(navigation)+len(text),'char_end':len(decoded)+len(navigation)+len(text),'source_file':str(decoded_source.relative_to(ROOT)),
         'source_sha256':sha(decoded_source),'source_char_start':at,'source_char_end':len(decoded)}
    ],ensure_ascii=False,indent=2)+'\n')
    manifest = {
        'format_version':'history-pdf-supplement-v1','book':'周书','volume':4,
        'title':'卷四 帝纪第四·明帝（PDF补文）','source_file':str(PDF.relative_to(ROOT)),
        'source_sha256':sha(PDF),'mapped_source_file':str(source.relative_to(ROOT)),
        'mapped_source_sha256':sha(source),'pdf_page_start':80,'pdf_page_end':96,
        'raw_pages_file':str(pages.relative_to(ROOT)),'raw_pages_sha256':sha(pages),
        'source_map_file':str(page_map.relative_to(ROOT)),'source_map_sha256':sha(page_map),
        'excluded_file':str(excluded.relative_to(ROOT)),'excluded_sha256':sha(excluded),
        'combined_file':str(combined.relative_to(ROOT)),'combined_sha256':sha(combined),
        'combined_map_file':str(joined_map.relative_to(ROOT)),'combined_map_sha256':sha(joined_map),
        'combined_editorial_heading':{'prefix':navigation,'title':'周书卷四  帝纪第四',
                                     'basis':'书名及经核对的卷号；新增导航前缀与PDF原文分开记录'},
        'insert_before':{'file':str(decoded_source.relative_to(ROOT)),'sha256':sha(decoded_source),
                         'char_offset':boundary.start(),'heading':'周书卷五  帝纪第五'},
        'original_txt_file':str(txt_source.relative_to(ROOT)),'original_txt_sha256':sha(txt_source),
        'headings':2,'paragraphs':len(groups)-2,'non_whitespace_characters':len(norm(text)),
        'transforms':['只移出每页书名和页码','保留PDF原字标点，合并机械折行与跨页续行',
                      '按PDF段首横坐标缩进分段，标题单列；不按现代语义重分段',
                      '全文阅读副本在卷四原题前加“周书卷四”导航前缀；单卷PDF来源文本不改'],
        'source_anomalies_preserved':[
            {'pdf_page':82,'text':'丁巳。雍州置十二郡。','note':'底本句点原样保留'},
            {'pdf_page':86,'text':'辛已','note':'日字底本原样保留，未擅改巳'},
            {'pdf_page':87,'text':'甲戌，云。','note':'本地PDF也如此，疑有底本文字问题，待校'},
            {'pdf_page':95,'text':'不提辄奔赴阙庭','note':'本地PDF也如此，不猜改'}],
        'checks':['pypdf与pdfplumber逐页正文字符一致','17页正文字符顺序守恒',
                  '80—96页渲染已人工核对，重建时锁定已核PDF哈希'],
        'status':'local_pdf_supplement_checked_pending_edition_review',
        'limitations':['仅对本地电子PDF核对，未核纸本；不声称校勘完成。',
                       '原TXT缺卷事实保留，补文作为独立PDF来源纳入阅读索引。']}
    if replacement:
        assert sha(combined)==replacement['target_sha256']
        manifest.update(canonical_txt_file=replacement['target_file'],canonical_txt_sha256=replacement['target_sha256'])
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pages':17,'paragraphs':manifest['paragraphs'],'characters':manifest['non_whitespace_characters'],
                      'insert_char':boundary.start()},ensure_ascii=False))


if __name__ == '__main__':
    main()
