import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { chromium } from 'playwright';

const base = process.env.TIMELINE_TEST_URL || 'http://127.0.0.1:5173/timeline';
const output = process.env.TIMELINE_SCREENSHOT_DIR || '/private/tmp/histree-timeline-layout';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  let eventRequests = 0;
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.pathname.endsWith('/api/v1/timeline') && url.searchParams.has('year')) eventRequests++;
  });
  await page.goto(`${base}?year=907`);
  const chart = page.locator('.timeline-chart');
  const preview = page.getByRole('complementary', { name: '年度史事选读' });
  const layoutBounds = () => page.evaluate(() => Object.fromEntries([
    '.timeline-river', '.timeline-workspace', '.timeline-period-bands',
    '.timeline-canvas-scroll', '.timeline-preview', '.timeline-overview',
  ].map(selector => {
    const rect = document.querySelector(selector).getBoundingClientRect();
    return [selector, { y: rect.y + scrollY, height: rect.height }];
  })));
  const assertStable = async (before, action) => {
    const after = await layoutBounds();
    for (const selector of Object.keys(before)) for (const dimension of ['y', 'height']) {
      assert.ok(Math.abs(before[selector][dimension] - after[selector][dimension]) < 1,
        `${action}: ${selector} ${dimension} remains stable`);
    }
  };
  const stressPreview = async () => {
    const before = await layoutBounds();
    await page.locator('.timeline-preview-content').evaluate(el => {
      const text = document.createElement('p');
      text.dataset.layoutStress = 'true';
      text.textContent = '长篇年度事件内容用于验证内部滚动。'.repeat(180);
      el.append(text);
    });
    assert.ok(await page.locator('.timeline-preview-content').evaluate(el => el.scrollHeight > el.clientHeight), 'Long annual text scrolls inside the preview');
    await assertStable(before, 'Long annual text');
    await page.locator('[data-layout-stress]').evaluate(el => el.remove());
  };
  await preview.getByRole('heading', { name: '907年', exact: true }).waitFor();
  await page.waitForLoadState('networkidle');
  const chartBox = await chart.boundingBox();
  const previewBox = await preview.boundingBox();
  assert.ok(previewBox.x > chartBox.x + chartBox.width, 'Desktop annual overview sits beside the painting');
  assert.ok(chartBox.height >= 280 && chartBox.height <= 325, 'Painting receives the main vertical space');
  assert.ok(chartBox.height > 1.5 * (await page.locator('.timeline-period-bands').boundingBox()).height, 'Painting remains taller than the four-row polity navigator');
  assert.ok((await page.locator('.timeline-preview-content').boundingBox()).width > 200, 'Desktop annual text has a full sidebar column');
  await stressPreview();
  const overviewBox = await page.locator('.timeline-overview').boundingBox();
  assert.ok(overviewBox.y + overviewBox.height < 900, 'Full time overview is visible in the desktop viewport');
  await page.screenshot({ path: `${output}/desktop.png` });
  await page.setViewportSize({ width: 1440, height: 768 });
  await page.goto(`${base}?year=907`);
  await preview.getByRole('heading', { name: '907年', exact: true }).waitFor();
  await page.waitForLoadState('networkidle');
  assert.equal(await page.locator('.timeline-canvas-scroll').getAttribute('data-view'), 'scroll', 'Short desktop viewport still opens on the painting');
  const shortOverview = await page.locator('.timeline-overview').boundingBox();
  const shortWorkspace = await page.locator('.timeline-workspace').boundingBox();
  assert.ok(shortOverview.y + shortOverview.height <= shortWorkspace.y + shortWorkspace.height, 'Short desktop overview stays in its allocated workspace');
  assert.ok((await chart.boundingBox()).height >= 240, 'Short desktop preserves a useful painting height');
  await page.screenshot({ path: `${output}/desktop-768.png` });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}?year=907`);
  await preview.getByRole('heading', { name: '907年', exact: true }).waitFor();
  await page.waitForLoadState('networkidle');

  const fixedUrl = page.url();
  const beforeBrowsing = eventRequests;
  const stableDesktop = await layoutBounds();
  for (const [label, start, end] of [['三国', 220, 280], ['两晋十六国', 280, 420], ['南北朝', 420, 581]]) {
    await page.getByRole('button', { name: `浏览${label}画卷`, exact: true }).click();
    const from = Number(await chart.getAttribute('data-from'));
    const to = Number(await chart.getAttribute('data-to'));
    assert.ok(from <= start - 1 && to >= end - 1, `${label} covers its full navigation interval`);
    assert.ok(Math.abs(to - from - (end - start) * 1.12) < 1, `${label} opens its own focused window`);
    if (label === '三国') for (const polity of ['wei', 'shu-han', 'wu']) {
      await page.locator(`[data-polity="${polity}"]`).waitFor();
    }
  }
  await page.getByRole('button', { name: '浏览秦汉画卷', exact: true }).click();
  for (const [polity, start, end] of [['qin-empire', -221, -207], ['western-han', -206, 8], ['xin', 9, 23], ['eastern-han', 25, 220]]) {
    const item = page.locator(`[data-polity="${polity}"]`);
    await item.waitFor();
    assert.equal(await item.getAttribute('data-start'), String(start));
    assert.equal(await item.getAttribute('data-end'), String(end));
  }
  await page.locator('[data-polity="qin-state"]').waitFor();
  const qinCountry = await page.locator('[data-duration-phase="qin-state"]').boundingBox();
  const qinEmpire = await page.locator('[data-duration-phase="qin-empire"]').boundingBox();
  const qinWhole = await page.locator('[data-duration-polity="qin"]').boundingBox();
  assert.ok(Math.abs(qinCountry.x + qinCountry.width - qinEmpire.x) < 1, 'Qin country and empire form one uninterrupted duration');
  assert.ok(Math.abs(qinWhole.width - qinCountry.width - qinEmpire.width) < 1);
  await page.locator('[data-transition-year="-221"] .timeline-transition-tick').waitFor();
  await page.getByText('◆ 前221 · 统一六国', { exact: true }).waitFor();
  await assertStable(stableDesktop, 'Qin/Han succession');
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeBrowsing, 'Qin/Han browsing does not fetch event lists');
  await page.screenshot({ path: `${output}/qin-han.png` });
  await page.getByRole('button', { name: '浏览宋画卷', exact: true }).click();
  await page.waitForTimeout(200);
  for (const polity of ['northern-song', 'southern-song', 'liao', 'jin', 'western-xia', 'yuan']) {
    await page.locator(`[data-polity="${polity}"]`).waitFor();
  }
  assert.equal(page.url(), fixedUrl, 'Era browsing preserves selected year');
  assert.equal(eventRequests, beforeBrowsing, 'Era browsing does not query event lists');
  await assertStable(stableDesktop, 'Era with more polities');
  const assertFourRowsFit = async () => {
    const strip = page.locator('.timeline-band-scroll');
    assert.ok(await page.locator('.timeline-polity-lane').count() >= 4, 'Every polity row is available without a second expansion');
    const stripBox = await strip.boundingBox();
    for (const id of ['northern-song', 'liao', 'jin', 'western-xia']) {
      const label = await page.locator(`[data-polity="${id}"]`).boundingBox();
      const duration = await page.locator(`[data-duration-polity="${id}"]`).boundingBox();
      assert.ok(label.y >= stripBox.y && duration.y + duration.height <= stripBox.y + stripBox.height, `${id} caption and duration are fully visible`);
    }
  };
  await assertFourRowsFit();
  const yuan = page.locator('[data-polity="yuan"]');
  assert.equal(await yuan.getAttribute('data-start'), '1271', 'Yuan is not truncated to the 1279 macro-era boundary');
  assert.ok(await page.locator('.timeline-band-scroll').evaluate(el => el.scrollHeight > el.clientHeight), 'Additional polities scroll inside the fixed strip');
  const yuanMark = await page.locator('[data-duration-polity="yuan"]').boundingBox();
  const paintingAtYuan = await chart.evaluate(svg => {
    const from = Number(svg.dataset.from), to = Number(svg.dataset.to);
    const point = new DOMPoint(40 + (1270 - from) / (to - from) * 920, 96).matrixTransform(svg.getScreenCTM());
    return point.x;
  });
  assert.ok(Math.abs(yuanMark.x - paintingAtYuan) < 1, 'Polity strip scrollbar preserves shared painting year coordinates');
  await page.locator('.timeline-band-scroll').evaluate(el => { el.scrollTop = el.scrollHeight; });
  await assertStable(stableDesktop, 'Expand and scroll polity strip');
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeBrowsing);
  await page.locator('.timeline-band-scroll').evaluate(el => { el.scrollTop = 0; });
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/song-liao-jin.png` });

  // Trackpad gestures over the polity band share the painting's time window.
  const strip = page.locator('.timeline-band-scroll');
  const wheelWindow = [Number(await chart.getAttribute('data-from')), Number(await chart.getAttribute('data-to'))];
  await strip.evaluate(el => { el.scrollTop = 20; });
  const verticalPosition = await strip.evaluate(el => el.scrollTop);
  await page.locator('.timeline-era-band').first().hover();
  await page.mouse.wheel(120, 0);
  await page.waitForFunction(previous => Number(document.querySelector('.timeline-chart').dataset.from) > previous, wheelWindow[0]);
  const movedWindow = [Number(await chart.getAttribute('data-from')), Number(await chart.getAttribute('data-to'))];
  assert.equal(movedWindow[1] - movedWindow[0], wheelWindow[1] - wheelWindow[0], 'Band wheel pans without zooming');
  assert.equal(await strip.evaluate(el => el.scrollTop), verticalPosition, 'Horizontal browsing preserves the vertical polity position');
  await page.mouse.wheel(-120, 0);
  await page.waitForFunction(previous => Math.abs(Number(document.querySelector('.timeline-chart').dataset.from) - previous) <= 1, wheelWindow[0]);
  const beforeVerticalWheel = await chart.getAttribute('data-from');
  await page.mouse.wheel(0, 80);
  await page.waitForFunction(previous => document.querySelector('.timeline-band-scroll').scrollTop > previous, verticalPosition);
  assert.equal(await chart.getAttribute('data-from'), beforeVerticalWheel, 'Vertical wheel scrolls polity rows without panning years');
  assert.equal(page.url(), fixedUrl, 'Band wheel preserves the selected year');
  assert.equal(eventRequests, beforeBrowsing, 'Band wheel does not query event lists');
  await assertStable(stableDesktop, 'Horizontal and vertical band wheel');

  await page.getByRole('button', { name: '浏览南北朝画卷', exact: true }).click();
  for (const polity of ['liu-song', 'southern-qi', 'liang', 'chen', 'northern-wei', 'eastern-wei', 'western-wei', 'northern-qi', 'northern-zhou']) {
    await page.locator(`[data-polity="${polity}"]`).waitFor();
  }
  assert.equal(await page.locator('[data-polity="southern-dynasties"], [data-polity="northern-dynasties"], [data-polity="sixteen-kingdoms"]').count(), 0, 'South/North and Sixteen Kingdoms never merge into summary polities');
  await assertStable(stableDesktop, 'Individual southern and northern dynasties');
  assert.equal(await page.locator('[data-polity="chen"]').getAttribute('data-end'), '589');
  await page.getByRole('button', { name: '浏览两晋十六国画卷', exact: true }).click();
  for (const polity of ['former-zhao', 'cheng-han', 'later-zhao', 'former-liang', 'former-yan', 'former-qin', 'later-qin', 'later-yan', 'western-qin', 'later-liang', 'southern-liang', 'southern-yan', 'western-liang', 'northern-liang', 'xia-sixteen', 'northern-yan']) {
    await page.locator(`[data-polity="${polity}"]`).waitFor();
  }
  await assertStable(stableDesktop, 'All sixteen distinct polities');
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/north-south.png` });
  await page.locator('[data-polity="xia-sixteen"]').click();
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeBrowsing, 'Expanded individual polity browsing is preview-only');
  await page.getByRole('button', { name: '浏览战国画卷', exact: true }).click();
  for (const polity of ['qin-state', 'qi-state', 'chu-state', 'yan-state', 'han-state', 'zhao-state', 'wei-state']) {
    await page.locator(`[data-polity="${polity}"]`).waitFor();
  }
  await assertStable(stableDesktop, 'Seven Warring States');
  assert.equal(await page.locator('.timeline-band-scroll').evaluate(el => el.scrollTop), 0, 'Switching periods starts the polity list at its first row');
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/seven-warring-states.png` });
  await page.getByRole('button', { name: '浏览五代画卷', exact: true }).click();
  for (const polity of ['later-liang-five', 'later-tang', 'later-jin-five', 'later-han', 'later-zhou']) {
    await page.locator(`[data-polity="${polity}"]`).waitFor();
  }
  assert.equal(await page.locator('[data-polity="five-dynasties"]').count(), 0);
  await assertStable(stableDesktop, 'Five individual dynasties');
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeBrowsing);
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/five-individual-dynasties.png` });
  await page.getByRole('button', { name: '浏览南北朝画卷', exact: true }).click();
  await page.getByRole('button', { name: '放大', exact: true }).click();
  await page.getByRole('button', { name: '放大', exact: true }).click();
  assert.ok(await page.locator('[data-polity="liu-song"], [data-polity="southern-qi"], [data-polity="liang"], [data-polity="chen"]').count(), 'Zoom preserves individual dynasties');
  assert.equal(page.url(), fixedUrl, 'Zooming preserves selected year');
  assert.equal(eventRequests, beforeBrowsing, 'Zooming sends no event list requests');
  await assertStable(stableDesktop, 'Zoom into individual dynasties');

  // The artwork remains available at close ranges, even in a short viewport.
  for (let i = 0; i < 4; i++) {
    assert.equal(await page.locator('.timeline-canvas-scroll').getAttribute('data-view'), 'scroll');
    assert.equal(await page.locator('[data-history-backdrop]').count(), 1);
    assert.ok((await chart.boundingBox()).height <= 325);
    if (await page.getByRole('button', { name: '放大', exact: true }).isEnabled()) {
      await page.getByRole('button', { name: '放大', exact: true }).click();
    }
  }
  assert.ok(Number(await chart.getAttribute('data-to')) - Number(await chart.getAttribute('data-from')) <= 20);
  const closeWindow = [await chart.getAttribute('data-from'), await chart.getAttribute('data-to')];
  const beforeArtworkPan = eventRequests;
  const imagePosition = page.getByRole('slider', { name: '上下查看画卷' });
  await imagePosition.fill('100');
  assert.equal(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position'), '1');
  assert.deepEqual([await chart.getAttribute('data-from'), await chart.getAttribute('data-to')], closeWindow, 'Artwork vertical pan preserves year coordinates');
  const beforeVerticalUrl = page.url(), beforeVerticalRequests = eventRequests;
  const closeBox = await chart.boundingBox();
  const dragArtwork = async (dx, dy) => {
    await page.mouse.move(closeBox.x + closeBox.width * .5, closeBox.y + closeBox.height * .4);
    await page.mouse.down();
    await page.mouse.move(closeBox.x + closeBox.width * .5 + dx, closeBox.y + closeBox.height * .4 + dy, { steps: 8 });
    await page.mouse.up();
  };
  await dragArtwork(2, 60);
  assert.ok(Number(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position')) < 1, 'Dragging down moves the painting down');
  assert.deepEqual([await chart.getAttribute('data-from'), await chart.getAttribute('data-to')], closeWindow, 'Vertical dragging with small horizontal jitter preserves year coordinates');
  await imagePosition.fill('0');
  await dragArtwork(0, 60);
  assert.equal(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position'), '0', 'Top artwork edge clamps');
  await imagePosition.fill('100');
  await dragArtwork(0, -60);
  assert.equal(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position'), '1', 'Bottom artwork edge clamps');
  await imagePosition.fill('50');
  await dragArtwork(0, -50);
  assert.ok(Number(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position')) > .5, 'Dragging up moves the painting up');
  assert.equal(page.url(), beforeVerticalUrl, 'Vertical dragging does not select a year');
  assert.equal(eventRequests, beforeVerticalRequests, 'Vertical dragging does not fetch event lists');
  await page.getByRole('button', { name: '史事细览', exact: true }).click();
  assert.equal(await page.locator('.timeline-canvas-scroll').getAttribute('data-view'), 'detail');
  await page.getByRole('button', { name: '画卷浏览', exact: true }).click();
  assert.equal(await page.locator('.timeline-canvas-scroll').getAttribute('data-view'), 'scroll');
  assert.deepEqual([await chart.getAttribute('data-from'), await chart.getAttribute('data-to')], closeWindow, 'Manual mode switching preserves the view window');
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeArtworkPan, 'Artwork movement and mode changes do not fetch event lists');
  await assertStable(stableDesktop, 'Pan artwork and switch modes');
  await page.getByRole('button', { name: '看完整画幅', exact: true }).click();
  assert.equal(await imagePosition.isDisabled(), true, 'Full image keeps the reserved controls slot');
  await assertStable(stableDesktop, 'Fit complete artwork');

  // Short-period captions stay readable without falsifying their duration.
  await page.getByRole('button', { name: '浏览两晋十六国画卷', exact: true }).click();
  await page.getByRole('button', { name: '缩小', exact: true }).click();
  await page.getByRole('button', { name: '缩小', exact: true }).click();
  await page.getByRole('button', { name: '缩小', exact: true }).click();
  const shu = page.locator('[data-polity="shu-han"]'), caption = shu.locator('.timeline-band-name');
  assert.equal(await caption.innerText(), '蜀汉');
  assert.ok((await caption.boundingBox()).width > (await page.locator('[data-duration-polity="shu-han"]').boundingBox()).width, 'Short caption is external to its true-duration mark');
  assert.equal(await caption.evaluate(el => getComputedStyle(el).fontSize), '14px');
  const qiMark = page.locator('[data-duration-polity="northern-qi"]');
  const zhouMark = page.locator('[data-duration-polity="northern-zhou"]');
  const suiMark = page.locator('[data-duration-polity="sui"]');
  const markColor = mark => mark.evaluate(el => getComputedStyle(el).backgroundColor);
  const qiColor = await markColor(qiMark), suiColor = await markColor(suiMark);
  assert.notEqual(qiColor, suiColor, 'Adjacent Northern Qi and Sui durations are visually distinct');
  const qiBox = await qiMark.boundingBox(), zhouBox = await zhouMark.boundingBox();
  assert.ok(qiBox.x + qiBox.width < zhouBox.x + zhouBox.width, 'Northern Qi ends before Northern Zhou at overview zoom');
  const qiButton = page.locator('[data-polity="northern-qi"]');
  const qiConnector = qiButton.locator('..').locator('.timeline-band-connectors line');
  await qiButton.hover();
  assert.notEqual(await markColor(qiMark), qiColor, 'Hovering the name highlights its duration');
  assert.equal(await markColor(suiMark), suiColor, 'Highlighting Northern Qi leaves Sui unchanged');
  assert.equal(await qiConnector.evaluate(el => getComputedStyle(el).strokeWidth), '2px', 'The matching connector highlights too');
  await page.screenshot({ path: `${output}/north-south-highlight.png` });
  await page.mouse.move(0, 0);
  await qiButton.focus();
  assert.notEqual(await markColor(qiMark), qiColor, 'Keyboard focus highlights the matching duration');
  await qiButton.evaluate(el => el.blur());
  assert.equal(page.url(), fixedUrl);
  assert.equal(eventRequests, beforeBrowsing, 'Highlighting is preview-only');
  assert.equal(await page.locator('.timeline-era-band .timeline-band-name').first().evaluate(el => getComputedStyle(el).backgroundColor), 'rgba(0, 0, 0, 0)', 'Era overview uses a header style rather than polity chips');
  for (const lane of await page.locator('.timeline-era-lane, .timeline-polity-lane').all()) {
    const labels = await lane.locator('.timeline-band-name').evaluateAll(elements => elements.map(el => {
      const box = el.getBoundingClientRect(); return { x: box.x, right: box.right, y: box.y };
    }).sort((a, b) => a.y - b.y || a.x - b.x));
    for (let i = 1; i < labels.length; i++) if (Math.abs(labels[i].y - labels[i-1].y) < 1) {
      assert.ok(labels[i].x >= labels[i-1].right + 2, 'Captions do not overlap');
    }
  }
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/readable-short-periods.png` });
  await page.getByRole('button', { name: '浏览南北朝画卷', exact: true }).click();
  await page.getByRole('button', { name: '放大', exact: true }).click();
  await page.getByRole('button', { name: '放大', exact: true }).click();

  const hovered = await chart.evaluate(svg => {
    const point = new DOMPoint(500, 160).matrixTransform(svg.getScreenCTM());
    return { x: point.x, y: point.y };
  });
  await page.mouse.move(hovered.x, hovered.y);
  await page.waitForTimeout(150);
  assert.equal(eventRequests, beforeBrowsing, 'Hovering sends no event list requests');
  const nextYearResponse = page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname.endsWith('/api/v1/timeline') && url.searchParams.get('year') !== '907';
  });
  await page.mouse.click(hovered.x, hovered.y);
  await page.waitForURL(url => url.href !== fixedUrl);
  await nextYearResponse;
  await page.waitForLoadState('networkidle');
  assert.ok(eventRequests > beforeBrowsing, 'Explicit year click loads its events');
  const beforeDrag = page.url();
  const beforeDragRequests = eventRequests;
  const box = await chart.boundingBox();
  const oldFrom = await chart.getAttribute('data-from');
  await page.mouse.move(box.x + box.width * .6, box.y + box.height * .5);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .4, box.y + box.height * .5, { steps: 8 });
  await page.mouse.up();
  assert.equal(page.url(), beforeDrag, 'Dragging does not select a year');
  assert.equal(eventRequests, beforeDragRequests, 'Dragging does not query events');
  assert.notEqual(await chart.getAttribute('data-from'), oldFrom, 'Dragging pans the chart');
  await imagePosition.fill('50');
  const beforeDiagonal = await chart.getAttribute('data-from');
  await page.mouse.move(box.x + box.width * .6, box.y + box.height * .4);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .4, box.y + box.height * .6, { steps: 8 });
  await page.mouse.up();
  assert.notEqual(await chart.getAttribute('data-from'), beforeDiagonal, 'Diagonal dragging pans years');
  assert.ok(Number(await page.locator('[data-artwork-position]').getAttribute('data-artwork-position')) < .5, 'Diagonal dragging also moves the painting down');
  assert.equal(page.url(), beforeDrag);
  assert.equal(eventRequests, beforeDragRequests);

  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(`${base}?year=907`);
    await preview.getByRole('heading', { name: '907年', exact: true }).waitFor();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'Mobile layout has no horizontal page overflow');
    const painting = await chart.boundingBox(), reading = await preview.boundingBox();
    assert.ok(await page.locator('.timeline-overview').evaluate(el => el.scrollHeight <= el.clientHeight), 'Mobile overview fits its reserved navigation slot');
    const stableMobile = await layoutBounds();
    await stressPreview();
    assert.ok(reading.y >= painting.y + painting.height, 'Mobile annual overview sits below the painting');
    assert.ok(reading.y < 844, 'Mobile annual preview begins in the first screen');
    await page.screenshot({ path: `${output}/mobile-${width}.png` });
    await page.getByRole('button', { name: '浏览宋画卷', exact: true }).click();
    await assertFourRowsFit();
    await page.locator('[data-polity="western-xia"]').waitFor();
    assert.ok((await chart.boundingBox()).height <= 210, 'Mobile expanded polity bands do not enlarge the painting');
    await assertStable(stableMobile, 'Mobile expanded polity strip');
    await page.mouse.move(0, 0);
    await page.screenshot({ path: `${output}/mobile-song-${width}.png` });
    await page.getByRole('button', { name: '浏览战国画卷', exact: true }).click();
    for (const polity of ['qin-state', 'qi-state', 'chu-state', 'yan-state', 'han-state', 'zhao-state', 'wei-state']) {
      await page.locator(`[data-polity="${polity}"]`).waitFor();
    }
    await assertStable(stableMobile, 'Mobile seven distinct Warring States');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${output}/mobile-warring-${width}.png` });
    await page.getByRole('button', { name: '浏览两晋十六国画卷', exact: true }).click();
    for (const polity of ['former-zhao', 'cheng-han', 'later-zhao', 'former-liang', 'former-yan', 'former-qin', 'later-qin', 'later-yan', 'western-qin', 'later-liang', 'southern-liang', 'southern-yan', 'western-liang', 'northern-liang', 'xia-sixteen', 'northern-yan']) {
      await page.locator(`[data-polity="${polity}"]`).waitFor();
    }
    await assertStable(stableMobile, 'Mobile sixteen distinct polities');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${output}/mobile-sixteen-${width}.png` });
  }
  const touchContext = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  try {
    const touchPage = await touchContext.newPage();
    let touchRequests = 0;
    touchPage.on('pageerror', error => errors.push(error.message));
    touchPage.on('request', request => {
      const url = new URL(request.url());
      if (url.pathname.endsWith('/api/v1/timeline') && url.searchParams.has('year')) touchRequests++;
    });
    await touchPage.goto(`${base}?year=907`);
    await touchPage.waitForLoadState('networkidle');
    await touchPage.getByRole('button', { name: '放大', exact: true }).click();
    const touchChart = touchPage.locator('.timeline-chart');
    await touchChart.scrollIntoViewIfNeeded();
    assert.equal(await touchChart.evaluate(el => getComputedStyle(el).touchAction), 'none', 'Cropped painting owns both touch drag axes');
    const touchBox = await touchChart.boundingBox();
    const touchBefore = { from: await touchChart.getAttribute('data-from'), to: await touchChart.getAttribute('data-to'), url: touchPage.url(), requests: touchRequests, scrollY: await touchPage.evaluate(() => scrollY) };
    const session = await touchContext.newCDPSession(touchPage);
    const finger = { x: touchBox.x + touchBox.width * .5, y: touchBox.y + touchBox.height * .3 };
    await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [finger] });
    for (let step = 1; step <= 6; step++) await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: finger.x, y: finger.y + step * 10 }] });
    await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    assert.ok(Number(await touchPage.locator('[data-artwork-position]').getAttribute('data-artwork-position')) < .5, 'Finger dragging moves the painting vertically');
    assert.equal(await touchPage.evaluate(() => scrollY), touchBefore.scrollY, 'Dragging the cropped painting does not scroll the page');
    assert.deepEqual([await touchChart.getAttribute('data-from'), await touchChart.getAttribute('data-to')], [touchBefore.from, touchBefore.to]);
    assert.equal(touchPage.url(), touchBefore.url);
    assert.equal(touchRequests, touchBefore.requests, 'Touch dragging does not fetch event lists');
  } finally {
    await touchContext.close();
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  for (const year of [-403, 1912]) {
    await page.goto(`${base}?year=${year}`);
    await chart.waitFor();
    await page.waitForLoadState('networkidle');
    const focus = year < 0 ? year : year - 1;
    assert.ok(Number(await chart.getAttribute('data-from')) <= focus && Number(await chart.getAttribute('data-to')) >= focus, 'Initial canvas fitting keeps the selected boundary year visible');
  }
  await page.goto(`${base}?year=907`);
  await preview.getByRole('heading', { name: '907年', exact: true }).waitFor();
  await page.waitForLoadState('networkidle');
  const beforeEmptyYear = await layoutBounds();
  await page.locator('.timeline-jump summary').click();
  await page.getByRole('spinbutton', { name: '跳至年份' }).fill('1303');
  await page.getByRole('button', { name: '前往', exact: true }).click();
  await page.waitForURL(url => url.searchParams.get('year') === '1303');
  await page.waitForLoadState('networkidle');
  await page.locator('.timeline-jump summary').click();
  await assertStable(beforeEmptyYear, 'Select an empty year');
  await page.goto(`${base}?year=1303`);
  await preview.getByRole('heading', { name: '1303年', exact: true }).waitFor();
  await page.waitForLoadState('networkidle');
  await page.mouse.move(0, 0);
  await page.screenshot({ path: `${output}/desktop-1303.png` });
  assert.deepEqual(errors, []);
  console.log('PASS: four complete polity rows, mouse/touch artwork dragging on both axes, clamped artwork edges, stable layout, desktop/mobile reading, and browse versus year selection.');
  console.log(`Screenshots: ${output}`);
} finally {
  await browser.close();
}
