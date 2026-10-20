// Real local Nest HTTP flow, no mocked clue responses or model calls.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const base=(process.env.E2E_WEB_URL||'http://127.0.0.1:5197/').replace(/\/?$/,'/');
const browser=await chromium.launch({headless:true,channel:'chrome'}),errors=[];
try{
 for(const viewport of [{width:1280,height:1000},{width:390,height:844}]){
  const context=await browser.newContext({viewport}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'ask?mode=guess');
  await page.getByRole('button',{name:'给我第一条线索',exact:true}).waitFor();
  await page.waitForFunction(()=>![...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='给我第一条线索')?.disabled);
  await page.screenshot({path:`/private/tmp/histree-clue-setup-${viewport.width}.png`,fullPage:true});
  const initial=page.waitForResponse(r=>r.url().endsWith('/clues/start')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'给我第一条线索',exact:true}).click();
  const data=await (await initial).json();assert.equal(data.clues.length,1);assert(!data.person&&!data.evidence);
  const list=page.getByRole('list',{name:'人物线索'});await list.locator('li').first().waitFor();assert.equal(await list.locator('li').count(),1);
  const input=page.getByLabel('想到是谁了吗？');await input.fill('绝不可能的测试名字');
  await input.dispatchEvent('compositionstart');await input.press('Enter');assert.equal(await page.getByRole('status').count(),0);await input.dispatchEvent('compositionend');
  await page.getByRole('button',{name:'猜一下',exact:true}).click();await page.getByRole('status').filter({hasText:'还没猜中'}).waitFor();assert.equal(await list.locator('li').count(),1);
  await input.fill('先留着的猜测');await page.getByRole('button',{name:'再看一条 · 第 2 条',exact:true}).click();await page.getByRole('button',{name:'再看一条 · 第 3 条',exact:true}).waitFor();assert.equal(await input.inputValue(),'先留着的猜测');assert.equal(await list.locator('li').count(),2);
  await page.reload();await page.getByRole('button',{name:'再看一条 · 第 3 条',exact:true}).waitFor();assert.equal(await page.getByRole('list',{name:'人物线索'}).locator('li').count(),2);
  await page.getByText('还没想到，想看看答案？',{exact:true}).click();
  const response=page.waitForResponse(r=>r.url().endsWith('/clues/act')&&r.request().postDataJSON().action==='reveal');await page.getByRole('button',{name:'结束并揭晓答案',exact:true}).click();
  const ended=await (await response).json();await page.getByRole('heading',{name:ended.person.name,exact:true}).waitFor();assert.equal(ended.outcome,'revealed');assert.equal(ended.clues.length,6);
  const person=page.getByRole('region',{name:'人物揭晓'});assert.equal(await person.getByRole('link').count(),ended.person.id?2:0);
  await page.getByText('看看线索里的故事',{exact:true}).click();await page.getByText(ended.evidence[0].explanation,{exact:true}).waitFor();
  const ratings=page.getByRole('region',{name:'难度评价'});await ratings.waitFor();
  assert.equal(await ratings.getByRole('button').count(),3);
  let failRating=true;
  await context.route('**/api/v1/ask/guess/clues/feedback',async route=>{
    if(failRating){failRating=false;return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({message:'难度反馈未能保存，请重试。'})})}
    return route.continue();
  });
  await ratings.getByRole('button',{name:'刚刚好',exact:true}).click();await page.getByRole('alert').filter({hasText:'未能保存'}).waitFor();
  assert.equal(await ratings.getByRole('button',{name:'刚刚好',exact:true}).isEnabled(),true);
  await ratings.getByRole('button',{name:'刚刚好',exact:true}).click();await ratings.getByRole('status').filter({hasText:'已收到'}).waitFor();
  assert.equal(await ratings.getByRole('button',{name:'刚刚好',exact:true}).getAttribute('aria-pressed'),'true');
  assert.equal(await ratings.getByRole('button',{name:'太难了',exact:true}).isDisabled(),true);
  await page.reload();await page.getByRole('region',{name:'难度评价'}).getByRole('status').filter({hasText:'已收到'}).waitFor();

  assert((await page.evaluate(()=>document.documentElement.scrollWidth))<=viewport.width,'No horizontal overflow');
  await page.screenshot({path:`/private/tmp/histree-clue-ended-${viewport.width}.png`,fullPage:true});
  await context.close();console.log(`PASS actual clue HTTP + browser ${viewport.width}px`);
 }
 assert.deepEqual(errors,[]);
}finally{await browser.close()}
