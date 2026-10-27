#!/usr/bin/env python3
"""Conservative ECS release retention. Python 3.6+, dry-run unless --apply."""
import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import urllib.request

RELEASE = re.compile(r'[a-f0-9]{40}-[0-9]+-[0-9]+\Z')
TAG = re.compile(r'histree-api:[a-f0-9]{40}\Z')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def regular(path):
    return path.exists() and stat.S_ISREG(path.lstat().st_mode)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(path):
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode), 'Not a regular file: ' + str(path))
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


class Docker:
    def run(self, *args):
        return subprocess.check_output(['docker'] + list(args), universal_newlines=True, timeout=120).strip()

    def containers(self):
        rows = []
        # Select only safe fields; never read runtime environment or secrets.
        fmt = '{"id":{{json .Id}},"name":{{json .Name}},"image_id":{{json .Image}},"running":{{json .State.Running}},"started_at":{{json .State.StartedAt}}}'
        for cid in self.run('ps', '-aq').splitlines():
            rows.append(json.loads(self.run('inspect', '--format', fmt, cid)))
        return sorted(rows, key=lambda row: row['id'])

    def images(self):
        rows = {}
        for line in self.run('image', 'ls', '--no-trunc', '--format', '{{json .}}').splitlines():
            row = json.loads(line)
            rows.setdefault(row['ID'], []).append(row['Repository'] + ':' + row['Tag'])
        return {key: sorted(set(tags)) for key, tags in rows.items()}

    def image(self, tag):
        fmt = '{"id":{{json .Id}},"architecture":{{json .Architecture}},"revision":{{json (index .Config.Labels "org.opencontainers.image.revision")}}}'
        return json.loads(self.run('image', 'inspect', '--format', fmt, tag))

    def remove(self, tags):
        # Never force removal, prune, or touch containers/volumes/build cache.
        self.run('image', 'rm', *tags)


def health():
    with urllib.request.urlopen('http://127.0.0.1:3000/api/v1/health', timeout=15) as response:
        row = json.load(response)
    require(row.get('status') == 'ok' and row.get('database') == 'mysql', 'MySQL health failed')


def disk(root):
    fs = os.statvfs(str(root))
    used = (fs.f_blocks - fs.f_bfree) * fs.f_frsize
    available = fs.f_bavail * fs.f_frsize
    return {'available_bytes': available, 'used_bytes': used,
            'used_percent': int(math.ceil(100 * used / (used + available)))}


def release_path(root, value):
    path = Path(value)
    require(path.parent == root / 'releases' and RELEASE.fullmatch(path.name), 'Invalid release pointer')
    require(path.is_dir() and not path.is_symlink(), 'Missing or linked release directory')
    return path


def plan(root, docker):
    require(root.is_dir() and not root.is_symlink(), 'Invalid deployment root')
    require((root / 'releases').is_dir() and not (root / 'releases').is_symlink(), 'Invalid releases root')
    current = (root / 'current-release').read_text().strip()
    kept, revisions, visited = [], set(), set()
    pointer = current
    while pointer and len(kept) < 3:
        folder = release_path(root, pointer)
        require(pointer not in visited, 'Cycle in release history')
        visited.add(pointer)
        tag = (folder / '.image').read_text().strip()
        require(TAG.fullmatch(tag) and folder.name.startswith(tag.split(':')[1] + '-'), 'Release revision mismatch')
        if tag not in revisions:
            for name in ('image.tar.gz', 'image.tar.gz.sha256', 'compose.yml', 'release-manifest.json'):
                require(regular(folder / name), 'Missing rollback file: ' + str(folder / name))
            checksum = (folder / 'image.tar.gz.sha256').read_text().split()
            require(len(checksum) == 2 and checksum[1] in ('image.tar.gz', '*image.tar.gz'), 'Invalid archive checksum record')
            require(digest(folder / 'image.tar.gz') == checksum[0], 'Rollback archive checksum mismatch')
            meta = docker.image(tag)
            require(meta['architecture'] == 'amd64' and meta['revision'] == tag.split(':')[1], 'Rollback image revision/architecture mismatch')
            require(json.loads((folder / 'release-manifest.json').read_text())['revision'] == meta['revision'], 'Rollback manifest mismatch')
            require('${HISTREE_IMAGE' in (folder / 'compose.yml').read_text(), 'Unexpected rollback compose')
            kept.append({'release': str(folder), 'tag': tag, 'image_id': meta['id'], 'archive_sha256': checksum[0]})
            revisions.add(tag)
        previous = folder / 'previous-release'
        pointer = previous.read_text().strip() if previous.exists() else ''
    # This installation has a rollback history; do not silently shrink its safety net.
    require(len(kept) == 3, 'Three distinct verified release versions required')
    containers = docker.containers()
    app = [row for row in containers if row['name'] == '/histree-api']
    require(len(app) == 1 and app[0]['running'] and app[0]['image_id'] == kept[0]['image_id'], 'Running app does not match current release')
    protected = {row['image_id'] for row in containers} | {row['image_id'] for row in kept}
    images = [{'id': key, 'tags': tags} for key, tags in sorted(docker.images().items())
              if key not in protected and tags and all(TAG.fullmatch(tag) for tag in tags)]
    kept_dirs = {row['release'] for row in kept}
    archives = []
    for folder in sorted((root / 'releases').iterdir()):
        if folder.is_symlink() or not folder.is_dir() or not RELEASE.fullmatch(folder.name):
            continue
        for name in ('image.tar.gz', 'bundle.zip'):
            path = folder / name
            if regular(path) and (str(folder) not in kept_dirs or name == 'bundle.zip'):
                archives.append({'path': str(path), 'identity': identity(path)})
    return {'current': current, 'keep': kept, 'containers': containers, 'images': images, 'archives': archives}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_audit(path, value):
    temporary = path.with_suffix('.next')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(str(temporary), 0o600)
    os.replace(str(temporary), str(path))


def apply(root, docker, value, check_health=health):
    # Freeze and recheck the entire plan, including rollback hashes, before mutation.
    require(plan(root, docker) == value, 'Cleanup plan changed')
    check_health()
    audits = root / 'cleanup-audits'
    require(not audits.is_symlink(), 'Linked audit directory')
    audits.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S%fZ')
    path = audits / ('retention-' + stamp + '-' + str(os.getpid()) + '.json')
    audit = {'status': 'in_progress', 'plan': value, 'plan_sha256': fingerprint(value),
             'before': disk(root), 'removed_images': [], 'removed_archives': []}
    write_audit(path, audit)

    def unchanged():
        require((root / 'current-release').read_text().strip() == value['current'], 'Current release changed')
        require(docker.containers() == value['containers'], 'Container state changed')

    try:
        for row in value['images']:
            unchanged()
            require(docker.images().get(row['id']) == row['tags'], 'Image tags changed')
            docker.remove(row['tags'])
            audit['removed_images'].append(row)
            write_audit(path, audit)
        for row in value['archives']:
            unchanged()
            file = Path(row['path'])
            release_path(root, str(file.parent))
            require(identity(file) == row['identity'], 'Archive changed')
            file.unlink()
            audit['removed_archives'].append(row['path'])
            write_audit(path, audit)
        unchanged()
        check_health()
        audit['after'] = disk(root)
        audit['status'] = 'complete'
        write_audit(path, audit)
    except Exception as error:
        audit['status'] = 'failed'
        audit['error'] = str(error)
        audit['after'] = disk(root)
        write_audit(path, audit)
        raise
    return {'audit': str(path), 'removed_images': len(audit['removed_images']),
            'removed_archives': len(audit['removed_archives']), 'before': audit['before'], 'after': audit['after']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='/opt/histree')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expect-plan')
    parser.add_argument('--lock-fd', type=int, help='Inherited release lock descriptor')
    args = parser.parse_args()
    root = Path(args.root).absolute()
    if args.lock_fd is None:
        lock = (root / 'release.lock').open('a')
        fd = lock.fileno()
    else:
        fd = args.lock_fd
        s = os.fstat(fd)
        target = (root / 'release.lock').stat()
        require((s.st_dev, s.st_ino) == (target.st_dev, target.st_ino), 'Incorrect inherited lock')
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    docker = Docker()
    value = plan(root, docker)
    sha = fingerprint(value)
    require(not args.expect_plan or sha == args.expect_plan, 'Expected cleanup plan changed')
    if args.apply:
        print(json.dumps(apply(root, docker, value), sort_keys=True))
    else:
        print(json.dumps({'apply': False, 'plan_sha256': sha, 'plan': value}, sort_keys=True))


if __name__ == '__main__':
    main()
