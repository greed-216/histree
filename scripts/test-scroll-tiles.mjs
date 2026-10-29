import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const ts=createRequire(new URL('../apps/web/package.json',import.meta.url))('typescript');
const moduleUrl=source=>'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64');
const viewportUrl=moduleUrl(await readFile(new URL('../apps/web/src/lib/timelineViewport.ts',import.meta.url),'utf8'));
const scroll=JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll.json',import.meta.url),'utf8'));
const manifest=JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll-tiles.json',import.meta.url),'utf8'));
const scrollUrl=moduleUrl((await readFile(new URL('../apps/web/src/lib/historyScroll.ts',import.meta.url),'utf8')).replace('import scroll from "../data/history-scroll.json";',`const scroll=${JSON.stringify(scroll)};`).replace('"./timelineViewport"',JSON.stringify(viewportUrl)));
const tileUrl=moduleUrl((await readFile(new URL('../apps/web/src/lib/scrollTiles.ts',import.meta.url),'utf8')).replace('import manifest from "../data/history-scroll-tiles.json";',`const manifest=${JSON.stringify(manifest)};`).replace('"./historyScroll"',JSON.stringify(scrollUrl)));
const {scrollPanels,scrollStart,annualStart}=await import(scrollUrl);
const {visibleScrollTiles}=await import(tileUrl);
const repair=scrollPanels.find(panel=>panel.id==='zhou-seam-repair-v2');
assert.equal(visibleScrollTiles(scrollPanels[0],annualStart,annualStart+20,repair).visible.length,0,'The original ghosted overlap is not fetched beneath the opaque repair');
for(const panel of manifest.panels){
 let cursor=panel.crop.x;
 for(const tile of panel.tiles){
  assert.equal(tile.content_x,cursor,'Tile core has no gap or repeated content');cursor+=tile.content_width;
  assert.ok(tile.x<=tile.content_x&&tile.x+tile.width>=cursor,'Bleed covers the entire core');
  for(const level of ['low','high']){
   const info=tile[level],data=await readFile(new URL('../apps/web/public/timeline-scroll/'+info.file,import.meta.url));
   assert.equal(data.length,info.bytes);assert.equal(createHash('sha256').update(data).digest('hex'),info.sha256);
   assert.match(info.file,/-[a-f0-9]{16}\.webp$/);
  }
 }
 assert.equal(cursor,panel.crop.x+panel.crop.width,'All pixels in the reviewed crop are covered');
}
const old=scrollPanels.at(-1),selection=visibleScrollTiles(old,800,1000);
assert.ok(selection.visible.length>0&&selection.visible.length<manifest.panels.at(-1).tiles.length,'A narrow annual window fetches a subset of the long scroll');
assert.equal(visibleScrollTiles(scrollPanels[0],800,1000,scrollPanels[1]).visible.length,0,'Offscreen ancient images do not load on a medieval page');
assert.equal(visibleScrollTiles(old,scrollStart,annualStart).visible.length,0,'Ancient pages do not fetch the old full scroll');
for(let i=0;i<scrollPanels.length-1;i++){
 const next=scrollPanels[i+1];
 assert.equal(visibleScrollTiles(scrollPanels[i],next.from_position+200,next.from_position+300,next).visible.length,0,'Fully covered reference overlaps are not fetched');
}
const firstBytes=selection.atlas.preview.bytes+selection.visible.reduce((sum,t)=>sum+t.low.bytes,0);
const original=(await readFile(new URL('../apps/web/public/timeline-scroll/history-scroll-v6.webp',import.meta.url))).length;
assert.ok(firstBytes<original*.15,'First viewport payload is materially smaller than the full source');
console.log(JSON.stringify({verified:true,first_view_low_plus_preview_bytes:firstBytes,original_bytes:original,visible_tiles:selection.visible.length,total_old_tiles:selection.atlas.tiles.length,payload_reduction_percent:Math.round((1-firstBytes/original)*100)},null,2));
