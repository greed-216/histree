import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';

const data = JSON.parse(await readFile(new URL('../apps/web/src/data/timeline-polities.json', import.meta.url), 'utf8'));
const ts = createRequire(new URL('../apps/web/package.json', import.meta.url))('typescript');
const moduleUrl = source => `data:text/javascript;base64,${Buffer.from(ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText).toString('base64')}`;
const viewportUrl = moduleUrl(await readFile(new URL('../apps/web/src/lib/timelineViewport.ts', import.meta.url), 'utf8'));
const { ordinal } = await import(viewportUrl);
const source = (await readFile(new URL('../apps/web/src/lib/timelinePeriods.ts', import.meta.url), 'utf8'))
  .replace('import data from "../data/timeline-polities.json";', `const data = ${JSON.stringify(data)};`)
  .replace('"./timelineViewport"', JSON.stringify(viewportUrl));
const { visiblePolityLanes, polityTones } = await import(moduleUrl(source));

assert.equal(new Set(data.polities.map(item => item.id)).size, data.polities.length);
for (const polity of data.polities) {
  assert.ok(Number.isInteger(polity.from_year) && Number.isInteger(polity.to_year));
  assert.ok(polity.from_year !== 0 && polity.to_year !== 0);
  assert.ok(polity.to_year > polity.from_year);
  assert.ok(polity.references.length && polity.references.every(id => data.references[id]?.url));
  assert.equal(polity.level, undefined, 'Specific polities never depend on zoom-level grouping');
}
for (const id of ['sixteen-kingdoms', 'southern-dynasties', 'northern-dynasties', 'five-dynasties']) {
  assert.equal(data.polities.some(item => item.id === id), false, 'Summary polities have been removed');
}

for (const [group, start, end, count] of [
  ['warring-states', -403, -221, 7],
  ['sixteen-kingdoms', 304, 439, 16],
  ['southern-dynasties', 400, 600, 4],
  ['northern-dynasties', 380, 600, 5],
  ['five-dynasties', 907, 960, 5],
  ['ten-kingdoms', 902, 979, 10],
]) {
  const full = data.polities.filter(item => item.group === group);
  assert.equal(full.length, count, group);
  const visible = visiblePolityLanes(ordinal(start), ordinal(end)).flat().filter(item => item.group === group);
  assert.deepEqual(new Set(visible.map(item => item.id)), new Set(full.map(item => item.id)), 'Every constituent is independently available in the group window');
}

const tenKingdoms = data.polities.filter(item => item.group === 'ten-kingdoms');
assert.deepEqual(new Set(tenKingdoms.map(item => item.id)), new Set([
  'southern-wu', 'former-shu', 'wuyue', 'chu-ten-kingdoms', 'min',
  'southern-han', 'jingnan', 'later-shu', 'southern-tang', 'northern-han',
]));
// The five-dynasty navigation window must include all ten states, including the late Northern Han.
const fiveDynastyWindow = visiblePolityLanes(ordinal(907), ordinal(960)).flat();
assert.deepEqual(new Set(fiveDynastyWindow.filter(item => item.group === 'ten-kingdoms').map(item => item.id)),
  new Set(tenKingdoms.map(item => item.id)));
for (const [id, start, end] of [
  ['southern-wu', 902, 937], ['former-shu', 907, 925], ['wuyue', 907, 978],
  ['chu-ten-kingdoms', 907, 951], ['min', 909, 945], ['southern-han', 917, 971],
  ['jingnan', 924, 963], ['later-shu', 934, 965], ['southern-tang', 937, 975],
  ['northern-han', 951, 979],
]) {
  const polity = fiveDynastyWindow.find(item => item.id === id);
  assert.equal(polity.from_year, start);
  assert.equal(polity.to_year, end, `${id} keeps its own endpoint across the Song navigation boundary`);
}

// A shared row expresses succession, never overlapping contemporaneous states.
for (const lane of new Set(data.polities.map(item => item.lane))) {
  const items = data.polities.filter(item => item.lane === lane).sort((a, b) => ordinal(a.from_year) - ordinal(b.from_year));
  for (let i = 1; i < items.length; i++) {
    assert.ok(ordinal(items[i - 1].to_year) <= ordinal(items[i].from_year), `${items[i - 1].id} and ${items[i].id} must not share an overlapping duration strip`);
    assert.notEqual(polityTones[items[i - 1].id], polityTones[items[i].id], 'Successive states on a shared row use distinct colors');
  }
}
const qin = data.polities.find(item => item.id === 'qin');
assert.equal(data.polities.some(item => item.id === 'qin-state'), false, 'Qin is one continuous polity');
assert.equal(qin.from_year, -403);
assert.equal(qin.to_year, -207);
assert.equal(qin.phases[0].to_year, qin.phases[1].from_year);
assert.equal(qin.transition.year, -221);
assert.deepEqual(qin.phases.map(item => item.label), ['秦国', '秦朝']);
assert.notEqual(polityTones['northern-qi'], polityTones.sui, 'Northern Qi and Sui use different colors');
assert.notEqual(polityTones['northern-qi'], polityTones['northern-zhou']);
assert.equal(data.polities.find(item => item.id === 'northern-qi').to_year, 577);
assert.equal(data.polities.find(item => item.id === 'northern-zhou').to_year, 581);
assert.equal(data.polities.filter(item => item.group === 'warring-states').every(item => item.note.includes('不用于判定')), true);
console.log('PASS: seven Warring States, sixteen kingdoms, four southern dynasties, five northern polities, five dynasties and all ten kingdoms stay distinct at every zoom, with sources and non-overlapping rows.');
