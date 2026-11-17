"""Check complete table coverage, year continuity, inherited cells and source hashes."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ming_layout',ROOT/'scripts/build-mingshi-reading-layout.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class MingLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data,cls.audit=M.build()
    def test_source_bound_complete_layout(self):
        self.assertEqual(self.data,json.loads(M.OUTPUT.read_text()))
        self.assertEqual(self.audit,json.loads(M.AUDIT.read_text()))
        self.assertEqual(len(self.data['paragraphs']),549)
        self.assertEqual(sorted((t['columns'],len(t['rows'])) for t in self.data['tables'].values()),[(2,512),(5,37)])
    def test_blank_and_merged_cells_preserve_office_positions(self):
        row=self.data['paragraphs']['mingshi-2f603db3d81e-p018062']
        cells=self.data['tables'][row['table_id']]['rows'][row['row_index']]
        self.assertEqual([c[0] for c in cells],[2,4])
        self.assertEqual(row['calendar_year'],1368)
        self.assertEqual(row['context_cells'][0]['paragraph_id'],'mingshi-2f603db3d81e-p018057')
    def test_dual_era_and_same_year_restoration(self):
        rows=self.data['paragraphs']
        self.assertEqual(rows['mingshi-2f603db3d81e-p018094']['calendar_year'],1402)
        headings=[r for r in self.audit['rows'] if r.get('year_context') and '改天順元年' in r['year_context']['source_heading']]
        self.assertTrue(headings)
        self.assertTrue(all(r['year_context']['year']==1457 for r in headings))
        years={r['year_context']['year'] for r in self.audit['rows'] if r['year_context']}
        self.assertEqual(years,set(range(1368,1381))|set(range(1402,1522)))
    def test_ganzhi_discrepancies_are_preserved_and_flagged(self):
        self.assertEqual([(r['source'],r['expected'],r['year']) for r in self.audit['issues']],[('己末','己未',1379),('乙酉','己酉',1489)])
    def test_every_inherited_cell_is_bound_to_its_original(self):
        for row in self.data['paragraphs'].values():
            for cell in row.get('context_cells',[]):
                owner=self.data['paragraphs'][cell['paragraph_id']]
                self.assertEqual(owner['table_id'],row['table_id'])
                self.assertLess(owner['row_index'],row['row_index'])
                self.assertTrue(any(a==cell['start'] and b==cell['end'] for _,a,b in owner['fragments']))
                self.assertGreater(cell['rowspan'],0)


if __name__=='__main__':unittest.main()
