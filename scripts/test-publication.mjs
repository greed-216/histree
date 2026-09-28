import { PGlite } from '@electric-sql/pglite';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';

const db = new PGlite();
await db.exec(`CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY);
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
CREATE ROLE anon; CREATE ROLE authenticated;
GRANT USAGE ON SCHEMA public, auth TO anon, authenticated; GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated;`);
for (const file of (await readdir(new URL('../supabase/migrations/', import.meta.url))).filter(f => f.endsWith('.sql')).sort()) {
  if (file === '20260928130000_clear_legacy_content.sql') {
    await db.exec(`INSERT INTO auth.users VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb');
      INSERT INTO user_roles(user_id,role) VALUES ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','admin');
      INSERT INTO topic(slug,title) VALUES ('legacy','Old topic');`);
  }
  await db.exec(await readFile(new URL(`../supabase/migrations/${file}`, import.meta.url), 'utf8'));
}
for (const table of ['person','event','person_relationship','person_event','event_causality','topic','source','fact_claim']) {
  assert.equal((await db.query(`SELECT count(*)::int AS count FROM ${table}`)).rows[0].count, 0, `${table} must be empty after all migrations`);
}
assert.equal((await db.query('SELECT count(*)::int AS count FROM auth.users')).rows[0].count, 1);
assert.equal((await db.query('SELECT count(*)::int AS count FROM user_roles')).rows[0].count, 1);
await db.exec(await readFile(new URL('./fixtures/reading.sql', import.meta.url), 'utf8'));
await assert.rejects(db.exec("INSERT INTO event(title,location_lat) VALUES ('Invalid pair',10)"));
await assert.rejects(db.exec("INSERT INTO event(title,location_lat,location_lng) VALUES ('Invalid latitude',91,0)"));
await assert.rejects(db.exec("INSERT INTO event(title,start_year,end_year) VALUES ('Invalid years',10,1)"));
await db.exec('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated;');
const person = '11111111-1111-1111-1111-111111111008';
const event = '22222222-2222-2222-2222-222222222007';
const rel = '33333333-3333-3333-3333-333333333003';
const source = '66666666-6666-6666-6666-666666666001';
const admin = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
const draft = 'dddddddd-dddd-dddd-dddd-dddddddddddd';
const scalar = async sql => Object.values((await db.query(sql)).rows[0])[0];
// Export fictional test records only for the local browser harness when explicitly requested.
if (process.env.HISTREE_FIXTURE_PATH) {
  const fixture = {};
  for (const table of ['person','event','person_relationship','person_event','event_causality','topic','source','fact_claim']) fixture[table] = (await db.query(`SELECT * FROM ${table}`)).rows;
  await writeFile(process.env.HISTREE_FIXTURE_PATH, JSON.stringify(fixture));
}
await db.exec(`INSERT INTO person(id,name) VALUES ('${draft}', 'Draft test');
INSERT INTO fact_claim(subject_table,subject_id,field_path,claim_text,source_id,citation,status) VALUES
 ('person_relationship','${rel}','description','关系测试','${source}','测试定位','published');`);
assert.equal(await scalar(`SELECT status FROM person WHERE id='${draft}'`), 'draft');
await db.exec('SET ROLE anon');
assert.equal(await scalar(`SELECT count(*)::int FROM person WHERE id='${draft}'`), 0);
assert.equal(await scalar(`SELECT count(*)::int FROM person WHERE id='${person}'`), 1);
assert.equal(await scalar(`SELECT count(*)::int FROM topic WHERE slug='test-reading'`), 1);
await assert.rejects(db.exec("INSERT INTO topic(slug,title) VALUES('forbidden','Forbidden')"));
await db.exec(`RESET ROLE; UPDATE person SET status='draft' WHERE id='${person}'; SET ROLE anon;`);
for (const sql of [
  `SELECT count(*)::int FROM person WHERE id='${person}'`,
  `SELECT count(*)::int FROM person_relationship WHERE person_a='${person}' OR person_b='${person}'`,
  `SELECT count(*)::int FROM person_event WHERE person_id='${person}'`,
  `SELECT count(*)::int FROM fact_claim WHERE subject_id IN ('${person}','${rel}')`,
]) assert.equal(await scalar(sql), 0);
await db.exec(`RESET ROLE; UPDATE person SET status='published' WHERE id='${person}'; UPDATE event SET status='draft' WHERE id='${event}'; SET ROLE anon;`);
assert.equal(await scalar(`SELECT count(*)::int FROM person_event WHERE event_id='${event}'`), 0);
assert.equal(await scalar(`SELECT count(*)::int FROM event_causality WHERE cause_event_id='${event}' OR effect_event_id='${event}'`), 0);
await db.exec(`RESET ROLE; UPDATE event SET status='published' WHERE id='${event}'; UPDATE person_relationship SET status='draft' WHERE id='${rel}'; SET ROLE anon;`);
assert.equal(await scalar(`SELECT count(*)::int FROM fact_claim WHERE subject_id='${rel}'`), 0);
await db.exec(`RESET ROLE; INSERT INTO auth.users VALUES ('${admin}'); INSERT INTO user_roles(user_id,role) VALUES('${admin}','admin'); SET ROLE authenticated; SELECT set_config('request.jwt.claim.sub','${admin}',false);`);
assert.equal(await scalar(`SELECT count(*)::int FROM person WHERE id='${draft}'`), 1);
assert.equal(await scalar(`SELECT count(*)::int FROM person_relationship WHERE id='${rel}'`), 1);
await db.exec(`RESET ROLE; SELECT set_config('request.jwt.claim.sub','',false); UPDATE topic SET status='draft'; SET ROLE anon;`);
assert.equal(await scalar('SELECT count(*)::int FROM topic'), 0);
await db.close();
console.log('PASS: all migrations end with empty content and preserved accounts/roles; fictional test fixtures; draft defaults; anonymous read/write isolation; hidden endpoint/relationship evidence; admin draft reads; topic unpublishing');
