// Additive game metadata only. Default is read-only: no writes, no model calls.
import { createRequire } from 'node:module';
import { readFile, writeFile, rename } from 'node:fs/promises';
import { randomBytes } from 'node:crypto';
const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { z } = require('zod'), { ConfigService } = require('@nestjs/config');
const { MysqlService } = require('./dist/modules/mysql/mysql.service.js');
const { GuessAgentService } = require('./dist/modules/ask/guess-agent.service.js');
const { GuessBankService } = require('./dist/modules/ask/guess-bank.js');
const { GuessCharacterCatalogue } = require('./dist/modules/ask/guess-character-catalogue.js');
const { GuessClueStore } = require('./dist/modules/ask/guess-clue-store.js');
const { GuessClueSetsService } = require('./dist/modules/ask/guess-clue-sets.service.js');
const { loadClueProfile, validateCachedClues, CLUE_VERSION } = require('./dist/modules/ask/guess-clues.js');
const config = new ConfigService(process.env), db = new MysqlService(config), store = new GuessClueStore(db);
const sets = new GuessClueSetsService(store, new GuessAgentService(config), db);
const args = process.argv.slice(2), apply = args.includes('--apply');
const value = flag => { const i = args.indexOf(flag); return i < 0 ? undefined : args[i + 1]; };
const limit = value('--limit') === undefined ? Infinity : Number(value('--limit'));
if (!(limit === Infinity || (Number.isInteger(limit) && limit > 0))) throw Error('Invalid --limit');
const only = value('--person');
if (only && !z.string().uuid().safeParse(only).success) throw Error('Invalid --person');
const charSchema = z.object({ id: z.string().uuid(), canonical_person_id: z.string().uuid().nullable(), name: z.string().min(1).max(100), aliases: z.array(z.string().min(1).max(100)), courtesy_name: z.string().max(100).nullable().optional(), era: z.string().max(100), birth_year: z.number().int().nullable(), death_year: z.number().int().nullable(), description: z.string().max(2000), period_from: z.number().int().nullable().optional(), period_to: z.number().int().nullable().optional(), difficulty: z.enum(['easy', 'hard']), knowledge_revision: z.number().int().positive().optional() }).strict();
const reportPath = value('--report');
const checkpoint = async summary => {
  if (!reportPath) return;
  await writeFile(reportPath + '.tmp', JSON.stringify(summary, null, 2) + '\n');
  await rename(reportPath + '.tmp', reportPath);
};
try {
  const characters = value('--import') ? z.array(charSchema).parse(JSON.parse(await readFile(value('--import'), 'utf8'))) : [];
  if (new Set(characters.map(c => c.id)).size !== characters.length) throw Error('Duplicate game character IDs');
  if (apply) {
    // Include every original bank member, even if this command runs before either game starts.
    await new GuessCharacterCatalogue(db, new GuessBankService(db)).sync(AbortSignal.timeout(60000));
    for (const p of characters) {
      const duplicate = await db.rows("SELECT id FROM person WHERE name=? AND status='published'", [p.name]);
      if (duplicate.length && (!p.canonical_person_id || !duplicate.some(x => x.id === p.canonical_person_id))) throw Error(`Explicit canonical mapping required for ${p.name}`);
      const existing = await db.rows('SELECT canonical_person_id FROM guess_character WHERE id=?', [p.id]);
      if (existing.length && existing[0].canonical_person_id !== p.canonical_person_id) throw Error('Character identity conflict: ' + p.id);
      await db.execute(`INSERT INTO guess_character(id,canonical_person_id,name,aliases,courtesy_name,era,birth_year,death_year,description,difficulty,period_from,period_to,question_difficulty,knowledge_revision)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE name=VALUES(name),aliases=VALUES(aliases),courtesy_name=VALUES(courtesy_name),era=VALUES(era),birth_year=VALUES(birth_year),death_year=VALUES(death_year),description=VALUES(description),period_from=VALUES(period_from),period_to=VALUES(period_to),knowledge_revision=GREATEST(knowledge_revision,VALUES(knowledge_revision)),difficulty=IF(difficulty_revision=1 AND vote_clue_revision IS NULL,VALUES(difficulty),difficulty)`,
      [p.id, p.canonical_person_id, p.name, JSON.stringify(p.aliases), p.courtesy_name || null, p.era, p.birth_year, p.death_year, p.description, p.difficulty, p.period_from ?? null, p.period_to ?? null, p.difficulty, p.knowledge_revision || 1]);
    }
  }
  const seed = value('--seed') ? JSON.parse(await readFile(value('--seed'), 'utf8')) : { entries: [] };
  let seeded = 0, seedSkipped = 0;
  if (apply) for (const entry of seed.entries) {
    const profile = await loadClueProfile(db, z.string().uuid().parse(entry.person_id), AbortSignal.timeout(10000));
    if (entry.generator_version !== CLUE_VERSION || entry.profile_revision !== profile.revision) { seedSkipped++; continue; }
    const clues = validateCachedClues(entry.clues, profile), signal = AbortSignal.timeout(10000);
    if (await sets.ready(profile, signal)) continue;
    const token = randomBytes(32).toString('hex'), row = await store.claim(profile, token, signal);
    if (row.lease_token !== token) throw Error('Preparation already running: ' + entry.person_id);
    if ((await store.complete(profile, token, clues, signal, entry.provenance || { kind: 'general_knowledge', method: 'ai', prompt_version: CLUE_VERSION })).affectedRows !== 1) throw Error('Seed save failed');
    seeded++;
  }
  const people = await store.candidates({ difficulty: 'easy' }, AbortSignal.timeout(60000));
  const selected = people.filter(p => !only || p.id === only);
  const summary = { mode: apply ? 'prepare-easy' : 'read-only', generatorVersion: CLUE_VERSION, importCharacters: characters.length, seeded, seedSkipped, easyPeople: people.length, selectedPeople: selected.length, prepared: 0, reused: 0, failed: 0, pending: 0, ready: 0, complete: false, details: [] };
  let attempts = 0;
  for (const p of selected) {
    try {
      const signal = AbortSignal.timeout(125000), profile = await loadClueProfile(db, p.id, signal);
      const hit = await sets.ready(profile, signal);
      let status;
      if (hit) { summary.reused++; summary.ready++; status = 'reused'; }
      else if (!apply || attempts >= limit) { summary.pending++; status = 'pending'; }
      else {
        attempts++; await sets.ensure(profile, signal); summary.prepared++; summary.ready++; status = 'prepared';
      }
      summary.details.push({ person_id: p.id, status, revision: profile.revision });
    } catch (error) {
      summary.failed++; summary.details.push({ person_id: p.id, status: 'failed', error: error.name });
    }
    // Resume checks the durable current profile revision, rather than trusting a previous report.
    await checkpoint(summary);
    if (apply) console.log(JSON.stringify({ progress: summary.details.length, prepared: summary.prepared, reused: summary.reused, failed: summary.failed, pending: summary.pending }));
  }
  summary.complete = summary.failed === 0 && summary.pending === 0;
  await checkpoint(summary);
  console.log(JSON.stringify(summary, null, 2));
  if (summary.failed || (args.includes('--require-complete') && !summary.complete)) process.exitCode = 1;
} finally { await db.onModuleDestroy(); }
