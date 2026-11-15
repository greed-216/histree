import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const root=new URL('../../../',import.meta.url);
const out=new URL('artifacts/stories-hundred-20261115/',root);
const stories=JSON.parse(await readFile(new URL('apps/web/src/data/stories.json',root),'utf8')).stories;
const browser=await chromium.launch({channel:'chrome',headless:true});
const results={shelf:0,samples:[],errors:[],requests:[]};
const page=await browser.newPage({viewport:{width:360,height:640}});
page.on('pageerror',e=>results.errors.push(e.message));
page.on('request',r=>{if(r.url().includes('/media/images/'))results.requests.push(r.url());});
async function jump(label){await page.keyboard.press('Escape');await page.getByRole('button',{name:'目录',exact:true}).click();await page.getByRole('button',{name:label,exact:true}).click();}
try {
  await page.goto('https://histree.wiki/stories',{waitUntil:'domcontentloaded'});
  await page.locator('.story-card').first().waitFor();
  results.shelf=await page.locator('.story-card').count();assert.equal(results.shelf,100);
  for(const story of stories)assert.ok(await page.locator(`.story-card h2 a[href="/stories/${story.slug}"]`).count());
  await page.screenshot({path:new URL('live-shelf.png',out).pathname});
  for(const slug of ['kong-zi-xue-qin','zhang-qian-shi-xi-yu','xi-men-bao-zhi-ye']) {
    const story=stories.find(s=>s.slug===slug);
    await page.goto('https://histree.wiki/stories/'+slug,{waitUntil:'domcontentloaded'});
    await page.locator('.story-reader').waitFor();
    await page.getByRole('button',{name:'翻开故事 →',exact:true}).click();
    await page.waitForFunction(()=>{const i=document.querySelector('.story-book img');return i?.complete&&i.naturalWidth>0;},undefined,{timeout:60000});
    await jump('故事后记');
    assert.equal(await page.locator('.story-prose-copy').count(),story.afterword.paragraphs.length);
    assert.ok(await page.locator('.story-prose-afterword').evaluate(el=>el.scrollHeight<=el.clientHeight+1));
    if(slug==='kong-zi-xue-qin') {
      await page.screenshot({path:new URL('live-afterword.png',out).pathname});
      const before=await page.locator('.story-reading-surface').getAttribute('data-page');
      await page.getByRole('button',{name:'目录',exact:true}).click();
      const [source]=await Promise.all([page.waitForEvent('popup'),page.locator('#story-directory a').filter({hasText:'读原文'}).click()]);
      const pid=new URL(story.sourceLinks[0].url,'https://histree.wiki').searchParams.get('paragraph');
      await source.locator('#paragraph-'+pid).waitFor({state:'visible',timeout:60000});
      results.sourceUrl=source.url();await source.close();
      const [person]=await Promise.all([page.waitForEvent('popup'),page.locator('#story-directory a').filter({hasText:'人物 · 孔子'}).click()]);
      await person.getByRole('heading',{name:'孔丘（春秋鲁国儒者）',exact:true}).waitFor({timeout:60000});
      results.personUrl=person.url();await person.close();
      assert.equal(await page.locator('.story-reading-surface').getAttribute('data-page'),before);
      results.storyPositionRetained=true;
    }
    await jump('故事寓意');
    assert.equal(await page.locator('.story-prose-meaning .story-prose-copy').innerText(),story.afterword.takeaway.text);
    assert.ok(await page.locator('.story-prose-meaning .story-source-link').count());
    results.samples.push(slug);
  }
  const current=await page.locator('.story-reader').getAttribute('data-story');
  await page.getByRole('button',{name:'随机再看一篇 →',exact:true}).click();
  await page.waitForFunction(slug=>document.querySelector('.story-reader')?.getAttribute('data-story')!==slug,current);
  results.readerRandomExcludesCurrent=(await page.locator('.story-reader').getAttribute('data-story'))!==current;
  assert.ok(results.readerRandomExcludesCurrent);
  await page.getByRole('button',{name:'全屏',exact:true}).click();
  await page.waitForFunction(()=>document.fullscreenElement||document.querySelector('.story-reader-notice'));
  if(await page.evaluate(()=>Boolean(document.fullscreenElement))) {
    results.fullscreen='entered';await page.getByRole('button',{name:'退出全屏',exact:true}).click();
    await page.waitForFunction(()=>!document.fullscreenElement);
  } else {
    assert.ok(await page.locator('.story-reader-notice').count());results.fullscreen='browser_declined_with_notice';
  }
  await page.locator('.story-reader-back').click();
  await page.locator('.site-header').waitFor({state:'visible'});
  assert.ok(await page.locator('footer a[href="https://beian.miit.gov.cn/"]').count());
  await page.getByRole('button',{name:/^随机看故事/}).click();
  await page.locator('.story-reader').waitFor();
  results.randomSlug=await page.locator('.story-reader').getAttribute('data-story');
  assert.ok(stories.some(s=>s.slug===results.randomSlug));
  assert.ok(!results.requests.some(url=>url.endsWith('.png')));
  assert.deepEqual(results.errors,[]);
  await writeFile(new URL('live-reading.json',out),JSON.stringify(results,null,2));
  console.log('PASS live shelf=100, all shelf links, three readers, afterwords/takeaways, source/person tabs, retained position and random entry');
} finally {await browser.close();}
