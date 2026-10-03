// Exercise the real game worker/dsh runtime against a local model fixture, without paid requests.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { fork } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
const directory = await mkdtemp(join(tmpdir(), 'histree-guess-smoke-'));
const input = {
  task: 'question',
  person: { name: '测试人物' },
  question: '你是皇帝吗？',
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
    assert.equal(requests, 1);
    assert.equal(
      (request.tools || []).length,
      0,
      'Game has no shell, filesystem, MCP or other tools',
    );
    assert.ok(JSON.stringify(request.messages).includes('你是皇帝吗'));
    assert.ok(JSON.stringify(request.messages).includes('测试人物称帝'));
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
        text: JSON.stringify({ verdict: 'yes', claims: ['c1'] }),
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
    data: { verdict: 'yes', claims: ['c1'] },
  });
  assert.equal(requests, 1);
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
