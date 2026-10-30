# coding: utf-8
"""Forward guards using portable synthetic fixtures, no real DB or network.

The actual pipeline/StageRunner, source exporter, canonical-source selector and
publisher entrypoint run here. Existing fixtures replace DB/HTTP/engine writes;
these tests are not native MySQL or historical-accuracy acceptance. No production
credential, original ingestion batch, fixed machine path or skipped assertion is
used. Run directly with Python's standard-library unittest runner.
"""
import copy
import gzip
import importlib.util
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import types
import unittest
from unittest.mock import patch
import uuid

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_fixture(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PIPELINE = load_fixture('forward_pipeline_fixture', 'test-history-ingest.py')
WORKBENCH = load_fixture('forward_workbench_fixture', 'test-history-workbench-portable.py')
REUSE = load_fixture('forward_reuse_fixture', 'test-reuse-history-sources.py')


class ForwardGuards(unittest.TestCase):
    def fixture(self, fixture_class, **attributes):
        fixture = fixture_class()
        for key, value in attributes.items():
            setattr(fixture, key, value)
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        return fixture

    def test_unpublished_sibling_blocks_before_mysql_preflight_or_freeze(self):
        fixture = self.fixture(PIPELINE.Pipeline)
        fixture.extra_batch = True
        with self.assertRaisesRegex(AssertionError, 'complete-volume|Multiple batches'):
            fixture.ready()
        self.assertEqual(fixture.calls['mysql-preflight'], 0)
        self.assertEqual(fixture.calls['mysql-publish'], 0)
        self.assertFalse((fixture.batch / '.workflow/freeze.json').exists())
        self.assertEqual(fixture.other.read_bytes(), fixture.other_before)

    def test_actual_target_and_api_changes_block_before_publication(self):
        fixture = self.fixture(PIPELINE.Pipeline)
        fixture.ready()
        fixture.args.apply = True
        fixture.target_fingerprint = 'different-synthetic-target'
        with self.assertRaisesRegex(AssertionError, 'target database'):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        fixture.target_fingerprint = 'offline-target'
        fixture.args.api = 'https://different-offline.invalid/api/v1'
        with self.assertRaisesRegex(AssertionError, 'public API'):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        self.assertEqual(fixture.calls['mysql-publish'], 0)
        self.assertFalse((fixture.batch / 'publication-mysql.json').exists())

    def test_period_data_invalidates_retry_cache_and_then_frozen_publish(self):
        fixture = self.fixture(PIPELINE.Pipeline)
        fixture.fail_once.add('time-review')
        with self.assertRaises(PIPELINE.P.StageExecutionError):
            fixture.ready()
        scroll = fixture.root / 'apps/web/src/data/history-scroll.json'
        value = fixture.read(scroll)
        value['periods'][0]['to_year'] = 201
        fixture.write(scroll, value)
        fixture.ready()
        self.assertEqual(fixture.calls['editorial'], 2)
        fixture.args.apply = True
        scroll.write_bytes(scroll.read_bytes() + b' ')
        with self.assertRaisesRegex(AssertionError, 'period data'):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        self.assertEqual(fixture.calls['mysql-publish'], 0)

    def test_interrupted_sidecars_reject_other_target_and_resume_original(self):
        fixture = self.fixture(PIPELINE.Pipeline)
        fixture.ready()
        fixture.args.apply = True
        fixture.fail_once.add('sidecars-apply')
        with self.assertRaises(PIPELINE.P.StageExecutionError), redirect_stdout(StringIO()):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        self.assertEqual(fixture.calls['mysql-publish'], 1)
        before = fixture.calls.copy()
        fixture.target_fingerprint = 'different-synthetic-target'
        with self.assertRaisesRegex(AssertionError, 'target database'):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        self.assertEqual(fixture.calls, before)
        fixture.target_fingerprint = 'offline-target'
        with redirect_stdout(StringIO()):
            PIPELINE.M.publish(fixture.args, fixture.batch)
        self.assertEqual(fixture.calls['mysql-publish'], 1)
        self.assertEqual(fixture.calls['sidecars-apply'], 2)
        self.assertTrue(fixture.read(fixture.batch / '.workflow/sidecars-receipt.json')['verified'])
        self.assertEqual(fixture.other.read_bytes(), fixture.other_before)

    def test_publisher_cli_checks_its_own_connection_before_any_request(self):
        fixture = self.fixture(PIPELINE.Pipeline)
        fixture.ready()
        coverage = fixture.read(fixture.batch / 'coverage.json')
        batch = fixture.read(fixture.batch / 'content-batch.json')
        coverage.update(primary_source_key=batch['sources'][0]['key'],
                        primary_source_keys=[row['key'] for row in batch['sources']],
                        supplements=[])
        fixture.write(fixture.batch / 'coverage.json', coverage)
        fixture.target_fingerprint = 'different-synthetic-target'
        sql_before = list(fixture.sql)
        store_class = sys.modules['mysql_content_store'].MysqlContentStore
        requests = []
        original_request = store_class.request

        def request(store, *args, **kwargs):
            requests.append((args, kwargs))
            return original_request(store, *args, **kwargs)

        argv = [str(SCRIPTS / 'publish-book-batch.py'),
                str(fixture.batch / 'content-batch.json'), '--apply',
                '--expected-target-fingerprint', 'offline-target',
                '--mysql-env', str(fixture.args.mysql_env)]
        # Validators are orthogonal to this first-connection guard. The entrypoint
        # still parses its real files/argv and instantiates the fixture's DB store.
        with patch.object(sys, 'argv', argv), \
                patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)), \
                patch.object(store_class, 'request', request), redirect_stdout(StringIO()):
            with self.assertRaisesRegex(AssertionError, 'Target differs'):
                runpy.run_path(str(SCRIPTS / 'publish-book-batch.py'), run_name='__main__')
        self.assertEqual(requests, [])
        self.assertEqual(fixture.sql, sql_before)
        self.assertFalse((fixture.batch / 'publication-mysql.json').exists())

    def test_actual_tongjian_supplement_export_uses_primary_source_namespace(self):
        fixture = self.fixture(WORKBENCH.Workbench)
        shutil.copyfile(SCRIPTS / 'search-history-library.py',
                        fixture.root / 'scripts/search-history-library.py')
        paragraph = copy.deepcopy(fixture.ps[0])
        paragraph.update(id='zizhi-tongjian-v2-p000001', book_key='zizhi-tongjian',
                         book='资治通鉴', source_version='v2', section_id='zizhi-tongjian-s1')
        locator = paragraph['locator']
        locator.update(original_file=locator['source_file'],
                       original_sha256=locator['source_sha256'])
        relative = 'resources/derived/history-library/zizhi-tongjian/paragraphs.jsonl.gz'
        path = fixture.root / relative
        path.parent.mkdir(parents=True)
        with gzip.open(path, 'wt', encoding='utf-8') as stream:
            stream.write(json.dumps(paragraph, ensure_ascii=False) + '\n')
        catalog = fixture.read(fixture.catalog)
        catalog['books'].append(dict(book_key='zizhi-tongjian', book='资治通鉴',
                                     source_version='v2', paragraph_file=relative))
        fixture.write(fixture.catalog, catalog)
        other_progress = fixture.root / 'content/books/zizhi-tongjian/progress.json'
        fixture.write(other_progress, dict(book_key='zizhi-tongjian', next_paragraph='unchanged'))
        other_before = other_progress.read_bytes()
        primary_cursor = fixture.read(fixture.batch / 'packet.json')['next_paragraph']
        args = types.SimpleNamespace(directory=fixture.batch, book='zizhi-tongjian',
                                     id=paragraph['id'],
                                     title='资治通鉴·卷1·合成本纪·' + paragraph['id'])
        with patch.object(WORKBENCH.M.subprocess, 'check_output', return_value='c' * 40), \
                redirect_stdout(StringIO()):
            WORKBENCH.M.add_supplement(args)
        manifest = fixture.read(fixture.batch / 'sources/manifest.json')[-1]
        expected = 'tongjian-' + paragraph['id']
        self.assertEqual(manifest['key'], expected)
        self.assertEqual(manifest['key'], WORKBENCH.M.source_key('zizhi-tongjian', paragraph['id']))
        raw = (fixture.batch / 'sources' / manifest['file']).read_bytes()
        self.assertEqual(WORKBENCH.M.sha(raw), locator['raw_excerpt_sha256'])
        self.assertEqual(other_progress.read_bytes(), other_before)
        self.assertEqual(fixture.read(fixture.batch / 'packet.json')['next_paragraph'], primary_cursor)

    def test_tongjian_canonical_source_is_reused_without_check_writes(self):
        fixture = self.fixture(REUSE.Tests, book_key='zizhi-tongjian', book='资治通鉴')
        key = WORKBENCH.M.source_key('zizhi-tongjian', fixture.pid)
        batch = fixture.read(fixture.old / 'content-batch.json')
        batch['sources'][0]['key'] = key
        fixture.write(fixture.old / 'content-batch.json', batch)
        old_manifest = fixture.read(fixture.old / 'sources/manifest.json')
        old_manifest[0]['key'] = key
        fixture.write(fixture.old / 'sources/manifest.json', old_manifest)
        source_id = str(uuid.uuid5(uuid.NAMESPACE_URL, key))
        fixture.write(fixture.old / 'sql/key-map.json', {key: source_id})
        fixture.refresh_receipt()
        current = fixture.read(fixture.cur / 'sources/manifest.json')
        current[0]['key'] = key
        fixture.write(fixture.cur / 'sources/manifest.json', current)
        current_before = (fixture.cur / 'sources/manifest.json').read_bytes()
        old_before = (fixture.old / 'sources/manifest.json').read_bytes()
        plan, _, proposed = REUSE.M.prepare(fixture.root, fixture.cur)
        self.assertEqual(len(plan['changes']), 1)
        self.assertEqual(proposed[0]['key'], key)
        self.assertNotIn(key, plan['new_source_keys_unchanged'])
        self.assertEqual(proposed[0]['url'], batch['sources'][0]['url'])
        self.assertEqual(proposed[0]['reviewed_citation'], batch['sources'][0]['note'])
        self.assertEqual(proposed[0]['canonical_source_reuse']['canonical_source_id'], source_id)
        self.assertEqual((fixture.cur / 'sources/manifest.json').read_bytes(), current_before)
        self.assertEqual((fixture.old / 'sources/manifest.json').read_bytes(), old_before)


if __name__ == '__main__':
    unittest.main()
