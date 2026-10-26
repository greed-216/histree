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
const {scrollYearX,scrollPanelGeometry,scrollBackgroundGeometry,scrollSceneLayout,scrollPeriodShare,initialScrollWindow,minimumScrollSpan,nextScrollZoomSpan,scrollPanels,scrollStart,ancientChapters}=await import(moduleUrl(source));
const art=scrollPanels.at(-1),first=ordinal(art.from_year),last=ordinal(art.to_year);
assert.equal(first,-403);assert.equal(last-first,2314);
assert.equal(ordinal(1)-ordinal(-1),1);
assert.equal(art.width,9360);assert.equal(scroll.logical_canvas.height,720);
assert.equal(scroll.panels.length,3);
assert.equal(scroll.from_year,-841);assert.equal(art.from_year,-403);assert.equal(art.to_year,scroll.to_year);
assert.equal(art.crop.x,0);assert.equal(art.crop.y,0);
assert.equal(art.crop.width,art.width);assert.equal(art.crop.height,art.height);
assert.equal(scrollPeriodShare(907,960),53/(last-scrollStart));
assert.ok(Math.abs(scroll.periods.reduce((sum,p)=>sum+scrollPeriodShare(p.from_year,p.to_year),0)+ancientChapters.reduce((sum,c)=>sum+(c.to-c.from)/(last-scrollStart),0)-1)<1e-12);
// Source-pixel anchors and data years must land at exactly the same screen x at every zoom.
const pixelForYear=y=>(ordinal(y)-first)/(last-first)*art.width;
for(const [from,to] of [[first,last],[606,1206],[-50,50],[850,958],[ordinal(907),ordinal(917)]]) {
 const g=scrollPanelGeometry(art,from,to),scene=scrollSceneLayout(from,to);
 assert.deepEqual(scrollBackgroundGeometry(art,from,to),g);
 assert.equal(scene.mode,"scroll");
 assert.equal(scene.naturalHeight,g.height);
 assert.equal(scene.cropped,g.height>scene.height+1);
 assert.ok(scene.bottom+24<=90+scene.viewBoxHeight,'year axis remains inside the fixed canvas');
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
// Zoom never changes the chosen view or its allocated canvas size.
for(const width of [320,555,1000,1440]) for(const budget of [190,294,434]) {
 const limit=minimumScrollSpan(width,budget);
 const fitted=scrollSceneLayout(906,906+limit,width,budget);
 assert.equal(fitted.mode,'scroll');
 assert.equal(fitted.cropped,false,'fitted artwork is fully visible');
 assert.ok(Math.abs(fitted.viewBoxHeight * width / 1000-budget)<1e-8);
 for(const span of [10,20,40,100,limit,2314]) {
  const close=scrollSceneLayout(906,906+span,width,budget);
  const detail=scrollSceneLayout(906,906+span,width,budget,'detail');
  assert.equal(close.mode,'scroll','close zoom keeps artwork');
  assert.equal(detail.mode,'detail','detail is explicitly selected');
  assert.equal(close.viewBoxHeight,fitted.viewBoxHeight);
  assert.equal(detail.viewBoxHeight,fitted.viewBoxHeight);
  assert.equal(close.height,fitted.height);
  assert.ok(close.bottom+24*1000/width<=90+close.viewBoxHeight,'fixed pixel year footer stays visible');
  assert.equal(detail.cropped,false);
  const riverHalf=80*detail.viewBoxHeight/270;
  assert.ok(detail.riverY-riverHalf>=90 && detail.riverY+riverHalf<detail.bottom,'detail river stays above the year axis');
 }
 assert.equal(nextScrollZoomSpan(20,true),10);
 assert.equal(nextScrollZoomSpan(10,true),10);
 assert.equal(nextScrollZoomSpan(100,false),200);
}
for(const year of [-403,-1,1,907,959,1912])for(const compact of [false,true]) {
 const w=initialScrollWindow(year,852,959,compact);
 assert.ok(w.from<=ordinal(year)&&w.to>=ordinal(year));assert.ok(w.from>=scrollStart&&w.to<=last);
}
assert.equal(initialScrollWindow(959,852,959,false).to-initialScrollWindow(959,852,959,false).from,600);
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
// Keep validating the unchanged v6 source and its original composition independently of new panels.
const provenance="design/history-scroll-v6";
const audit=JSON.parse(await readFile(new URL(`../${provenance}/composition.json`,import.meta.url),'utf8'));
assert.equal(audit.width,9360);assert.equal(audit.overlap_px,360);assert.equal(audit.seams.length,4);
assert.equal(2160+4*1800,9360,'duplicate overlap pixels must be removed');
const png=await readFile(new URL(`../${provenance}/history-scroll-v6.png`,import.meta.url));
assert.equal(png.readUInt32BE(16),9360);assert.equal(png.readUInt32BE(20),720);
assert.equal(createHash('sha256').update(png).digest('hex'),audit.lossless_png_sha256);
for(const original of audit.originals) {
 const raw=await readFile(new URL(`../${original.file}`,import.meta.url));
 assert.equal(createHash('sha256').update(raw).digest('hex'),original.sha256);
}
if(art.id==='history-scroll-v6') {
 const ending=audit.late_ending;
 assert.equal(ending.from_year,1850);
 assert.equal(ending.global_start_px,Math.ceil(pixelForYear(1850)));
 assert.equal(ending.local_start_px,ending.global_start_px-4*audit.step_px);
 const raw=await readFile(new URL(`../${ending.file}`,import.meta.url));
 assert.equal(createHash('sha256').update(raw).digest('hex'),ending.source_sha256);
 const storyboard=JSON.parse(await readFile(new URL(`../${provenance}/storyboard.json`,import.meta.url),'utf8'));
 assert.deepEqual(scroll.scene_notes.slice(3),storyboard.display_notes);
 assert.equal(storyboard.display_notes.length,10);
}
console.log('PASS: 403 BCE–1912, original stitched pixels, era proportions, no year zero, exact artwork/data anchors and pan speed at all zooms, fixed canvas, independent view modes, cropped zoom, complete year axes and asset hashes.');
