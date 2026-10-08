"""Compile curated reading routes from published archives; no database writes."""
import json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
events, people, claims, sources, ids = {}, {}, {}, {}, {}
participations, relationships = {}, {}
for path in sorted((ROOT/'content').glob('**/content-batch.json')):
    if '/revisions/' in str(path): continue
    mapping = path.parent/'sql/key-map.json'
    if not mapping.exists(): continue
    batch = json.loads(path.read_text())
    ids.update(json.loads(mapping.read_text()))
    for row in batch.get('person_events', []): participations.setdefault(row['key'], row)
    for row in batch.get('person_relationships', []): relationships.setdefault(row['key'], row)
    for event in batch.get('events', []): events.setdefault(event['key'], (event, path))
    for person in batch.get('people', []): people.setdefault(person['key'], person)
    for source in batch.get('sources', []): sources[source['key']] = source
    for claim in batch.get('claims', []): claims.setdefault(claim['subject_key'], []).append(claim)
overrides = json.loads((ROOT/'content/guides/entity-overrides.json').read_text())
citation_overrides = {}
applied_revisions = []
for revision in sorted((ROOT/'content/revisions').glob('**/publication.json')):
    plan = revision.with_name('plan.json')
    if not plan.exists(): continue
    publication = json.loads(revision.read_text())
    verified = publication.get('anonymous_readback_verified') is True and publication.get('verified') is True or publication.get('status') == 'applied_anonymous_readback_verified'
    if not verified or not publication.get('plan_sha256'): continue
    assert publication['plan_sha256'] == hashlib.sha256(plan.read_bytes()).hexdigest(), f'Revision changed: {plan}'
    selected = [c for c in json.loads(plan.read_text()).get('changes',[]) if c.get('table') == 'fact_claim' and 'citation' in c.get('after',{})]
    if selected:
        applied_revisions.append(str(plan.relative_to(ROOT)))
        citation_overrides.update({c['id']: c['after']['citation'] for c in selected})
used_batches = set()
def event_record(key):
    event, path = events[key]
    event = {**event, **{k:v for k,v in overrides.get(key, {}).items() if k in ('title','description')}}
    publication = json.loads((path.parent/'publication.json').read_text())
    assert publication.get('verified') is True, f'Unverified publication: {path}'
    used_batches.add(str(path.relative_to(ROOT)))
    evidence = []
    matching = claims.get(key, [])
    for claim in matching:
        if claim['field_path'] not in ('description', 'title'): continue
        source = sources[claim['source_key']]
        if not source.get('url', '').startswith('https://github.com/'): continue
        note = claim['note']
        quote = note.split('原文：', 1)[-1].split('；核对说明：', 1)[0]
        assert quote.strip()
        evidence.append(dict(id=ids[claim['key']], sourceId=ids[source['key']], title=source['title'], quote=quote, url=source['url'], citation=citation_overrides.get(ids[claim['key']],claim['citation'])))
        if len(evidence) == 3: break
    assert evidence, f'No traceable evidence: {key}'
    return dict(key=key, id=ids[key], title=event['title'], year=event['start_year'], description=event['description'], evidence=evidence)
def compile_part(part):
    part = dict(part)
    event_keys = part.pop('event_keys')
    part['events'] = [event_record(key) for key in event_keys]
    assert all(e['year'] is None or part['years'][0] <= e['year'] <= part['years'][1] for e in part['events']), 'Selected event outside chapter dates'
    if 'person_keys' in part:
        person_keys = part.pop('person_keys')
        part['people'] = [dict(key=key,id=ids[key], name=people[key]['name']) for key in person_keys]
        nodes = [{**people[key], 'id': ids[key], 'type': 'person', 'status':'published'} for key in person_keys]
        nodes += [{**events[key][0], 'title': record['title'], 'id':ids[key], 'type':'event', 'status':'published'} for key,record in zip(event_keys,part['events'])]
        edges = []
        for key,row in participations.items():
            if row['person_key'] in person_keys and row['event_key'] in event_keys:
                edges.append(dict(id=ids[key],subject_table='person_event',source=ids[row['person_key']],target=ids[row['event_key']],type=row['role']))
        for key,row in relationships.items():
            if row['person_a_key'] in person_keys and row['person_b_key'] in person_keys:
                edges.append(dict(id=ids[key],subject_table='person_relationship',source=ids[row['person_a_key']],target=ids[row['person_b_key']],type=row['relation_type'],description=row.get('description','')))
        part['graph'] = dict(center=nodes[0],nodes=nodes,edges=edges)
        assert len({e['id'] for e in edges})==len(edges)
        assert all(e['source'] in {n['id'] for n in nodes} and e['target'] in {n['id'] for n in nodes} for e in edges)
    return part
zhou = json.loads((ROOT/'content/guides/later-zhou.json').read_text())
overview = json.loads((ROOT/'content/guides/five-dynasties.json').read_text())
zhou['chapters'] = [compile_part(c) for c in zhou['chapters']]
overview['stages'] = [compile_part(c) for c in overview['stages']]
catalog = json.loads((ROOT/'content/guides/catalog.json').read_text())
assert len({e['id'] for e in catalog})==len(catalog)
assert all(e['kind'] in ('period','topic','question','person') and e['path'].startswith('/') and not e['path'].startswith('//') for e in catalog)
data = dict(catalog=catalog, overview=overview, zhou=zhou)
target = ROOT/'apps/web/src/data/history-guides.json'
target.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
audit = dict(status='compiled_from_published_archives', scope='五代总览与950—959年后周六章导读', batches=sorted(used_batches), applied_citation_revisions=applied_revisions, generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), note='导读为编辑概括；事件、UUID和逐字引文取自发布档案。线上条目应在发布前匿名回查。')
(ROOT/'content/guides/audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(f'Compiled {len(zhou["chapters"])} chapters from {len(used_batches)} published batches')
