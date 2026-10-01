"""Prepare user-supplied TXT reading copies with strict decoding and source maps.

Uses audited correction overlays where present; does not adopt sources,
update ingestion progress, or publish.
Chapter headings are candidates, never automatically assigned canonical volumes.
"""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'resources/originals/twenty-four-histories'
OUT = ROOT / 'resources/derived/readable-txt'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'scripts/prepare-readable-history.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
repair_spec = importlib.util.spec_from_file_location('repairs', ROOT / 'scripts/repair-history-txt.py')
repairs = importlib.util.module_from_spec(repair_spec)
repair_spec.loader.exec_module(repairs)
NUM = r'[一二三四五六七八九十百千〇零廿卅0-9]+'
LABEL = r'(?:本纪|帝纪|列传|志|表|[梁唐晋汉周]本纪|[梁唐晋汉周]家人传|[梁唐晋汉周]臣传|太祖纪|高祖纪|武皇纪|庄宗纪|明宗纪|隐帝纪|世宗纪|末帝纪|.*?世家|.*?附录|.*?考|.*?传)'


def heading(raw):
    line = raw.strip().lstrip('●○*').strip()
    if not line or len(line) > 80 or re.search(r'[，。；：！？“”]', line):
        return None
    if re.match(r'^(?:周书)?卷' + NUM + r'(?:[上下中]|\s|·|$)', line) or re.match('^' + LABEL + '(?:第)?' + NUM + r'(?:[上下中]|\s|$)', line):
        return line
    return None


def decode(raw):
    for encoding in ['utf-8-sig', 'gb18030']:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    # Fail closed; no replacement or deletion of undecodable source bytes.
    raw.decode('gb18030')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build(source):
    raw = source.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    result = {'source_file': str(source.relative_to(ROOT)), 'source_sha256': checksum,
              'bytes': len(raw), 'source_origin': '用户提供；电子底本待考',
              'status': 'reading_only_requires_review'}
    overlay = repairs.OUT / source.stem / 'manifest.json'
    corrected = None
    try:
        if overlay.exists():
            corrected = json.loads(overlay.read_text())
            assert corrected['source_file'] == result['source_file']
            text = repairs.verify_replay(corrected)
            encoding = corrected['original_encoding']
            result.update(corrected_source_file=corrected['corrected_file'],
                          corrected_source_sha256=corrected['corrected_sha256'],
                          corrections_manifest=str(overlay.relative_to(ROOT)),
                          corrections_manifest_sha256=reader.digest(overlay),
                          corrections_count=corrected['changes'],
                          corrections_unresolved_count=len(corrected['unresolved']),
                          mapped_source_file=corrected['corrected_file'])
        else:
            text, encoding = decode(raw)
            result['mapped_source_file'] = result['source_file']
    except UnicodeDecodeError as error:
        result.update(status='blocked_decoding', decode_error={
            'encoding': error.encoding, 'byte_start': error.start,
            'byte_end': error.end, 'reason': error.reason})
        return result
    result['encoding'] = encoding
    lines = text.splitlines()
    result['lines'] = len(lines)
    folder = OUT / source.stem
    folder.mkdir(parents=True, exist_ok=True)
    # This is a decoded source copy, including every existing line delimiter.
    (folder / 'decoded-source.txt').write_text(text)
    issues = []
    for i, line in enumerate(lines, 1):
        if '〔缺字：原字节' in line:
            issues.append({'line': i, 'kind': 'explicit_missing_glyph', 'sample': line[:250]})
        private = [(j + 1, f'U+{ord(c):04X}') for j, c in enumerate(line) if 0xe000 <= ord(c) <= 0xf8ff]
        if private:
            issues.append({'line': i, 'kind': 'private_use_characters', 'positions': private})
        if re.search(r'无产阶级|布哈林|黑格尔|唯物主义|劳动价值论', line):
            issues.append({'line': i, 'kind': 'suspected_modern_text', 'sample': line[:250]})
        if re.search(r'A:visited|A:active|TEXT-DECORATION|COLOR:|^\s*}\s*$', line):
            issues.append({'line': i, 'kind': 'web_style_residue', 'sample': line[:160]})
        if source.stem.startswith('清史稿') and (re.match(r'^(\S{2})\1', line) or re.search(r'[古斋知主]$', line)):
            issues.append({'line': i, 'kind': 'possible_web_watermark_or_repetition', 'sample': line[:160]})
    starts = [(i, heading(line)) for i, line in enumerate(lines) if heading(line)]
    if not starts or starts[0][0] > 0:
        starts.insert(0, (0, '卷界未定／卷前文字'))
    mapped = []
    units = []
    all_seen = []
    for n, (start, title) in enumerate(starts, 1):
        end = starts[n][0] if n < len(starts) else len(lines)
        rows = []
        groups = []
        def flush():
            nonlocal rows
            if rows:
                groups.append(rows)
                rows = []
        for i in range(start, end):
            line = lines[i]
            if not line.strip():
                flush()
                continue
            if heading(line) or line.startswith(('    ', '\u3000\u3000')):
                flush()
            # Very long lines occur in several user files. These fixed-size
            # reading chunks are not claims about natural paragraph boundaries.
            for pos in range(0, len(line), 1600):
                if pos:
                    flush()
                piece = line[pos:pos+1600]
                rows.append({'line': i + 1, 'char_start': pos, 'char_end': pos + len(piece),
                             'raw': piece})
            if heading(line):
                flush()
        flush()
        blocks = []
        for group in groups:
            original = ''.join(r['raw'].strip() for r in group)
            clean = reader.compact(original)
            assert re.sub(r'\s', '', original) == re.sub(r'\s', '', clean)
            block = {'id': f'{source.stem}-txt-v1-u{n:04d}-b{len(blocks)+1:05d}',
                     'text': clean, 'kind': 'reading_block', 'source_spans': group,
                     'requires_review': True}
            blocks.append(block)
            all_seen.extend((r['line'], r['char_start'], r['char_end']) for r in group)
        slug = f'unit-{n:04d}'
        jp, tp = folder / (slug + '.jsonl'), folder / (slug + '.txt')
        jp.write_text(''.join(json.dumps(b, ensure_ascii=False) + '\n' for b in blocks))
        tp.write_text('\n\n'.join(b['text'] for b in blocks) + '\n')
        unit = {'title': title, 'source_line_start': start + 1, 'source_line_end': end,
                'canonical_volume': None, 'boundary_basis': '原文件标题候选；卷号未人工校核',
                'blocks': len(blocks), 'text_file': str(tp.relative_to(ROOT)),
                'mapped_file': str(jp.relative_to(ROOT)),
                'text_sha256': reader.digest(tp), 'mapped_sha256': reader.digest(jp)}
        units.append(unit)
        mapped.extend(blocks)
    expected = [(i+1, p, min(p+1600, len(line))) for i, line in enumerate(lines)
                if line.strip() for p in range(0, len(line), 1600)]
    assert all_seen == expected, f'Lost/reordered/duplicated source text: {source}'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == checksum
    assert (folder / 'decoded-source.txt').read_bytes().decode('utf-8') == text
    if not corrected:
        assert text.encode(encoding) == raw or encoding == 'utf-8-sig'
    save(folder / 'issues.json', issues)
    result.update(candidate_headings=sum(heading(line) is not None for line in lines),
                  units=units, private_use_characters=sum(len(x.get('positions', [])) for x in issues),
                  issue_counts=dict((kind, sum(x['kind'] == kind for x in issues)) for kind in sorted({x['kind'] for x in issues})),
                  issues_file=str((folder / 'issues.json').relative_to(ROOT)),
                  checks=['strict decoding or verified correction replay', 'source byte hash unchanged', 'all nonblank mapped source spans covered in order', 'effective source non-whitespace characters unchanged'],
                  warnings=['采用已留审计的纠正副本（如存在）；剩余缺字、私用字和底本待核。', '标题候选和阅读块不代表史书完整卷目或自然段。'])
    supplement = ROOT/'resources/derived/supplements/zhoushu-volume-04/manifest.json'
    if source.stem=='12周书' and supplement.exists():
        info=json.loads(supplement.read_text())
        assert info.get('canonical_txt_sha256',info['original_txt_sha256'])==checksum
        assert reader.digest(ROOT/info['combined_file'])==info['combined_sha256']
        result.update(supplement_manifest=str(supplement.relative_to(ROOT)),
                      supplemented_reading_file=info['combined_file'],
                      supplemented_reading_sha256=info['combined_sha256'])
        result['warnings'].append('当前TXT已按用户要求替换为含卷四的UTF-8全文；原件归档，PDF补文定位见supplement_manifest。'
                                 if info.get('canonical_txt_sha256') else
                                 '本TXT缺卷四，已另存PDF补卷全文；本目录行号仍指向原TXT，补文定位见supplement_manifest。')
    save(folder / 'index.json', result)
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in BASE.iterdir() if p.suffix.lower() == '.txt')
    entries = [build(p) for p in sources]
    save(OUT / 'catalog.json', {'format_version': 'txt-readable-v1', 'files': entries})
    readme = '# 用户提供的史书TXT阅读副本\n\n优先采用经逐行审计验证的纠正副本，再整理排版。未纠正的原字保留；原件、校改日志与行号可追溯，卷目和底本待审核。\n\n'
    for entry in entries:
        source = ROOT / entry['source_file']
        if entry['status'] == 'blocked_decoding':
            readme += f'- {source.name}：含不能严格解码的字节，未生成阅读文本。\n'
        else:
            readme += f'- [{source.name}]({source.stem}/index.json)：{len(entry["units"])} 个导航单元；{entry["private_use_characters"]} 个私用字。\n'
            if entry.get('supplemented_reading_file'):
                readme += '  [周书补入卷四的全文阅读副本](../supplements/zhoushu-volume-04/combined-reading.txt)（PDF补文单独记录来源）。\n'
    (OUT / 'README.md').write_text(readme)
    print(json.dumps({'input_files': len(entries), 'prepared': sum(e['status'] != 'blocked_decoding' for e in entries),
                      'blocked': [e['source_file'] for e in entries if e['status'] == 'blocked_decoding']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
