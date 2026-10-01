"""Extract the local Wikisource EPUB as a separate, traceable TXT supplement.

No network, original TXT replacement, index rebuild, or publication.
"""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EPUB = ROOT / 'resources/originals/twenty-four-histories/舊五代史.epub'
TXT = ROOT / 'resources/originals/twenty-four-histories/18旧五代史.TXT'
OUT = ROOT / 'resources/derived/supplements/jiuwudaishi-epub'
NS = {'h': 'http://www.w3.org/1999/xhtml', 'o': 'http://www.idpf.org/2007/opf'}
BLOCKS = {'p', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'li', 'tr', 'table', 'dl', 'dt', 'dd'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(text):
    return re.sub(r'\s+', '', text)


def extract(raw):
    body = ET.fromstring(raw).find('h:body', NS)
    assert body is not None
    removed = []

    def clean(parent):
        for child in list(parent):
            tag = child.tag.rsplit('}', 1)[-1]
            classes = set(child.get('class', '').split())
            if tag in {'style', 'script'} or classes & {'ws-header', 'licenseContainer', 'noprint'}:
                removed.append({'tag': tag, 'class': child.get('class'),
                                'text': ''.join(child.itertext()).strip()})
                tail = child.tail or ''
                index = list(parent).index(child)
                parent.remove(child)
                if index:
                    parent[index - 1].tail = (parent[index - 1].tail or '') + tail
                else:
                    parent.text = (parent.text or '') + tail
            else:
                clean(child)

    clean(body)
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
    assert 'Public domain' not in text and '姊妹计划' not in text
    assert '\ufffd' not in text
    return text, removed


def main():
    original = TXT.read_bytes().decode('gb18030')
    original_body = original.rsplit(' 上一页 EasySea.COM', 1)[0].rstrip()
    assert original_body.endswith('非激忠之道也。'), 'Original TXT boundary changed'
    OUT.mkdir(parents=True, exist_ok=True)
    records, excluded, volumes = [], [], {}
    with zipfile.ZipFile(EPUB) as archive:
        opf = ET.fromstring(archive.read('OPS/content.opf'))
        manifest = {e.get('id'): e.get('href') for e in opf.find('o:manifest', NS)}
        spine = [manifest[e.get('idref')] for e in opf.find('o:spine', NS)]
        entries = [(int(m[1]), href) for href in spine
                   if (m := re.fullmatch(r'c\d+_jiu_wu_dai_shi_juan(\d+)\.xhtml', href))]
        assert [number for number, _ in entries] == list(range(1, 151))
        for number, href in entries:
            raw = archive.read('OPS/' + href)
            text, removed = extract(raw)
            assert len(norm(text)) > 500, f'Empty or short volume {number}'
            title = ET.fromstring(raw).find('h:head/h:title', NS).text
            volumes[number] = text
            excluded.append({'volume': number, 'excluded': removed})
            records.append({'volume': number, 'title': title, 'epub_member': 'OPS/' + href,
                            'member_sha256': sha(raw), 'text_sha256': sha(text.encode()),
                            'non_whitespace_characters': len(norm(text)),
                            'review_status': 'pending_textual_review'})
        assert '張敬達，字志通' in volumes[70]
        assert volumes[70].rstrip().endswith('非激忠之道也。')
        assert volumes[71].startswith('馬郁，')
        assert volumes[75].startswith('高祖聖文章武明德孝皇帝，姓石氏，諱敬瑭')
        assert '溥州' in volumes[150]
        combined, supplement, offset = [], [], 0
        for record in records:
            number = record['volume']
            heading = f'舊五代史 卷{number}（EPUB原題：{record["title"]}）\n\n'
            chunk = heading + volumes[number] + '\n'
            record['full_txt_char_start'] = offset + len(heading)
            record['full_txt_char_end'] = offset + len(heading) + len(volumes[number])
            offset += len(chunk)
            combined.append(chunk)
            if number >= 71:
                supplement.append(chunk)
        full_text = ''.join(combined)
        for record in records:
            assert sha(full_text[record['full_txt_char_start']:record['full_txt_char_end']].encode()) == record['text_sha256']
        (OUT / 'full-source.txt').write_text(full_text, encoding='utf-8')
        (OUT / 'supplement-vol-071-150.txt').write_text(''.join(supplement), encoding='utf-8')
        (OUT / 'volumes.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
        (OUT / 'excluded.json').write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + '\n')
        metadata = {e.tag.rsplit('}', 1)[-1]: e.text for e in opf.find('o:metadata', NS)
                    if e.tag.startswith('{http://purl.org/dc/elements/1.1/}') and e.text}
    audit = {'format_version': 'history-epub-supplement-v1', 'book': '旧五代史',
             'epub_file': str(EPUB.relative_to(ROOT)), 'epub_sha256': sha(EPUB.read_bytes()),
             'epub_metadata': metadata,
             'original_txt': str(TXT.relative_to(ROOT)), 'original_txt_sha256': sha(TXT.read_bytes()),
             'boundary': {'original_ends_at_volume': 70, 'last_text': '非激忠之道也。',
                          'supplement_first_volume': 71, 'supplement_last_volume': 150},
             'volumes': 150, 'supplement_volumes': 80,
             'supplement_non_whitespace_characters': sum(r['non_whitespace_characters'] for r in records if r['volume'] >= 71),
             'outputs': {name: sha((OUT / name).read_bytes()) for name in
                         ['full-source.txt', 'supplement-vol-071-150.txt', 'volumes.json', 'excluded.json']},
             'transforms': ['按OPF spine顺序提取卷1至150；附录不混入正文',
                            '移除网页导航、姊妹计划和许可展示框；移除记录见excluded.json',
                            '将HTML块和br转为换行，整理空白；保留原字、标点、正文内注文和异体字',
                            '每卷加入明确的数字卷号及EPUB原题；保留卷内原有标题'],
             'validation': '150卷都有非空正文；清理后非空白字符守恒；卷定位哈希通过；卷70末句与原TXT衔接',
             'review_status': 'pending_textual_review',
             'notes': ['这是用户提供的维基文库EPUB快照，不是纸本校勘完成的定本。',
                       '80卷补文单独保存，原TXT和已引用段落未改；未加入检索库或发布。',
                       '卷目覆盖通过不代表逐段无漏字；正文自身的原本阙佚、异文和电子转写错误仍待校核。']}
    (OUT / 'manifest.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: audit[key] for key in ['volumes', 'supplement_volumes', 'supplement_non_whitespace_characters', 'validation']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
