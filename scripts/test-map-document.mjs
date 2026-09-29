import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require = createRequire(new URL('../apps/web/package.json', import.meta.url));
const ts = require('typescript');
const source = await readFile(new URL('../apps/web/src/lib/mapDocument.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}});
const { emptyMap, geometry, vertices, parseMap } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const points = [[112, 35], [114, 35], [113, 34]];
const feature = {type:'Feature', id:'test', geometry:geometry('Polygon', points), properties:{name:'测试区域',color:'#0f766e',start_year:907,end_year:923,source:'测试依据',note:'非历史内容',status:'draft'}};
const doc = {...emptyMap(),features:[feature]};
assert.deepEqual(vertices(feature),points);
assert.deepEqual(feature.geometry.coordinates[0].at(-1),points[0]);
assert.deepEqual(parseMap(JSON.stringify(doc)),doc);
for (const type of ['Point','LineString']) {
 const f={...feature,geometry:geometry(type,type==='Point'?points.slice(0,1):points)};
 assert.deepEqual(parseMap(JSON.stringify({...doc,features:[f]})).features[0],f);
}
function rejects(edit) {const copy=structuredClone(doc);edit(copy);assert.throws(()=>parseMap(JSON.stringify(copy)));}
rejects(d=>d.features.push(d.features[0]));
rejects(d=>d.features[0].properties.end_year=906);
rejects(d=>d.features[0].geometry.coordinates[0][1]=[181,35]);
rejects(d=>d.features[0].geometry.coordinates[0].pop());
rejects(d=>d.features[0].geometry.coordinates.push(points));
rejects(d=>d.features[0].properties.status='published');
rejects(d=>d.features[0].geometry={type:'LineString',coordinates:[[112,35]]});
console.log('Map document tests passed: geometry round trips, closure, IDs, dates, coordinates, draft-only import.');
