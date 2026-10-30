"""Synthetic table fixtures: empty physical columns, source binding and no year 0."""
import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('table_review',Path(__file__).with_name('history-table-review.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class Tables(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.batch=Path(self.tmp.name).resolve()
        self.text='甲\t\t元年，乙受封。\t二年，丙继。'
        self.raw=(self.text+'\n\n').encode();(self.batch/'sources/p1').mkdir(parents=True)
        (self.batch/'sources/p1/source.txt').write_bytes(self.raw)
        M.write(self.batch/'sources/manifest.json',[dict(paragraph_id='p1',file='p1/source.txt',sha256=M.digest(self.raw))])
        M.write(self.batch/'packet.json',dict(book_key='synthetic',volume=8,paragraphs=[dict(id='p1',text=self.text)],supplementary_paragraphs=[]))
        M.write(self.batch/'curation.json',dict(items=[dict(group='events',row=dict(key='event_乙'),evidence=[dict(paragraph_id='p1')])]))
        self.review=M.template(self.batch)
        row=self.review['rows'][0];row.update(decision='verified',reason='已核表头与乙、丙各自行动',column_labels=['国','空白栏','初封','继侯'],header_basis='前一表头，空栏保留')
        self.review['items'][0].update(decision='verified',reason='初封与继承分别核',time_review='元年初封；后格是继侯，不混为同年',bindings=[dict(paragraph_id='p1',column_indices=[2],quote='元年，乙受封。')],regnal_checks=[dict(anchor_year=-1,regnal_year=2,expected_year=1,anchor_basis='合成锚点',era_column_basis='初封栏')])
    def tearDown(self):self.tmp.cleanup()
    def test_empty_cells_are_not_collapsed(self):
        self.assertEqual(self.review['rows'][0]['raw_cells'],['甲','','元年，乙受封。','二年，丙继。'])
        self.assertTrue(M.check(self.batch,self.review)['verified'])
    def test_extraction_is_not_review(self):
        with self.assertRaises(AssertionError):M.check(self.batch,M.template(self.batch))
    def test_source_packet_and_curation_changes_fail(self):
        for path in [self.batch/'sources/p1/source.txt',self.batch/'packet.json',self.batch/'curation.json']:
            old=path.read_bytes();path.write_bytes(old+b' ')
            with self.assertRaises(AssertionError):M.check(self.batch,self.review)
            path.write_bytes(old)
    def test_omitted_and_duplicate_rows_fail(self):
        for rows in [[],self.review['rows']*2]:
            value=copy.deepcopy(self.review);value['rows']=rows
            with self.assertRaises(AssertionError):M.check(self.batch,value)
    def test_cell_shift_and_missing_header_fail(self):
        for key,value in [('raw_cells',['甲','元年，乙受封。','二年，丙继。']),('column_labels',['国','初封','继侯']),('header_basis','')]:
            r=copy.deepcopy(self.review);r['rows'][0][key]=value
            with self.assertRaises(AssertionError):M.check(self.batch,r)
    def test_missing_or_duplicate_items_fail(self):
        for items in [[],self.review['items']*2]:
            value=copy.deepcopy(self.review);value['items']=items
            with self.assertRaises((AssertionError,KeyError)):M.check(self.batch,value)
    def test_wrong_column_and_absent_quote_fail(self):
        for changes in [dict(column_indices=[-1]),dict(column_indices=[4]),dict(column_indices=[3]),dict(quote='从未出现')]:
            r=copy.deepcopy(self.review);r['items'][0]['bindings'][0].update(changes)
            with self.assertRaises(AssertionError):M.check(self.batch,r)
    def test_missing_evidence_binding_fails(self):
        self.review['items'][0]['bindings']=[]
        with self.assertRaises(AssertionError):M.check(self.batch,self.review)
    def test_cross_cell_quote_requires_reason(self):
        b=self.review['items'][0]['bindings'][0];b.update(column_indices=[2,3],quote='元年，乙受封。\t二年，丙继。')
        with self.assertRaises(AssertionError):M.check(self.batch,self.review)
        b['cross_cell_reason']='两次行动分别跨两栏引用，时间并未合并';self.assertTrue(M.check(self.batch,self.review)['verified'])
    def test_wrong_regnal_arithmetic_and_missing_anchor_fail(self):
        for changes in [dict(expected_year=0),dict(expected_year=2),dict(regnal_year=0),dict(anchor_basis='')]:
            r=copy.deepcopy(self.review);r['items'][0]['regnal_checks'][0].update(changes)
            with self.assertRaises(AssertionError):M.check(self.batch,r)
    def test_year_zero_is_skipped_both_directions(self):
        self.assertEqual(M.advance_year(-206,11),-195);self.assertEqual(M.advance_year(-1,1),1);self.assertEqual(M.advance_year(1,-1),-1)
        with self.assertRaises(AssertionError):M.advance_year(0,1)
    def test_corrected_needs_independent_revision(self):
        for target in [self.review['rows'][0],self.review['items'][0]]:
            target['decision']='corrected'
            with self.assertRaises(AssertionError):M.check(self.batch,self.review)
            target['revisions']=['content/revisions/synthetic/plan.json'];self.assertTrue(M.check(self.batch,self.review)['verified'])
    def test_deferred_is_reported_without_becoming_truth(self):
        self.review['items'][0].update(decision='deferred',reason='两书记载不同，暂缓规范关系')
        result=M.check(self.batch,self.review);self.assertTrue(result['structural_only']);self.assertFalse(result['ready_to_publish']);self.assertEqual(result['deferred_items'],['event_乙'])

if __name__=='__main__':unittest.main()
