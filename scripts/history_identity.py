"""Validate the narrow exception for an audited, hidden merged-person record."""
import uuid
NAMESPACE=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
def matching_edges(store,table,rows):
    """Query only exact candidate endpoints/roles; never scan the global edge table."""
    fields={'person_event':('person_id','event_id','role'),
            'person_relationship':('person_a','person_b','relation_type')}
    if table not in fields:raise ValueError('Unsupported identity edge table')
    columns=fields[table];result={}
    values=list(dict.fromkeys(tuple(row[c] for c in columns) for row in rows))
    for offset in range(0,len(values),75):
        chunk=values[offset:offset+75]
        where=' OR '.join('('+' AND '.join('r.`'+c+'`=%s' for c in columns)+')' for _ in chunk)
        found=store.read(table,where,[v for row in chunk for v in row],
                         'id,'+','.join(columns),'r.id',1000,0)
        if len(found)==1000:raise ValueError('Too many matching identity edges; resolve duplicates before publishing')
        result.update({row['id']:row for row in found})
    return list(result.values())

def merged_identity_target(plan,audit,people):
    if not (audit.get('verified') and audit.get('anonymous_readback_verified')):
        return None
    if not plan.get('canonical_key') or not plan.get('duplicate_key'):
        return None
    canonical=str(uuid.uuid5(NAMESPACE,plan['canonical_key']))
    duplicate=str(uuid.uuid5(NAMESPACE,plan['duplicate_key']))
    if canonical==duplicate or audit.get('canonical_person_id')!=canonical or audit.get('hidden_duplicate_person_id')!=duplicate:
        raise ValueError('Merge audit IDs do not match its stable keys')
    if canonical not in people or duplicate not in people:
        raise ValueError('Merge person missing')
    if people[canonical]['status']!='published' or people[duplicate]['status']!='draft':
        raise ValueError('Merge must have a published canonical person and hidden duplicate')
    return duplicate,canonical
