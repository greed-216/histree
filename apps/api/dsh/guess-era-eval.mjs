// Opt-in real-model regression using published Zhu Wen evidence. Never logs keys or game tokens.
import assert from 'node:assert/strict';
import { fork } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

if (!process.argv.includes('--live')) {
  console.log(
    'Use --live with HISTREE_PUBLIC_API_URL and DEEPSEEK_API_KEY to run paid model checks.',
  );
  process.exit(0);
}
const base=(process.env.HISTREE_PUBLIC_API_URL || 'https://123.56.189.146/api/v1').replace(/\/$/,'');
const read=async(path)=>{const response=await fetch(base+path,{signal:AbortSignal.timeout(15000)});assert.equal(response.status,200);return response.json();};
const people=await read('/catalog/person?q='+encodeURIComponent('朱温'));
const summary=people.items.find(p=>p.name==='朱温');assert.ok(summary);
const person=await read('/entry/'+summary.id);
const data=await read('/catalog/fact_claim?subject=person&subject_id='+person.id+'&limit=50');
const claims = data.items.filter(
  (c) => c.source?.title && c.note?.startsWith('原文：'),
);
assert.ok(claims.length);
const cases = [
  ['你是宋以及宋以前的么', 'yes'],
  ['你是宋或更早的人吗？', 'yes'],
  ['你生活的年代不晚于宋代吗？', 'yes'],
  ['你是宋朝人吗？', 'no'],
  ['你生活在宋朝以前吗？', 'yes'],
  ['你生活在宋朝及宋朝以后吗？', 'no'],
  ['你是明清的么', 'no'],
  ['你是元的？', 'no'],
  ['你是哪个朝代的？', 'refuse'],
];
async function run(input) {
  const directory = await mkdtemp(join(tmpdir(), 'histree-guess-era-'));
  const child = fork(
    fileURLToPath(new URL('./guess-worker.mjs', import.meta.url)),
    [],
    {
      detached: process.platform !== 'win32',
      stdio: ['ignore', 'ignore', 'ignore', 'ipc'],
      env: {
        PATH: process.env.PATH,
        HOME: directory,
        TMPDIR: directory,
        DSH_HOME: directory,
        HISTREE_MODEL: process.env.HISTREE_MODEL || 'deepseek-flash',
        DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY,
      },
    },
  );
  const kill = () => {
    try {
      if (process.platform !== 'win32' && child.pid)
        process.kill(-child.pid, 'SIGKILL');
      else child.kill('SIGKILL');
    } catch {
      /* exited */
    }
  };
  const timer = setTimeout(kill, 120000);
  try {
    return await new Promise((resolve, reject) => {
      let result;
      child.on('message', (message) => {
        if (message.type === 'result') result = message.data;
      });
      child.once('error', reject);
      child.once('close', () =>
        result === undefined
          ? reject(new Error('Model check did not complete'))
          : resolve(result),
      );
      child.send(input);
    });
  } finally {
    clearTimeout(timer);
    kill();
    await rm(directory, { recursive: true, force: true });
  }
}
let count = 0;
// Repeat the exact reported sentence and its equivalents; stale contradictory history must not override evidence.
for (let round = 0; round < 2; round++) {
  for (const [question, expected] of cases) {
    const history =
      round === 1
        ? [{ text: '你是宋以及宋以前的么', answer: '不是', kind: 'question' }]
        : [];
    const result = await run({
      task: 'question',
      person,
      claims,
      history,
      question,
    });
    assert.equal(
      result.verdict,
      expected,
      `round ${round + 1}: ${question}; result=${JSON.stringify(result)}`,
    );
    if (['yes', 'no'].includes(expected)) {
      assert.ok(
        result.claims.length &&
          result.claims.every((id) => claims.some((c) => c.id === id)),
      );
    }
    console.log(`PASS ${++count}: ${question} => ${result.verdict}`);
  }
}
const unsupported = await run({
  task: 'question',
  person: { name: '未具名人物' },
  claims: [],
  history: [],
  question: '你是宋以及宋以前的人吗？',
});
assert.equal(unsupported.verdict, 'unknown');
console.log(`PASS ${++count}: no evidence => unknown`);
