"""Exercise bounded REST filters without importing the publisher's executable CLI."""
import ast
from pathlib import Path
import unittest


class ChunkTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(Path(__file__).with_name('publish-book-batch.py').read_text())
        definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('selected_rows', 'table_rows')]
        self.calls = []
        def req(table, query, method='GET', body=None):
            ids = query.split('id=in.(', 1)[1].split(')', 1)[0].split(',')
            self.calls.append((table, ids, query, method, body))
            return [{'id': key} for key in ids]
        self.scope = {'req': req, 'rows': {'fact_claim': [{'id': str(i)} for i in range(568)]}}
        exec(compile(ast.Module(body=definitions, type_ignores=[]), '<publisher-chunks>', 'exec'), self.scope)

    def test_large_anonymous_readback_keeps_all_ids_and_source_join(self):
        result = self.scope['table_rows']('fact_claim', '&select=*,source:source_id(*)')
        self.assertEqual([r['id'] for r in result], [str(i) for i in range(568)])
        self.assertEqual([len(c[1]) for c in self.calls], [100,100,100,100,100,68])
        self.assertTrue(all(c[2].endswith('&select=*,source:source_id(*)') for c in self.calls))

    def test_patch_uses_the_same_selected_ids_only(self):
        result = self.scope['selected_rows']('person', ['p'+str(i) for i in range(201)], method='PATCH', body={'status':'published'})
        self.assertEqual(len(result), 201)
        self.assertTrue(all(c[3:] == ('PATCH', {'status':'published'}) for c in self.calls))

    def test_empty_selection_does_not_request_unfiltered_rows(self):
        self.assertEqual(self.scope['selected_rows']('event', []), [])
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
