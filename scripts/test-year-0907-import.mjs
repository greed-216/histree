import { pg_trgm } from '@electric-sql/pglite/contrib/pg_trgm';
import {PGlite} from '@electric-sql/pglite';
import {readFile,readdir,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const db=new PGlite({ extensions: { pg_trgm } }), dir=await mkdtemp(join(tmpdir(),'histree-907-'));
try {
 await db.exec(`CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY); CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT null::uuid $$; CREATE ROLE service_role; CREATE ROLE anon; CREATE ROLE authenticated; GRANT USAGE ON SCHEMA public TO anon;`);
 for (const f of (await readdir('supabase/migrations')).filter(x=>x.endsWith('.sql')).sort()) await db.exec(await readFile('supabase/migrations/'+f,'utf8'));
 await db.exec('GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon');
 execFileSync('python3',['scripts/prepare-content-import.py','content/later-liang-907-923/content-batch.json',dir]);
 await db.exec(await readFile(join(dir,'import-draft.sql'),'utf8'));await db.exec(await readFile(join(dir,'publish.sql'),'utf8'));
 const tables=['person','event','person_event','person_relationship','fact_claim','source','topic'];
 const baseline={};for(const t of tables)baseline[t]=(await db.query(`SELECT * FROM ${t} ORDER BY id`)).rows;
 const sql=await readFile('content/year-0907/sql/import-draft.sql','utf8');
 await db.exec(sql);const first={};for(const t of tables)first[t]=(await db.query(`SELECT count(*)::int n FROM ${t}`)).rows[0].n;
 await db.exec(sql);for(const t of tables)assert.equal((await db.query(`SELECT count(*)::int n FROM ${t}`)).rows[0].n,first[t],'idempotence '+t);
 for(const t of tables){const ids=baseline[t].map(x=>x.id);const rows=(await db.query(`SELECT * FROM ${t} WHERE id=ANY($1::uuid[]) ORDER BY id`,[ids])).rows;assert.deepEqual(rows,baseline[t],'must preserve existing '+t);}
 assert.equal(first.person,93);assert.equal(first.event,67);
 assert.equal((await db.query(`SELECT count(*)::int n FROM (SELECT person_id,event_id FROM person_event GROUP BY person_id,event_id HAVING count(*)>1) q`)).rows[0].n,0,'no duplicate person/event pairs');
 await db.exec('SET ROLE anon');for(const t of tables.filter(x=>x!=='source'))assert.equal((await db.query(`SELECT count(*)::int n FROM ${t}`)).rows[0].n,baseline[t].length,'new drafts hidden '+t);await db.exec('RESET ROLE');
 const corrections=JSON.parse(await readFile('content/year-0907/release-changes.json','utf8'));
 for (const change of corrections) {
   const cols=Object.keys(change.before);
   await db.query(`UPDATE ${change.table} SET ${cols.map(c=>`${c}=v.${c}`).join(',')} FROM jsonb_populate_record(NULL::${change.table}, $1::jsonb) v WHERE ${change.table}.id=$2`,[JSON.stringify(change.before),change.id]);
 }
 const release=await readFile('content/year-0907/sql/release.sql','utf8');
 await db.exec(release);
 for (const change of corrections) {
   const row=(await db.query(`SELECT * FROM ${change.table} WHERE id=$1`,[change.id])).rows[0];
   for (const [key,value] of Object.entries(change.after)) assert.deepEqual(row[key],key==='status'?'published':value,'applied correction '+change.key+':'+key);
 }
 for(const t of tables){const rows=(await db.query(`SELECT * FROM ${t} WHERE id=ANY($1::uuid[]) ORDER BY id`,[baseline[t].map(x=>x.id)])).rows;assert.deepEqual(rows,baseline[t],'release preserves existing '+t);}

 await db.exec('SET ROLE anon');for(const t of tables.filter(x=>x!=='source'))assert.equal((await db.query(`SELECT count(*)::int n FROM ${t}`)).rows[0].n,first[t],'reviewed data published '+t);await db.exec('RESET ROLE');
 const originalQuotes=(await db.query('SELECT id,note FROM fact_claim ORDER BY id')).rows.map(r=>[r.id,r.note.split('；核对说明：')[0]]);
 const copySql=await readFile('content/revisions/2026-09-29-public-copy/apply.sql','utf8');
 await db.exec(copySql); await db.exec(copySql);
 for(const change of JSON.parse(await readFile('content/revisions/2026-09-29-public-copy/changes.json','utf8'))) {
   const row=(await db.query(`SELECT * FROM ${change.table} WHERE id=$1`,[change.id])).rows[0];
   for (const [key,value] of Object.entries(change.after)) assert.deepEqual(row[key],value,'public copy '+change.id+':'+key);
 }
 assert.deepEqual((await db.query('SELECT id,note FROM fact_claim ORDER BY id')).rows.map(r=>[r.id,r.note.split('；核对说明：')[0]]),originalQuotes,'copy edits preserve all quotations');
 await db.exec(await readFile('content/revisions/2026-09-29-reference-links/apply.sql','utf8'));
 for(const source of JSON.parse(await readFile('content/revisions/2026-09-29-reference-links/links.json','utf8')).sources) {
   assert.equal((await db.query('SELECT url FROM source WHERE id=$1',[source.id])).rows[0].url,source.after,'source archive link');
 }
 console.log('PASS: 907 import and retry, preserved all existing rows, no duplicate participation, new drafts invisible to anonymous readers',first);
} finally {await db.close();await rm(dir,{recursive:true,force:true});}
