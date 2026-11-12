/** Validate author-managed story records before publishing new illustrated stories. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const catalog = JSON.parse(await readFile(new URL('../apps/web/src/data/stories.json', import.meta.url), 'utf8'));
assert.ok(Array.isArray(catalog.stories) && catalog.stories.length > 0);
const slugs = new Set();
for (const story of catalog.stories) {
  assert.match(story.slug, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert.ok(!slugs.has(story.slug), `Duplicate story: ${story.slug}`);
  slugs.add(story.slug);
  for (const key of ['title', 'description']) assert.ok(typeof story[key] === 'string' && story[key].trim(), key);
  assert.ok(Number.isFinite(story.readingMinutes) && story.readingMinutes > 0);
  assert.match(story.image.sha256, /^[a-f0-9]{64}$/);
  assert.match(story.image.url, new RegExp(`^/api/v1/media/images/${story.image.sha256}\\.(png|jpg|webp|gif)$`));
  for (const key of ['width', 'height']) assert.ok(Number.isInteger(story.image[key]) && story.image[key] > 0);
  assert.ok(Array.isArray(story.panels) && story.panels.length > 0);
  story.panels.forEach((panel, index) => {
    assert.equal(panel.number, index + 1, `Reading order: ${story.slug}`);
    for (const key of ['title', 'caption', 'alt']) assert.ok(typeof panel[key] === 'string' && panel[key].trim(), key);
    const { x, y, width, height } = panel.crop;
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
