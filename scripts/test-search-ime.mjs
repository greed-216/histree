import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.HISTREE_SEARCH_URL || 'http://127.0.0.1:5199/histree/';
const live = process.env.HISTREE_SEARCH_LIVE === 'true';
const browser = await chromium.launch({
  executablePath: process.env.HISTREE_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});

try {
  const page = await browser.newPage();
  const errors = [];
  const queries = [];
  page.setDefaultTimeout(60000);
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname === '/api/v1/search') queries.push(url.searchParams.get('q'));
  });
  if (!live) await page.route('**/api/v1/search?**', route =>
    route.fulfill({ json: { items: [], has_more: false } }));
  const loaded = query => page.getByText(
    new RegExp(`^已加载 \\d+ 条结果${query ? ` · “${query}”` : ''}$`), { exact: true }).waitFor();
  await page.goto(new URL('search?q=李白&kind=person', base).href);
  const input = page.getByRole('searchbox', { name: '搜索关键词' });
  await input.focus();
  await loaded('李白');
  const initialUrl = page.url();
  const initialRequests = queries.length;
  const cdp = await page.context().newCDPSession(page);

  // Real Chromium composition events, including pauses longer than the search debounce.
  for (const text of ['s', 'si', 'sima']) {
    await cdp.send('Input.imeSetComposition', {
      text, selectionStart: text.length, selectionEnd: text.length,
      replacementStart: 0, replacementEnd: 2,
    });
    await page.waitForTimeout(350);
    assert.equal(await input.inputValue(), text, 'Keep the active composition in the input');
    assert.equal(page.url(), initialUrl, 'Do not navigate while the IME is composing');
    assert.equal(queries.length, initialRequests, 'Do not search unfinished IME text');
    assert.equal(await input.evaluate(el => el === document.activeElement), true);
  }
  await cdp.send('Input.insertText', { text: '司马' });
  await page.waitForURL(url => url.searchParams.get('q') === '司马');
  await loaded('司马');
  assert.equal(await input.inputValue(), '司马');
  assert.equal(queries.at(-1), '司马');

  // Continue composing after committed Chinese without losing the earlier characters.
  await input.press('End');
  await cdp.send('Input.imeSetComposition', { text: 'qian', selectionStart: 4, selectionEnd: 4 });
  await page.waitForTimeout(350);
  assert.equal(await input.inputValue(), '司马qian');
  assert.equal(new URL(page.url()).searchParams.get('q'), '司马');
  assert.equal(queries.at(-1), '司马');
  await cdp.send('Input.insertText', { text: '迁' });
  await loaded('司马迁');
  assert.equal(await input.inputValue(), '司马迁');
  assert.ok(!queries.some(q => /[a-z]/i.test(q)), 'No intermediate pinyin reaches the API');

  const committedRequests = queries.length;
  await cdp.send('Input.imeSetComposition', { text: 'x', selectionStart: 1, selectionEnd: 1 });
  await cdp.send('Input.imeSetComposition', { text: '', selectionStart: 0, selectionEnd: 0 });
  await page.waitForTimeout(350);
  assert.equal(await input.inputValue(), '司马迁', 'Cancelling composition retains committed Chinese');
  assert.equal(queries.length, committedRequests);

  await page.getByRole('button', { name: '事件', exact: true }).click();
  await page.waitForURL(url => url.searchParams.get('kind') === 'event');
  assert.equal(await input.inputValue(), '司马迁');
  await input.fill('');
  await page.waitForURL(url => url.searchParams.get('q') === '');
  await loaded('');
  await input.pressSequentially('history', { delay: 10 });
  await loaded('history');
  assert.equal(await input.inputValue(), 'history');

  // Same-page navigation, followed by browser Back/Forward, must restore URL text and kind.
  await page.evaluate(() => {
    history.pushState(null, '', `${location.pathname}?q=${encodeURIComponent('杜甫')}&kind=topic`);
    dispatchEvent(new PopStateEvent('popstate'));
  });
  await loaded('杜甫');
  assert.equal(await input.inputValue(), '杜甫');
  assert.equal(await page.getByRole('button', { name: '专题', exact: true }).getAttribute('aria-pressed'), 'true');
  await page.goBack();
  await loaded('history');
  assert.equal(await input.inputValue(), 'history');
  await page.goForward();
  await loaded('杜甫');
  assert.equal(await input.inputValue(), '杜甫');
  assert.deepEqual(errors, []);
  console.log('PASS: Chinese composition stays local; committed Chinese searches; continued/cancelled composition, kind filters, clearing, rapid Latin input, URL changes and Back/Forward work without page errors.');
  console.log(JSON.stringify({ base, live, queries, pageErrors: errors }));
} finally {
  await browser.close();
}
