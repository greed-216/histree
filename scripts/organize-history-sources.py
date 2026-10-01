"""Keep the 25 selected EPUB-derived TXT sources at the source directory root.

Other source editions are moved intact into backup, with hash-bound aliases.
This command does not delete derived outputs or change any content batch.
"""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'resources/originals/twenty-four-histories'
BACKUP = BASE / 'backup'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = json.loads((ROOT / 'resources/derived/epub-txt/catalog.json').read_text())
    active = {Path(b['txt_file']).name for b in catalog['books']}
    assert len(active) == 25
    for book in catalog['books']:
        assert digest(ROOT / book['txt_file']) == book['txt_sha256']
    BACKUP.mkdir(exist_ok=True)
    manifest_file = BACKUP / 'manifest.json'
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {
        'format_version': 'history-source-backup-v1', 'moves': [],
        'note': '保留来源原件、旧TXT与残稿；当前目录仅25份选定TXT，不改已发布引用。'}
    aliases_file = ROOT / 'resources/catalog/source-replacements.json'
    aliases = json.loads(aliases_file.read_text())
    for item in sorted(BASE.iterdir()):
        if item.name in active or item == BACKUP:
            continue
        destination = BACKUP / item.name
        assert not destination.exists(), f'Backup collision: {destination}'
        files = [item] if item.is_file() else sorted(p for p in item.rglob('*') if p.is_file())
        moves = []
        for source in files:
            target = destination if item.is_file() else destination / source.relative_to(item)
            moves.append({'file': str(source.relative_to(ROOT)), 'backup_file': str(target.relative_to(ROOT)),
                          'sha256': digest(source), 'bytes': source.stat().st_size})
        shutil.move(str(item), str(destination))
        for move in moves:
            assert digest(ROOT / move['backup_file']) == move['sha256']
            # Existing aliases retain their logical historical filename.
            for alias in aliases['aliases']:
                if alias['backup_file'] == move['file']:
                    alias['backup_file'] = move['backup_file']
            if not any(a['file'] == move['file'] and a['sha256'] == move['sha256'] for a in aliases['aliases']):
                aliases['aliases'].append({k: move[k] for k in ('file', 'sha256', 'backup_file')})
        manifest['moves'].extend(moves)
    manifest['active_txt_files'] = sorted(active)
    for move in manifest['moves']:
        assert digest(ROOT / move['backup_file']) == move['sha256']
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    aliases_file.write_text(json.dumps(aliases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert {p.name for p in BASE.iterdir()} == active | {'backup'}
    print(json.dumps({'active_txt': len(active), 'archived_files': len(manifest['moves']),
                      'backup': str(BACKUP.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
