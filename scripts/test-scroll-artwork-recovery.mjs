import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const base=process.env.E2E_WEB_URL || 'http://127.0.0.1:5194/';
const artwork=fileURLToPath(new URL('../apps/web/public/timeline-scroll/history-scroll-v6.webp',import.meta.url));
const imagePath='**/timeline-scroll/history-scroll-v6.webp';
const emptySvg='<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"></svg>';
const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHROME_CHANNEL || 'chrome'});
try {
 for(const mode of ['normal','zero-size','image-error','invalid-recovery']) {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];let fetches=0;
  page.on('pageerror',error=>errors.push(error.message));
  await page.addInitScript(()=>{
   window.__revokedArtwork=[];
   const revoke=URL.revokeObjectURL.bind(URL);
   URL.revokeObjectURL=url=>{window.__revokedArtwork.push(url);revoke(url);};
  });
  await page.route('**/api/v1/**',route=>{
   const path=new URL(route.request().url()).pathname;
   if(path.endsWith('/timeline/overview'))return route.fulfill({json:{years:[{year:907,count:1,highlights:[]}],total:1,undated:0,from:907,to:907}});
   if(path.endsWith('/timeline'))return route.fulfill({json:{items:[],has_more:false}});
   return route.fulfill({status:404,json:{message:'test fixture'}});
  });
  await page.route(imagePath,route=>{
   if(route.request().resourceType()==='fetch') {
    fetches++;
    return mode==='invalid-recovery'
     ? route.fulfill({contentType:'image/webp',body:'not the published image'})
     : route.fulfill({contentType:'image/webp',path:artwork});
   }
   if(mode==='normal')return route.fulfill({contentType:'image/webp',path:artwork});
   if(mode==='image-error')return route.fulfill({status:404,body:'missing'});
   return route.fulfill({contentType:'image/svg+xml',body:emptySvg});
  });
  await page.goto(mode==='zero-size' ? new URL('?scroll-debug=1',base).href : base);
  await page.locator('.home-timeline').scrollIntoViewIfNeeded();
  const image=page.locator('[data-history-backdrop] image');
  await image.waitFor();
  if(mode==='normal') {
   await image.evaluate(async node=>{const probe=new Image();probe.src=node.getAttribute('href');await probe.decode();assertWidth(probe);function assertWidth(image){if(image.naturalWidth!==9360)throw Error('Normal artwork did not decode');}});
   assert.equal(await image.getAttribute('data-artwork-status'),'original');
   assert.equal(fetches,0,'Healthy images must not trigger a binary retry');
  } else if(mode==='invalid-recovery') {
   await page.waitForFunction(()=>document.querySelector('[data-history-backdrop] image')?.dataset.artworkStatus==='failed');
   assert.ok(!(await image.getAttribute('href')).startsWith('blob:'),'Unexpected response must not replace the artwork');
   assert.equal(fetches,1);
  } else {
   await page.waitForFunction(()=>document.querySelector('[data-history-backdrop] image')?.dataset.artworkStatus==='blob');
   const url=await image.getAttribute('href');
   assert.ok(url.startsWith('blob:'));
   assert.equal(await image.getAttribute('xlink:href'),url);
   assert.equal(await image.getAttribute('data-artwork-bytes'),'3865286');
   const dimensions=await image.evaluate(async node=>{const probe=new Image();probe.src=node.getAttribute('href');await probe.decode();return [probe.naturalWidth,probe.naturalHeight];});
   assert.deepEqual(dimensions,[9360,720]);
   if(mode==='zero-size') {
    const originalDimensions=await page.evaluate(()=>new Promise((resolve,reject)=>{const probe=new Image();probe.onload=()=>resolve([probe.naturalWidth,probe.naturalHeight]);probe.onerror=reject;probe.src='/timeline-scroll/history-scroll-v6.webp';}));
    assert.deepEqual(originalDimensions,[0,0],'Reproduce a load callback with unavailable image dimensions');
    await page.waitForFunction(()=>{
     try {
      const report=JSON.parse(document.querySelector('#scroll-runtime-panel textarea').value);
      return report.image.attrs.href.startsWith('blob:') && report.decodedImage.width===9360;
     } catch {return false;}
    });
   }
   await page.getByRole('button',{name:'前一段历史',exact:true}).click();
   assert.equal(await image.getAttribute('href'),url,'Panning keeps the recovered image alive');
   assert.equal(fetches,1,'Retry is bounded to one fetch');
   await page.getByRole('link',{name:'搜索',exact:true}).click();
   await page.waitForFunction(url=>window.__revokedArtwork.includes(url),url);
  }
  assert.deepEqual(errors,[]);
  await page.close();
  console.log(`PASS: artwork ${mode}; binary retries=${fetches}`);
 }
 console.log('PASS: real zero-size load event, image error recovery, invalid body rejection, pan stability and object URL cleanup; production API/model calls=0');
} finally {await browser.close();}
