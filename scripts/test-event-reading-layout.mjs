import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const base = process.env.E2E_WEB_URL || 'http://127.0.0.1:5179/histree/';
const directory = 'content/books/zizhi-tongjian/vol-015/from-start/event-structure-pilot-2026-10-13/part-01';
const batch = JSON.parse(await readFile(`${directory}/content-batch.json`, 'utf8'));
const ids = JSON.parse(await readFile(`${directory}/sql/key-map.json`, 'utf8'));
const event = batch.events[0];
const paragraphs = event.description.split('\n\n');
const claim = batch.claims.find(claim => claim.subject_key === event.key && claim.field_path === 'description');
const screenshots = process.env.HISTREE_SCREENSHOTS || '/tmp/histree-narrative-layout';
await mkdir(screenshots, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROME_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHROME_CHANNEL } : {}) });
const errors = [];
try {
  for (const width of [1280, 390, 320]) {
    const page = await browser.newPage({ viewport: { width, height: width > 640 ? 900 : 844 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}events/${ids[event.key]}`);
    await page.locator('.event-narrative').waitFor();
    await page.evaluate(() => document.fonts.ready);
    await page.locator('.entry-source-names').waitFor();
    assert((await page.locator('#evidence > summary').innerText()).includes('12 条引用'));
    assert((await page.locator('.entry-source-names').innerText()).includes('卷15'));
    assert.equal(await page.getByRole('navigation', { name: '相关人物', exact: true }).locator('a').count(), batch.people.length, 'Person links are visible before expanding relationship details');
    assert.deepEqual(await page.locator('.event-narrative > p').allTextContents(), paragraphs, 'Stored event description is rendered verbatim as continuous paragraphs');
    assert.equal(await page.locator('.context-insight, .context-tracks').count(), 0, 'No questions or extra reading connections');
    const phases = page.locator('#chronology');
    assert.equal(await phases.count(), event.phases?.length ? 1 : 0);
    if (event.phases?.length) {
      await phases.locator(':scope > summary').click();
      assert.deepEqual(await phases.locator('.event-phase-records h3').allTextContents(), event.phases.map(phase => phase.title));
      assert.deepEqual(await phases.locator('.event-phase-records li > p:not(.eyebrow)').allTextContents(), event.phases.map(phase => phase.description));
      assert.equal(await phases.locator('.eyebrow').count(), 0, 'Same-year stages do not repeat the event year');
      await phases.locator(':scope > summary').click();
    }
    assert(!await page.locator('.entry-reading-page').innerText().then(text => text.includes('术语说明')));
    await page.evaluate(() => { scrollTo(0, 0); });
    const geometry = await page.evaluate(() => {
      const rect = selector => { const r = document.querySelector(selector).getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right }; };
      return { lead: rect('.event-narrative > p'), launcher: rect('.entry-assistant-launcher'), header: rect('.site-header'), scrollWidth: document.documentElement.scrollWidth, viewport: innerWidth };
    });
    assert(geometry.lead.top > geometry.header.bottom && geometry.lead.bottom < 844, `The complete event introduction appears below the header in the first viewport at ${width}px`);
    assert(geometry.scrollWidth <= geometry.viewport, `No horizontal overflow at ${width}px`);
    if (width <= 640) assert(geometry.launcher.bottom <= geometry.header.bottom, 'Mobile assistant stays in the header');
    await page.screenshot({ path: `${screenshots}/reading-${width}.png`, fullPage: true });
    await page.screenshot({ path: `${screenshots}/first-screen-${width}.png` });

    const evidence = page.locator('#evidence');
    await page.getByRole('navigation', { name: '本页阅读' }).getByRole('link', { name: '史料依据', exact: true }).click();
    assert(await evidence.evaluate(element => element.open), 'Source navigation opens the disclosure');
    await evidence.locator(':scope > summary').click();
    await page.getByRole('navigation', { name: '本页阅读' }).getByRole('link', { name: '史料依据', exact: true }).click();
    assert(await evidence.evaluate(element => element.open), 'Clicking the same source hash reopens a manually closed disclosure');
    const card = page.locator(`#claim-${ids[claim.key]}`);
    await card.waitFor({ state: 'visible' });
    await card.getByText('查看所引原文', { exact: true }).click();
    assert.equal(await card.locator('blockquote').textContent(), claim.note.slice(3).split('；核对说明：')[0]);
    await card.getByRole('link', { name: '此条引用的固定链接' }).click();
    await page.locator(`#claim-${ids[claim.key]} blockquote`).waitFor({ state: 'visible' });
    assert(page.url().includes(`/evidence/event/${ids[event.key]}#claim-${ids[claim.key]}`));
    await page.goBack();
    await page.locator('.event-narrative').waitFor();
    await page.locator('#overview').scrollIntoViewIfNeeded();
    await page.evaluate(() => {
      const text = document.querySelector('#overview > p').firstChild;
      const range = document.createRange(); range.setStart(text, 0); range.setEnd(text, 18);
      const selected = getSelection(); selected.removeAllRanges(); selected.addRange(range);
    });
    await page.getByRole('button', { name: /问这句话/ }).click();
    const dialog = page.getByRole('dialog', { name: '本页阅读助手' });
    await dialog.waitFor({ state: 'visible' });
    assert((await dialog.locator('.assistant-selection').textContent()).includes('汉文帝'));
    await dialog.getByLabel('向本页助手提问').fill('贾谊为什么建议这样改封？');
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('button', { name: '✦ 本页助手', exact: true }).click();
    assert.equal(await dialog.getByLabel('向本页助手提问').inputValue(), '贾谊为什么建议这样改封？');
    await dialog.getByRole('button', { name: '收起本页助手' }).click();
    console.log(JSON.stringify({ width, geometry, evidence: 'verbatim quote and pinned citation navigation', assistant: 'selection, dialog, draft, Escape' }));
    await page.close();
  }
  const origin = new URL(base).origin;
  for (const id of ['4b28f296-2a86-5b7b-ba9a-28bf91aea574', 'b95447c8-745b-5854-935c-67b6444f19f9']) {
    for (const width of [1280, 390]) {
      const page = await browser.newPage({ viewport: { width, height: width > 640 ? 900 : 844 } });
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.request.get(`${origin}/api/v1/entry-context/${id}`);
      assert(response.ok(), 'Existing published event remains available');
      const stored = (await response.json()).center;
      await page.goto(`${base}events/${id}`);
      await page.locator('.event-narrative').waitFor();
      await page.locator('.entry-source-names').waitFor();
      const people = page.getByRole('navigation', { name: '相关人物', exact: true });
      assert(await people.isVisible(), 'Related names remain visible on old events');
      const linkedPeople = (await response.json()).nodes.filter(node => node.type === 'person');
      assert.deepEqual(await people.locator('a[href*="/people/"]').allTextContents(), linkedPeople.slice(0, 10).map(person => person.name));
      assert.equal(await page.locator('.entry-reading-page').count(), 1, 'All events share the reading layout regardless of paragraph count');
      assert.equal(await page.locator('aside a[href="#overview"]').count(), 0, 'The former sidebar is removed from every event');
      assert.deepEqual(await page.locator('.event-narrative > p').allTextContents(), (stored.description || '事件说明正在整理。').split(/\r?\n\s*\r?\n/).filter(Boolean), 'Published prose remains unchanged');
      assert.equal(await page.locator('#chronology').count(), stored.phases?.length ? 1 : 0, 'Only actual phase data creates phase records');
      await page.getByRole('button', { name: '✦ 本页助手' }).click();
      await page.getByRole('dialog', { name: '本页阅读助手' }).waitFor({ state: 'visible' });
      await page.keyboard.press('Escape');
      const bounds = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth, launcherBottom: document.querySelector('.entry-assistant-launcher').getBoundingClientRect().bottom, headerBottom: document.querySelector('.site-header').getBoundingClientRect().bottom }));
      assert(bounds.scroll <= bounds.width, 'Existing events have no horizontal overflow');
      if (width === 390) assert(bounds.launcherBottom <= bounds.headerBottom, 'Existing events also place the mobile assistant in the header');
      await page.goto(`${base}events/${id}#evidence`);
      await page.locator('#evidence[open]').waitFor();
      assert(await page.locator('#evidence > div').isVisible(), 'Direct source bookmarks open their contents');
      await page.getByRole('navigation', { name: '本页阅读' }).getByRole('link', { name: '事件叙述' }).click();
      await page.locator('#evidence > summary').click();
      await page.evaluate(() => scrollTo(0, 0));
      await page.screenshot({ path: `${screenshots}/existing-${id}-${width}.png`, fullPage: true });
      console.log(JSON.stringify({ existingEvent: id, width, unifiedLayout: true, originalProsePreserved: true }));
      await page.close();
    }
  }
  const person = await browser.newPage();
  await person.goto(`${base}people/3ddce59a-2d7a-5a32-8c6e-d09d330d167f`);
  await person.locator('article > header h1').waitFor();
  assert.equal(await person.locator('.entry-reading-page').count(), 0, 'Person pages retain their layout');
  assert.equal(await person.locator('aside a[href="#overview"]').count(), 1);
  assert.deepEqual(errors, [], 'No browser runtime errors');
  console.log('One event layout accepted for the sample and two published events on desktop/mobile; prose and person layout preserved.');
} finally { await browser.close(); }
