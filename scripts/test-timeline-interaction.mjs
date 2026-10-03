import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const base=process.env.TIMELINE_TEST_URL||'http://127.0.0.1:5176/histree/timeline';
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];let yearRequests=0;
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.url().includes('/rest/v1/event?')||r.url().includes('/timeline?year='))yearRequests++;});
 await page.goto(`${base}?year=900`);
 await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
 const slider=page.getByRole('slider',{name:'选择历史年份'});
 const min=Number(await slider.getAttribute('min')),max=Number(await slider.getAttribute('max'));
 const ordinal=y=>y<0?y:y-1;
 async function point(ratio,click=false) {
  const p=await page.locator('.timeline-chart').evaluate((svg,ratio)=>{const p=new DOMPoint(40+ratio*920,208).matrixTransform(svg.getScreenCTM());return{x:p.x,y:p.y};},ratio);
  await page.mouse.move(p.x,p.y);if(click)await page.mouse.click(p.x,p.y);
 }
 const requestsBefore=yearRequests;
 await page.evaluate(()=>scrollTo(0,180));const scrollBefore=await page.evaluate(()=>scrollY);
 const ratio907=(ordinal(907)-min)/(max-min);
 await point(ratio907);
 await page.getByRole('complementary',{name:'年度大事提要'}).getByRole('heading',{name:'907年',exact:true}).waitFor();
 assert.match(await page.getByRole('complementary',{name:'年度大事提要'}).innerText(),/朱温称帝，后梁建立/);
 await page.waitForTimeout(600);
 assert.equal(yearRequests,requestsBefore,'Hover sends no event queries');
 assert.match(page.url(),/year=900$/,'Hover does not change fixed URL year');
 assert.equal(await slider.inputValue(),String(ordinal(900)),'Hover does not change fixed selection');
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-scrollBefore)<2,'Hover preserves scroll');
 await page.evaluate(()=>scrollTo(0,0));await point(ratio907);
 await page.screenshot({path:'/tmp/histree-timeline-preview-v2.png'});
 await page.evaluate(()=>scrollTo(0,180));
 await point(ratio907,true);
 await page.waitForURL(/year=907$/);
 await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
 assert.equal(await slider.inputValue(),String(ordinal(907)));
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-scrollBefore)<2,'Click preserves scroll');
 const afterClick=yearRequests;
 for(const ratio of [.3,.4,.5,.6]){await point(ratio);await page.waitForTimeout(250);}
 assert.equal(yearRequests,afterClick,'Even prolonged hovering does not refetch list');
 await page.mouse.move(5,5);assert.equal(await slider.inputValue(),String(ordinal(907)));
 const zoom=page.getByRole('button',{name:'放大当前年代'});await zoom.focus();await zoom.press('Enter');
 const ticks=await page.locator('.timeline-chart text').allTextContents();await point(.4);
 assert.deepEqual(await page.locator('.timeline-chart text').allTextContents(),ticks,'Hover leaves zoom axis fixed');
 const card=page.getByRole('link',{name:/阅读全文与出处/}).first();await card.scrollIntoViewIfNeeded();const returnScroll=await page.evaluate(()=>scrollY);
 await card.click();await page.waitForURL(/events\//);await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>scrollY),0);
 await page.goBack();await slider.waitFor();await page.waitForTimeout(400);
 assert.ok(Math.abs(await page.evaluate(()=>scrollY)-returnScroll)<3,'Back restores fixed year scroll');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.screenshot({path:'/tmp/histree-timeline-preview-v2-mobile.png'});
 assert.deepEqual(errors,[]);
 console.log('PASS: local yearly highlights, zero hover requests, click locks year/list, no scroll reset, fixed zoom, Back restoration and mobile layout.');
}finally{await browser.close();}
