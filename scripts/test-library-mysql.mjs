// Explicit native MySQL acceptance; feedback probes are rolled back.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createHash, randomUUID } from 'node:crypto';
const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { ConfigService } = require('@nestjs/config');
const { MysqlService } = require('./dist/modules/mysql/mysql.service.js');
const { LibraryService } = require('./dist/modules/library/library.service.js');
const { FeedbackService } = require('./dist/modules/feedback/feedback.service.js');
const envPath = process.argv[process.argv.indexOf('--mysql-env') + 1];
if (!process.argv.includes('--mysql-env') || !envPath) throw new Error('Explicit --mysql-env required');
const env = Object.fromEntries(fs.readFileSync(envPath, 'utf8').split('\n').filter(s => s && !s.startsWith('#') && s.includes('=')).map(s => { const at = s.indexOf('='); return [s.slice(0, at).trim(), s.slice(at + 1).trim().replace(/^(['"])(.*)\1$/, '$2')]; }));
const db = new MysqlService(new ConfigService({ ...env, HISTREE_DATABASE: 'mysql' }));
const library = new LibraryService(db);
try {
  assert.equal((await library.books()).items.length, 26);
  const count = await db.rows('SELECT COUNT(*) AS n FROM library_paragraph');
  assert.equal(Number(count[0].n), 376987);
  const book = await library.book('zizhi-tongjian');
  const section = book.sections.find(s => Number(s.volume) === 13);
  assert(section);
  const reading = await library.section('zizhi-tongjian', section.id, { paragraph: 'zizhi-tongjian-a63549944a71-p000146' });
  const paragraph = reading.paragraphs.find(p => p.id === 'zizhi-tongjian-a63549944a71-p000146');
  assert(paragraph?.content.includes('太尉绛侯勃不得主兵'));
  const searchMs = {};
  for (const [q, scope] of [['郦商', 'zizhi-tongjian'], ['黃帝', undefined], ['不存在的原文字句驗收', undefined], ['%_', undefined]]) {
    const start = performance.now();
    const result = await library.search(q, scope);
    searchMs[q] = Math.round(performance.now() - start);
    if (q === '郦商' || q === '黃帝') assert(result.items.length);
    if (q === '%_') assert(result.items.every(x => x.snippet.includes('%_')));
  }
  const links = await db.rows(`SELECT l.source_id FROM library_source_link l JOIN source_text t ON t.source_id=l.source_id AND t.archive_url_sha256=l.archive_url_sha256 JOIN source s ON s.id=t.source_id AND s.url=t.archive_url LIMIT 1`);
  assert(links[0]);
  const source = await db.sourceText(links[0].source_id);
  assert(source);
  assert.equal(createHash('sha256').update(source.content).digest('hex'), source.content_sha256);
  assert(await library.sourceLocation(links[0].source_id));
  const tx = await db.connectionPool().getConnection();
  const probe = Object.create(db);
  probe.connectionPool = () => ({ execute: (...args) => tx.execute(...args), getConnection: async () => new Proxy(tx, { get(target, key) { if (key === 'release') return () => {}; const value = target[key]; return typeof value === 'function' ? value.bind(target) : value; } }) });
  const feedback = new FeedbackService(probe), id = randomUUID();
  try {
    await tx.beginTransaction();
    const payload = { id, source_id: source.source_id, page_path: '/library', message: '自动验收：事务回滚验证，不是用户反馈。' };
    assert.deepEqual(await feedback.submit(payload, 'native-acceptance'), { received: true });
    assert.deepEqual(await feedback.submit(payload, 'native-acceptance'), { received: true });
    const [rows] = await tx.execute('SELECT email,context_label FROM feedback WHERE id=?', [id]);
    assert.equal(rows.length, 1); assert.equal(rows[0].email, null); assert(rows[0].context_label);
    await assert.rejects(feedback.submit({ ...payload, message: '相同编号不同内容不能覆盖。' }, 'native-acceptance'), error => error.status === 409);
  } finally { await tx.rollback(); tx.release(); }
  assert.equal(Number((await db.rows('SELECT COUNT(*) n FROM feedback WHERE id=?', [id]))[0].n), 0);
  console.log(JSON.stringify({ passed: true, books: 26, paragraphs: Number(count[0].n), source_location: true, optional_email_and_idempotency: true, feedback_probes_rolled_back: true, search_ms: searchMs }));
} catch (error) {
  console.error(JSON.stringify({ failed: true, code: error.code || error.name, message: error instanceof assert.AssertionError ? error.message : 'Native acceptance failed; connection diagnostics suppressed' }));
  process.exitCode = 1;
} finally { await db.onModuleDestroy(); }
