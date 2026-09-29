// Real dsh + MCP, deterministic local model server; no API key or paid requests.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DeepSeekHarness } from '@deepseek-ai/dsh-sdk-client';
import { createLibrary, validateAnswer } from './retrieval.mjs';

const dir = await mkdtemp(join(tmpdir(), 'histree-smoke-'));
const id = '11111111-1111-4111-8111-111111111111';
const data = { person: [{ id, name: '测试人物', status: 'published' }], event: [], topic: [], person_relationship: [], person_event: [], event_causality: [], fact_claim: [{ id: 'c1', subject_table: 'person', subject_id: id, status: 'published', claim_text: '虚构测试记载', note: '原文：虚构测试原文。；核对说明：', source: { id: 's1', title: '测试书' } }] };
await writeFile(join(dir, 'snapshot.json'), JSON.stringify(data));
await writeFile(join(dir, 'retrieved.txt'), '');
let requests = 0;
let requestError;
const expected = ['mcp__histree__search_entries', 'mcp__histree__get_entry', 'mcp__histree__get_relations', 'mcp__histree__get_evidence'];
const allowed = new Set([...expected, 'list_mcp_resources', 'list_mcp_resource_templates', 'read_mcp_resource']);
const server = createServer(async (req, res) => {
  try {
    let body = '';
    for await (const chunk of req) body += chunk;
    const request = JSON.parse(body);
    const names = request.tools.map(x => x.name);
    assert.ok(expected.every(x => names.includes(x)), `Missing Histree tools: ${names.join(',')}`);
    assert.ok(names.every(x => allowed.has(x)), `Unexpected tools: ${names.join(',')}`);
    const step = ++requests;
    assert.ok(step <= 3, 'Agent did not settle');
    const block = step === 1 ? { type: 'tool_use', id: 't1', name: expected[0], input: { keywords: ['测试人物'] } }
      : step === 2 ? { type: 'tool_use', id: 't2', name: expected[3], input: { kind: 'person', id } }
      : { type: 'text', text: JSON.stringify({ answer: '测试记载[C1]', insufficientEvidence: false }) };
    if (step > 1) assert.ok(JSON.stringify(request.messages).includes(step === 2 ? '测试人物' : '虚构测试原文'));
    res.writeHead(200, { 'Content-Type': 'text/event-stream' });
    const send = (type, value) => res.write(`event: ${type}\ndata: ${JSON.stringify({ type, ...value })}\n\n`);
    send('message_start', { message: { id: `m${step}`, type: 'message', role: 'assistant', model: 'deepseek-flash', content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 10, output_tokens: 0 } } });
    send('content_block_start', { index: 0, content_block: block.type === 'text' ? { type: 'text', text: '' } : { ...block, input: {} } });
    send('content_block_delta', { index: 0, delta: block.type === 'text' ? { type: 'text_delta', text: block.text } : { type: 'input_json_delta', partial_json: JSON.stringify(block.input) } });
    send('content_block_stop', { index: 0 });
    send('message_delta', { delta: { stop_reason: block.type === 'text' ? 'end_turn' : 'tool_use', stop_sequence: null }, usage: { output_tokens: 10 } });
    send('message_stop', {});
    res.end();
  } catch (error) { requestError = error; res.writeHead(400); res.end('test request rejected'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const harness = new DeepSeekHarness({ profile: 'sdk-minimal', patches: [fileURLToPath(new URL('./readonly.patch.yml', import.meta.url))], cwd: dir, dshHome: dir, model: 'deepseek-flash', initializeTimeoutMs: 30000,
  env: { PATH: process.env.PATH, HOME: dir, DSH_HOME: dir, DEEPSEEK_API_KEY: 'test-only', DEEPSEEK_BASE_URL: `http://127.0.0.1:${server.address().port}/anthropic/v1`, HISTREE_MCP: fileURLToPath(new URL('./mcp.mjs', import.meta.url)), HISTREE_SNAPSHOT: join(dir, 'snapshot.json'), HISTREE_RETRIEVED: join(dir, 'retrieved.txt') } });
const timer = setTimeout(() => { void harness.close(); }, 45000);
try {
  const result = await harness.run('检索测试人物并读取史料依据，然后给出测试回答。');
  if (requestError) throw requestError;
  const retrieved = new Set((await readFile(join(dir, 'retrieved.txt'), 'utf8')).trim().split('\n'));
  assert.equal(validateAnswer(result.finalResponse, createLibrary(data), retrieved).citations[0].claimId, 'c1');
  assert.equal(requests, 3);
  console.log('DSH smoke passed: exact read-only tool roster, search → evidence → verified answer');
} finally {
  clearTimeout(timer); await harness.close(); server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); await rm(dir, { recursive: true, force: true });
}
