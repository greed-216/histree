// Actual native SDK, local model protocol only; no paid calls.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { setTimeout as delay } from 'node:timers/promises';
import { PreparedClueAgent } from './guess-preparer.mjs';
let active = 0,
  maxActive = 0,
  requests = 0,
  failure;
const server = createServer(async (req, res) => {
  let counted = false;
  try {
    let body = '';
    for await (const chunk of req) body += chunk;
    const request = JSON.parse(body),
      messages = JSON.stringify(request.messages),
      system = JSON.stringify(request.system);
    const markers = [...new Set(messages.match(/resident-[a-z0-9-]+/g) || [])];
    assert.equal(
      markers.length,
      1,
      'Every SDK activity has a fresh session, with no other person history',
    );
    assert.equal(
      (request.tools || []).length,
      0,
      'No shell, filesystem or external tools',
    );
    assert(system.includes('不能重复'));
    if (markers[0].includes('review'))
      assert(system.includes('独立复核proposed'));
    active++;
    counted = true;
    requests++;
    maxActive = Math.max(maxActive, active);
    res.once('close', () => {
      if (counted) {
        active--;
        counted = false;
      }
    });
    await delay(markers[0].includes('abort') ? 3000 : 150);
    if (res.destroyed) return;
    res.writeHead(200, { 'Content-Type': 'text/event-stream' });
    const send = (type, value) =>
      res.write(
        `event: ${type}\ndata: ${JSON.stringify({ type, ...value })}\n\n`,
      );
    send('message_start', {
      message: {
        id: 'fixture-' + requests,
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
        text: JSON.stringify({ marker: markers[0] }),
      },
    });
    send('content_block_stop', { index: 0 });
    send('message_delta', {
      delta: { stop_reason: 'end_turn', stop_sequence: null },
      usage: { output_tokens: 10 },
    });
    send('message_stop', {});
    res.end();
  } catch (error) {
    failure = error;
    res.writeHead(400);
    res.end();
  }
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const agent = new PreparedClueAgent({
  apiKey: 'test-only',
  baseUrl: `http://127.0.0.1:${server.address().port}/anthropic/v1`,
  recycleAfter: 8,
});
const input = (marker) => ({
  task: 'clues',
  person: { name: '合成测试人物' },
  marker,
});
try {
  const results = await Promise.all(
    Array.from({ length: 8 }, (_, i) =>
      agent.run(input('resident-person-' + i), AbortSignal.timeout(45000)),
    ),
  );
  assert.deepEqual(
    results.map((r) => r.marker),
    Array.from({ length: 8 }, (_, i) => 'resident-person-' + i),
  );
  assert.equal(
    agent.metrics().runtimeStarts,
    1,
    'One runtime handles concurrent independent sessions',
  );
  assert(maxActive >= 2, 'Provider requests overlap');
  assert.deepEqual(
    await agent.run(input('resident-recycled'), AbortSignal.timeout(45000)),
    { marker: 'resident-recycled' },
  );
  assert.equal(
    agent.metrics().runtimeStarts,
    2,
    'Retires old sessions within a bounded generation',
  );
  assert.deepEqual(
    await agent.run(
      { ...input('resident-review'), task: 'review_clues' },
      AbortSignal.timeout(45000),
    ),
    { marker: 'resident-review' },
  );
  assert.equal(
    agent.metrics().runtimeStarts,
    3,
    'Review gets its own system prompt and runtime',
  );
  const controller = new AbortController();
  const aborted = agent.run(input('resident-abort'), controller.signal);
  const timer = setTimeout(() => controller.abort(), 200);
  await assert.rejects(aborted);
  clearTimeout(timer);
  assert.deepEqual(
    await agent.run(input('resident-after-abort'), AbortSignal.timeout(45000)),
    { marker: 'resident-after-abort' },
  );
  await agent.close();
  assert.equal(agent.metrics().runtimes, 0);
  assert.equal(failure, undefined);
  console.log(
    JSON.stringify({
      status: 'passed',
      requests,
      maxActive,
      runtimeStarts: agent.metrics().runtimeStarts,
      freshSessions: true,
      recycled: true,
      abortRecovered: true,
      paidCalls: 0,
    }),
  );
} finally {
  await agent.close();
  server.closeAllConnections();
  await new Promise((resolve) => server.close(resolve));
}
