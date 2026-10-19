/** Keep reading links and feedback in Histree; archive URLs remain internal metadata. */
export function sourceReadingPath(sourceId?: string | null, claimId?: string, archive?: string) {
  const params = new URLSearchParams();
  params.set('read', '1');
  if (claimId) params.set('claim', claimId);
  if (!sourceId && archive) params.set('archive', archive);
  const query = params.toString();
  return `/sources/${sourceId || 'read'}${query ? `?${query}` : ''}#original`;
}

export function sourceTitle(title: string) {
  return title.split('·').filter(part => !/^[a-z][a-z0-9-]*-p\d+$/.test(part.trim())).join(' · ');
}

export function sourceCitation(citation?: string) {
  return (citation || '').replace(/[·；，]?\s*[a-z][a-z0-9-]*-p\d+/gi, '').trim();
}
