"""Convert the local Bei Qi Shu EPUB into independent, traceable UTF-8 TXT files."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / 'resources/originals/twenty-four-histories/北齊書.epub'
TXT = ROOT / 'resources/originals/twenty-four-histories/11北齐书.TXT'
OUT = ROOT / 'resources/derived/supplements/beiqishu-epub'
NS = {'h': 'http://www.w3.org/1999/xhtml', 'o': 'http://www.idpf.org/2007/opf'}
BLOCKS = {'p', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'li', 'tr', 'table', 'dl', 'dt', 'dd'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', text)


def extract(raw):
    body = ET.fromstring(raw).find('h:body', NS)
    assert body is not None
    removed, restored = [], []

    def clean(parent, path='body'):
        for index, child in enumerate(list(parent)):
            tag = child.tag.rsplit('}', 1)[-1]
            locator = f'{path}/{tag}[{index + 1}]'
            classes = set(child.get('class', '').split())
            if tag in {'style', 'script'} or classes & {'ws-header', 'licenseContainer', 'noprint'}:
                removed.append({'element_path': locator, 'tag': tag, 'class': child.get('class'),
                                'text': ''.join(child.itertext()).strip()})
                tail = child.tail or ''
                at = list(parent).index(child)
                parent.remove(child)
                if at:
                    parent[at - 1].tail = (parent[at - 1].tail or '') + tail
                else:
                    parent.text = (parent.text or '') + tail
                continue
            if child.get('data-mw-variant'):
                value = json.loads(child.get('data-mw-variant'))
                # This snapshot stores unconverted literal characters in empty spans.
                assert set(value) == {'disabled'} and set(value['disabled']) == {'t'}, value
                assert not ''.join(child.itertext()), 'Unexpected visible variant content'
                child.text = value['disabled']['t']
                assert isinstance(child.text, str) and child.text
                restored.append({'element_path': locator, 'text': child.text, 'data_mw_variant': value})
            clean(child, locator)

    clean(body)
    # Volume 39 also contains literal, escaped span markup in text nodes.
    literal_span = re.compile(r'<span\b[^>]*data-mw-variant=[^>]*></span>')

    def restore_literal(match, path):
        raw_span = match.group()
        element = ET.fromstring(raw_span)
        value = json.loads(element.get('data-mw-variant'))
        assert set(value) == {'disabled'} and set(value['disabled']) == {'t'}, value
        text = value['disabled']['t']
        assert isinstance(text, str) and text
        restored.append({'element_path': path, 'text': text, 'data_mw_variant': value,
                         'kind': 'escaped_literal_span', 'original_markup': raw_span})
        return text

    def restore_text_nodes(element, path='body'):
        for field in ('text', 'tail'):
            value = getattr(element, field)
            if value:
                setattr(element, field, literal_span.sub(lambda m: restore_literal(m, path + '/' + field), value))
        for index, child in enumerate(element):
            restore_text_nodes(child, f'{path}/{child.tag.rsplit("}", 1)[-1]}[{index + 1}]')

    restore_text_nodes(body)
    parts = []

    def render(element):
        tag = element.tag.rsplit('}', 1)[-1]
        if tag in BLOCKS or tag == 'br':
            parts.append('\n')
        parts.append(element.text or '')
        for child in element:
            render(child)
            parts.append(child.tail or '')
        if tag in BLOCKS:
            parts.append('\n')

    render(body)
    text = '\n\n'.join(line.strip() for line in ''.join(parts).splitlines() if line.strip()) + '\n'
    assert norm(text) == norm(''.join(body.itertext())), 'Lost or duplicated content'
    assert '\ufffd' not in text and 'Public domain' not in text and 'data-mw-variant' not in text
    return text, removed, restored


def main():
    original_hash, epub_hash = sha(TXT.read_bytes()), sha(EPUB.read_bytes())
    original = TXT.read_bytes().decode('gb18030')
    assert '子液嗣。' in original and '卷三十' in original and '卷三十一' not in original
    records, excluded, variants, volumes = [], [], [], {}
    with zipfile.ZipFile(EPUB) as archive:
        opf = ET.fromstring(archive.read('OPS/content.opf'))
        manifest = {e.get('id'): e.get('href') for e in opf.find('o:manifest', NS)}
        spine = [manifest[e.get('idref')] for e in opf.find('o:spine', NS)]
        entries = [(int(m[1]), href) for href in spine
                   if (m := re.fullmatch(r'c\d+_bei_qi_shu_juan(\d+)\.xhtml', href))]
        assert [n for n, _ in entries] == list(range(1, 51))
        for number, href in entries:
            raw = archive.read('OPS/' + href)
            text, removed, restored = extract(raw)
            assert len(norm(text)) > 500, f'Empty or short volume {number}'
            title = ET.fromstring(raw).find('h:head/h:title', NS).text
            volumes[number] = text
            excluded.append({'volume': number, 'excluded': removed})
            variants.append({'volume': number, 'epub_member': 'OPS/' + href, 'restored': restored})
            records.append({'volume': number, 'title': title, 'epub_member': 'OPS/' + href,
                            'member_sha256': sha(raw), 'text_sha256': sha(text.encode()),
                            'non_whitespace_characters': len(norm(text)),
                            'restored_variant_spans': len(restored), 'review_status': 'pending_textual_review'})
        assert '子液嗣。' in volumes[30]
        assert volumes[31].startswith('王昕')
        assert '贊曰：危亡之祚，昏亂之朝，小人道長，君子道消。' in volumes[50]
        combined, supplement, full_offset, supplement_offset = [], [], 0, 0
        for record in records:
            number = record['volume']
            heading = f'北齊書 卷{number}（EPUB原題：{record["title"]}）\n\n'
            chunk = heading + volumes[number] + '\n'
            record['full_txt_char_start'] = full_offset + len(heading)
            record['full_txt_char_end'] = full_offset + len(heading) + len(volumes[number])
            full_offset += len(chunk)
            combined.append(chunk)
            if number >= 31:
                record['supplement_txt_char_start'] = supplement_offset + len(heading)
                record['supplement_txt_char_end'] = supplement_offset + len(heading) + len(volumes[number])
                supplement_offset += len(chunk)
                supplement.append(chunk)
        full_text, supplement_text = ''.join(combined), ''.join(supplement)
        for record in records:
            assert sha(full_text[record['full_txt_char_start']:record['full_txt_char_end']].encode()) == record['text_sha256']
            if record['volume'] >= 31:
                assert sha(supplement_text[record['supplement_txt_char_start']:record['supplement_txt_char_end']].encode()) == record['text_sha256']
        metadata = {}
        for element in opf.find('o:metadata', NS):
            if element.tag.startswith('{http://purl.org/dc/elements/1.1/}') and element.text:
                metadata.setdefault(element.tag.rsplit('}', 1)[-1], []).append(element.text)
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {'full-source.txt': full_text, 'supplement-vol-031-050.txt': supplement_text,
               'volumes.json': records, 'excluded.json': excluded, 'restored-variants.json': variants}
    for name, content in outputs.items():
        (OUT / name).write_text(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert sha(TXT.read_bytes()) == original_hash and sha(EPUB.read_bytes()) == epub_hash
    audit = {
        'format_version': 'history-epub-supplement-v1', 'book': '北齐书',
        'epub_file': str(EPUB.relative_to(ROOT)), 'epub_sha256': epub_hash, 'epub_metadata': metadata,
        'original_txt': str(TXT.relative_to(ROOT)), 'original_txt_sha256': original_hash,
        'boundary': {'original_ends_at_volume': 30, 'last_body_text': '子液嗣。',
                     'supplement_first_volume': 31, 'supplement_last_volume': 50},
        'volumes': 50, 'supplement_volumes': 20,
        'supplement_non_whitespace_characters': sum(r['non_whitespace_characters'] for r in records if r['volume'] >= 31),
        'restored_variant_spans': sum(r['restored_variant_spans'] for r in records),
        'supplement_restored_variant_spans': sum(r['restored_variant_spans'] for r in records if r['volume'] >= 31),
        'outputs': {name: sha((OUT / name).read_bytes()) for name in outputs},
        'transforms': ['按OPF spine顺序提取卷1至50，保留繁体原字、标点、卷内标题与注文',
                       '移出网页导航、姊妹计划与许可展示框，原文字记录于excluded.json',
                       '将空异体字span的data-mw-variant.disabled.t还原为文字，逐处记录于restored-variants.json',
                       '卷39转义成文字的异体字span同样按disabled.t还原，保留原始标签审计',
                       'HTML块与br转为换行，整理空白；每卷加入数字卷号与EPUB原题',
                       '卷末校核说明保留在各卷中，不将其当作纸本已核证据'],
        'validation': '50卷连续且正文非空；还原后非空白字符守恒；全文及补文定位哈希通过；原TXT与EPUB哈希未变',
        'review_status': 'pending_textual_review',
        'notes': ['用户提供的维基文库EPUB快照，未核纸本；卷目齐全不等于逐段校勘完成。',
                  '卷31至50另存补文；原TXT、已有索引与引用保留；未重建检索库或发布。',
                  '卷头的补帝纪、补列传等历史补配标识保存在导航移出记录中；不将后世补配误作李百药原本。']}
    (OUT / 'manifest.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ['volumes', 'supplement_volumes', 'supplement_non_whitespace_characters',
                                           'restored_variant_spans', 'supplement_restored_variant_spans', 'validation']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
