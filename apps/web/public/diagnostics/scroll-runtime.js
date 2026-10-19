(function () {
  'use strict';
  if (document.getElementById('scroll-runtime-panel')) return;
  var panel = document.createElement('aside');
  panel.id = 'scroll-runtime-panel';
  panel.setAttribute('aria-label', '画卷运行诊断');
  panel.style.cssText = 'position:fixed;z-index:10000;left:8px;right:8px;bottom:8px;max-height:45vh;overflow:auto;padding:10px;border:1px solid #829580;border-radius:8px;background:#fffdf7;color:#294e43;font:13px/1.6 system-ui,sans-serif;box-shadow:0 2px 15px #0002';
  panel.innerHTML = '<details open><summary>画卷运行诊断 · runtime-2（点此收起）</summary><p style="margin:6px 0">先定位画卷、读取状态，再试两个对照开关。结果只留在本页，刷新恢复。</p><div style="display:flex;gap:6px;flex-wrap:wrap"><button data-action="locate">定位画卷</button><button data-action="read">读取状态</button><button data-action="isolate" aria-pressed="false">只看底图</button><button data-action="native" aria-pressed="false">普通图片对照</button></div><textarea aria-label="画卷运行状态" readonly style="display:block;width:100%;height:135px;margin-top:8px;padding:6px;border:1px solid #c3cdbd;font:11px/1.5 monospace;color:#294e43;background:white">等待画卷加载…</textarea></details>';
  var style = document.createElement('style');
  style.textContent = '#scroll-runtime-panel button{padding:4px 8px;border:1px solid #bbc8b4;border-radius:4px;background:#eef1e7;color:#294e43}#scroll-runtime-panel button[aria-pressed="true"]{background:#315e4e;color:white}.scroll-diagnostic-isolated>:not([data-history-backdrop]):not(defs){visibility:hidden!important}.scroll-diagnostic-native>[data-history-backdrop]{visibility:hidden!important}';
  panel.appendChild(style);
  document.body.appendChild(panel);
  var output = panel.querySelector('textarea');
  var nativeLayer = null;
  var isolated = false;
  var native = false;
  var sequence = 0;
  var probe = null;
  var settleTimer = null;
  function target() { return document.querySelector('.timeline-chart'); }
  function rounded(value) { return Math.round(value * 1000) / 1000; }
  function rect(element) {
    if (!element) return null;
    var box = element.getBoundingClientRect();
    return { x: rounded(box.x), y: rounded(box.y), width: rounded(box.width), height: rounded(box.height) };
  }
  function describe(element) {
    if (!element) return null;
    var css = getComputedStyle(element);
    var attrs = {};
    ['viewBox', 'x', 'y', 'width', 'height', 'transform', 'clip-path', 'href', 'xlink:href'].forEach(function (key) {
      if (element.hasAttribute(key)) attrs[key] = element.getAttribute(key);
    });
    return { tag: element.tagName, namespace: element.namespaceURI, rect: rect(element), attrs: attrs,
      style: { display: css.display, visibility: css.visibility, opacity: css.opacity, width: css.width, height: css.height, overflow: css.overflow, clipPath: css.clipPath, transform: css.transform, filter: css.filter, mixBlendMode: css.mixBlendMode } };
  }
  function imageProbe(url) {
    if (!url) return Promise.resolve({ error: '没有找到图片地址' });
    if (!probe) probe = new Promise(function (resolve) {
      var image = new Image();
      var timer = setTimeout(function () { resolve({ error: '图片读取超过 8 秒' }); }, 8000);
      image.onload = function () { clearTimeout(timer); resolve({ width: image.naturalWidth, height: image.naturalHeight }); };
      image.onerror = function () { clearTimeout(timer); resolve({ error: '普通图片加载失败' }); };
      image.src = url;
    });
    return probe;
  }
  function drawNative(chart) {
    if (!native) return;
    var canvas = chart.parentElement;
    var image = chart.querySelector('[data-history-backdrop] image');
    var clip = chart.querySelector('[data-history-backdrop] clipPath rect');
    var matrix = chart.getScreenCTM();
    if (!image || !clip || !matrix) throw Error('缺少画卷或裁剪尺寸');
    var canvasBox = canvas.getBoundingClientRect();
    var imageBox = image.getBoundingClientRect();
    var left = matrix.a * Number(clip.getAttribute('x')) + matrix.e;
    var top = matrix.d * Number(clip.getAttribute('y')) + matrix.f;
    var width = matrix.a * Number(clip.getAttribute('width'));
    var height = matrix.d * Number(clip.getAttribute('height'));
    if (![left, top, width, height, imageBox.width, imageBox.height].every(Number.isFinite) || width <= 0 || height <= 0) throw Error('画卷尺寸无效');
    if (nativeLayer) nativeLayer.remove();
    nativeLayer = document.createElement('div');
    nativeLayer.setAttribute('data-diagnostic-native', 'true');
    nativeLayer.style.cssText = 'position:absolute;pointer-events:none;overflow:hidden;z-index:0;background:#f0ecdf';
    nativeLayer.style.left = left - canvasBox.left + 'px';
    nativeLayer.style.top = top - canvasBox.top + 'px';
    nativeLayer.style.width = width + 'px';
    nativeLayer.style.height = height + 'px';
    nativeLayer.style.borderRadius = 12 * matrix.a + 'px';
    var plain = document.createElement('img');
    plain.alt = '';
    plain.src = image.getAttribute('href') || image.getAttributeNS('http://www.w3.org/1999/xlink', 'href');
    plain.style.cssText = 'position:absolute;display:block;max-width:none;pointer-events:none';
    plain.style.left = imageBox.left - left + 'px';
    plain.style.top = imageBox.top - top + 'px';
    plain.style.width = imageBox.width + 'px';
    plain.style.height = imageBox.height + 'px';
    nativeLayer.appendChild(plain);
    canvas.style.position = 'relative';
    chart.style.position = 'relative';
    chart.style.zIndex = '1';
    canvas.appendChild(nativeLayer);
  }
  async function snapshot() {
    var current = ++sequence;
    var chart = target();
    if (!chart) { output.value = '诊断版本：runtime-2\n尚未找到画卷，请点击“定位画卷”并等待加载。'; return; }
    var image = chart.querySelector('[data-history-backdrop] image');
    var clip = chart.querySelector('[data-history-backdrop] clipPath');
    var url = image && (image.getAttribute('href') || image.getAttributeNS('http://www.w3.org/1999/xlink', 'href'));
    var matrix = chart.getScreenCTM();
    var report = { version: 'runtime-2', userAgent: navigator.userAgent, mode: chart.parentElement.getAttribute('data-view'),
      viewport: { width: innerWidth, height: innerHeight, dpr: devicePixelRatio },
      cssSupport: { svh: CSS.supports('height', '100svh'), aspectRatio: CSS.supports('aspect-ratio', '1 / 1'), grid: CSS.supports('display', 'grid') },
      from: chart.getAttribute('data-from'), to: chart.getAttribute('data-to'),
      canvas: describe(chart.parentElement), chart: describe(chart),
      matrix: matrix && { a: matrix.a, b: matrix.b, c: matrix.c, d: matrix.d, e: matrix.e, f: matrix.f },
      clipId: clip && clip.id, clipRect: describe(clip && clip.querySelector('rect')),
      backdrop: describe(chart.querySelector('[data-history-backdrop]')), panel: describe(chart.querySelector('[data-panel]')), image: describe(image),
      duplicateClipIds: clip ? Array.from(document.querySelectorAll('[id]')).filter(function (el) { return el.id === clip.id; }).length : 0,
      tests: { isolated: isolated, native: native },
      scripts: Array.from(document.scripts).map(function (script) { return script.src; }).filter(function (src) { return src.indexOf('/assets/') >= 0; }) };
    try {
      panel.style.visibility = 'hidden';
      var box = chart.getBoundingClientRect();
      var stack = document.elementsFromPoint(box.left + box.width / 2, box.top + box.height / 2);
      report.coveringElements = stack.slice(0, 6).map(function (el) { return el.tagName + (el.id ? '#' + el.id : '') + (el.getAttribute('class') ? '.' + el.getAttribute('class') : ''); });
    } finally { panel.style.visibility = ''; }
    output.value = JSON.stringify(report, null, 2);
    report.decodedImage = await imageProbe(url);
    if (current === sequence) output.value = JSON.stringify(report, null, 2);
  }
  panel.addEventListener('click', function (event) {
    var button = event.target.closest('button[data-action]');
    if (!button) return;
    var action = button.getAttribute('data-action');
    var chart = target();
    if (action === 'locate') {
      var section = document.querySelector('.home-timeline') || chart;
      if (section) section.scrollIntoView({ block: 'start' });
    } else if (action === 'isolate' && chart) {
      isolated = !isolated;
      chart.classList.toggle('scroll-diagnostic-isolated', isolated);
      button.setAttribute('aria-pressed', String(isolated));
    } else if (action === 'native' && chart) {
      native = !native;
      try { drawNative(chart); } catch (error) { native = false; output.value = String(error); return; }
      chart.classList.toggle('scroll-diagnostic-native', native);
      if (!native && nativeLayer) { nativeLayer.remove(); nativeLayer = null; }
      button.setAttribute('aria-pressed', String(native));
    }
    void snapshot();
  });
  function readySnapshot() {
    void snapshot();
    clearTimeout(settleTimer);
    settleTimer = setTimeout(function () { void snapshot(); }, 1500);
  }
  var observer = new MutationObserver(function () {
    var chart = target();
    if (chart && chart.querySelector('[data-history-backdrop] image')) { observer.disconnect(); readySnapshot(); }
  });
  observer.observe(document.getElementById('root'), { childList: true, subtree: true });
  if (target()) { observer.disconnect(); readySnapshot(); }
  window.addEventListener('pagehide', function () { observer.disconnect(); clearTimeout(settleTimer); }, { once: true });
})();
