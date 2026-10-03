import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const ts = createRequire(new URL('../apps/web/package.json', import.meta.url))('typescript');
const source = await readFile(new URL('../apps/web/src/lib/timelineViewport.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } });
const { ordinal, calendar, timeWindow, moveWindow } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
assert.equal(calendar(ordinal(-1) + 1), 1);
assert.equal(calendar(ordinal(1) - 1), -1);
for (const [first, last] of [[-3000, 2025], [851, 922], [899, 899], [-1, 0]]) {
  for (const width of [1, 10, 100, 10000]) {
    const window = timeWindow(first, last, last, width);
    assert.ok(window.from >= first && window.to <= last);
    assert.equal(window.to - window.from, Math.min(width, last - first));
    const left = moveWindow(window, first, last, -100000);
    const right = moveWindow(window, first, last, 100000);
    assert.equal(left.from, first);
    assert.equal(right.to, last);
    assert.equal(left.to - left.from, window.to - window.from);
    assert.equal(right.to - right.from, window.to - window.from);
  }
}
assert.deepEqual(timeWindow(-3000, 2025, 0, 100), { from: -50, to: 50 });
console.log('PASS: 5,000-year windows, clamped boundaries, stable span, single year and BCE/CE continuity.');
