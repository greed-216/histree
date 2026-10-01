"""Remove explicitly superseded history-text artifacts after full validation.

Historical sources referenced by content batches are preserved and hash-checked.
Only the paths enumerated below are eligible for removal.
"""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'resources/derived'
BACKUP = ROOT / 'resources/originals/twenty-four-histories/backup'
REPORT = ROOT / 'resources/catalog/history-text-cleanup.json'
REMOVED_DIRS = ['readable', 'readable-txt', 'corrected-txt', 'coverage-review', 'history-library.previous']
OBSOLETE_SCRIPTS = ['prepare-history-txt.py', 'test-history-txt.py', 'repair-history-txt.py',
                    'test-history-txt-repairs.py', 'extract-history-repair-pdf.py',
                    'prepare-readable-history.py', 'test-readable-history.py',
                    'prepare-zhoushu-volume-04.py', 'test-zhoushu-supplement.py',
                    'replace-zhoushu-txt.py', 'prepare-jiuwudaishi-epub.py', 'prepare-beiqishu-epub.py']
OLD_CATALOGS = ['beiqishu-epub-txt.json', 'jiuwudaishi-epub-txt.json', 'history-source-coverage.json',
                'china-history-audit.json', 'twenty-four-histories-tex-audit.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    assert json.loads((BASE / 'history-library/validation.json').read_text())['status'] == 'verified'
    report = json.loads(REPORT.read_text())
    protected = dict(report['protected_files'])
    protected.update({p: h for p, h in report.get('local_unversioned_protected_files', {}).items() if (ROOT / p).exists()})
    for path, h in protected.items():
        assert sha(ROOT / path) == h, path
    aliases_file = ROOT / 'resources/catalog/source-replacements.json'
    aliases = json.loads(aliases_file.read_text())
    report.setdefault('removed', [])
    report.setdefault('archived_artifacts', [])

    def remove(path):
        if not path.exists():
            return
        files = [path] if path.is_file() else [p for p in path.rglob('*') if p.is_file()]
        assert not any(str(p.relative_to(ROOT)) in protected for p in files)
        record = {'path': str(path.relative_to(ROOT)), 'files': len(files), 'bytes': sum(p.stat().st_size for p in files)}
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        report['removed'].append(record)

    def archive(path, target):
        if not path.exists():
            return
        assert not target.exists(), target
        files = [path] if path.is_file() else [p for p in path.rglob('*') if p.is_file()]
        moves = [(p, target if path.is_file() else target / p.relative_to(path), sha(p)) for p in files]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        for source, destination, h in moves:
            assert sha(destination) == h
            for alias in aliases['aliases']:
                if alias['backup_file'] == str(source.relative_to(ROOT)):
                    alias['backup_file'] = str(destination.relative_to(ROOT))
        report['archived_artifacts'].append({'from': str(path.relative_to(ROOT)), 'to': str(target.relative_to(ROOT)), 'files': len(files)})

    # Retain the small, earlier Zhou Shu PDF collation as historical evidence.
    archive(BASE / 'supplements/zhoushu-volume-04', BACKUP / 'legacy-zhoushu-volume-04')
    for path in (BASE / 'supplements/jiuwudaishi-epub', BASE / 'supplements/beiqishu-epub'):
        remove(path)
    if (BASE / 'supplements').exists():
        remove(BASE / 'supplements')
    for name in REMOVED_DIRS:
        remove(BASE / name)
    for folder in sorted((BASE / 'epub-txt').glob('[0-9]*')):
        for name in ('sections', 'paragraphs.jsonl', 'excluded.json', 'restored-variants.json', 'epub-metadata.json'):
            remove(folder / name)
    for name in OBSOLETE_SCRIPTS:
        archive(ROOT / 'scripts' / name, BACKUP / 'legacy-processing-scripts' / name)
        for cache in (ROOT / 'scripts/__pycache__').glob(Path(name).stem + '.*.pyc'):
            remove(cache)
    for name in OLD_CATALOGS:
        archive(ROOT / 'resources/catalog' / name, BACKUP / 'legacy-metadata' / name)
    archive(ROOT / 'resources/catalog/archive', BACKUP / 'legacy-catalog-archive')
    # Aliases for deleted, unreferenced intermediate editions are now retired.
    retired = [a for a in aliases['aliases'] if not (ROOT / a['backup_file']).exists()]
    aliases['aliases'] = [a for a in aliases['aliases'] if (ROOT / a['backup_file']).exists()]
    report['retired_intermediate_aliases'] = retired
    save(aliases_file, aliases)
    for path, h in protected.items():
        assert sha(ROOT / path) == h, path
    after = []
    for name in ('epub-txt', 'history-library'):
        files = [p for p in (BASE / name).rglob('*') if p.is_file()]
        after.append({'directory': str((BASE / name).relative_to(ROOT)), 'files': len(files),
                      'bytes': sum(p.stat().st_size for p in files)})
    report.update(after=after, status='cleaned_and_protected_sources_verified',
                  validation='25份TXT规范化、26书本地索引通过；已发布批次及引用源的1459个文件哈希不变')
    save(REPORT, report)
    print(json.dumps({'deleted_bytes': sum(x['bytes'] for x in report['removed']),
                      'active_derived_bytes': sum(x['bytes'] for x in after),
                      'protected_files': len(report['protected_files'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
