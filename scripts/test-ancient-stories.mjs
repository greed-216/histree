import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';

const read = (path) => readFile(new URL('../' + path, import.meta.url), 'utf8');
const data = JSON.parse(await read('apps/web/src/data/ancient-stories.json'));
const audit = JSON.parse(await read('docs/audits/ancient-stories-20261029.json'));
const scroll = JSON.parse(await read('apps/web/src/data/history-scroll.json'));
const ts = createRequire(new URL('../apps/web/package.json', import.meta.url))('typescript');
const source = (await read('apps/web/src/lib/ancientStories.ts')).replace(
  'import data from "../data/ancient-stories.json";', `const data=${JSON.stringify(data)};`,
);
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { ancientStoryEvents, ancientStorySource, ancientStoriesPath } = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));

assert.deepEqual(data.chapters.map((chapter) => chapter.id), scroll.ancient_chapters.map((chapter) => chapter.id));
const stories = data.chapters.flatMap((chapter) => chapter.stories);
assert.equal(stories.length, 20);
assert.equal(new Set(stories.map((story) => story.event_id)).size, 20, 'Dynasty transitions appear once');
const query = new URL(ancientStoriesPath, 'https://histree.local');
assert.deepEqual(query.searchParams.get('ids').split(','), stories.map((story) => story.event_id));
assert.ok(stories.length <= Number(query.searchParams.get('limit')), 'One bounded request includes every selected record');

for (const chapter of data.chapters) {
  assert.ok(chapter.stories.length >= 4 && chapter.stories.length <= 6);
  const rows = chapter.stories.map((story) => ({ id: story.event_id, title: 'Live title', description: 'Live description', start_year: null, end_year: null }));
  const ordered = ancientStoryEvents(chapter.id, [...rows].reverse());
  assert.deepEqual(ordered.map((story) => story.event.id), rows.map((row) => row.id), 'Database ordering cannot change the reviewed reading sequence');
  assert.ok(ordered.every((story) => story.event.description === 'Live description'), 'Published descriptions are used without a second copy');
  assert.equal(ancientStoryEvents(chapter.id, rows.slice(1)).length, rows.length - 1, 'Unavailable events never fall back to hardcoded titles');
  for (const story of chapter.stories) {
    const proof = audit.events.find((event) => event.event_id === story.event_id);
    assert.equal(proof?.chapter, chapter.id);
    assert.equal(proof.order, chapter.stories.indexOf(story) + 1, 'Navigation changes require an updated order review');
    assert.equal(proof.claim_id, story.source.claim_id);
    assert.equal(proof.paragraph_id, story.source.paragraph_id);
    assert.match(proof.archive_url, /\/blob\/[a-f0-9]{40}\//);
    assert.match(proof.snapshot_sha256, /^[a-f0-9]{64}$/);
    assert.ok(proof.quote && proof.review_note);
    const link = new URL(ancientStorySource(story), 'https://histree.local');
    assert.equal(link.searchParams.get('claim'), proof.claim_id);
    assert.equal(link.searchParams.get('paragraph'), proof.paragraph_id);
    assert.equal(link.hash, '#paragraph-' + proof.paragraph_id);
    assert.equal(story.start_year, undefined, 'Navigation never supplies fabricated calendar dates');
  }
}
assert.deepEqual(ancientStoryEvents('unknown-era', stories), []);
assert.deepEqual(ancientStoryEvents('xia'), []);
console.log('PASS: reviewed ancient reading order, 20 unique published-record references, hidden-record omission, and evidence deep links.');
