"""Derive index rows from accepted, hash-bound source-scoped time revisions."""
import hashlib
import json
import uuid

NS = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')


def derive_time_revision_claims(root, books):
    result = {}
    for path in sorted((root / 'content/revisions').glob('*/plan.json')):
        plan = json.loads(path.read_text())
        if plan.get('kind') != 'source_scoped_time_revision':
            continue
        receipt_path = path.parent / 'publication-mysql.json'
        if not receipt_path.exists():
            continue
        receipt = json.loads(receipt_path.read_text())
        if not receipt.get('verified'):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert receipt['plan_sha256'] == digest, 'Time revision plan changed'
        assert receipt['target_fingerprint'] == plan['target_fingerprint']
        assert receipt['anonymous_readback_verified'] is True
        assert receipt['inserts']['fact_claim'] == len(plan['new_claims'])
        keys = plan['key_map']
        for row in plan['new_claims']:
            ck, sk, subject = [keys[row[k]] for k in ['id', 'source_id', 'subject_id']]
            for key, value in [(ck, row['id']), (sk, row['source_id']), (subject, row['subject_id'])]:
                assert str(uuid.uuid5(NS, key)) == value, 'Revision stable UUID differs'
            matches = [book for book, (_, prefixes) in books.items() if sk.startswith(prefixes)]
            assert len(matches) == 1, 'Time revision source book is ambiguous'
            assert row['status'] == 'published'
            book = matches[0]
            assert ck not in result.setdefault(book, {}), 'Duplicate revision claim'
            result[book][ck] = dict(claim_key=ck, source_key=sk, subject_table=row['subject_table'],
                                   subject_key=subject, citation=row['citation'], batch_files=[],
                                   revision_files=[str(path.relative_to(root))], revision_plan_sha256=digest)
    return result
