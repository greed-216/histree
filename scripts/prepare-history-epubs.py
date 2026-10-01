"""Convert the 25 local history EPUBs without replacing their older source editions.

Run with Python's standard library. Text, paragraph offsets, source element paths,
removed website chrome, character restorations and defects are recorded separately.
"""
import hashlib
import gzip
import json
from pathlib import Path
import re
from html.parser import HTMLParser
import posixpath
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / 'resources/originals/twenty-four-histories'
OUT = ROOT / 'resources/derived/epub-txt'
TRAD = '史記 漢書 後漢書 三國志 晉書 宋書 南齊書 梁書 陳書 魏書 北齊書 周書 隋書 南史 北史 舊唐書 新唐書 舊五代史 新五代史 宋史 遼史 金史 元史 明史 清史稿'.split()
SIMP = '史记 汉书 后汉书 三国志 晋书 宋书 南齐书 梁书 陈书 魏书 北齐书 周书 隋书 南史 北史 旧唐书 新唐书 旧五代史 新五代史 宋史 辽史 金史 元史 明史 清史稿'.split()
COUNTS = [130, 100, 120, 65, 130, 100, 59, 56, 36, 114, 50, 50, 85, 80, 100, 200, 225, 150, 74, 496, 116, 135, 210, 332, 529]
PARTS = {'': (0, ''), 'shang': (1, '上'), 'zhong': (2, '中'), 'xia': (3, '下'),
         'zhi_yi': (1, '之一'), 'zhi_er': (2, '之二'), 'zhi_san': (3, '之三'), 'zhi_si': (4, '之四')}
NS = {'h': 'http://www.w3.org/1999/xhtml', 'o': 'http://www.idpf.org/2007/opf',
      'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
BLOCKS = {'p', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'table', 'dl', 'dt', 'dd', 'blockquote', 'pre', 'caption'}
CHROME = {'ws-header', 'licenseContainer', 'noprint', 'sistersitebox'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', text)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_compressed_json(path, data):
    path.write_bytes(gzip.compress((json.dumps(data, ensure_ascii=False) + '\n').encode(), mtime=0))


def chinese(n):
    if n < 10:
        return '零一二三四五六七八九'[n]
    if n < 100:
        return (chinese(n // 10) if n >= 20 else '') + '十' + (chinese(n % 10) if n % 10 else '')
    rest = n % 100
    return chinese(n // 100) + '百' + ('零' if 0 < rest < 10 else '') + (chinese(rest) if rest else '')


class PlainHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_html(text):
    parser = PlainHTML()
    parser.feed(text)
    return ''.join(parser.parts)


def extract(raw):
    root = ET.fromstring(raw)
    body = root.find('h:body', NS)
    assert body is not None
    excluded, variants, headers, issues = [], [], [], []
    paths = {}

    def index(element, path):
        paths[id(element)] = path
        counts = {}
        for child in element:
            tag = child.tag.rsplit('}', 1)[-1]
            counts[tag] = counts.get(tag, 0) + 1
            index(child, f'{path}/{tag}[{counts[tag]}]')

    index(body, 'body')

    def restore(element):
        attr = element.get('data-mw-variant')
        if attr:
            value = json.loads(attr)
            visible = ''.join(element.itertext())
            action = 'preserve_visible_text'
            selected = visible
            if not visible:
                if 'disabled' in value:
                    selected = value['disabled']['t']
                    action = 'restore_literal'
                elif value.get('title'):
                    selected = ''
                    action = 'title_directive_no_body_text'
                elif 'twoway' in value:
                    options = value['twoway']
                    order = ['zh-hant', 'zh-tw', 'zh-hk', 'zh', '*', 'zh-hans']
                    selected = next((o['t'] for lang in order for o in options if o['l'] == lang), None)
                    assert selected is not None, value
                    action = 'restore_declared_traditional_variant'
                elif 'filter' in value:
                    selected = plain_html(value['filter']['t'])
                    action = 'restore_source_editorial_notice'
                else:
                    raise ValueError(f'Unsupported variant: {value}')
                element.text = selected
            variants.append({'element_path': paths[id(element)], 'directive': value,
                             'action': action, 'text': selected})
        for child in element:
            restore(child)

    # Restore header glyphs as well so historical titles such as 補列傳 survive.
    restore(body)

    def clean(parent):
        for child in list(parent):
            classes = set(child.get('class', '').split())
            is_header = 'ws-header' in classes or child.get('id', '').startswith('headerContainer')
            tag = child.tag.rsplit('}', 1)[-1]
            if is_header:
                # Keep the central title cell, exclude adjacent-volume navigation.
                for cell in child.findall('.//h:td', NS):
                    if re.search(r'width\s*:\s*50%', cell.get('style', '')):
                        value = ' '.join(''.join(cell.itertext()).split())
                        if value:
                            headers.append({'text': value, 'element_path': paths[id(cell)], 'kind': 'source_heading'})
            if is_header or classes & CHROME or tag in {'script', 'style'}:
                excluded.append({'element_path': paths[id(child)], 'tag': tag,
                                 'class': child.get('class'), 'text': ''.join(child.itertext()),
                                 'xml_sha256': sha(ET.tostring(child)),
                                 'reason': 'website_header' if is_header else 'website_chrome'})
                at = list(parent).index(child)
                tail = child.tail or ''
                parent.remove(child)
                if at:
                    parent[at - 1].tail = (parent[at - 1].tail or '') + tail
                else:
                    parent.text = (parent.text or '') + tail
            else:
                clean(child)

    clean(body)
    literal = re.compile(r'<span\b[^>]*data-mw-variant=[^>]*></span>')

    def restore_literal(match, path):
        value = json.loads(ET.fromstring(match.group()).get('data-mw-variant'))
        assert set(value) == {'disabled'}, value
        text = value['disabled']['t']
        variants.append({'element_path': path, 'directive': value, 'action': 'restore_escaped_literal',
                         'original_markup': match.group(), 'text': text})
        return text

    for element in body.iter():
        for field in ('text', 'tail'):
            value = getattr(element, field)
            if value:
                setattr(element, field, literal.sub(lambda m: restore_literal(m, paths[id(element)] + '/' + field), value))
        if element.tag.rsplit('}', 1)[-1] == 'img':
            issues.append({'kind': 'nontext_image', 'element_path': paths[id(element)],
                           'src': element.get('src'), 'alt': element.get('alt')})
            # Some rare glyphs are images. Use the source's own alternative text,
            # including literal component descriptions, without guessing a glyph.
            alt = element.get('alt')
            if alt and not ''.join(element.itertext()):
                element.text = alt
                variants.append({'element_path': paths[id(element)], 'action': 'restore_image_alt',
                                 'src': element.get('src'), 'text': alt})
        if element.tag.rsplit('}', 1)[-1] == 'a':
            link = urllib.parse.unquote(element.get('href', ''))
            if re.search(r'/卷\d+/', link):
                issues.append({'kind': 'external_volume_subpage', 'href': link,
                               'text': ''.join(element.itertext()), 'element_path': paths[id(element)]})

    for header in headers:
        header['text'] = literal.sub(lambda m: restore_literal(m, header['element_path']), header['text'])
        assert 'data-mw-variant=' not in header['text'], 'Unrestored header markup'

    rows, current, contexts, kinds = [], [], [], []

    def append(value, context, kind):
        if not value:
            return
        current.append(re.sub(r'\s+', ' ', value))
        if value.strip():
            if context not in contexts:
                contexts.append(context)
            kinds.append(kind)

    def flush():
        text = ''.join(current).strip(' \t')
        if text:
            kind = next((k for k in ('editorial_notice', 'annotation', 'heading', 'table_row') if k in kinds), 'body')
            rows.append({'text': text, 'element_paths': list(contexts), 'kind': kind})
        current.clear()
        contexts.clear()
        kinds.clear()

    def render(element, context='body', kind='body', in_row=False):
        tag = element.tag.rsplit('}', 1)[-1]
        classes = set(element.get('class', '').split())
        if classes & {'mbox-text', 'boilerplate', 'mw-disambig'}:
            kind = 'editorial_notice'
        elif classes & {'references', 'mw-references', 'reference-text', 'mw-reference-text', 'reflist'}:
            kind = 'annotation'
        elif tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            kind = 'heading'
        elif tag == 'tr' and kind != 'annotation':
            kind = 'table_row'
        boundary = tag in BLOCKS and (not in_row or tag == 'tr')
        if boundary or tag == 'br':
            flush()
        if tag in BLOCKS:
            context = paths[id(element)]
        append(element.text, context, kind)
        for child in element:
            render(child, context, kind, in_row or tag == 'tr')
            append(child.tail, context, kind)
            if child.tag.rsplit('}', 1)[-1] in {'td', 'th'}:
                current.append('\t')
        if boundary:
            flush()

    render(body)
    flush()
    text = '\n\n'.join(row['text'] for row in rows) + ('\n' if rows else '')
    assert norm(text) == norm(''.join(body.itertext())), 'Body character conservation failed'
    assert 'data-mw-variant=' not in text, 'Unrestored literal markup'
    assert 'Public domainPublic domain' not in text, 'License banner leaked'
    if '\ufffd' in text:
        issues.append({'kind': 'source_replacement_character', 'count': text.count('\ufffd')})
    private = sum(0xe000 <= ord(c) <= 0xf8ff for c in text)
    if private:
        issues.append({'kind': 'source_private_use_characters', 'count': private})
    if '表略' in text or '表格略' in text:
        issues.append({'kind': 'explicit_table_omission', 'note': '原来源的略表标识保留，未自动补写'})
    if len(norm(text)) < 500:
        issues.append({'kind': 'short_content_requires_review', 'characters': len(norm(text))})
    return headers, rows, excluded, variants, issues


def convert(number, trad, simp, expected):
    epub = ORIGINALS / 'backup' / f'{trad}.epub'
    target = ORIGINALS / f'{number:02d}{simp}-EPUB全文.txt'
    folder = OUT / f'{number:02d}{simp}'
    folder.mkdir(parents=True, exist_ok=True)
    records, mappings, exclusions, restorations, issues, chunks = [], [], [], [], [], []
    offset, line = 0, 1
    with zipfile.ZipFile(epub) as archive:
        assert archive.testzip() is None
        container = ET.fromstring(archive.read('META-INF/container.xml'))
        opf_path = container.find('c:rootfiles/c:rootfile', NS).get('full-path')
        opf = ET.fromstring(archive.read(opf_path))
        manifest = {e.get('id'): e.get('href') for e in opf.find('o:manifest', NS)}
        spine = [manifest[e.get('idref')] for e in opf.find('o:spine', NS)]
        metadata = [{'name': e.tag.rsplit('}', 1)[-1], 'attributes': e.attrib, 'text': e.text}
                    for e in opf.find('o:metadata', NS)]
        entries, metadata_pages = [], []
        for order, href in enumerate(spine):
            match = re.search(r'_juan(\d+)([^.]*)\.xhtml$', href)
            member = posixpath.normpath(posixpath.join(posixpath.dirname(opf_path), urllib.parse.unquote(href)))
            if match:
                vol, suffix = int(match[1]), match[2]
                assert suffix in PARTS, (trad, href)
                entries.append(((1, vol, PARTS[suffix][0]), member, vol, suffix, order, 'volume'))
            elif re.match(r'c\d+_', posixpath.basename(href)):
                entries.append(((0 if re.match(r'c0_', posixpath.basename(href)) else 2, order, 0),
                                member, None, '', order, 'front_matter' if re.match(r'c0_', posixpath.basename(href)) else 'appendix'))
            else:
                raw = archive.read(member)
                metadata_pages.append({'epub_member': member, 'sha256': sha(raw),
                                       'text': ''.join(ET.fromstring(raw).itertext())})
        assert {e[2] for e in entries if e[2] is not None} == set(range(1, expected + 1)), trad
        for _, member, vol, suffix, order, section_kind in sorted(entries):
            raw = archive.read(member)
            title = ET.fromstring(raw).find('h:head/h:title', NS).text or ''
            headers, rows, removed, variants, defects = extract(raw)
            label = f'{simp}卷{chinese(vol)}{PARTS[suffix][1]}' if vol else f'{simp} {"卷前资料" if section_kind == "front_matter" else "附录"}'
            heading = f'{label}（EPUB原题：{title}）\n\n'
            chunk_parts = [heading]
            chunk_offset, chunk_line = offset + len(heading), line + heading.count('\n')
            for row in [dict(h, element_paths=[h['element_path']]) for h in headers] + rows:
                text = row['text']
                mappings.append({'section': len(records) + 1, 'volume': vol, 'part': suffix,
                                 'kind': row['kind'], 'section_kind': section_kind, 'epub_member': member,
                                 'element_paths': row['element_paths'], 'char_start': chunk_offset,
                                 'char_end': chunk_offset + len(text), 'line_start': chunk_line,
                                 'line_end': chunk_line + text.count('\n'), 'text_sha256': sha(text.encode())})
                chunk_parts.append(text + '\n\n')
                chunk_offset += len(text) + 2
                chunk_line += text.count('\n') + 2
            chunk = ''.join(chunk_parts)
            record = {'section': len(records) + 1, 'section_kind': section_kind, 'volume': vol, 'part': suffix,
                      'title': title, 'epub_member': member, 'member_sha256': sha(raw), 'spine_position': order,
                      'full_txt_char_start': offset, 'full_txt_char_end': offset + len(chunk),
                      'full_txt_line_start': line, 'full_txt_line_end': chunk_line - 1,
                      'text_sha256': sha(chunk.encode()), 'body_non_whitespace_characters': sum(len(norm(r['text'])) for r in rows),
                      'paragraphs': len(rows), 'review_status': 'pending_textual_review'}
            records.append(record)
            context = {'section': record['section'], 'volume': vol, 'part': suffix, 'epub_member': member}
            exclusions.extend(dict(context, **r) for r in removed)
            restorations.extend(dict(context, **r) for r in variants)
            issues.extend(dict(context, **r) for r in defects)
            chunks.append(chunk)
            offset += len(chunk)
            line = chunk_line
        write_compressed_json(folder / 'epub-metadata.json.gz', {'opf': metadata, 'non_source_pages': metadata_pages})
    full = ''.join(chunks)
    # Existing conversion editions are preserved by content hash before replacement.
    previous = None
    if target.exists() and target.read_bytes() != full.encode():
        old = target.read_bytes()
        backup = ORIGINALS / 'backup' / 'previous-conversions' / folder.name / f'{sha(old)}.txt'
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(old)
        previous = {'file': str(backup.relative_to(ROOT)), 'sha256': sha(old)}
    target.write_text(full, encoding='utf-8')
    for m in mappings:
        assert sha(full[m['char_start']:m['char_end']].encode()) == m['text_sha256']
    write_json(folder / 'sections.json', records)
    with (folder / 'paragraphs.jsonl.gz').open('wb') as fileobj, gzip.GzipFile(fileobj=fileobj, mode='wb', filename='', mtime=0) as handle:
        for m in mappings:
            handle.write((json.dumps(m, ensure_ascii=False) + '\n').encode())
    for name, value in [('excluded.json.gz', exclusions), ('restored-variants.json.gz', restorations)]:
        write_compressed_json(folder / name, value)
    write_json(folder / 'issues.json', issues)
    manifest = {'format_version': 'history-epub-txt-v1', 'book': simp, 'book_number': number,
                'epub_file': str(epub.relative_to(ROOT)), 'epub_sha256': sha(epub.read_bytes()),
                'txt_file': str(target.relative_to(ROOT)), 'txt_sha256': sha(full.encode()),
                'encoding': 'utf-8', 'expected_volumes': expected, 'volume_sections': sum(r['volume'] is not None for r in records),
                'all_source_sections': len(records), 'mapped_paragraphs_including_headings': len(mappings),
                'restored_variant_records': len(restorations), 'issue_records': len(issues),
                'validation': {'zip_crc': 'passed', 'numbered_volume_coverage': 'passed',
                               'retained_body_character_conservation': 'passed', 'paragraph_offsets': 'passed'},
                'review_status': 'pending_textual_review', 'previous_conversion': previous,
                'transforms': ['正文按数字卷号与上中下、之一至之四排序；卷前资料和附录单独标记',
                               '保留原字形和标点；按属性恢复文字及来源提示；多向转换选择原声明的繁体显示',
                               '图像字按EPUB自身alt文字或部件描述还原，不猜测原字；图片仍列入待核项',
                               '网页导航和许可框另存；中间题名栏保留，包含补帝纪、补列传等标识',
                               'HTML段落、标题和换行转为文本分段；表格行列用换行和制表符表达',
                               '段落偏移按Python Unicode字符计数，行号从1开始；未作纸本校勘或补写缺文'],
                'outputs': {name: sha((folder / name).read_bytes()) for name in
                            ('sections.json', 'paragraphs.jsonl.gz', 'excluded.json.gz',
                             'restored-variants.json.gz', 'epub-metadata.json.gz', 'issues.json')}}
    # Retain archive provenance on deterministic reruns.
    old_manifest = folder / 'manifest.json'
    if previous is None and old_manifest.exists():
        manifest['previous_conversion'] = json.loads(old_manifest.read_text()).get('previous_conversion')
        if manifest['previous_conversion']:
            prior = manifest['previous_conversion']
            archived = ORIGINALS / 'backup' / 'previous-conversions' / folder.name / f'{prior["sha256"]}.txt'
            assert sha(archived.read_bytes()) == prior['sha256']
            manifest['previous_conversion'] = {'file': str(archived.relative_to(ROOT)), 'sha256': prior['sha256']}
    manifest['previous_conversion_archives'] = [
        {'file': str(p.relative_to(ROOT)), 'sha256': sha(p.read_bytes())}
        for p in sorted((ORIGINALS / 'backup' / 'previous-conversions' / folder.name).glob('*.txt'))]
    write_json(old_manifest, manifest)
    return manifest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    originals_before = {str(p): sha(p.read_bytes()) for p in ORIGINALS.rglob('*')
                        if p.is_file() and p.suffix.lower() in ('.txt', '.epub', '.pdf')
                        and not p.name.endswith('-EPUB全文.txt')}
    books = []
    for number, (trad, simp, count) in enumerate(zip(TRAD, SIMP, COUNTS), 1):
        result = convert(number, trad, simp, count)
        books.append(result)
        print(f'{number:02d} {simp}: {result["volume_sections"]}卷文件，{result["mapped_paragraphs_including_headings"]}段/标题，字符与定位校验通过', flush=True)
    assert all(sha(Path(p).read_bytes()) == h for p, h in originals_before.items()), 'An original was modified'
    aliases_path = ROOT / 'resources/catalog/source-replacements.json'
    aliases = json.loads(aliases_path.read_text()) if aliases_path.exists() else {'format_version': 1, 'aliases': []}
    for book in books:
        for previous in book['previous_conversion_archives']:
            alias = {'file': book['txt_file'], 'sha256': previous['sha256'], 'backup_file': previous['file']}
            if not any(a['file'] == alias['file'] and a['sha256'] == alias['sha256'] for a in aliases['aliases']):
                aliases['aliases'].append(alias)
    write_json(aliases_path, aliases)
    write_json(OUT / 'catalog.json', {'format_version': 'history-epub-txt-catalog-v1', 'books': books,
                                   'original_source_hashes_preserved': {str(Path(p).relative_to(ROOT)): h for p, h in originals_before.items()},
                                   'note': '转换完成不等于逐段校勘完成；清史稿转换归档不改变现有录入范围。'})
    rows = ['# EPUB 转换文本\n',
            '二十四史及《清史稿》全部转换为 UTF-8 TXT；原 EPUB、旧 TXT、PDF及已补卷版本归入 originals/twenty-four-histories/backup。分段和检索统一见 ../history-library/README.md。\n',
            '保留繁体原字、标点、卷内题名和注文；按卷号及上下分部排序。正文缺表、外部子页、私用字和图片待核见各书 issues.json，不自动补写。网页题名栏中的补配标识保留，不视作原作者原本。卷前目录、序文与附录保留并独立标记。\n',
            '每书 sections.json 提供全文的卷界偏移，不额外复制逐卷TXT。paragraphs.jsonl.gz 提供原 XHTML 元素路径、全文行号、字符区间和片段哈希；excluded.json.gz、restored-variants.json.gz 保存移出与还原记录。Gzip采用标准UTF-8 JSON/JSONL，可用Python gzip读取。表格的 rowspan/colspan 须回查原 XHTML。\n',
            '重建：`python3 scripts/prepare-history-epubs.py`；校验：`python3 scripts/test-history-epubs.py`。\n',
            '| 书名 | 全文 TXT | 分卷与审计 |\n| --- | --- | --- |']
    for b in books:
        n, title = b['book_number'], b['book']
        rows.append(f'| {title} | [全文](../../originals/twenty-four-histories/{n:02d}{title}-EPUB全文.txt) | [分卷]({n:02d}{title}/sections.json) · [异常]({n:02d}{title}/issues.json) |')
    (OUT / 'README.md').write_text('\n\n'.join(rows[:5]) + '\n\n' + '\n'.join(rows[5:]) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
