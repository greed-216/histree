"""Validate the narrow exception for an audited, hidden merged-person record."""
import uuid
NAMESPACE=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
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
