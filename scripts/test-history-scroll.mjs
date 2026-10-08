import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const ts=createRequire(new URL('../apps/web/package.json',import.meta.url))('typescript');
const scroll=JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll.json',import.meta.url),'utf8'));
const opts={target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext};
const moduleUrl=source=>`data:text/javascript;base64,${Buffer.from(ts.transpileModule(source,{compilerOptions:opts}).outputText).toString('base64')}`;
const viewportUrl=moduleUrl(await readFile(new URL('../apps/web/src/lib/timelineViewport.ts',import.meta.url),'utf8'));
const {ordinal}=await import(viewportUrl);
const source=(await readFile(new URL('../apps/web/src/lib/historyScroll.ts',import.meta.url),'utf8'))
 .replace('import scroll from "../data/history-scroll.json";',`const scroll=${JSON.stringify(scroll)};`)
 .replace('"./timelineViewport"',JSON.stringify(viewportUrl));
const {scrollYearX,scrollPanelGeometry,scrollBackgroundGeometry,scrollSceneLayout,scrollPeriodShare,initialScrollWindow}=await import(moduleUrl(source));
const first=ordinal(scroll.from_year),last=ordinal(scroll.to_year),art=scroll.panels[0];
assert.equal(first,-403);assert.equal(last-first,2314);
assert.equal(ordinal(1)-ordinal(-1),1);
assert.equal(scroll.logical_canvas.width,9360);assert.equal(scroll.logical_canvas.height,720);
assert.equal(scroll.panels.length,1);
assert.equal(art.from_year,scroll.from_year);assert.equal(art.to_year,scroll.to_year);
assert.equal(art.crop.x,0);assert.equal(art.crop.y,0);
assert.equal(art.crop.width,art.width);assert.equal(art.crop.height,art.height);
assert.equal(scrollPeriodShare(907,960),53/2314);
assert.ok(Math.abs(scroll.periods.reduce((sum,p)=>sum+scrollPeriodShare(p.from_year,p.to_year),0)-1)<1e-12);
// Source-pixel anchors and data years must land at exactly the same screen x at every zoom.
const pixelForYear=y=>(ordinal(y)-first)/(last-first)*art.width;
for(const [from,to] of [[first,last],[606,1206],[-50,50],[850,958],[ordinal(907),ordinal(917)]]) {
 const g=scrollPanelGeometry(art,from,to),scene=scrollSceneLayout(from,to);
 assert.deepEqual(scrollBackgroundGeometry(art,from,to),g);
 assert.equal(g.height,scene.height);assert.equal(g.y+g.height,scene.bottom);
 assert.ok(scene.bottom+30<=90+scene.viewBoxHeight,'entire height and ticks fit, without vertical crop');
 assert.ok(Math.abs(g.width/g.height-art.width/art.height)<1e-12);
 for(const year of [-403,-221,-1,1,220,581,907,960,1279,1368,1644,1912]) {
  const artworkX=g.x+pixelForYear(year)/art.width*g.width;
  assert.ok(Math.abs(artworkX-scrollYearX(year,from,to))<1e-8,`art/data anchor differs at ${year}`);
 }
 const shifted=scrollPanelGeometry(art,from+7,to+7);
 const artShift=shifted.x-g.x;
 const dataShift=scrollYearX(907,from+7,to+7)-scrollYearX(907,from,to);
 assert.ok(Math.abs(artShift-dataShift)<1e-8,'drag speed must match exactly');
}
for(const year of [-403,-1,1,907,959,1912])for(const compact of [false,true]) {
 const w=initialScrollWindow(year,852,959,compact);
 assert.ok(w.from<=ordinal(year)&&w.to>=ordinal(year));assert.ok(w.from>=first&&w.to<=last);
}
assert.deepEqual(initialScrollWindow(959,852,959,false),{from:858,to:958});
const bytes=await readFile(new URL(`../apps/web/public/timeline-scroll/${art.file}`,import.meta.url));
assert.equal(bytes.length,art.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),art.sha256);
assert.equal(bytes.toString('ascii',0,4),'RIFF');assert.equal(bytes.toString('ascii',8,12),'WEBP');
let dimensions;
for(let offset=12;offset+8<bytes.length;) {
 const kind=bytes.toString('ascii',offset,offset+4),size=bytes.readUInt32LE(offset+4),p=offset+8;
 if(kind==='VP8X')dimensions=[bytes.readUIntLE(p+4,3)+1,bytes.readUIntLE(p+7,3)+1];
 if(kind==='VP8 ')dimensions=[bytes.readUInt16LE(p+6)&0x3fff,bytes.readUInt16LE(p+8)&0x3fff];
 offset+=8+size+(size%2);
}
assert.deepEqual(dimensions,[9360,720]);
const audit=JSON.parse(await readFile(new URL('../design/history-scroll-v5/composition.json',import.meta.url),'utf8'));
assert.equal(audit.width,9360);assert.equal(audit.overlap_px,360);assert.equal(audit.seams.length,4);
assert.equal(2160+4*1800,9360,'duplicate overlap pixels must be removed');
const png=await readFile(new URL('../design/history-scroll-v5/history-scroll-v5.png',import.meta.url));
assert.equal(png.readUInt32BE(16),9360);assert.equal(png.readUInt32BE(20),720);
assert.equal(createHash('sha256').update(png).digest('hex'),audit.lossless_png_sha256);
console.log('PASS: 403 BCE–1912, original stitched pixels, era proportions, no year zero, exact artwork/data anchors and pan speed at all zooms, full height and asset hashes.');
