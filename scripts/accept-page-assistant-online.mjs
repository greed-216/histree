import assert from 'node:assert/strict';
import { writeFile,readFile } from 'node:fs/promises';
import {chromium} from 'playwright';
assert.equal(process.env.HISTREE_REAL_ASK_ACCEPTANCE, '1', 'Set HISTREE_REAL_ASK_ACCEPTANCE=1 to run one real, quota-consuming question.');
const base=(process.env.E2E_WEB_URL || 'https://123.56.189.146').replace(/\/$/, '');
const id='88309f5d-4302-5431-97c9-98505a221fdf';
const dir='content/books/zizhi-tongjian/vol-015/from-start/event-structure-pilot-2026-10-13/part-01';
const batch=JSON.parse(await readFile(`${dir}/content-batch.json`,'utf8'));
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const errors=[];page.on('pageerror',err=>errors.push(err.message));
 let requestBody;let result;let httpStatus;
 page.on('request',r=>{if(r.url()===`${base}/api/v1/ask`&&r.method()==='POST') requestBody=r.postDataJSON();});
 const answerResponse=new Promise((resolve,reject)=>page.on('response',async r=>{
  if(r.url()===`${base}/api/v1/ask`&&r.request().method()==='POST') {
   try {httpStatus=r.status();const lines=(await r.text()).trim().split('\n').map(x=>JSON.parse(x));result=lines.find(x=>x.type==='result'); resolve();} catch(e){reject(e);}
  }
 }));
 await page.goto(`${base}/events/${id}`);
 await page.locator('.event-narrative').waitFor();
 await page.getByRole('button',{name:'✦ 本页助手',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'本页阅读助手'});
 await dialog.getByText('提问时查阅本页及相关已发布史料，回答附出处。',{exact:true}).waitFor();
 const question='贾谊为什么建议改封刘武？请区分他的建议与文帝实际做成的事。';
 await dialog.getByLabel('向本页助手提问').fill(question);
 await dialog.getByRole('button',{name:'提问 ↑',exact:true}).click();
 await dialog.locator('.assistant-turn .assistant-answer').waitFor({timeout:120000});
 await answerResponse;
 assert.equal(httpStatus,200);assert.deepEqual(requestBody.context,{kind:'event',id});
 assert(result?.answer.length>30); assert(result.citations.length>0);assert.equal(result.insufficientEvidence,false);
 assert(result.citations.some(c=>c.subjectId===id),'Response cites this exact event');
 const snapshot=await readFile(`${dir}/sources/zizhi-tongjian-a63549944a71-p000164/source.txt`,'utf8');
 for(const c of result.citations.filter(c=>c.subjectId===id)) {
  assert(c.quote&&snapshot.includes(c.quote),'Event quote is verbatim in pinned source');
 }
 assert.equal(await dialog.locator('.assistant-evidence').count(),result.citations.length);
 const first=dialog.locator('.assistant-evidence').first();
 await first.locator('summary').click();
 assert((await first.locator('blockquote').textContent()).length>0);
 assert((await first.locator('a').getAttribute('href')).includes('#claim-'));
 assert.deepEqual(errors,[]);
 await page.screenshot({path:'/tmp/histree-online-assistant.png',fullPage:true});
 const audit={date:'2026-10-14',url:page.url(),question,requestContext:requestBody.context,httpStatus,answer:result.answer,citations:result.citations,insufficientEvidence:result.insufficientEvidence,realModelAnswer:true,sourceQuotesVerified:true,browserErrors:errors};
 await writeFile(`${dir}/assistant-online-acceptance.json`,JSON.stringify(audit,null,2)+'\n');
 console.log(JSON.stringify(audit));
} finally {await browser.close();}
