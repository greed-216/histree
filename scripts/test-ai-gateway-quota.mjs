import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';
const db = new PGlite();
await db.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;');
await db.exec(await readFile(new URL('../supabase/migrations/20261003120000_ai_gateway_quota.sql', import.meta.url), 'utf8'));
const actor = 'anon:' + 'a'.repeat(64);
const consume = async (a, op = 'ask') => (await db.query('SELECT public.consume_ai_gateway_quota($1,$2) accepted', [a,op])).rows[0].accepted;
try {
  for (let i=0;i<10;i++) assert.equal(await consume(actor),true);
  assert.equal(await consume(actor),false);
  const global = await db.query("SELECT used FROM ai_gateway_quota WHERE actor='global' AND operation='ask'");
  assert.equal(global.rows[0].used,10,'denied actor must not debit global capacity');
  const outcomes = await Promise.all(Array.from({length:12},()=>consume('anon:'+'b'.repeat(64))));
  assert.equal(outcomes.filter(Boolean).length,10);
  for (let i=0;i<180;i++) assert.equal(await consume('anon:'+i.toString(16).padStart(64,'0')),true);
  assert.equal(await consume('anon:'+'c'.repeat(64)),false,'global cap survives fresh anonymous identities');
  await assert.rejects(()=>consume('user:forged'));
  await assert.rejects(()=>consume(actor,'arbitrary'));
  await db.exec('SET ROLE anon');
  await assert.rejects(()=>consume(actor));
  await assert.rejects(()=>db.query('SELECT * FROM ai_gateway_quota'));
  await db.exec('RESET ROLE; SET ROLE service_role');
  assert.equal(await consume(actor,'guess'),true);
  console.log('Gateway quota: atomic limits, shared ceilings, denied-debit rollback and role isolation passed');
} finally { await db.close(); }
