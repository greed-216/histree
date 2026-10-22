import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const base = process.env.HISTREE_HOME_URL || 'http://127.0.0.1:5187/histree/';
const output = process.env.HISTREE_HOME_SCREENSHOTS || '/private/tmp/histree-home-preview';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.HISTREE_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));

  // An unavailable timeline must not prevent searching or using the home links.
  let releaseOverview;
  const overviewGate = new Promise(resolve => { releaseOverview = resolve; });
  await page.route('**/api/v1/timeline/overview', async route => {
    await overviewGate;
    await route.continue().catch(() => {});
  });
  await page.goto(base);
  await page.getByRole('heading', { name: /从一个名字，\s*走进一段历史。/ }).waitFor();
  await page.getByText('画卷即将展开', { exact: true }).waitFor();
  assert.equal(await page.getByRole('navigation', { name: '主导航' }).getByRole('link', { name: '探索', exact: true }).count(), 0);
  assert.equal(await page.locator('.home-play-grid a').count(), 2);
  assert.equal(await page.locator('.home-play-upcoming a,.home-play-upcoming button').count(), 0);
  await page.locator('#home-search').fill('  朱温  ');
  await page.getByRole('search', { name: '搜索历史' }).getByRole('button', { name: '搜索', exact: true }).click();
  await page.waitForURL(url => url.pathname.endsWith('/search') && url.searchParams.get('q') === '朱温');
  releaseOverview();
  await page.unroute('**/api/v1/timeline/overview');

  await page.goto(base);
  const chart = page.locator('.timeline-chart');
  await chart.waitFor({ timeout: 45000 });
  assert.ok(await page.locator('.timeline-polity-lane').count() > 0, 'Polities load automatically on the homepage');
  assert.equal(await page.locator('.timeline-band-caption button').count(), 0, 'There is no expansion step');
  const slider = page.getByRole('slider', { name: '选择历史年份' });
  const fixed = { url: page.url(), year: await slider.inputValue() };
  const assertScrollHint = async () => {
    const strip = page.locator('.timeline-band-scroll');
    const hint = page.locator('[data-remaining-polities]');
    await strip.evaluate(el => { el.scrollTop = 0; });
    await hint.waitFor();
    const remainingBelow = () => strip.evaluate(el => {
      const bottom = el.getBoundingClientRect().bottom;
      return [...el.querySelectorAll('[data-polity]')].filter(item => item.getBoundingClientRect().bottom > bottom + 1).length;
    });
    const expected = await remainingBelow();
    await page.waitForFunction(count => Number(document.querySelector('[data-remaining-polities]')?.dataset.remainingPolities) === count, expected);
    await strip.evaluate(el => { el.scrollTop = (el.scrollHeight - el.clientHeight) / 2; });
    const midway = await remainingBelow();
    assert.ok(midway < expected, 'Scrolling reveals more of the remaining polities');
    await page.waitForFunction(count => Number(document.querySelector('[data-remaining-polities]')?.dataset.remainingPolities) === count, midway);
    await strip.evaluate(el => { el.scrollTop = el.scrollHeight; });
    await hint.waitFor({ state: 'detached' });
    await strip.evaluate(el => { el.scrollTop = 0; });
    await hint.waitFor();
  };
  await page.getByRole('button', { name: '浏览战国画卷', exact: true }).click();
  for (const id of ['qin-state', 'qi-state', 'chu-state', 'yan-state', 'han-state', 'zhao-state', 'wei-state']) {
    await page.locator(`[data-polity="${id}"]`).waitFor();
  }
  await assertScrollHint();
  await page.locator('[data-polity="wei-state"]').scrollIntoViewIfNeeded();
  assert.ok(await page.locator('.timeline-band-scroll').evaluate(el => el.scrollTop > 0), 'All seven states can be reached by scrolling without another expansion');
  assert.equal(page.url(), fixed.url, 'Opening the Warring States does not select a year');
  assert.equal(await slider.inputValue(), fixed.year);

  await page.getByRole('button', { name: '放大', exact: true }).click();
  assert.equal(page.url(), fixed.url, 'Browsing must not commit a year');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${output}/desktop.png`, fullPage: true });

  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: width < 500 ? 844 : 1000 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
      `Home must fit a ${width}px viewport`);
    await page.getByRole('button', { name: '浏览战国画卷', exact: true }).click();
    await assertScrollHint();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
      `Expanded timeline must fit a ${width}px viewport`);
    if (width === 390) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${output}/mobile.png`, fullPage: true });
    }
  }

  await page.locator('.home-play-guess').click();
  await page.waitForURL(url => url.pathname.endsWith('/ask') && url.searchParams.get('mode') === 'guess');
  await page.getByRole('heading', { name: '猜猜我是谁', exact: true }).waitFor();
  await page.goto(base);
  await page.locator('.home-play-ask').click();
  await page.getByRole('heading', { name: '问史料', exact: true }).waitFor();

  await page.goto(base);
  await page.getByRole('button', { name: '随便走走', exact: true }).click();
  await page.waitForURL(url => url.pathname.endsWith('/timeline') && url.searchParams.has('year'), { timeout: 30000 });
  await chart.waitFor({ timeout: 45000 });
  assert.equal(await page.getByRole('slider', { name: '选择历史年份' }).inputValue(),
    String(Number(new URL(page.url()).searchParams.get('year')) > 0
      ? Number(new URL(page.url()).searchParams.get('year')) - 1
      : Number(new URL(page.url()).searchParams.get('year'))));

  // The full timeline also shows polities without an expansion step.
  await page.goto(new URL('timeline?year=907', base).href);
  await chart.waitFor({ timeout: 45000 });
  assert.ok(await page.locator('.timeline-polity-lane').count() > 0);
  assert.equal(await page.getByRole('button', { name: '展开政权时间线', exact: true }).count(), 0);
  assert.deepEqual(errors, []);
  console.log('PASS: search while timeline is blocked; live timeline and random entry; automatic polity rows and scroll hint count/disappearance; gameplay links; 320/390/768/1440px; full timeline unchanged; no page errors.');
  console.log(`Screenshots: ${output}`);
} finally {
  await browser.close();
}
