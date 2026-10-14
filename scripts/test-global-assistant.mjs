import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';
const base=process.env.E2E_WEB_URL || 'http://127.0.0.1:5178';
const person='3ddce59a-2d7a-5a32-8c6e-d09d330d167f';
const jiayi='a49e6156-fa49-5f34-9a0a-f99e0b47d788';
const event='88309f5d-4302-5431-97c9-98505a221fdf';
await mkdir('/tmp/histree-global-assistant',{recursive:true});
const browser=await chromium.launch({headless:true,channel:'chrome'});
const errors=[];
try {
 for(const width of [1280,390,320]) {
  const page=await browser.newPage({viewport:{width,height:900}});
  page.on('pageerror',e=>errors.push(e.message));
  for(const id of [person,jiayi]) {
   const stored=await page.request.get(`${base}/api/v1/entry/${id}`);assert(stored.ok());const row=await stored.json();
   await page.goto(`${base}/people/${id}`);await page.locator('.person-overview > p').first().waitFor();
   assert.equal(await page.locator('.entry-reading-page aside').count(),0);
   const context = await (await page.request.get(`${base}/api/v1/entry-context/${id}`)).json();
   const roles = context.edges.filter(e => e.subject_table === 'person_event').map(e => e.type).filter(role => role !== '参与');
   for (const role of await page.locator('.person-event-role').allTextContents()) assert(roles.includes(role.replace('在这件事中 · ', '')));
   assert.deepEqual(await page.locator('.person-overview > p').allTextContents(),(row.description || '人物简介正在整理。').split(/\r?\n\s*\r?\n/).filter(Boolean));
   await page.locator('.entry-source-names').waitFor();
   await page.getByRole('navigation',{name:'本页阅读'}).getByRole('link',{name:'史料依据'}).click();assert(await page.locator('#evidence').evaluate(e=>e.open));
   await page.getByRole('button',{name:'✦ 史料助手',exact:true}).click();
   const dialog=page.getByRole('dialog',{name:'史料助手',exact:true});await dialog.waitFor();
   assert((await dialog.locator('.assistant-context').textContent()).includes(row.name));
   await dialog.getByLabel('向本页助手提问').fill('请解释这个人物。');
   await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});
   await page.getByRole('button',{name:'✦ 史料助手',exact:true}).click();
   assert.equal(await dialog.getByLabel('向本页助手提问').inputValue(),'请解释这个人物。');
   const geom=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,header:document.querySelector('.site-header').getBoundingClientRect().bottom,launcher:document.querySelector('.entry-assistant-launcher').getBoundingClientRect().bottom}));assert(geom.scroll<=width);
   if(width<=640)assert(geom.launcher<=geom.header);
   await page.screenshot({path:`/tmp/histree-global-assistant/person-assistant-${id}-${width}.png`});
   await page.keyboard.press('Escape');await page.locator('#evidence > summary').click();await page.evaluate(()=>scrollTo(0,0));
   await page.screenshot({path:`/tmp/histree-global-assistant/person-${id}-${width}.png`,fullPage:true});
  }
  await page.goto(`${base}/events/${event}`);await page.locator('.event-narrative').waitFor();
  await page.evaluate(()=>{const text=document.querySelector('.event-narrative > p').firstChild;const r=document.createRange();r.setStart(text,0);r.setEnd(text,18);getSelection().removeAllRanges();getSelection().addRange(r);});
  await page.getByRole('button',{name:/问这句话/}).click();assert((await page.locator('.assistant-selection').textContent()).includes('汉文帝'));await page.keyboard.press('Escape');
  await page.goto(`${base}/graph/${event}`);await page.locator('.graph-detail h2').waitFor();
  await page.getByRole('button',{name:'问这个条目 ✦'}).click();assert((await page.locator('.assistant-context').textContent()).includes('文帝采纳'));await page.keyboard.press('Escape');
  await page.locator('.graph-workspace details > summary').filter({hasText:'关系清单'}).click();
  const relation=page.locator('.graph-workspace details button').filter({hasText:'贾谊'}).first();await relation.click();
  await page.getByRole('button',{name:'问这条关系 ✦'}).click();
  assert((await page.locator('.assistant-context').textContent()).includes('贾谊'));
  await page.waitForFunction(() => document.querySelector('#page-question')?.value === '这条关系是什么意思？有什么史料依据？');
  assert.equal(await page.getByLabel('向本页助手提问').inputValue(),'这条关系是什么意思？有什么史料依据？');
  await page.screenshot({path:`/tmp/histree-global-assistant/graph-relation-${width}.png`,fullPage:true});
  // Desktop panel is non-modal: graph controls remain interactive while it stays open.
  if(width===1280){await page.getByRole('button',{name:'取消选择',exact:true}).click();await page.waitForFunction(() => document.querySelector('.assistant-context')?.textContent.includes('历史图谱'));assert((await page.locator('.assistant-context').textContent()).includes('历史图谱'));}
  await page.keyboard.press('Escape');
  for(const route of ['search?q=贾谊','people','events','']){
   await page.goto(`${base}/${route}`);await page.getByRole('button',{name:'✦ 史料助手',exact:true}).click();await page.getByRole('dialog',{name:'史料助手',exact:true}).waitFor();assert((await page.locator('.assistant-context').textContent()).includes('全站史料'));await page.keyboard.press('Escape');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  console.log(JSON.stringify({width,personNarrativePreserved:true,personSources:true,draftRestored:true,eventSelection:true,graphNodeAndRelation:true,globalPages:true}));
  await page.close();
 }
 // Mock only the model transport in this test to verify request scoping and per-object conversation isolation.
 const page=await browser.newPage();const sent=[];
 await page.route('**/api/v1/ask',async route=>{const body=route.request().postDataJSON();sent.push(body);await route.fulfill({contentType:'application/x-ndjson',body:JSON.stringify({type:'conversation',conversation:'a'.repeat(64)})+'\n'+JSON.stringify({type:'result',answer:'测试回答：仅用于检查上下文传递。',citations:[],insufficientEvidence:true})+'\n'});});
 await page.goto(`${base}/people/${person}`);await page.locator('.person-overview').waitFor();await page.getByRole('button',{name:'✦ 史料助手'}).click();await page.getByText('提问时查阅当前条目及相关已发布史料，回答附出处。',{exact:true}).waitFor();await page.getByLabel('向本页助手提问').fill('这个人是谁？');await page.getByRole('button',{name:'提问 ↑'}).click();await page.locator('.assistant-answer').waitFor();assert.deepEqual(sent[0].context,{kind:'person',id:person});
 await page.keyboard.press('Escape');await page.getByRole('navigation',{name:'主导航'}).getByRole('link',{name:'事件',exact:true}).click();await page.getByRole('button',{name:'✦ 史料助手'}).click();await page.getByText('提问时检索已发布史料，回答附出处。',{exact:true}).waitFor();await page.getByLabel('向本页助手提问').fill('贾谊做了什么？');await page.getByRole('button',{name:'提问 ↑'}).click();await page.locator('.assistant-answer').waitFor();assert.equal(sent[1].context,undefined);assert.equal(sent[1].conversation,undefined);
 await page.getByLabel('阅读中的讨论').selectOption(`person:${person}`);assert((await page.locator('.assistant-context').textContent()).includes('刘恒'));assert.equal(await page.locator('.assistant-answer').count(),1);await page.keyboard.press('Escape');
 await page.goto(`${base}/graph/${event}`);await page.locator('.graph-detail h2').waitFor();await page.locator('.graph-workspace details > summary').filter({hasText:'关系清单'}).click();await page.locator('.graph-workspace details button').filter({hasText:'贾谊'}).first().click();await page.getByRole('button',{name:'问这条关系 ✦'}).click();await page.getByText('提问时查阅当前条目及相关已发布史料，回答附出处。',{exact:true}).waitFor();await page.getByRole('button',{name:'提问 ↑'}).click();await page.locator('.assistant-answer').waitFor();assert.equal(sent[2].context.kind,'person_event');assert(sent[2].context.id!==event);assert(sent[2].question.includes('贾谊'));assert.equal(sent[2].conversation,undefined);
 assert.deepEqual(errors,[]);console.log('Context-specific requests, past discussions and independent conversations verified.');
} finally {await browser.close();}
