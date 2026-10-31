"""Source-level regression: layout never changes ancient text or shifts column identities."""
import copy
import gzip
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile
from build_shiji_layout_loader import load_layout_builder

M=load_layout_builder();ROOT=M.ROOT


class ReadingLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=M.build();cls.committed=json.loads(M.OUTPUT.read_text())
        cls.raw=(ROOT/'resources/originals/twenty-four-histories/01史记-EPUB全文.txt').read_text()
        with gzip.open(ROOT/'resources/derived/history-library/shiji/paragraphs.jsonl.gz','rt',encoding='utf-8') as f:cls.ps={p['id']:p for p in map(json.loads,f)}
    def paragraph(self,suffix):return self.data['paragraphs']['shiji-174f8dfa444c-'+suffix]
    def test_all_ten_tables_and_130_named_chapters_are_bound(self):
        self.assertEqual(self.data,self.committed)
        self.assertEqual(len(self.data['chapters']),130);self.assertEqual(len(self.data['paragraphs']),1620)
        self.assertEqual({self.ps[p]['volume_candidate'] for p in self.data['paragraphs']},set(range(13,23)))
        self.assertEqual([(d['start_volume'],d['end_volume']) for d in self.data['divisions']],[(1,12),(13,22),(23,30),(31,60),(61,130)])
        titles={c['volume']:c['title'] for c in self.data['chapters']}
        self.assertEqual(titles[110],'匈奴列傳');self.assertEqual(titles[126],'滑稽列傳');self.assertEqual(titles[13],'三代世表')
    def test_opt_in_capture_is_byte_for_byte_equivalent_to_existing_conversion(self):
        with zipfile.ZipFile(ROOT/'resources/originals/twenty-four-histories/backup/史記.epub') as z:
            for member in sorted({t['epub_member'] for t in self.data['tables'].values()}):
                raw=z.read(member);old=M.EPUB.extract(raw);new=M.EPUB.extract(raw,capture_layout=True)
                self.assertEqual(old[0],new[0]);self.assertEqual(old[2:],new[2:])
                self.assertEqual(old[1],[{k:v for k,v in row.items() if k!='cell_fragments'} for row in new[1]])
    def test_missing_leading_empty_cells_do_not_move_a_month_to_column_zero(self):
        row=self.paragraph('p001800');table=self.data['tables'][row['table_id']]
        self.assertEqual(table['rows'][row['row_index']][row['fragments'][0][0]][0],2)
    def test_split_epub_row_keeps_its_distinct_paragraphs_and_cell_positions(self):
        a=self.paragraph('p001413');b=self.paragraph('p001422');self.assertEqual((a['table_id'],a['row_index']),(b['table_id'],b['row_index']))
        self.assertEqual(b['fragments'][0][0],15)
    def test_spans_and_codepoint_offsets_cover_every_body_character(self):
        found_span=False;found_rare=False
        for pid,row in self.data['paragraphs'].items():
            p=self.ps[pid];source=self.raw[p['locator']['char_start']:p['locator']['char_end']]
            self.assertEqual(M.sha(source.encode()),row['content_sha256']);covered=set();cells=self.data['tables'][row['table_id']]['rows'][row['row_index']]
            for cell,start,end in row['fragments']:
                self.assertTrue(0<=start<end<=len(source));self.assertLess(cell,len(cells));covered.update(range(start,end))
            self.assertTrue(all(i in covered or c.isspace() for i,c in enumerate(source)))
            found_span|=any(c[1]>1 for c in cells);found_rare|=any(ord(c)>0xffff for c in source)
        self.assertTrue(found_span);self.assertTrue(found_rare)
    def test_grid_preserves_rowspan_and_rejects_overlaps(self):
        trs=[ET.fromstring('<tr><td rowspan="2">甲</td><td>乙</td></tr>'),ET.fromstring('<tr><td>丙</td></tr>')]
        rows,_,width=M.grid([('r'+str(i),r) for i,r in enumerate(trs)]);self.assertEqual(width,2);self.assertEqual(rows[1][0][0],1)
        trs[1][0].set('colspan','2');trs[0][0].set('rowspan','3')
        with self.assertRaisesRegex(AssertionError,'span'):M.grid([('r'+str(i),r) for i,r in enumerate(trs)])


if __name__=='__main__':unittest.main()
