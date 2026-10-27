import copy
import fcntl
import subprocess
import sys
from unittest import mock
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2] / 'deploy/ecs/cleanup-releases.py'
spec = importlib.util.spec_from_file_location('release_cleanup', str(SOURCE))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


class FakeDocker:
    def __init__(self):
        self.rows = {}
        self.refs = []
        self.removed = []

    def images(self):
        return copy.deepcopy(self.rows)

    def containers(self):
        return copy.deepcopy(self.refs)

    def image(self, tag):
        return {'id': next(key for key, tags in self.rows.items() if tag in tags),
                'architecture': 'amd64', 'revision': tag.split(':')[1]}

    def remove(self, tags):
        key = next(key for key, values in self.rows.items() if values == tags)
        self.removed.append(key)
        del self.rows[key]


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'releases').mkdir()
        self.docker = FakeDocker()
        self.folders = []
        previous = ''
        for n in range(1, 6):
            revision = str(n) * 40
            folder = self.root / 'releases' / (revision + '-123-1')
            folder.mkdir()
            self.folders.append(folder)
            (folder / 'previous-release').write_text(previous)
            (folder / '.image').write_text('histree-api:' + revision)
            (folder / 'compose.yml').write_text('image: ${HISTREE_IMAGE:?required}')
            (folder / 'release-manifest.json').write_text(json.dumps({'revision': revision}))
            (folder / 'image.tar.gz').write_bytes(b'archive' + bytes([n]))
            sha = hashlib.sha256((folder / 'image.tar.gz').read_bytes()).hexdigest()
            (folder / 'image.tar.gz.sha256').write_text(sha + '  image.tar.gz\n')
            (folder / 'bundle.zip').write_bytes(b'zip')
            self.docker.rows['image' + str(n)] = ['histree-api:' + revision]
            previous = str(folder)
        (self.root / 'current-release').write_text(previous)
        self.docker.refs = [{'id': 'app', 'name': '/histree-api', 'image_id': 'image5', 'running': True, 'started_at': 'before'},
                            {'id': 'job', 'name': '/stopped-job', 'image_id': 'image1', 'running': False, 'started_at': 'old'}]
        self.docker.rows['mysql'] = ['mysql:8.0']
        self.docker.rows['unknown'] = ['histree-api:manual']
        (self.root / 'runtime.env').write_text('preserve')

    def test_apply_only_removes_surplus_and_keeps_metadata(self):
        value = gc.plan(self.root, self.docker)
        self.assertEqual([r['id'] for r in value['images']], ['image2'])
        self.assertEqual(len(value['archives']), 7)
        result = gc.apply(self.root, self.docker, value, lambda: None)
        self.assertEqual(result['removed_images'], 1)
        self.assertEqual(result['removed_archives'], 7)
        self.assertEqual(set(self.docker.rows), {'image1', 'image3', 'image4', 'image5', 'mysql', 'unknown'})
        for folder in self.folders:
            self.assertTrue((folder / 'release-manifest.json').exists())
            self.assertTrue((folder / 'image.tar.gz.sha256').exists())
        self.assertEqual((self.root / 'runtime.env').read_text(), 'preserve')
        self.assertEqual(json.loads(Path(result['audit']).read_text())['status'], 'complete')

    def test_dry_plan_does_not_mutate(self):
        gc.plan(self.root, self.docker)
        self.assertEqual(self.docker.removed, [])
        self.assertEqual(len(list((self.root / 'releases').glob('*/bundle.zip'))), 5)

    def test_duplicate_success_does_not_reduce_distinct_rollback_set(self):
        folder = self.root / 'releases' / ('5' * 40 + '-124-1')
        folder.mkdir()
        (folder / '.image').write_text('histree-api:' + '5' * 40)
        (folder / 'previous-release').write_text(str(self.folders[-1]))
        for name in ('image.tar.gz', 'image.tar.gz.sha256', 'compose.yml', 'release-manifest.json'):
            (folder / name).write_bytes((self.folders[-1] / name).read_bytes())
        (self.root / 'current-release').write_text(str(folder))
        value = gc.plan(self.root, self.docker)
        self.assertEqual([r['image_id'] for r in value['keep']], ['image5', 'image4', 'image3'])
        self.assertIn(str(self.folders[-1] / 'image.tar.gz'), [r['path'] for r in value['archives']])

    def test_bad_rollback_hash_aborts_before_deletion(self):
        (self.folders[-2] / 'image.tar.gz').write_bytes(b'corrupt')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            gc.plan(self.root, self.docker)
        self.assertFalse(self.docker.removed)

    def test_manifest_and_image_mismatch_abort(self):
        (self.folders[-2] / 'release-manifest.json').write_text('{"revision":"wrong"}')
        with self.assertRaisesRegex(RuntimeError, 'manifest mismatch'):
            gc.plan(self.root, self.docker)

    def test_manual_and_symlink_files_are_skipped(self):
        manual = self.root / 'releases/manual'
        manual.mkdir()
        (manual / 'image.tar.gz').write_bytes(b'keep')
        (self.folders[0] / 'bundle.zip').unlink()
        (self.folders[0] / 'bundle.zip').symlink_to(manual / 'image.tar.gz')
        value = gc.plan(self.root, self.docker)
        gc.apply(self.root, self.docker, value, lambda: None)
        self.assertEqual((manual / 'image.tar.gz').read_bytes(), b'keep')
        self.assertTrue((self.folders[0] / 'bundle.zip').is_symlink())

    def test_changed_archive_or_container_invalidates_plan(self):
        for mutation in ('archive', 'container', 'current'):
            value = gc.plan(self.root, self.docker)
            if mutation == 'archive':
                (self.folders[0] / 'bundle.zip').write_bytes(b'changed')
            elif mutation == 'container':
                self.docker.refs[1]['started_at'] = 'changed'
            else:
                (self.root / 'current-release').write_text(str(self.folders[3]))
            with self.assertRaises(RuntimeError):
                gc.apply(self.root, self.docker, value, lambda: None)
            self.assertFalse(self.docker.removed)

    def test_health_failure_prevents_mutation(self):
        def fail():
            raise RuntimeError('unhealthy')
        with self.assertRaisesRegex(RuntimeError, 'unhealthy'):
            gc.apply(self.root, self.docker, gc.plan(self.root, self.docker), fail)
        self.assertFalse(self.docker.removed)

    def test_concurrent_release_lock_blocks_cleanup(self):
        with (self.root / 'release.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run([sys.executable, str(SOURCE), '--root', str(self.root), '--apply'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'BlockingIOError', result.stderr)
        self.assertFalse((self.root / 'cleanup-audits').exists())

    def test_docker_removal_uses_only_explicit_tags_without_force(self):
        with mock.patch.object(gc.subprocess, 'check_output', return_value='removed') as command:
            gc.Docker().remove(['histree-api:' + '2' * 40])
        self.assertEqual(command.call_args[0][0], ['docker', 'image', 'rm', 'histree-api:' + '2' * 40])

    def test_partial_failure_has_durable_audit_and_keeps_app(self):
        def fail(tags):
            raise RuntimeError('busy image')
        self.docker.remove = fail
        before = self.docker.containers()
        with self.assertRaisesRegex(RuntimeError, 'busy image'):
            gc.apply(self.root, self.docker, gc.plan(self.root, self.docker), lambda: None)
        audit = json.loads(next((self.root / 'cleanup-audits').glob('*.json')).read_text())
        self.assertEqual(audit['status'], 'failed')
        self.assertFalse(audit['removed_archives'])
        self.assertEqual(self.docker.containers(), before)


if __name__ == '__main__':
    unittest.main()
