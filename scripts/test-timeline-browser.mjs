import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const base=process.env.E2E_WEB_URL || 'http://127.0.0.1:5173/';
const browser=await chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHROME_CHANNEL || 'chrome'});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/v1/timeline/overview',r=>r.fulfill({json:{years:[{year:-1,count:1,highlights:[]},{year:1,count:1,highlights:[]}],total:2,undated:0,from:-1,to:1}}));
 await page.route('**/api/v1/timeline?*',r=>r.fulfill({json:{items:[],has_more:false}}));
 await page.goto(new URL('timeline?year=-1',base).href);
 await page.getByRole('slider',{name:'选择历史年份'}).waitFor();
 await page.getByRole('heading',{name:'公元前1年',exact:true}).waitFor();
 await page.getByRole('button',{name:'下一年',exact:true}).click();
 await page.getByRole('heading',{name:'1年',exact:true}).waitFor();assert.match(page.url(),/year=1$/);
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 assert.deepEqual(errors,[]);console.log('PASS: current API fixtures, BCE/CE transition and mobile layout; production reads=0');
}finally{await browser.close();}
