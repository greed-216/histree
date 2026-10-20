/** Model-free verification of the exact deployed image and its public read paths. */
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const base=(process.argv[2] || 'http://127.0.0.1:3000').replace(/\/$/,'');
const manifest=JSON.parse(await readFile(process.argv[3] || 'release-manifest.json','utf8'));
let checks=0;
const request=async(path,init)=>fetch(base+path,{...init,signal:AbortSignal.timeout(10000)});
const json=async(path)=>{const r=await request(path);assert.equal(r.status,200,path);checks++;return r.json();};
assert.deepEqual(await json('/api/v1/health'),{status:'ok',database:'mysql'});
for(const path of ['/','/people','/timeline/scroll','/learn/five-dynasties/later-zhou','/graph','/ask?mode=guess','/ask?mode=guess&play=questions']){
 const r=await request(path);assert.equal(r.status,200,path);const html=await r.text();assert.ok(html.includes('<div id="root"></div>'));assert.match(html,/\/assets\/[^" ]+\.js/);checks++;
 for(const asset of html.matchAll(/(?:src|href)="(\/assets\/[^" ]+)"/g))assert.equal((await request(asset[1])).status,200,asset[1]);
}
for(const asset of manifest.scroll){
 const r=await request('/timeline-scroll/'+asset.file);assert.equal(r.status,200);
 assert.equal(createHash('sha256').update(Buffer.from(await r.arrayBuffer())).digest('hex'),asset.sha256,'Scroll asset differs from this release');checks++;
}
const people=await json('/api/v1/catalog/person?limit=1');assert.ok(Array.isArray(people.items));assert.equal(typeof people.has_more,'boolean');
if(people.items.length){const p=people.items[0];assert.equal(p.status,'published');assert.equal((await json('/api/v1/entry/'+p.id)).id,p.id);}
for(const path of ['/api/v1/ask/status','/api/v1/ask/guess/status','/api/v1/ask/guess/clues/status'])assert.equal(typeof(await json(path)).available,'boolean');
for(const path of ['/api/v1/does-not-exist','/assets/does-not-exist.js','/api/v1/editorial/person','/api/v1/upload']){assert.equal((await request(path)).status,404,path);checks++;}
assert.equal((await request('/api/v1/read/consume_ai_gateway_quota',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status,404);checks++;
console.log(`PASS: ${checks} release checks; MySQL readiness, SPA/deep links, exact scroll hash, published data and retired/private routes; model calls=0`);
