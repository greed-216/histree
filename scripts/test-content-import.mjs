import { PGlite } from '@electric-sql/pglite';
import { readdir, readFile, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
const dir = await mkdtemp(join(tmpdir(), 'histree-import-'));
const db = new PGlite();
try {
 execFileSync('python3',['scripts/prepare-content-import.py','content/later-liang-907-923/content-batch.json',dir]);
 await db.exec(`CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY);
 CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT null::uuid $$;
 CREATE ROLE anon; CREATE ROLE authenticated; GRANT USAGE ON SCHEMA public TO anon;`);
 for (const file of (await readdir('supabase/migrations')).filter(f=>f.endsWith('.sql')).sort()) {
  await db.exec(await readFile(`supabase/migrations/${file}`,'utf8'));
 }
 await db.exec('GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;');
 const run = async name => db.exec(await readFile(join(dir,name),'utf8'));
 const count = async table => (await db.query(`SELECT count(*)::int AS n FROM ${table}`)).rows[0].n;
 await run('import-draft.sql');
 await run('import-draft.sql');
 const expected = {person:6,event:9,person_event:15,person_relationship:4,source:14,fact_claim:85,topic:1};
 for(const [t,n] of Object.entries(expected)) assert.equal(await count(t),n,t);
 await db.exec('SET ROLE anon');
 for(const t of Object.keys(expected).filter(t=>t!=='source')) assert.equal(await count(t),0,`draft ${t}`);
 await db.exec('RESET ROLE');
 await run('publish.sql');
 await run('import-draft.sql'); // Must preserve publication and later editorial changes.
 await db.exec('SET ROLE anon');
 for(const [t,n] of Object.entries(expected)) assert.equal(await count(t),n,`published ${t}`);
 const topic = (await db.query('SELECT sections FROM topic')).rows[0];
 const nodes = new Set((await db.query('SELECT id FROM person UNION SELECT id FROM event')).rows.map(r=>r.id));
 for(const s of topic.sections) for(const id of s.node_ids) assert(nodes.has(id));
 assert.equal((await db.query('SELECT count(*)::int AS n FROM fact_claim c JOIN source s ON c.source_id=s.id')).rows[0].n,85);
 await db.exec('RESET ROLE');
 await run('unpublish.sql');
 await db.exec('SET ROLE anon');
 assert.equal(await count('topic'),0);
 assert.equal(await count('fact_claim'),0);
 console.log('PASS: real content import, repeat import, draft isolation, publication, node/source references and unpublishing');
} finally { await db.close(); await rm(dir,{recursive:true,force:true}); }
