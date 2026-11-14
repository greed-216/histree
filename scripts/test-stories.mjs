/** Validate author-managed story records before publishing new illustrated stories. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pickRandomStory } from '../apps/web/src/lib/story-random.ts';
import { createStoryPreloader, storyPreloadUrls } from '../apps/web/src/lib/story-preload.ts';
const catalog = JSON.parse(await readFile(new URL('../apps/web/src/data/stories.json', import.meta.url), 'utf8'));
assert.ok(Array.isArray(catalog.stories) && catalog.stories.length > 0);
const slugs = new Set();
for (const story of catalog.stories) {
  assert.match(story.slug, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert.ok(!slugs.has(story.slug), `Duplicate story: ${story.slug}`);
  slugs.add(story.slug);
  for (const key of ['title', 'description']) assert.ok(typeof story[key] === 'string' && story[key].trim(), key);
  for (const section of [story.introduction, story.afterword.takeaway]) {
    for (const key of ['title', 'text']) assert.ok(typeof section[key] === 'string' && section[key].trim(), key);
  }
  assert.ok(story.afterword.title?.trim() && story.afterword.sourceNote?.trim());
  assert.ok(Array.isArray(story.afterword.paragraphs) && story.afterword.paragraphs.length > 0);
  for (const text of story.afterword.paragraphs) assert.ok(typeof text === 'string' && text.trim());
  assert.ok(Number.isFinite(story.readingMinutes) && story.readingMinutes > 0);
  assert.ok(Array.isArray(story.people));
  for (const person of story.people) {
    assert.ok(person.name.trim());
    assert.match(person.id, /^[a-f0-9-]{36}$/);
  }
  assert.ok(story.sourceLinks.length > 0);
  for (const source of story.sourceLinks) {
    assert.ok(source.label.trim());
    const url = new URL(source.url, 'https://histree.wiki');
    assert.equal(url.protocol, 'https:');
    assert.ok(['histree.wiki', 'zh.wikisource.org'].includes(url.hostname));
    if (url.hostname === 'histree.wiki') {
      assert.ok(url.pathname.startsWith('/library/'));
      assert.ok(url.searchParams.get('paragraph'));
    }
  }
  assert.match(story.image.sha256, /^[a-f0-9]{64}$/);
  assert.match(story.image.url, new RegExp(`^/api/v1/media/images/${story.image.sha256}\\.(png|jpg|webp|gif)$`));
  for (const key of ['width', 'height']) assert.ok(Number.isInteger(story.image[key]) && story.image[key] > 0);
  function derivative(image) {
    assert.match(image.sha256, /^[a-f0-9]{64}$/);
    assert.equal(image.url, `/api/v1/media/images/${image.sha256}.webp`);
    for (const key of ['width', 'height', 'bytes']) assert.ok(Number.isInteger(image[key]) && image[key] > 0);
    assert.notEqual(image.url, story.image.url, 'Reader must not fetch the original sheet');
    assert.ok(image.bytes <= 160 * 1024, `Oversized derivative: ${story.slug}`);
  }
  derivative(story.cover);
  assert.ok(Math.max(story.cover.width, story.cover.height) <= 360);
  assert.ok(Array.isArray(story.panels) && story.panels.length > 0);
  story.panels.forEach((panel, index) => {
    assert.equal(panel.number, index + 1, `Reading order: ${story.slug}`);
    for (const key of ['title', 'caption', 'alt']) assert.ok(typeof panel[key] === 'string' && panel[key].trim(), key);
    const { x, y, width, height } = panel.crop;
    derivative(panel.image);
    assert.equal(panel.image.width, width);
    assert.equal(panel.image.height, height);
    for (const n of [x, y, width, height]) assert.ok(Number.isInteger(n));
    assert.ok(x >= 0 && y >= 0 && width > 0 && height > 0);
    assert.ok(x + width <= story.image.width && y + height <= story.image.height, `Crop outside sheet: ${story.slug}/${panel.number}`);
  });
  const audit = JSON.parse(await readFile(new URL(`../docs/stories/${story.slug}.json`, import.meta.url), 'utf8'));
  assert.equal(audit.imageSha256, story.image.sha256);
  assert.equal(audit.status, 'approved');
  assert.ok(audit.source.locator && audit.source.excerpt && audit.adaptations.length);
}
console.log(`PASS: ${catalog.stories.length} story catalogs, image references, panel order/bounds and editorial audits`);
// The random entry opens actual readable slugs and never reopens the current story.
const shelf = [{ slug: 'a' }, { slug: 'b' }, { slug: 'c' }];
assert.equal(pickRandomStory([], undefined, () => 0), undefined);
assert.equal(pickRandomStory(shelf.slice(0, 1), 'a', () => 0)?.slug, 'a');
assert.equal(pickRandomStory(shelf, undefined, () => 0)?.slug, 'a');
assert.equal(pickRandomStory(shelf, undefined, () => 0.5)?.slug, 'b');
assert.equal(pickRandomStory(shelf, undefined, () => 0.999)?.slug, 'c');
for (const current of shelf) {
  const picked = [0, 0.25, 0.5, 0.999].map(value => pickRandomStory(shelf, current.slug, () => value)?.slug);
  assert.ok(!picked.includes(current.slug));
  assert.deepEqual(new Set(picked), new Set(shelf.filter(s => s !== current).map(s => s.slug)));
}
assert.equal(pickRandomStory(shelf, 'missing', () => 0)?.slug, 'a');
assert.equal(pickRandomStory(shelf, undefined, () => 1)?.slug, 'c');
console.log('PASS: random story reachability, exclusion and empty/single-story behavior');

const panels = Array.from({ length: 10 }, (_, i) => ({ image: { url: String(i + 1) } }));
assert.deepEqual(storyPreloadUrls(panels, 0), ['1','2','3','4','5','6']);
assert.deepEqual(storyPreloadUrls(panels, 1), ['2','3','4','5','6']);
assert.deepEqual(storyPreloadUrls(panels, 8), ['9','10']);
assert.deepEqual(storyPreloadUrls(panels, 11), []);
const requests = [], deferred = new Map();
const loader = createStoryPreloader(url => new Promise((resolve, reject) => {
  requests.push(url); deferred.set(url, { resolve, reject });
}));
const settle = () => new Promise(resolve => setImmediate(resolve));
loader.warm(['1','2','3','3','4']); await settle();
assert.deepEqual(requests, ['1','2'], 'At most two speculative requests');
loader.warm(['2','7','8']);
deferred.get('1').resolve(); await settle();
assert.deepEqual(requests, ['1','2','7'], 'Replace stale queued panels after a jump');
deferred.get('2').reject(); await settle();
assert.deepEqual(requests, ['1','2','7','8'], 'A failed preload does not block the queue');
deferred.get('7').resolve(); deferred.get('8').resolve(); await settle();
loader.warm(['1','7','8','2']); await settle();
assert.deepEqual(requests, ['1','2','7','8','2'], 'Reuse successes, allow failed request to retry');
loader.warm(['9','10']); loader.dispose(); deferred.get('2').resolve(); await settle();
assert.ok(!requests.includes('10'), 'Leaving the story stops queued requests');
console.log('PASS: preload window, concurrency, deduplication, jumps, failure and disposal');
