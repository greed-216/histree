"""Verify reviewed seven-office positions, year carry and immutable source coverage."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ming_office_layout', ROOT / 'scripts/build-mingshi-office-reading-layout.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class MingOfficeLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = M.build()

    def row(self, n):
        return self.data['paragraphs'][f'mingshi-2f603db3d81e-p{n:06d}']

    def test_complete_reproducible_source_bound_layout(self):
        self.assertEqual(self.data, json.loads(M.OUTPUT.read_text()))
        self.assertEqual(len(self.data['paragraphs']), 1826)
        self.assertEqual(sorted((t['columns'], len(t['rows'])) for t in self.data['tables'].values()), [(2, 528), (8, 647), (8, 651)])

    def test_missing_empty_cells_do_not_shift_offices(self):
        for n, expected in [(19148, [3, 4, 5, 6, 7]), (19145, [1, 2])]:
            row = self.row(n)
            self.assertEqual([c[0] for c in self.data['tables'][row['table_id']]['rows'][row['row_index']]], expected)
        self.assertEqual(self.row(19148)['calendar_year'], 1380)
        self.assertEqual(self.row(19148)['context_cells'][0]['paragraph_id'], 'mingshi-2f603db3d81e-p019142')

    def test_all_pagination_contexts_reference_exact_earlier_fragments(self):
        for row in self.data['paragraphs'].values():
            for cell in row.get('context_cells', []):
                owner = self.data['paragraphs'][cell['paragraph_id']]
                self.assertEqual(owner['table_id'], row['table_id'])
                self.assertLess(owner['row_index'], row['row_index'])
                self.assertTrue(any(a == cell['start'] and b == cell['end'] for _, a, b in owner['fragments']))
                actual = self.data['tables'][row['table_id']]['rows'][row['row_index']]
                self.assertTrue(all(c[0] != 0 for c in actual))

    def test_dual_reign_and_last_year(self):
        for n in [18931, 20279]:
            self.assertEqual(self.row(n)['calendar_year'], 1620)
        for n in [19135, 20438]:
            self.assertEqual(self.row(n)['calendar_year'], 1644)

    def test_year_labels_preserve_source_discrepancies(self):
        self.assertIn('戌寅', self.row(18796)['calendar_note'])
        self.assertIn('己丑', self.row(19454)['calendar_note'])
        self.assertIn('原历', self.row(19148)['calendar_note'])


if __name__ == '__main__':
    unittest.main()
