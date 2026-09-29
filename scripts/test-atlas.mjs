import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const ts = require('typescript');
const source = await readFile(new URL('../apps/web/src/lib/atlas.ts', import.meta.url), 'utf8');
const {outputText} = ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}});
const {parseAtlas,cloneSnapshot,snapshotAt,regionPoints} = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const raw = await readFile(new URL('../apps/web/src/data/atlas-907.json',import.meta.url),'utf8');
const doc=parseAtlas(raw);
assert.deepEqual(parseAtlas(JSON.stringify(doc)),doc);
assert.equal(snapshotAt(doc,923),undefined,'Unknown year must not show old borders');
const original=structuredClone(snapshotAt(doc,907));
const copy=cloneSnapshot(original,908);
assert.notEqual(copy.id,original.id);
assert.equal(copy.reference,null,'Old reference must not become new-year evidence');
const shared=Object.keys(original.nodes).find(id=>original.regions.filter(r=>r.nodes.includes(id)).length>1);
assert.ok(shared,'The fixture must contain shared border vertices');
copy.nodes[shared][0]+=1;
copy.regions[0].name='Edited';
assert.deepEqual(original,snapshotAt(doc,907),'Version edits must not mutate the source');
const adjoining=copy.regions.filter(r=>r.nodes.includes(shared));
assert.ok(adjoining.every(r=>regionPoints(copy,r).includes(copy.nodes[shared].join(','))));
assert.equal(parseAtlas(JSON.stringify({...doc,snapshots:[original,copy]})).snapshots.length,2);
for (const mutate of [
 d=>d.snapshots.push(d.snapshots[0]),
 d=>d.snapshots[0].regions[0].nodes.push('missing-node'),
 d=>d.snapshots[0].nodes[shared]=[NaN,0],
 d=>d.snapshots[0].nodes[shared]=[577,0],
 d=>d.snapshots[0].regions[0].nodes=['missing','missing','missing'],
 d=>d.snapshots[0].regions[0].color='url(https://example.com)',
 d=>d.snapshots[0].status='published',
 d=>d.snapshots[0].year=0,
]) {const draft=structuredClone(doc);mutate(draft);assert.throws(()=>parseAtlas(JSON.stringify(draft)));}
console.log('Atlas tests passed: valid fixture, exact-year lookup, isolated snapshots, shared borders, malformed imports.');
