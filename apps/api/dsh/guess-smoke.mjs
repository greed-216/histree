// Exercise the real game worker/dsh runtime against a local model fixture, without paid requests.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { fork } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  basicQuestion,
  nameGuess,
  questionFixtures,
} from './guess-question-fixtures.mjs';
const guessing = process.argv.includes('--guess');
const selecting = process.argv.includes('--easy')
  ? 'easy'
  : process.argv.includes('--hard')
    ? 'hard'
    : null;
const directory = await mkdtemp(join(tmpdir(), 'histree-guess-smoke-'));
const fixtures = selecting
  ? [
      {
        name: `${selecting} selection`,
        input: {
          task: 'select',
          filters: { difficulty: selecting },
          candidates: [
            {
              id: 'easy-person',
              name: '朱温',
              game_difficulty: 'easy',
              fixedDifficulty: 2,
            },
            {
              id: 'hard-person',
              name: '刘交',
              game_difficulty: 'hard',
              fixedDifficulty: 4,
            },
          ],
        },
        expected: { ids: [selecting + '-person'] },
      },
    ]
  : process.argv.includes('--questions')
    ? questionFixtures
    : [guessing ? nameGuess : basicQuestion];
let fixture;
let totalRequests = 0;
let requests = 0;
let error;
const server = createServer(async (req, res) => {
  try {
    let body = '';
    for await (const chunk of req) body += chunk;
    const request = JSON.parse(body);
    requests++;
    totalRequests++;
    assert.equal(requests, 1, `${fixture.name}: exactly one model request`);
    assert.equal(
      (request.tools || []).length,
      0,
      'Game has no shell, filesystem, MCP or other tools',
    );
    const messages = JSON.stringify(request.messages);
    const system = JSON.stringify(request.system);
    if (selecting) {
      assert.ok(system.includes('合并旧1、2档'));
      assert.ok(system.includes('合并旧3、4、5档'));
      assert.ok(messages.includes('fixedDifficulty'));
      assert.ok(messages.includes(selecting));
    } else {
      // The first and only request must contain the original question AND evidence.
      // The old normalization request fails these assertions before any reply.
      assert.ok(
        messages.includes(fixture.input.question),
        'Original question is preserved',
      );
      assert.ok(
        messages.includes(fixture.input.person.name),
        'Judge receives the secret person',
      );
      for (const claim of fixture.input.claims)
        assert.ok(
          messages.includes(claim.note),
          'Judge receives each original-text claim',
        );
      for (const turn of fixture.input.history)
        assert.ok(messages.includes(turn.answer), 'Prior turns remain data');
      for (const rule of [
        '同一次调用内先理解用户的完整命题',
        '具体姓名猜测只允许',
        'name只能摘取用户原文中的那个名字',
        '关系是非问题',
        '保留否定及其作用范围',
        '否定不能变为肯定',
        '宋以前',
        '宋及以前',
        '宋以后',
        '宋及以后',
        '按是否有交集判断',
        '按是否全部落入判断',
        '条件或边界无法确认用unknown',
        '前轮错误回答不得成为本轮证据',
        '输出no前须确认证据排除了问题允许的全部范围',
      ])
        assert.ok(
          system.includes(rule),
          `Single system prompt retains: ${rule}`,
        );
      assert.ok(
        !system.includes('任务normalize'),
        'No separate normalization prompt',
      );
    }
    res.writeHead(200, { 'Content-Type': 'text/event-stream' });
    const send = (type, value) =>
      res.write(
        `event: ${type}\ndata: ${JSON.stringify({ type, ...value })}\n\n`,
      );
    send('message_start', {
      message: {
        id: 'm1',
        type: 'message',
        role: 'assistant',
        model: 'deepseek-flash',
        content: [],
        stop_reason: null,
        stop_sequence: null,
        usage: { input_tokens: 10, output_tokens: 0 },
      },
    });
    send('content_block_start', {
      index: 0,
      content_block: { type: 'text', text: '' },
    });
    send('content_block_delta', {
      index: 0,
      delta: {
        type: 'text_delta',
        text: JSON.stringify(fixture.expected),
      },
    });
    send('content_block_stop', { index: 0 });
    send('message_delta', {
      delta: { stop_reason: 'end_turn', stop_sequence: null },
      usage: { output_tokens: 10 },
    });
    send('message_stop', {});
    res.end();
  } catch (err) {
    error = err;
    res.writeHead(400);
    res.end();
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
try {
  for (const test of fixtures) {
    fixture = test;
    requests = 0;
    error = undefined;
    const caseDirectory = await mkdtemp(join(directory, 'case-'));
    const child = fork(
      fileURLToPath(new URL('./guess-worker.mjs', import.meta.url)),
      [],
      {
        stdio: ['ignore', 'ignore', 'inherit', 'ipc'],
        env: {
          PATH: process.env.PATH,
          HOME: caseDirectory,
          DSH_HOME: caseDirectory,
          HISTREE_GUESS_DEBUG: '1',
          HISTREE_MODEL: 'deepseek-flash',
          DEEPSEEK_API_KEY: 'test-only',
          DEEPSEEK_BASE_URL: `http://127.0.0.1:${server.address().port}/anthropic/v1`,
        },
      },
    );
    const timer = setTimeout(() => child.kill('SIGKILL'), 45000);
    try {
      let result;
      child.on('message', (message) => {
        result = message;
      });
      const closed = new Promise((resolve, reject) => {
        child.once('error', reject);
        child.once('close', resolve);
      });
      child.send(fixture.input);
      await closed;
      if (error) throw error;
      assert.deepEqual(
        result,
        { type: 'result', data: fixture.expected },
        fixture.name,
      );
      assert.equal(requests, 1, fixture.name);
      console.log(`PASS: ${fixture.name}; model requests=1`);
    } finally {
      clearTimeout(timer);
      child.kill('SIGKILL');
    }
  }
  assert.equal(totalRequests, fixtures.length);
  console.log(
    `Guess worker/dsh smoke passed: ${fixtures.length} fixtures, ${totalRequests} model requests, no tools, no paid calls`,
  );
} finally {
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
  await rm(directory, { recursive: true, force: true });
}
