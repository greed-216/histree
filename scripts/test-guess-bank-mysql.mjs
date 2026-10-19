/** Real HTTP/Nest/MySQL benchmark and durable feedback regression. Synthetic, disposable data only. */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createHash, randomUUID, randomBytes } from 'node:crypto';
import { performance } from 'node:perf_hooks';
const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
require('reflect-metadata');
const { ConfigService } = require('@nestjs/config');
const { Module } = require('@nestjs/common');
const { NestFactory } = require('@nestjs/core');
const { createConnection } = require('mysql2/promise');
const { MysqlService } = require('./dist/modules/mysql/mysql.service.js');
const { GuessService } = require('./dist/modules/ask/guess.service.js');
const { GuessBankService } = require('./dist/modules/ask/guess-bank.js');
const { GuessController } = require('./dist/modules/ask/guess.controller.js');
const { AiAccessService } = require('./dist/modules/ask/ai-access.service.js');
const { GatewayGuard } = require('./dist/common/guards/gateway.guard.js');
const { loadGuessCatalogue } = require('./dist/modules/ask/guess-catalogue.js');
const env = process.env;
assert.match(env.MYSQL_DATABASE || '', /^histree_test_[a-z0-9_]+$/);
assert.ok(['127.0.0.1', 'localhost'].includes(env.MYSQL_HOST));
const config = new ConfigService({ ...env, HISTREE_DATABASE: 'mysql', HISTREE_GATEWAY_SECRET: 'test-only-guess-bank-secret-at-least-32-chars', HISTREE_ALLOW_ANONYMOUS: 'true' });
const db = new MysqlService(config);
const conn = await createConnection({ host: env.MYSQL_HOST, port: Number(env.MYSQL_PORT || 3306), user: env.MYSQL_USER, password: env.MYSQL_PASSWORD, database: env.MYSQL_DATABASE, charset: 'utf8mb4' });
const [empty] = await conn.query('SELECT COUNT(*) count FROM person');
assert.equal(Number(empty[0].count), 0, 'Game tests require an empty disposable person table');
const source = randomUUID(), event = randomUUID();
const people = Array.from({ length: 15022 }, (_, i) => ({ id: randomUUID(), name: i === 0 ? '曹操' : i === 1 ? '刘琨' : `合成题库人物${i}` }));
let app, checks = 0, modelCalls = 0;
const bank = new GuessBankService(db);
const agent = { available: () => true, run: () => { modelCalls++; throw new Error('Ordinary games must not call a model'); } };
const service = new GuessService(db, agent, bank);
const hash = (value) => createHash('sha256').update(value).digest('hex');
const rating = (person, revision, actor, vote) => ({ person_id: person, revision, actor_hash: hash(actor), game_hash: randomBytes(32).toString('hex'), rating: vote, turns: 1, hints: 0 });
try {
  await conn.execute('INSERT INTO source(id,title,source_type) VALUES(?,?,?)', [source, '题库测试原文来源', 'primary']);
  for (let offset = 0; offset < people.length; offset += 250) {
    const batch = people.slice(offset, offset + 250);
    await conn.query('INSERT INTO person(id,name,status) VALUES ?', [batch.map((p) => [p.id, p.name, 'published'])]);
    await conn.query('INSERT INTO fact_claim(id,subject_table,subject_id,claim_text,source_id,status,field_path,note) VALUES ?', [batch.map((p) => [randomUUID(), 'person', p.id, '合成测试事实，非历史资料', source, 'published', 'description', '原文：仅用于独立测试库的合成原文。'])]);
  }
  await conn.execute('INSERT INTO event(id,title,start_year,end_year,status) VALUES(?,?,?,?,?)', [event, '合成活动事件', 900, 907, 'published']);
  for (const person of people.slice(0, 2)) await conn.execute('INSERT INTO person_event(id,person_id,event_id,role,status) VALUES(?,?,?,?,?)', [randomUUID(), person.id, event, '测试', 'published']);
  const prepStart = performance.now();
  const catalogue = await loadGuessCatalogue(db, AbortSignal.timeout(60000));
  const prepared = await bank.prepare(catalogue, AbortSignal.timeout(60000));
  const preparationMs = performance.now() - prepStart;
  assert.equal(prepared.length, people.length);
  assert.equal(prepared.filter((p) => p.game_difficulty === 'easy').length, 1); checks++;
  const access = new AiAccessService(config, db);
  class BenchmarkModule {}
  Module({ controllers: [GuessController], providers: [GatewayGuard, { provide: GuessService, useValue: service }, { provide: AiAccessService, useValue: access }] })(BenchmarkModule);
  app = await NestFactory.create(BenchmarkModule, { logger: false, rawBody: true });
  await app.listen(0, '127.0.0.1');
  const base = await app.getUrl();
  const session = async () => (await access.issueSession()).token;
  const post = async (path, body, actor, expected = 201) => {
    const res = await fetch(`${base}/api/v1/ask/guess/${path}`, { method: 'POST', headers: { 'content-type': 'application/json', 'x-histree-anonymous': actor }, body: JSON.stringify(body) });
    const data = await res.json();
    assert.equal(res.status, expected, JSON.stringify(data));
    return data;
  };
  const actor = await session();
  const coldStart = performance.now();
  const first = await post('start', { difficulty: 'easy' }, actor);
  const coldStartMs = performance.now() - coldStart;
  assert.equal(first.remaining, 30); assert.ok(!first.person); checks++;
  const samples = [];
  for (let i = 0; i < 30; i++) {
    const start = performance.now();
    await post('start', { difficulty: i % 2 ? 'hard' : 'easy', ...(i % 3 === 0 ? { from: 900, to: 960 } : {}) }, actor);
    samples.push(performance.now() - start);
  }
  assert.equal(modelCalls, 0); checks++;
  samples.sort((a, b) => a - b);
  const stats = { environment: 'isolated MySQL 8 / Nest HTTP / synthetic published corpus; not production latency', people: people.length, preparationMs: Math.round(preparationMs), coldStartMs: Math.round(coldStartMs), warmSamples: samples.length, warmP50Ms: Math.round(samples[Math.ceil(samples.length * .5) - 1]), warmP95Ms: Math.round(samples[Math.ceil(samples.length * .95) - 1]), modelCalls };
  // Own token, played outcome, and idempotency are enforced by the actual HTTP route.
  await post('feedback', { token: first.token, rating: 'hard' }, actor, 400);
  const other = await session();
  await post('feedback', { token: first.token, rating: 'hard' }, other, 403);
  const won = await post('act', { token: first.token, action: 'question', text: '曹操' }, actor);
  assert.equal(won.outcome, 'won'); assert.equal(won.ratingEligible, true); checks++;
  assert.equal((await post('feedback', { token: first.token, rating: 'hard' }, actor)).rating, 'hard');
  assert.equal((await post('feedback', { token: first.token, rating: 'easy' }, actor)).rating, 'hard');
  const row = async (person) => (await db.rows('SELECT * FROM guess_bank WHERE person_id=?', [person]))[0];
  assert.equal((await row(people[0].id)).hard_votes, 1); checks++;
  const anotherGame = await post('start', { difficulty: 'easy' }, actor);
  await post('act', { token: anotherGame.token, action: 'guess', text: '曹操' }, actor);
  await post('feedback', { token: anotherGame.token, rating: 'hard' }, actor);
  assert.equal((await row(people[0].id)).hard_votes, 1); checks++;
  const oldGame = await post('start', { difficulty: 'easy' }, other);
  for (let i = 1; i < 12; i++) {
    const voter = await session();
    const game = await post('start', { difficulty: 'easy' }, voter);
    await post('act', { token: game.token, action: 'guess', text: '曹操' }, voter);
    await post('feedback', { token: game.token, rating: 'hard' }, voter);
    if (i === 10) assert.equal((await row(people[0].id)).difficulty, 'easy');
  }
  assert.equal((await row(people[0].id)).difficulty, 'hard');
  assert.equal((await row(people[0].id)).revision, 2); checks++;
  await post('start', { difficulty: 'easy' }, await session(), 400);
  const oldWon = await post('act', { token: oldGame.token, action: 'guess', text: '曹操' }, other);
  assert.equal(oldWon.filters.difficulty, 'easy');
  await post('feedback', { token: oldGame.token, rating: 'easy' }, other);
  assert.equal((await row(people[0].id)).easy_votes, 0); checks++;
  const restored = await new GuessBankService(db).prepare(catalogue, AbortSignal.timeout(60000));
  assert.equal(restored.find((p) => p.id === people[0].id).game_difficulty, 'hard'); checks++;
  await db.seedGuessBank([{ person_id: people[0].id, difficulty: 'easy' }]);
  assert.equal((await row(people[0].id)).difficulty, 'hard'); checks++;
  // Reclassification resets the vote round; the reverse direction needs new consensus.
  for (let i = 0; i < 12; i++) await db.rateGuessPerson(rating(people[0].id, 2, `new-round-${i}`, 'easy'));
  assert.equal((await row(people[0].id)).difficulty, 'easy');
  assert.equal((await row(people[0].id)).revision, 3); checks++;
  // Concurrent games from one actor count once, with no lost/doubled increment.
  await Promise.all(Array.from({ length: 16 }, () => db.rateGuessPerson(rating(people[1].id, 1, 'same-actor', 'easy'))));
  assert.equal((await row(people[1].id)).easy_votes, 1); checks++;
  // Exactly 9/12 contrary votes (75%) moves a level; 8/12 must not.
  for (let i = 0; i < 11; i++) await db.rateGuessPerson(rating(people[1].id, 1, `threshold-${i}`, i < 8 ? 'easy' : 'right'));
  assert.equal((await row(people[1].id)).difficulty, 'easy');
  assert.equal((await row(people[1].id)).revision, 2); checks++;
  for (let i = 0; i < 12; i++) await db.rateGuessPerson(rating(people[2].id, 1, `mixed-${i}`, i < 8 ? 'easy' : 'right'));
  assert.equal((await row(people[2].id)).difficulty, 'hard'); checks++;
  assert.equal(modelCalls, 0);
  console.log(`PASS: ${checks} durable guess-bank/HTTP contracts; zero model calls`);
  console.log(`GUESS_START_BENCHMARK ${JSON.stringify(stats)}`);
} finally {
  await app?.close();
  service.onModuleDestroy();
  await conn.execute('DELETE FROM fact_claim WHERE source_id=?', [source]);
  for (let offset = 0; offset < people.length; offset += 1000) {
    const batch = people.slice(offset, offset + 1000);
    await conn.execute(`DELETE FROM person WHERE id IN (${batch.map(() => '?').join(',')})`, batch.map((p) => p.id));
  }
  await conn.execute('DELETE FROM event WHERE id=?', [event]);
  await conn.execute('DELETE FROM source WHERE id=?', [source]);
  await conn.end();
  await db.onModuleDestroy();
}
