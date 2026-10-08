import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const ts = createRequire(new URL('../apps/web/package.json', import.meta.url))('typescript');
const scroll = JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll.json', import.meta.url), 'utf8'));
const viewportSource = await readFile(new URL('../apps/web/src/lib/timelineViewport.ts', import.meta.url), 'utf8');
const options = { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext };
const viewportUrl = `data:text/javascript;base64,${Buffer.from(ts.transpileModule(viewportSource, { compilerOptions: options }).outputText).toString('base64')}`;
const { ordinal } = await import(viewportUrl);
const source = (await readFile(new URL('../apps/web/src/lib/historyScroll.ts', import.meta.url), 'utf8'))
  .replace('import scroll from "../data/history-scroll.json";', `const scroll = ${JSON.stringify(scroll)};`)
  .replace('"./timelineViewport"', JSON.stringify(viewportUrl));
const { scrollPanelGeometry, scrollPeriodShare, initialScrollWindow } = await import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(source, { compilerOptions: options }).outputText).toString('base64')}`);
const first = ordinal(scroll.from_year), last = ordinal(scroll.to_year);
assert.equal(last - first, 2681);
assert.equal(ordinal(1) - ordinal(-1), 1);
assert.equal(scroll.panels.reduce((n, p) => n + ordinal(p.to_year) - ordinal(p.from_year), 0), 2681);
assert.ok(Math.abs(scroll.periods.reduce((n, p) => n + scrollPeriodShare(p.from_year, p.to_year), 0) - 1) < 1e-12);
assert.equal(scrollPeriodShare(907, 960), 53 / 2681);
for (const [from, to] of [[first, last], [ordinal(607), ordinal(1207)], [-50, 50]]) {
  const geometry = scroll.panels.map(p => scrollPanelGeometry(p, from, to));
  for (let i = 0; i < geometry.length; i++) {
    const g = geometry[i], p = scroll.panels[i];
    assert.ok(Math.abs(g.width / g.height - p.crop.width / p.crop.height) < 1e-12);
    if (i) assert.ok(Math.abs(geometry[i-1].x + geometry[i-1].width - g.x) < 1e-9);
  }
}
assert.equal(scroll.panels.length, 1, 'continuous artwork must not join independent pictures');
assert.equal(scroll.panels[0].from_year, scroll.from_year);
assert.equal(scroll.panels[0].to_year, scroll.to_year);
for (const panel of scroll.panels) {
  assert.ok(panel.crop.x >= 0 && panel.crop.y >= 0);
  assert.ok(panel.crop.x + panel.crop.width <= panel.width);
  assert.ok(panel.crop.y + panel.crop.height <= panel.height);
  const bytes = await readFile(new URL(`../apps/web/public/timeline-scroll/${panel.file}`, import.meta.url));
  assert.equal(bytes.readUInt32BE(16), panel.width);
  assert.equal(bytes.readUInt32BE(20), panel.height);
  assert.equal(bytes.length, panel.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), panel.sha256);
}
console.log('PASS: proportional periods, BCE/CE continuity, adjacent undistorted panels and original asset hashes.');

for (const year of [-495, -1, 1, 907, 959, 1912]) {
  for (const compact of [false, true]) {
    const w = initialScrollWindow(year, 852, 959, compact);
    assert.ok(w.from <= ordinal(year) && w.to >= ordinal(year), `direct year ${year} must be visible`);
    assert.ok(w.from >= first && w.to <= last);
  }
}
assert.deepEqual(initialScrollWindow(959, 852, 959, false), {from:858, to:958});
console.log('PASS: direct links include selected years outside the recorded corpus, with legacy recorded-year windows preserved.');

const art = scroll.panels[0];
assert.equal(scroll.logical_canvas.width, art.crop.width, 'gallery must use native width');
assert.equal(scroll.logical_canvas.height, art.crop.height, 'gallery must use native height');
const overview = scrollPanelGeometry(art, first, last);
assert.equal(overview.y, 0);
assert.ok(overview.height + 4 <= 178, 'overview must fit its entire artwork above the range bar');
console.log('PASS: complete artwork height fits overview and gallery uses native resolution.');
