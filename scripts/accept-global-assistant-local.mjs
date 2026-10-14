import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
assert.equal(process.env.HISTREE_REAL_ASK_ACCEPTANCE,'1','Explicitly opt in to two real model requests.');
const base='http://127.0.0.1:5178';
const person='a49e6156-fa49-5f34-9a0a-f99e0b47d788';
const event='88309f5d-4302-5431-97c9-98505a221fdf';
const browser=await chromium.launch({headless:true,channel:'chrome'});
const audit=[];await mkdir('/tmp/histree-global-assistant',{recursive:true});
try {
 for(const kind of ['person','relation']) {
  const page=await browser.newPage({viewport:{width:1440,height:900}});
  let body;let response;
  await page.addInitScript(() => {
    const original = window.fetch;
    window.fetch = async (...args) => {
      const result = await original(...args);
      if (String(args[0]).endsWith('/api/v1/ask')) result.clone().text().then(text => { window.__assistantResult = text.trim().split('\n').filter(Boolean).map(x => JSON.parse(x)).find(x => x.type === 'result'); });
      return result;
    };
  });
  page.on('request',r=>{if(r.url()===`${base}/api/v1/ask`&&r.method()==='POST')body=r.postDataJSON();});
  if(kind==='person'){
   await page.goto(`${base}/people/${person}`);await page.locator('.person-overview').waitFor();await page.getByRole('button',{name:'✦ 史料助手'}).click();
  }else{
   await page.goto(`${base}/graph/${event}`);await page.locator('.graph-detail h2').waitFor();await page.locator('.graph-workspace details > summary').filter({hasText:'关系清单'}).click();await page.locator('.graph-workspace details button').filter({hasText:'贾谊'}).first().click();await page.getByRole('button',{name:'问这条关系 ✦'}).click();
  }
  await page.getByText('提问时查阅当前条目及相关已发布史料，回答附出处。',{exact:true}).waitFor();
  const question=kind==='person'?'贾谊在改封刘武为梁王这件事中做了什么？':'图上这条贾谊与改封事件的连线是什么意思？请给出这条参与记录的出处。';
  await page.getByLabel('向本页助手提问').fill(question);await page.getByRole('button',{name:'提问 ↑',exact:true}).click();
  await Promise.race([page.locator('.assistant-answer').waitFor({timeout:125000}), page.getByRole('alert').waitFor({timeout:125000}).then(async()=>{throw new Error(await page.getByRole('alert').innerText());})] );await page.waitForFunction(() => window.__assistantResult);response = await page.evaluate(() => window.__assistantResult);
  assert(response?.answer);assert.equal(response.insufficientEvidence,false);assert(response.citations.length>0);
  assert.equal(body.context.kind,kind==='person'?'person':'person_event');if(kind==='person')assert.equal(body.context.id,person);else assert(response.citations.some(c=>c.subjectId===body.context.id),'Answer must cite the exact selected relation');
  for(const c of response.citations){const params=new URLSearchParams({subject:c.subjectTable,subject_id:c.subjectId,claim:c.claimId});const readback=await page.request.get(`${base}/api/v1/catalog/fact_claim?${params}`);assert(readback.ok());const claim=(await readback.json()).items.find(x=>x.id===c.claimId);assert(claim?.note);assert.equal(claim.note.slice(3).split('；核对说明：')[0],c.quote);}
  const source=page.locator('.assistant-evidence').first();await source.locator('summary').click();assert((await source.locator('blockquote').textContent()).length>0);await page.screenshot({path:`/tmp/histree-global-assistant/real-${kind}.png`});
  audit.push({kind,url:page.url(),question,context:body.context,answer:response.answer,citationCount:response.citations.length,relationCited:kind==='relation',quotesMatchPublishedClaims:true});
  console.log(JSON.stringify(audit.at(-1)));await page.close();
 }
 await writeFile('/tmp/histree-global-assistant/real-answers.json',JSON.stringify(audit,null,2)+'\n');
}finally{await browser.close();}
