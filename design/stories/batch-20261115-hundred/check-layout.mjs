import assert from 'node:assert/strict';
import { readFile,writeFile,mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';
const root=new URL('../../../',import.meta.url);
const out=new URL('artifacts/stories-hundred-20261115/',root);await mkdir(out,{recursive:true});
const spec=JSON.parse(await readFile(new URL('scripts.json',import.meta.url),'utf8')).stories;
const catalog=JSON.parse(await readFile(new URL('apps/web/src/data/stories.json',root),'utf8')).stories;
const fresh=catalog.filter(s=>spec.some(x=>x.slug===s.slug));assert.equal(fresh.length,50);assert.equal(catalog.length,100);
const base=process.env.STORY_BASE||'http://127.0.0.1:48751';
const browser=await chromium.launch({headless:true,channel:'chrome'});
const results=[];const requests=[];
try {
  for (const viewport of [{width:1440,height:693},{width:390,height:844},{width:360,height:640},{width:844,height:390}]) {
    const context=await browser.newContext({viewport});const page=await context.newPage();
    page.on('request',r=>{if(r.url().includes('/media/images/'))requests.push(r.url());});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    for(const story of fresh) {
      await page.goto(`${base}/stories/${story.slug}`,{waitUntil:'domcontentloaded'});
      await page.locator('.story-reader').waitFor();
      const count=story.panels.length+3;
      for(let index=0;index<count;index++) {
        await page.waitForFunction(i=>document.querySelector('.story-reading-surface')?.getAttribute('data-page')===String(i+1),index);
        if(index>0 && index<=story.panels.length) await page.waitForFunction(()=>{
          const img=document.querySelector('.story-book img');return img?.complete&&img.naturalWidth>0;
        },undefined,{timeout:60000}).catch(async error=>{
          const image=await page.locator('.story-reading-surface').innerHTML();
          await page.screenshot({path:new URL('layout-failure.png',out).pathname});
          throw new Error(`${story.slug}/${index} at ${viewport.width}: ${image}\n${error.message}`);
        });
        const state=await page.evaluate(()=>{
          const surface=document.querySelector('.story-reading-surface');
          const prose=document.querySelector('.story-prose-page');
          const rect=document.querySelector('.story-reader-controls').getBoundingClientRect();
          const content=document.querySelector('.story-book')||prose;
          const c=content.getBoundingClientRect();
          return {chapter:surface.dataset.chapter,documentOverflow:document.documentElement.scrollHeight-innerHeight,
            documentWidth:document.documentElement.scrollWidth-innerWidth,
            proseOverflow:prose?prose.scrollHeight-prose.clientHeight:0,
            contentTop:c.top,contentBottom:c.bottom,controlsBottom:rect.bottom,height:innerHeight};
        });
        results.push({slug:story.slug,viewport,page:index+1,...state});
        assert.ok(state.documentOverflow<=1 && state.documentWidth<=1,JSON.stringify(results.at(-1)));
        assert.ok(state.contentTop>=0 && state.contentBottom<=state.height+1 && state.controlsBottom<=state.height+1,JSON.stringify(results.at(-1)));
        assert.ok(state.proseOverflow<=1,JSON.stringify(results.at(-1)));
        if(story.slug==='zhang-qian-shi-xi-yu' && [1,story.panels.length+1,story.panels.length+2].includes(index))
          await page.screenshot({path:new URL(`layout-${viewport.width}-${index}.png`,out).pathname});
        if(index<count-1)await page.keyboard.press('ArrowRight');
      }
    }
    assert.deepEqual(errors,[]);
    await context.close();
  }
  assert.ok(!requests.some(url=>url.endsWith('.png')),'Normal reading must not request original PNGs');
  await writeFile(new URL('layout.json',out),JSON.stringify({states:results,requests:[...new Set(requests)]},null,2));
  console.log(`PASS ${results.length} actual page states, images loaded, afterwords/takeaways visible, original PNGs not requested`);
} finally {await browser.close();}
