"""Validate the narrow exception for an audited, hidden merged-person record."""
import uuid
import hashlib,json
from pathlib import Path
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

def audited_hidden_edge(root,store,table,old,canonical_id):
    """Exempt only an unchanged, claim-free archived edge from a verified merge."""
    fields={'person_event':('person_id','event_id','role'),
            'person_relationship':('person_a','person_b','relation_type')}
    if table not in fields or old['id']==canonical_id:return False
    full=store.read(table,'r.id=%s',[old['id']],'*','r.id',2,0)
    if len(full)!=1 or full[0].get('status')!='draft' or any(full[0].get(k)!=v for k,v in old.items()):return False
    shadow=full[0];targets=[];root=Path(root).resolve();folder=root/'content/revisions'
    for path in sorted(folder.glob('*/plan.json')):
        receiptpath=path.with_name('publication-mysql.json')
        if not path.resolve().is_relative_to(folder) or not receiptpath.exists() or not receiptpath.resolve().is_relative_to(folder):continue
        raw=path.read_bytes();plan=json.loads(raw);receipt=json.loads(receiptpath.read_bytes())
        if plan.get('kind')!='reviewed_history_correction' or not (receipt.get('verified') is True and receipt.get('anonymous_readback_verified') is True):continue
        if receipt.get('plan_sha256')!=hashlib.sha256(raw).hexdigest() or plan.get('target_fingerprint')!=store.target_fingerprint or receipt.get('target_fingerprint')!=store.target_fingerprint:continue
        changes=[u for u in plan.get('updates',[]) if u.get('table')==table and u.get('id')==old['id'] and u.get('after',{}).get('status')=='draft']
        if len(changes)!=1:continue
        u=changes[0]
        if u.get('full_before',{}).get('id')!=u['id'] or any(u['full_before'].get(k)!=v for k,v in u.get('before',{}).items()):continue
        if u['full_before'].get(fields[table][-1])!=shadow[fields[table][-1]]:continue
        after=[r['full_after'] for r in receipt.get('after_rows',[]) if r.get('table')==table and r.get('full_after',{}).get('id')==old['id']]
        if after!=[shadow] or dict(u['full_before'],**u['after'])!=shadow:continue
        moved_updates=[v for v in plan.get('updates',[]) if v.get('table')=='fact_claim' and v.get('full_before',{}).get('subject_table')==table and v.get('before',{}).get('subject_id')==old['id'] and 'subject_id' in v.get('after',{})]
        if any(v['full_before'].get('id')!=v['id'] or
               any(v['full_before'].get(k)!=value for k,value in v.get('before',{}).items()) or
               (v['full_before'].get('subject_table'),v['full_before'].get('subject_id'))!=(table,old['id']) or
               dict(v['full_before'],**v['after']).get('subject_table')!=table for v in moved_updates):continue
        moved={v['after']['subject_id'] for v in moved_updates}
        if len(moved)!=1:continue
        if not all([r['full_after'] for r in receipt.get('after_rows',[]) if r.get('table')=='fact_claim' and r.get('full_after',{}).get('id')==v['id']]==[dict(v['full_before'],**v['after'])] for v in moved_updates):continue
        target=next(iter(moved));protected=[]
        protected.extend(r['full_after'] for r in receipt.get('after_rows',[]) if r.get('table')==table and r.get('full_after',{}).get('id')==target)
        protected.extend(r['full_before'] for r in plan.get('protected_rows',[]) if r.get('table')==table and r.get('full_before',{}).get('id')==target)
        unique=[]
        for row in protected:
            if row not in unique:unique.append(row)
        if len(unique)>1 or unique and (unique[0].get('status')!='published' or any(unique[0].get(k)!=shadow[k] for k in fields[table])):continue
        moved_ids=sorted({v['id'] for v in moved_updates})
        if len(moved_ids)>=1000:continue
        claims=store.read('fact_claim','r.id IN ('+','.join('%s' for _ in moved_ids)+')',moved_ids,'id,subject_table,subject_id','r.id',1000,0)
        if {r['id'] for r in claims}!=set(moved_ids) or any((r['subject_table'],r['subject_id'])!=(table,target) for r in claims):continue
        # Older receipts did not snapshot the canonical prose. The verified
        # shadow after-row plus exact claim transfer still bind its ID, endpoints
        # and role. Never invent a historical full-row guard for those receipts.
        targets.append((target,unique[0] if unique else None))
    if not targets or {t for t,_ in targets}!={canonical_id}:return False
    canonical=store.read(table,'r.id=%s',[canonical_id],'*','r.id',2,0)
    if len(canonical)!=1 or canonical[0].get('status')!='published' or any(canonical[0].get(k)!=shadow[k] for k in fields[table]) or any(row is not None and canonical[0]!=row for _,row in targets):return False
    endpoints=[('person',shadow['person_a']),('person',shadow['person_b'])] if table=='person_relationship' else [('person',shadow['person_id']),('event',shadow['event_id'])]
    for kind,ident in endpoints:
        entity=store.read(kind,'r.id=%s',[ident],'id,status','r.id',2,0)
        if len(entity)!=1 or entity[0]['status']!='published':return False
    remaining=store.read('fact_claim','r.subject_table=%s AND r.subject_id=%s',[table,old['id']],'id','r.id',1,0)
    return not remaining

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
