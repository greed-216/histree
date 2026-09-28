import { chromium } from 'playwright';
import { readFile, mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';

// Run against a Vite server configured with the local test URLs documented in FIRST_READING_RELEASE.md.
const base = process.env.E2E_WEB_URL || 'http://127.0.0.1:5175/histree/';
const db = JSON.parse(await readFile(process.env.HISTREE_FIXTURE_PATH || '/tmp/histree-fixture.json', 'utf8'));
const screenshots = process.env.HISTREE_SCREENSHOTS || '/tmp/histree-screenshots';
await mkdir(screenshots, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROME_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHROME_CHANNEL } : {}) });
const errors = [];
const personId = '11111111-1111-1111-1111-111111111008';
const eventId = '22222222-2222-2222-2222-222222222007';
let failTopics = false;
const asNode = (row, type) => ({ ...row, type, image_url: null });
const allNodes = () => [...db.person.map(p => asNode(p, 'person')), ...db.event.map(e => asNode(e, 'event'))];
function graph(id) {
  const center = allNodes().find(n => n.id === id); const edges = [];
  for (const r of db.person_relationship) if ([r.person_a,r.person_b].includes(id)) edges.push({ id:r.id, subject_table:'person_relationship', source:r.person_a, target:r.person_b, type:r.relation_type, description:r.description });
  for (const r of db.person_event) if ([r.person_id,r.event_id].includes(id)) edges.push({ id:r.id, subject_table:'person_event', source:r.person_id, target:r.event_id, type:r.role });
  for (const r of db.event_causality) if ([r.cause_event_id,r.effect_event_id].includes(id)) edges.push({ id:r.id, subject_table:'event_causality', source:r.cause_event_id, target:r.effect_event_id, type:'causes', description:r.description });
  const ids = new Set([id, ...edges.flatMap(e => [e.source,e.target])]);
  return { center, edges, nodes:allNodes().filter(n => ids.has(n.id)) };
}
async function context(options = {}) {
  const ctx = await browser.newContext(options);
  await ctx.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin === new URL(base).origin) return route.continue();
    if (url.origin !== 'http://127.0.0.1:4319') return route.abort();
    const reply = (body, status = 200) => route.fulfill({ status, contentType:'application/json', body:JSON.stringify(body) });
    const path = url.pathname.replace('/api/v1', '');
    if (path.startsWith('/event/') && route.request().method() === 'PATCH') {
      assert.ok(route.request().headers().authorization);
      const row = db.event.find(e => e.id === path.split('/')[2]);
      Object.assign(row,route.request().postDataJSON());
      return reply(row);
    }
    if (path === '/relationships') return reply({person_relationships:db.person_relationship,person_events:db.person_event,event_causalities:db.event_causality});
    if (path === '/people') return reply(db.person.filter(r => r.status === 'published').map(p => asNode(p, 'person')));
    if (path === '/event') return reply(db.event.filter(r => r.status === 'published').map(e => asNode(e, 'event')));
    if (path === '/topics') return reply(failTopics ? { message:'offline' } : db.topic.filter(t => t.status === 'published'), failTopics ? 503 : 200);
    if (path.startsWith('/topics/')) return reply(db.topic.find(t => t.slug === path.split('/')[2]));
    if (path.startsWith('/graph/')) return reply(graph(path.split('/')[2]));
    if (path.startsWith('/evidence/')) { const [, , subject,id] = path.split('/'); return reply(db.fact_claim.filter(c => c.subject_table === subject && c.subject_id === id).map(c => ({...c,source:db.source.find(s => s.id === c.source_id)}))); }
    if (path.startsWith('/editorial/')) {
      assert.ok(route.request().headers().authorization, 'admin calls carry bearer token');
      const [, , table, id] = path.split('/');
      if (route.request().method() === 'GET') return reply(db[table]);
      const body = route.request().postDataJSON();
      if (route.request().method() === 'POST') { const row = { ...body, id: crypto.randomUUID() }; db[table].push(row); return reply(row); }
      if (route.request().method() === 'PATCH') { const row = db[table].find(r => r.id === id); Object.assign(row,body); return reply(row); }
    }
    if (path.startsWith('/rest/v1/user_roles')) return reply({ role:'admin' });
    if (path.startsWith('/auth/v1/user')) return reply({ id:'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', email:'editor@example.test' });
    return reply({ message:`Unmocked ${path}` },404);
  });
  ctx.on('page', page => page.on('pageerror', e => errors.push(e.message)));
  return ctx;
}
try {
  const ctx = await context({ viewport:{width:1440,height:1000} }); const page = await ctx.newPage();
  await ctx.route('**/api/v1/topics', route => route.fulfill({contentType:'application/json',body:'[]'}));
  await page.goto(base);
  await page.getByText('五代十国专题正在整理，审核完成后将在这里发布。',{exact:true}).waitFor();
  assert.equal(await page.locator('a[href*="/topics/"]').count(),0);
  await ctx.unroute('**/api/v1/topics');
  await page.goto(base); await page.getByRole('heading',{name:'沿着专题阅读'}).waitFor();
  await page.getByRole('link').filter({hasText:'测试阅读专题'}).waitFor();
  await page.screenshot({path:`${screenshots}/home-desktop.png`,fullPage:true});
  await page.getByRole('link').filter({hasText:'测试阅读专题'}).click();
  await page.getByRole('heading',{name:'测试阅读专题',exact:true,level:1}).waitFor();
  assert.equal(await page.locator('section[id^="chapter-"]').count(),3);
  const timeline = page.getByRole('list',{name:'专题事件时间线'});
  await timeline.getByRole('button',{name:/测试事件甲/}).waitFor();
  await page.getByRole('heading', {name:'907 年形势参考图 · 史图馆'}).waitFor();
  await page.getByRole('button', {name:'现代地理底图', exact:true}).click();
  await page.getByTitle('测试地点甲 · 1 个事件',{exact:true}).waitFor();
  await timeline.getByRole('button',{name:/测试事件乙/}).click();
  await page.getByRole('article',{name:'选中事件'}).getByRole('heading',{name:'测试事件乙'}).waitFor();
  await page.getByTitle('测试地点甲 · 1 个事件',{exact:true}).click();
  await page.getByRole('article',{name:'选中事件'}).getByRole('heading',{name:'测试事件甲'}).waitFor();
  await page.getByLabel('筛选起始年').fill('2');
  assert.equal(await timeline.getByRole('button').count(),2);
  await page.getByText('当前事件尚无已核实坐标。下方显示方位参考底图；古地名可在事件列表中查看，核实坐标后才会出现标记。',{exact:true}).waitFor();
  await page.getByLabel('筛选结束年').fill('1');
  await page.getByText('起始年不能晚于结束年。',{exact:true}).waitFor();
  await page.getByRole('button',{name:'重置筛选'}).click();
  await page.getByLabel('参与人物',{exact:true}).selectOption(personId);
  assert.equal(await timeline.getByRole('button').count(),1);
  await page.getByRole('button',{name:'重置筛选'}).click();

  await page.screenshot({path:`${screenshots}/topic-desktop.png`,fullPage:true});
  await page.locator(`#chapter-0 a[href$="${personId}"]`).click();
  await page.getByRole('heading',{name:'测试人物甲',exact:true,level:1}).waitFor();
  await page.getByText('测试文献·人物段',{exact:false}).waitFor();
  await page.getByText('查看这条关系的依据').first().click();
  await page.getByText('测试文献·关系段',{exact:false}).waitFor();
  await page.screenshot({path:`${screenshots}/entry-desktop.png`,fullPage:true});
  await page.getByRole('link',{name:'在图谱中探索 →'}).click();
  await page.locator('svg .nodes').waitFor();
  await page.getByRole('link',{name:'阅读全文与出处 →'}).click();
  await page.getByRole('heading',{name:'测试人物甲',exact:true,level:1}).waitFor();
  await page.goto(`${base}events/${eventId}`); await page.getByText('测试阶段',{exact:true}).waitFor();
  await page.goto(`${base}search?q=测试别名`); await page.getByRole('heading',{name:'测试人物甲',exact:true}).waitFor();
  await page.getByRole('searchbox').fill('不存在的条目xyz'); await page.getByText('暂时没有匹配的条目',{exact:false}).waitFor();
  await page.reload(); assert.ok(page.url().includes('q='));
  failTopics=true; await page.goto(base); await page.getByRole('alert').waitFor(); failTopics=false; await page.getByRole('button',{name:'重新加载'}).click(); await page.getByRole('heading',{name:'测试阅读专题',exact:true}).waitFor();
  const mobile = await context({viewport:{width:390,height:844},isMobile:true,deviceScaleFactor:1}); const mp = await mobile.newPage();
  for (const path of ['', 'topics/test-reading', `people/${personId}`]) { await mp.goto(base+path); await mp.getByRole('heading',{level:1}).waitFor(); assert.ok(await mp.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `mobile overflow: ${path}`); }
  await mp.screenshot({path:`${screenshots}/entry-mobile.png`,fullPage:true});
  await mp.goto(base); await mp.getByRole('heading',{name:'测试阅读专题',exact:true}).waitFor(); await mp.screenshot({path:`${screenshots}/home-mobile.png`,fullPage:true});
  const admin = await context({viewport:{width:1280,height:900}});
  await admin.addInitScript(() => { if (location.origin !== 'http://127.0.0.1:5175') return; const enc=o=>btoa(JSON.stringify(o)); const token=`${enc({alg:'HS256',typ:'JWT'})}.${enc({sub:'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',exp:4102444800})}.local-test`; localStorage.setItem('sb-127-auth-token',JSON.stringify({access_token:token,refresh_token:'local-refresh',expires_at:4102444800,expires_in:3600,token_type:'bearer',user:{id:'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',email:'editor@example.test'}})); });
  const ap = await admin.newPage(); await ap.goto(`${base}admin`); await ap.getByRole('link',{name:'专题与出处管理 →'}).waitFor(); await ap.getByRole('link',{name:'专题与出处管理 →'}).click();
  await ap.getByRole('button',{name:'＋ 新增'}).click(); await ap.getByLabel('标题',{exact:true}).fill('测试专题'); await ap.getByLabel('专题地址').fill('test-topic'); await ap.getByLabel('导读').fill('测试导读'); await ap.getByLabel('章节标题').fill('第一章'); await ap.getByLabel('正文',{exact:true}).fill('阅读内容'); await ap.getByLabel('发布状态').selectOption('draft'); await ap.getByRole('button',{name:'保存',exact:true}).click(); await ap.getByRole('status').waitFor();
  assert.equal(db.topic.find(t => t.slug === 'test-topic').status,'draft');
  await ap.getByRole('button',{name:'来源库',exact:true}).click(); await ap.getByRole('button',{name:'＋ 新增'}).click(); await ap.getByLabel('书名／资料标题').fill('测试来源'); await ap.getByRole('button',{name:'保存',exact:true}).click(); await ap.getByRole('status').waitFor();
  await ap.getByRole('button',{name:'陈述与引用',exact:true}).click(); await ap.getByRole('button',{name:'＋ 新增'}).click(); await ap.getByLabel('具体条目或关系').selectOption(personId); await ap.getByLabel('具体陈述').fill('测试陈述'); await ap.getByLabel('来源',{exact:true}).selectOption(db.source.at(-1).id); await ap.getByLabel('定位').fill('卷一'); await ap.getByRole('button',{name:'保存',exact:true}).click(); await ap.getByRole('status').waitFor(); assert.equal(db.fact_claim.at(-1).status,'draft');
  await ap.screenshot({path:`${screenshots}/editorial-desktop.png`,fullPage:true});
  await ap.goto(`${base}admin`);
  await ap.getByRole('button',{name:'事件',exact:true}).click();
  await ap.getByRole('row').filter({hasText:'测试事件甲'}).getByRole('button').first().click();
  await ap.getByPlaceholder('纬度',{exact:true}).fill('');
  await ap.getByPlaceholder('经度',{exact:true}).fill('');
  await ap.getByLabel('定位精度',{exact:true}).selectOption('unknown');
  await ap.getByRole('button',{name:'保存',exact:true}).click();
  await ap.getByRole('heading',{name:'事件管理',exact:true}).waitFor();
  await ap.waitForFunction(() => !document.querySelector('input[placeholder="纬度"]'));
  assert.equal(db.event.find(e=>e.id===eventId).location_lat,null);
  assert.equal(db.event.find(e=>e.id===eventId).location_lng,null);
  assert.deepEqual(errors,[]);
  console.log('PASS: map/timeline selection, year/person filters, missing coordinates, zero coordinates, clearing saved coordinates; topic → entry → evidence → graph; event phases; alias search; empty/error/retry; mobile overflow; admin draft topic/source/claim forms; no page exceptions');
} finally { await browser.close(); }
