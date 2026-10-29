// Read-only acceptance against an explicitly selected public API; no model calls.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const base = (process.argv[2] || 'https://histree.wiki/api/v1').replace(/\/$/, '');
const data = JSON.parse(await readFile(new URL('../apps/web/src/data/ancient-stories.json', import.meta.url)));
const audit = JSON.parse(await readFile(new URL('../docs/audits/ancient-stories-20261029.json', import.meta.url)));
const stories = data.chapters.flatMap((chapter) => chapter.stories);
async function get(path) {
  const response = await fetch(base + path, { signal: AbortSignal.timeout(30000) });
  assert.equal(response.status, 200, path);
  return response.json();
}
const [events, claims] = await Promise.all([
  get('/catalog/event?limit=50&ids=' + stories.map((story) => story.event_id).join(',')),
  get('/catalog/fact_claim?limit=50&ids=' + stories.map((story) => story.source.claim_id).join(',')),
]);
assert.equal(events.items.length, stories.length);
assert.equal(claims.items.length, stories.length);
for (let start = 0; start < stories.length; start += 4) {
  const results = await Promise.allSettled(stories.slice(start, start + 4).map(async (story) => {
    const event = events.items.find((row) => row.id === story.event_id);
    const claim = claims.items.find((row) => row.id === story.source.claim_id);
    const proof = audit.events.find((row) => row.event_id === story.event_id);
    assert.equal(event.status, 'published');
    assert.equal(claim.status, 'published');
    assert.equal(claim.subject_id, event.id);
    assert.equal(claim.subject_table, 'event');
    assert.equal(claim.source_id, proof.source_id);
    assert.ok(claim.note.includes(proof.quote));
    const [location, reading] = await Promise.all([
      get('/sources/' + proof.source_id + '/location'),
      get(`/library/shiji/sections/${story.source.section_id}?paragraph=${story.source.paragraph_id}`),
    ]);
    assert.deepEqual(location, { book_key: 'shiji', section_id: story.source.section_id, paragraph_id: story.source.paragraph_id });
    const paragraph = reading.paragraphs.find((row) => row.id === story.source.paragraph_id);
    assert.ok(paragraph?.content.includes(proof.quote), story.event_id + ': original text must support the displayed story');
  }));
  for (const result of results) if (result.status === 'rejected') throw result.reason;
}
for (const basis of audit.order_corroboration ?? []) {
  const reading = await get(`/library/${basis.book_key}/sections/${basis.section_id}?paragraph=${basis.paragraph_id}`);
  assert.ok(reading.paragraphs.find((row) => row.id === basis.paragraph_id)?.content.includes(basis.quote));
}
console.log(JSON.stringify({ verified: true, api: base, chapters: data.chapters.length, published_events: events.items.length, published_claims: claims.items.length, original_paragraphs: stories.length, order_corroboration: audit.order_corroboration?.length ?? 0, writes: 0, model_calls: 0 }, null, 2));
