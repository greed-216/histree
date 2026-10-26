import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const ts=createRequire(new URL('../apps/web/package.json',import.meta.url))('typescript');
const moduleUrl=source=>'data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64');
const viewportUrl=moduleUrl(await readFile(new URL('../apps/web/src/lib/timelineViewport.ts',import.meta.url),'utf8'));
const scroll=JSON.parse(await readFile(new URL('../apps/web/src/data/history-scroll.json',import.meta.url),'utf8'));
const source=(await readFile(new URL('../apps/web/src/lib/historyScroll.ts',import.meta.url),'utf8')).replace('import scroll from "../data/history-scroll.json";',`const scroll=${JSON.stringify(scroll)};`).replace('"./timelineViewport"',JSON.stringify(viewportUrl));
const {ancientChapters,annualStart,scrollStart,scrollPanels,scrollPanelGeometry,scrollPositionLabel,chapterAtPosition,chapterById,scrollYearX}=await import(moduleUrl(source));
assert.equal(annualStart,-841);
assert.equal(ancientChapters.at(-1).to,annualStart,'Chapter positions end exactly at the annual threshold');
assert.equal(ancientChapters.reduce((sum,c)=>sum+c.width_pixels,0),1600);
for(let i=0;i<ancientChapters.length;i++){
 const c=ancientChapters[i];assert.equal(c.from_year,undefined,'Chapter bounds never assert calendar dates');
 assert.equal(chapterAtPosition((c.from+c.to)/2)?.id,c.id);
 assert.equal(scrollPositionLabel((c.from+c.to)/2),c.label);
 if(i)assert.ok(Math.abs(ancientChapters[i-1].to-c.from)<1e-9,'Chapter bounds are continuous');
}
assert.equal(chapterAtPosition(annualStart),undefined);
assert.equal(chapterById('untrusted-chapter'),undefined);
assert.equal(scrollPositionLabel(-841),'前841年');
assert.equal(scrollPositionLabel(-1),'前1年');assert.equal(scrollPositionLabel(0),'1年');
assert.equal(scrollPositionLabel(-0.1),'1年','Rounding a fractional viewport endpoint never introduces year zero');
const from=scrollStart,to=1911;
const geometry=scrollPanels.map(p=>scrollPanelGeometry(p,from,to));
for(const g of geometry)assert.ok(Math.abs(g.height-geometry[0].height)<1e-9,'All paintings share the same height without stretching');
assert.ok(Math.abs((scrollYearX(-403,from,to)-scrollYearX(-841,from,to))*scroll.pixels_per_elapsed_year*(to-from)/920-1771.685393258427)<1e-7,'438 annual years keep the existing artwork scale');
assert.ok(Math.abs((scrollYearX(1,from,to)-scrollYearX(-1,from,to))-(scrollYearX(2,from,to)-scrollYearX(1,from,to)))<1e-9,'Annual positions have no year zero');
for(const panel of scrollPanels){const bytes=await readFile(new URL('../apps/web/public/timeline-scroll/'+panel.file,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),panel.sha256,panel.file);}
assert.equal(scrollPanels.at(-1).sha256,'04eadb90c98471d1dc08dbd3453bfdbddbe998594e600c202c5c9a6bb208606f','The existing source artwork is unchanged');
console.log('PASS: undated chapters, continuous 841 BCE threshold, 438-year artwork scale, equal panel heights, no year zero, and preserved source bytes.');
