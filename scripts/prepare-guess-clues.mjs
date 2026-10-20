// Additive game metadata only. Default is read-only: no writes, no model calls.
import { createRequire } from 'node:module';
import { readFile, writeFile, rename, appendFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';
import { PreparedClueAgent } from '../apps/api/dsh/guess-preparer.mjs';
import { randomBytes } from 'node:crypto';
const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { z } = require('zod'), { ConfigService } = require('@nestjs/config');
const { MysqlService } = require('./dist/modules/mysql/mysql.service.js');
const { GuessAgentService } = require('./dist/modules/ask/guess-agent.service.js');
const { GuessBankService } = require('./dist/modules/ask/guess-bank.js');
const { GuessCharacterCatalogue } = require('./dist/modules/ask/guess-character-catalogue.js');
const { GuessClueStore } = require('./dist/modules/ask/guess-clue-store.js');
const { GuessClueResearch } = require('./dist/modules/ask/guess-clue-research.js');
const { GuessClueSetsService } = require('./dist/modules/ask/guess-clue-sets.service.js');
const { loadClueProfile, validateCachedClues, CLUE_VERSION } = require('./dist/modules/ask/guess-clues.js');
const config = new ConfigService(process.env), db = new MysqlService(config), store = new GuessClueStore(db);
const sets = new GuessClueSetsService(store, new GuessAgentService(config), db, new GuessClueResearch(db));
const args = process.argv.slice(2), apply = args.includes('--apply');
const value = flag => { const i = args.indexOf(flag); return i < 0 ? undefined : args[i + 1]; };
const limit = value('--limit') === undefined ? Infinity : Number(value('--limit'));
if (!(limit === Infinity || (Number.isInteger(limit) && limit > 0))) throw Error('Invalid --limit');
const difficulty = value('--difficulty') || 'all';
if (!['easy', 'hard', 'all'].includes(difficulty)) throw Error('Invalid --difficulty');
const engine = value('--engine') || 'resident';
if (!['resident', 'isolated'].includes(engine)) throw Error('Invalid --engine');
const concurrency = Number(value('--concurrency') || 8), passes = Number(value('--passes') || 1);
if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > (engine === 'resident' ? 32 : 8)) throw Error('Invalid --concurrency');
if (!Number.isInteger(passes) || passes < 1 || passes > 3) throw Error('Invalid --passes (1 to 3)');
const sample = value('--sample') === undefined ? Infinity : Number(value('--sample'));
if (!(sample === Infinity || (Number.isInteger(sample) && sample > 0))) throw Error('Invalid --sample');
const manifestPath = value('--manifest');
const only = value('--person');
if (only && !z.string().uuid().safeParse(only).success) throw Error('Invalid --person');
const charSchema = z.object({ id: z.string().uuid(), canonical_person_id: z.string().uuid().nullable(), name: z.string().min(1).max(100), aliases: z.array(z.string().min(1).max(100)), courtesy_name: z.string().max(100).nullable().optional(), era: z.string().max(100), birth_year: z.number().int().nullable(), death_year: z.number().int().nullable(), description: z.string().max(2000), period_from: z.number().int().nullable().optional(), period_to: z.number().int().nullable().optional(), difficulty: z.enum(['easy', 'hard']), knowledge_revision: z.number().int().positive().optional() }).strict();
const reportPath = value('--report');
const checkpoint = async summary => {
  if (!reportPath) return;
  await writeFile(reportPath + '.tmp', JSON.stringify(summary, null, 2) + '\n');
  await rename(reportPath + '.tmp', reportPath);
};
const resident = engine === 'resident' ? new PreparedClueAgent({enabled: config.get('HISTREE_ASK_ENABLED') === 'true', apiKey: config.get('DEEPSEEK_API_KEY'), model: config.get('HISTREE_MODEL')}) : null;
try {
  const characters = value('--import') ? z.array(charSchema).parse(JSON.parse(await readFile(value('--import'), 'utf8'))) : [];
  if (new Set(characters.map(c => c.id)).size !== characters.length) throw Error('Duplicate game character IDs');
  if (apply) {
    // Include every original bank member, even if this command runs before either game starts.
    if (!args.includes('--skip-sync')) await new GuessCharacterCatalogue(db, new GuessBankService(db)).sync(AbortSignal.timeout(60000));
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
  const levels = difficulty === 'all' ? ['easy', 'hard'] : [difficulty];
  const people = [];
  for (const level of levels) people.push(...await store.candidates({ difficulty: level }, AbortSignal.timeout(60000)));
  let selected = people.filter(p => !only || p.id === only).slice(0, sample);
  if (manifestPath) {
    const manifest = z.array(z.object({id: z.string().uuid()}).strict()).parse(JSON.parse(await readFile(manifestPath, 'utf8')));
    const unique = new Set(manifest.map(p => p.id)); if (unique.size !== manifest.length) throw Error('Duplicate manifest people');
    selected = manifest.filter(p => !only || p.id === only).slice(0, sample);
  }
  if (reportPath) await writeFile(reportPath + '.people.json', JSON.stringify(selected) + '\n');
  const summary = { mode: apply ? 'prepare-bank' : 'read-only', generatorVersion: CLUE_VERSION, engine, difficulty, concurrency, passes, startedAt: new Date().toISOString(), updatedAt: null, importCharacters: characters.length, seeded, seedSkipped, totalPeople: people.length, selectedPeople: selected.length, attempted: 0, modelCalls: 0, modelTasks: {}, prepared: 0, reused: 0, disabled: 0, failed: 0, pending: selected.length, ready: 0, complete: false, interrupted: false, details: [] };
  const results = new Map();
  let stopped = false, savedAt = 0;
  const stop = () => { stopped = true; summary.interrupted = true; };
  process.on('SIGTERM', stop); process.on('SIGINT', stop);
  const save = async (force = false) => {
    if (!force && Date.now() - savedAt < 10000) return;
    savedAt = Date.now();
    Object.assign(summary, { prepared: 0, reused: 0, disabled: 0, failed: 0, ready: 0 });
    for (const item of results.values()) {
      if (['prepared', 'reused'].includes(item.status)) { summary[item.status]++; summary.ready++; }
      else summary[item.status]++;
    }
    summary.pending = selected.length - results.size;
    summary.details = [...results.values()]; summary.agent = resident?.metrics(); summary.updatedAt = new Date().toISOString();
    await checkpoint(summary);
  };
  let saving = Promise.resolve();
  const persist = (force = false) => { saving = saving.then(() => save(force)); return saving; };
  await persist(true);
  for (let pass = 1; pass <= (apply ? passes : 1) && !stopped; pass++) {
    summary.pass = pass;
    const queue = selected.filter(p => !results.has(p.id) || results.get(p.id).status === 'failed');
    if (pass > 1 && queue.length) await delay(61000);
    let cursor = 0;
    await Promise.all(Array.from({ length: concurrency }, async () => {
      const workerAgent = resident || new GuessAgentService(config);
      const countedAgent = { available: () => workerAgent.available(), run: (input, signal) => { summary.modelCalls++; summary.modelTasks[input.task] = (summary.modelTasks[input.task] || 0) + 1; return workerAgent.run(input, signal); } };
      const workerSets = new GuessClueSetsService(store, countedAgent, db, new GuessClueResearch(db));
      while (!stopped && cursor < queue.length) {
        const p = queue[cursor++], started = Date.now();
        let item;
        try {
          const signal = AbortSignal.timeout(125000), profile = await loadClueProfile(db, p.id, signal);
          item = { person_id: p.id, name: profile.person.name, revision: profile.revision, pass };
          if (await sets.ready(profile, signal)) item.status = results.get(p.id)?.status === 'prepared' ? 'prepared' : 'reused';
          else if (!apply || summary.attempted >= limit) { if (!results.has(p.id)) continue; else item.status = 'failed'; }
          else {
            summary.attempted++; await workerSets.ensure(profile, signal); item.status = 'prepared';
          }
        } catch (error) {
          item = { ...item, person_id: p.id, pass, status: error.name === 'UnsuitableGamePerson' ? 'disabled' : 'failed', error: error.name, message: error.message?.slice(0, 240) };
          if (error.name === 'BadRequestException') {
            const current = await db.rows('SELECT enabled FROM guess_character WHERE id=?', [p.id], AbortSignal.timeout(5000)).catch(() => []);
            if (current.length && !current[0].enabled) item.status = 'disabled';
          }
        }
        item.elapsedMs = Date.now() - started; item.finishedAt = new Date().toISOString();
        results.set(p.id, item);
        if (reportPath && apply) await appendFile(reportPath + '.jsonl', JSON.stringify(item) + '\n');
        await persist();
        if (apply) console.log(JSON.stringify({ progress: results.size, total: selected.length, attempted: summary.attempted, ...item }));
      }
    }));
  }
  await persist(true);
  summary.complete = summary.failed === 0 && summary.pending === 0 && !summary.interrupted;
  await checkpoint(summary);
  if (reportPath) console.log(JSON.stringify({ ...summary, details: undefined }));
  else console.log(JSON.stringify(summary, null, 2));
  process.off('SIGTERM', stop); process.off('SIGINT', stop);
  if (summary.failed || (args.includes('--require-complete') && !summary.complete)) process.exitCode = 1;

} finally { try { await resident?.close(); } finally { await db.onModuleDestroy(); } }
