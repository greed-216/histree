import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
const env = Object.fromEntries((await readFile(new URL('../apps/web/.env.local', import.meta.url), 'utf8')).split('\n').filter(line => /^[A-Z_]+=/.test(line)).map(line => { const i = line.indexOf('='); return [line.slice(0,i),line.slice(i+1).trim().replace(/^['"]|['"]$/g,'')]; }));
const rows = [];
for (let offset = 0; ; offset += 500) {
  const response = await fetch(`${env.VITE_SUPABASE_URL}/rest/v1/event?select=id,start_year,end_year&status=eq.published&order=id&offset=${offset}&limit=500`, {headers:{apikey:env.VITE_SUPABASE_ANON_KEY,Authorization:`Bearer ${env.VITE_SUPABASE_ANON_KEY}`}});
  if (!response.ok) throw new Error(`Published data read failed: ${response.status}`);
  const batch = await response.json(); rows.push(...batch); if (batch.length < 500) break;
}
const dated = rows.filter(row => row.start_year !== null), counts = new Map();
for (const row of dated) counts.set(row.start_year,(counts.get(row.start_year)||0)+1);
const overview = {years:[...counts].sort((a,b)=>a[0]-b[0]).map(([year,count])=>({year,count})),total:rows.length,undated:rows.length-dated.length,from:Math.min(...dated.map(r=>r.start_year)),to:Math.max(...dated.map(r=>Math.max(r.start_year,r.end_year??r.start_year)))};
const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
try {
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  // The new aggregation migration is not deployed. Preview its contract with
  // the same published dates read above; event detail requests remain live.
  await page.route('**/rest/v1/rpc/timeline_overview', route => route.fulfill({json:overview}));
  await page.goto(process.env.TIMELINE_TEST_URL || 'http://127.0.0.1:5174/histree/timeline');
  await page.getByRole('heading',{name:'让历史，沿时间展开'}).waitFor();
  await page.getByRole('slider',{name:'选择历史年份'}).waitFor();
  await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
  await page.getByRole('button',{name:'放大当前年代'}).click();
  assert.equal(await page.getByRole('button',{name:'查看全部年代'}).getAttribute('aria-pressed'),'true');
  await page.getByRole('button',{name:'查看全部年代'}).click();
  await page.getByRole('spinbutton',{name:'跳至年份'}).fill(String(overview.from));
  await page.getByRole('button',{name:'前往',exact:true}).click();
  await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
  assert.match(page.url(),new RegExp(`year=${overview.from}`));
  await page.getByRole('spinbutton',{name:'跳至年份'}).fill('0');
  await page.getByRole('button',{name:'前往',exact:true}).click();
  await page.getByRole('alert').waitFor();
  await page.getByRole('spinbutton',{name:'跳至年份'}).fill('900');
  await page.getByRole('button',{name:'前往',exact:true}).click();
  await page.getByRole('link',{name:/阅读全文与出处/}).first().waitFor();
  await page.screenshot({path:'/tmp/histree-timeline-desktop.png',fullPage:false});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true,'Mobile should not overflow');
  await page.screenshot({path:'/tmp/histree-timeline-mobile.png',fullPage:true});
  await page.unroute('**/rest/v1/rpc/timeline_overview');
  await page.route('**/rest/v1/rpc/timeline_overview', route => route.fulfill({json:{years:[{year:-1,count:1},{year:1,count:1}],total:2,undated:0,from:-1,to:1}}));
  await page.route('**/rest/v1/event?*', route => route.fulfill({json:[]}));
  await page.goto('http://127.0.0.1:5174/histree/timeline?year=-1');
  await page.getByRole('heading',{name:'公元前1年',exact:true}).waitFor();
  await page.getByRole('button',{name:'下一年',exact:true}).click();
  await page.getByRole('heading',{name:'1年',exact:true}).waitFor();
  assert.match(page.url(), /year=1$/);
  assert.deepEqual(errors,[]);
  console.log(`Browser passed with ${rows.length} real published events: navigation, zoom, year jump, invalid year, live year queries, desktop/mobile layout. Overview RPC contract intercepted pending migration.`);
} finally { await browser.close(); }
