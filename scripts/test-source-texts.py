#!/usr/bin/env python3
"""Offline source provenance and immutable import guards. No database connections."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).parent))
import source_texts as texts

URL = 'https://github.com/greed-216/histree/blob/17b5e3f2bb31476c2c8c1622897cafebde7cfa6f/content/books/zizhi-tongjian/vol-013/from-start/release-2026-10-13/part-01/sources/zizhi-tongjian-a63549944a71-p000146/source.txt'
SID = '11111111-1111-1111-1111-111111111111'


class SourceTextsTests(unittest.TestCase):
    def setUp(self):
        self.row = texts.fill_content([{'source_id': SID, 'archive_url': URL}])[0]

    def test_fixed_git_blob_preserves_original_bytes(self):
        self.assertIn('高帝与吕后共定天下', self.row['content'])
        self.assertEqual(self.row['content_sha256'], self.row['archive_blob_sha256'])
        texts.validate_rows([self.row])

    def test_mutation_is_rejected(self):
        edited = dict(self.row, content=self.row['content'] + '伪改')
        with self.assertRaises(ValueError):
            texts.validate_rows([edited])
        with self.assertRaises(ValueError):
            texts.validate_rows([self.row, copy.deepcopy(self.row)])

    def test_mutable_refs_private_paths_and_ambiguous_jsonl_are_rejected(self):
        for url in [URL.replace('17b5e3f2bb31476c2c8c1622897cafebde7cfa6f', 'main'), URL.replace('github.com', 'example.org'), URL.replace('source.txt', '../../.env'), URL.replace('source.txt', 'source.jsonl')]:
            with self.assertRaises(ValueError):
                texts.blob_spec(url)

    def test_only_claimed_sources_are_selected(self):
        sources = [{'key': 'used', 'url': URL}, {'key': 'draft', 'url': URL}]
        self.assertEqual(texts.source_rows(sources, [{'source_key': 'used'}], {'used': SID, 'draft': '22222222-2222-2222-2222-222222222222'}), [{'source_id': SID, 'archive_url': URL}])

    def test_legacy_jsonl_uses_exact_located_text_not_serialized_json(self):
        url = 'https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/twenty-four-histories/19%E6%96%B0%E4%BA%94%E4%BB%A3%E5%8F%B2.jsonl#L778'
        row = texts.fill_content([{'source_id': SID, 'archive_url': url}])[0]
        raw = texts.load_blobs([url])[url]
        self.assertEqual(row['content'], json.loads(raw.decode().splitlines()[777])['text'])
        self.assertEqual(row['archive_blob_sha256'], texts.digest(raw))

    def test_existing_different_text_stops_before_any_insert(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [texts.record_values(dict(self.row, content='changed'))]
        with self.assertRaises(ValueError):
            texts.insert_texts(connection, [self.row])
        self.assertEqual(cursor.execute.call_count, 1)
        self.assertTrue(cursor.execute.call_args[0][0].startswith('SELECT'))
        cursor.executemany.assert_not_called()

    def test_identical_text_is_reused_without_update(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [texts.record_values(self.row)]
        texts.insert_texts(connection, [self.row])
        self.assertEqual(cursor.execute.call_count, 1)
        self.assertFalse(connection.commit.called)
        cursor.executemany.assert_not_called()


if __name__ == '__main__':
    unittest.main()
