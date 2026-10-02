import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const base = process.env.TIMELINE_TEST_URL || 'http://127.0.0.1:5175/histree/timeline';
const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try {
 const page = await browser.newPage({viewport:{width:1440,height:800}});
 const errors=[]; let yearRequests=0;
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.url().includes('/rest/v1/event?') || r.url().includes('/timeline?year=')) yearRequests++;});
 await page.goto(`${base}?year=900`);
 await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
 await page.evaluate(()=>scrollTo(0,220));
 const before=await page.evaluate(()=>scrollY);
 const slider=page.getByRole('slider',{name:'选择历史年份'});
 const min=Number(await slider.getAttribute('min')), max=Number(await slider.getAttribute('max'));
 const calendar=n=>n<0?n:n+1;
 async function hover(ratio) {
  const point=await page.locator('.timeline-chart').evaluate((svg,ratio)=>{const p=new DOMPoint(40+ratio*920,180).matrixTransform(svg.getScreenCTM());return{x:p.x,y:p.y};},ratio);
  await page.mouse.move(point.x,point.y);
 }
 await hover(.6);
 await page.getByRole('heading',{name:`${calendar(Math.round(min+.6*(max-min)))}年`,exact:true}).waitFor();
 await page.waitForTimeout(500);
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-before)<2,'Hover preserves scroll');
 const requestsBefore=yearRequests;
 for(const ratio of [.35,.4,.45,.5,.55,.65])await hover(ratio);
 await page.waitForTimeout(650);
 assert.ok(yearRequests-requestsBefore<=2,'Rapid hover coalesces event requests');
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-before)<2,'Rapid changes preserve scroll');
 const zoom=page.getByRole('button',{name:'放大当前年代'});
 await zoom.focus(); await zoom.press('Enter');
 const axisBefore=await page.locator('.timeline-chart text').allTextContents();
 await hover(.55);await page.waitForTimeout(300);
 assert.deepEqual(await page.locator('.timeline-chart text').allTextContents(),axisBefore,'Zoom axis stays fixed during hover');
 await page.getByRole('button',{name:'查看全部年代'}).focus();await page.getByRole('button',{name:'查看全部年代'}).press('Enter');
 const next=page.getByRole('button',{name:'下一年',exact:true});await next.focus();await next.press('Enter');await page.waitForTimeout(600);
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-before)<2,'Year button preserves scroll');
 const card=page.getByRole('link',{name:/阅读全文与出处/}).first();await card.waitFor();await card.scrollIntoViewIfNeeded();
 const returnScroll=await page.evaluate(()=>scrollY);
 await card.click();await page.waitForURL(/events\//);await page.waitForTimeout(300);
 assert.equal(await page.evaluate(()=>scrollY),0,'Entry navigation starts at top');
 await page.goBack();await page.getByRole('slider').waitFor();await page.waitForTimeout(500);
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-returnScroll)<3,`Back restores timeline position: expected ${returnScroll}, actual ${await page.evaluate(()=>scrollY)}`);
 assert.deepEqual(errors,[]);
 console.log('PASS: hover follows pointer, coalesced requests, stable zoom, no year-change scroll reset, entry navigation and Back restoration.');
} finally {await browser.close();}
