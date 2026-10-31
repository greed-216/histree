"""Bounded identity collision queries preserve roles and directed relationship endpoints."""
import unittest
from history_identity import matching_edges


class Store:
    def __init__(self, existing=()):self.existing=list(existing);self.calls=[]
    def read(self,table,where,params,selection,order,limit,offset):
        self.calls.append((table,where,params,selection,limit,offset))
        columns=selection.split(',')[1:];wanted={tuple(params[i:i+3]) for i in range(0,len(params),3)}
        return [r for r in self.existing if tuple(r[c] for c in columns) in wanted][:limit]


class Edges(unittest.TestCase):
    def test_large_global_table_needs_only_selected_endpoint_batches(self):
        current=[dict(id=str(i),person_id='p'+str(i),event_id='e',role='参与') for i in range(151)]
        existing=[dict(r,id='old-'+r['id']) for r in current]
        store=Store(existing)
        self.assertEqual(len(matching_edges(store,'person_event',current)),151)
        self.assertEqual([len(c[2]) for c in store.calls],[225,225,3])
        self.assertTrue(all(c[4:]==(1000,0) for c in store.calls))
        self.assertTrue(all(' IN ' not in c[1] and ' OR ' in c[1] for c in store.calls[:2]))

    def test_role_and_direction_are_part_of_collision_identity(self):
        old=dict(id='old',person_a='father',person_b='son',relation_type='父亲')
        store=Store([old])
        self.assertEqual(matching_edges(store,'person_relationship',[old]),[old])
        self.assertEqual(matching_edges(store,'person_relationship',[dict(old,person_a='son',person_b='father')]),[])
        self.assertEqual(matching_edges(store,'person_relationship',[dict(old,relation_type='老师')]),[])

    def test_values_stay_bound_and_empty_selection_does_not_scan(self):
        store=Store();self.assertEqual(matching_edges(store,'person_event',[]),[]);self.assertEqual(store.calls,[])
        text="role' OR 1=1 --"
        matching_edges(store,'person_event',[dict(person_id='p',event_id='e',role=text)])
        self.assertNotIn(text,store.calls[0][1]);self.assertIn(text,store.calls[0][2])
        with self.assertRaises(ValueError):matching_edges(store,'person',[])

    def test_saturated_result_fails_instead_of_hiding_duplicates(self):
        row=dict(person_id='p',event_id='e',role='参与')
        store=Store([dict(row,id=str(i)) for i in range(1000)])
        with self.assertRaisesRegex(ValueError,'Too many'):matching_edges(store,'person_event',[row])


if __name__=='__main__':unittest.main()
