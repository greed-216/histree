"""Extract immutable table cells and check an authored, source-bound review.

No name/date inference, database access or source edits. Empty tab cells remain
in place. A draft review is deliberately incomplete; a human supplies column
meanings, identity/time/relation decisions and any revision references.
"""
import argparse
import hashlib
import json
from pathlib import Path

def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def advance_year(anchor,offset):
    assert type(anchor) is int and anchor and type(offset) is int
    astronomical=(anchor if anchor>0 else anchor+1)+offset
    return astronomical if astronomical>0 else astronomical-1

def bundle(batch):
    batch=batch.resolve();packet=read(batch/'packet.json');curation=read(batch/'curation.json')
    manifest={m['paragraph_id']:m for m in read(batch/'sources/manifest.json')}
    records={p['id']:p for p in packet['paragraphs']+packet.get('supplementary_paragraphs',[])}
    assert len(records)==len(packet['paragraphs'])+len(packet.get('supplementary_paragraphs',[]))
    rows=[]
    for p in records.values():
        m=manifest[p['id']];path=(batch/'sources'/m['file']).resolve()
        assert batch in path.parents and not path.is_symlink()
        raw=path.read_bytes();assert digest(raw)==m['sha256']
        # Some exports include terminal line endings; keep snapshot and text hashes separately.
        text=raw.decode('utf-8-sig')  # Raw snapshot, never normalized heading/rendered packet text
        rows.append(dict(paragraph_id=p['id'],primary=p['id'] in {r['id'] for r in packet['paragraphs']},source_sha256=m['sha256'],text_sha256=digest(text.encode()),raw_cells=text.split('\t'),raw_text=text))
    identity=[(i['group'],i['row']['key']) for i in curation['items']]
    assert len(set(identity))==len(identity)
    return packet,curation,rows

def template(batch):
    p,c,rows=bundle(batch)
    return dict(format_version=1,book_key=p['book_key'],volume=p['volume'],packet_sha256=digest((batch/'packet.json').read_bytes()),curation_sha256=digest((batch/'curation.json').read_bytes()),rows=[dict(r,decision=None,reason='',column_labels=None) for r in rows],items=[dict(group=i['group'],key=i['row']['key'],decision=None,reason='',bindings=[],identity_review='',time_review='',relationship_review='',revisions=[]) for i in c['items']])

def check(batch,review):
    expected=template(batch);p,c,rows=bundle(batch)
    for field in ('format_version','book_key','volume','packet_sha256','curation_sha256'):
        assert review[field]==expected[field], 'Review binding changed: '+field
    assert len(review['rows'])==len(rows)
    byid={r['paragraph_id']:r for r in review['rows']}
    assert len(byid)==len(rows) and set(byid)=={r['paragraph_id'] for r in rows}
    decisions=('verified','deferred','corrected')
    for row in rows:
        authored=byid[row['paragraph_id']]
        for field in row:assert authored[field]==row[field], 'Source/cell position changed: '+row['paragraph_id']
        assert authored['decision'] in decisions and authored['reason'].strip(), 'Unreviewed source row'
        if '\t' in row['raw_text']:
            labels=authored['column_labels']
            assert isinstance(labels,list) and len(labels)==len(row['raw_cells']), 'Every physical cell needs its reviewed column meaning'
            assert all(isinstance(x,str) and x.strip() for x in labels), 'Empty cell still needs an explicit column meaning'
            assert authored.get('header_basis','').strip(), 'Table row needs a reviewed header/context basis'
        if authored['decision']=='corrected':assert authored.get('revisions'), 'Corrected row needs independent revision reference'
    items={(r['group'],r['key']):r for r in review['items']}
    assert len(items)==len(review['items'])==len(c['items'])
    for item in c['items']:
        authored=items[(item['group'],item['row']['key'])]
        assert authored['decision'] in decisions and authored['reason'].strip(), 'Unreviewed fact item'
        field={'people':'identity_review','events':'time_review','person_events':'identity_review','person_relationships':'relationship_review'}[item['group']]
        assert authored[field].strip(), 'Missing substantive review: '+field
        evidence_ids={e['paragraph_id'] for e in item['evidence']}
        assert authored['bindings'] and {b['paragraph_id'] for b in authored['bindings']}==evidence_ids, 'Review must cover every cited paragraph'
        for binding in authored['bindings']:
            raw=byid[binding['paragraph_id']];indices=binding['column_indices'];quote=binding['quote']
            assert isinstance(indices,list) and indices and len(set(indices))==len(indices)
            assert all(type(n) is int and 0<=n<len(raw['raw_cells']) for n in indices), 'Invalid physical column'
            assert quote and quote in raw['raw_text'], 'Review quote absent from unchanged source'
            assert any(quote in raw['raw_cells'][n] for n in indices) or binding.get('cross_cell_reason','').strip(), 'Quote spans cells without an explicit review reason'
        for dating in authored.get('regnal_checks',[]):
            assert dating.get('anchor_basis','').strip() and dating.get('era_column_basis','').strip()
            assert type(dating['regnal_year']) is int and dating['regnal_year']>=1
            assert advance_year(dating['anchor_year'],dating['regnal_year']-1)==dating['expected_year'], 'Regnal conversion mismatch (no year zero)'
        if authored['decision']=='corrected':assert authored['revisions'], 'Corrected item needs independent revision reference'
    deferred=[r['key'] for r in review['items'] if r['decision']=='deferred']
    return dict(verified=True,structural_only=True,ready_to_publish=not deferred,deferred_items=deferred,book_key=p['book_key'],volume=p['volume'],rows=len(rows),physical_cells=sum(len(r['raw_cells']) for r in rows),items=len(items),review_sha256=digest(json.dumps(review,ensure_ascii=False,sort_keys=True).encode()),note='Checks immutable source/cell bindings and authored coverage, not historical truth. Deferred facts require separate publication isolation.')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['extract','check']);ap.add_argument('batch',type=Path);ap.add_argument('--review',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--require-publishable',action='store_true');a=ap.parse_args();batch=a.batch.resolve()
    if a.command=='extract':
        assert not a.output.exists(),'Do not replace an authored review'
        result=template(batch)
    else:
        assert a.review and a.review.resolve()!=a.output.resolve()
        result=check(batch,read(a.review))
    write(a.output,result)
    if a.require_publishable:assert result.get('ready_to_publish'),'Deferred fact items must be isolated before publication'
    print(a.command,result.get('verified',False),a.output)
if __name__=='__main__':main()
