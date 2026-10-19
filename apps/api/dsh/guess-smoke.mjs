// Exercise the real game worker/dsh runtime against a local model fixture, without paid requests.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { fork } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const guessing = process.argv.includes('--guess');
const selecting = process.argv.includes('--easy')
  ? 'easy'
  : process.argv.includes('--hard')
    ? 'hard'
    : null;
const directory = await mkdtemp(join(tmpdir(), 'histree-guess-smoke-'));
const input = selecting
  ? {
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
    }
  : {
      task: 'question',
      person: { name: '测试人物' },
      question: guessing ? '你是李亚子吗？' : '你是皇帝吗？',
      claims: [{ id: 'c1', note: '原文：测试人物称帝。' }],
    };
let requests = 0;
let error;
const server = createServer(async (req, res) => {
  try {
    let body = '';
    for await (const chunk of req) body += chunk;
    const request = JSON.parse(body);
    requests++;
    assert.ok(requests <= 2);
    assert.equal(
      (request.tools || []).length,
      0,
      'Game has no shell, filesystem, MCP or other tools',
    );
    if (selecting) {
      assert.equal(requests, 1);
      const messages = JSON.stringify({
        system: request.system,
        messages: request.messages,
      });
      assert.ok(messages.includes('合并旧1、2档'));
      assert.ok(messages.includes('合并旧3、4、5档'));
      assert.ok(messages.includes('fixedDifficulty'));
      assert.ok(messages.includes(selecting));
    } else {
      assert.ok(
        JSON.stringify(request.messages).includes(
          guessing ? '你是李亚子吗' : '你是皇帝吗',
        ),
      );
      if (requests === 1) {
        assert.ok(
          !JSON.stringify(request.messages).includes('测试人物称帝'),
          'Normalization cannot see secret evidence',
        );
        assert.ok(
          !JSON.stringify(request.messages).includes('测试人物'),
          'Normalization cannot see secret identity',
        );
      } else {
        assert.ok(JSON.stringify(request.messages).includes('测试人物称帝'));
        assert.ok(
          JSON.stringify(request.messages).includes('你曾经担任皇帝吗'),
          'Judge receives the normalized proposition',
        );
      }
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
        text: JSON.stringify(
          selecting
            ? { ids: [selecting + '-person'] }
            : guessing
              ? { kind: 'guess', question: '李亚子' }
              : requests === 1
                ? { kind: 'yes_no', question: '你曾经担任皇帝吗？' }
                : { verdict: 'yes', claims: ['c1'] },
        ),
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
const child = fork(
  fileURLToPath(new URL('./guess-worker.mjs', import.meta.url)),
  [],
  {
    stdio: ['ignore', 'ignore', 'inherit', 'ipc'],
    env: {
      PATH: process.env.PATH,
      HOME: directory,
      DSH_HOME: directory,
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
  child.send(input);
  await closed;
  if (error) throw error;
  assert.deepEqual(result, {
    type: 'result',
    data: selecting
      ? { ids: [selecting + '-person'] }
      : guessing
        ? { verdict: 'guess', name: '李亚子', claims: [] }
        : { verdict: 'yes', claims: ['c1'] },
  });
  assert.equal(requests, guessing || selecting ? 1 : 2);
  console.log(
    'Guess worker/dsh smoke passed: no tools, bounded JSON reply, fixture evidence, clean worker exit',
  );
} finally {
  clearTimeout(timer);
  child.kill('SIGKILL');
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
  await rm(directory, { recursive: true, force: true });
}
