// Game metadata only. Default is read-only; --apply seeds missing rows, never historical content.
import { createRequire } from 'node:module';
import { performance } from 'node:perf_hooks';
const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { ConfigService } = require('@nestjs/config');
const { MysqlService } = require('./dist/modules/mysql/mysql.service.js');
const { loadGuessCatalogue } = require('./dist/modules/ask/guess-catalogue.js');
const { GuessBankService, initialGuessDifficulty } = require('./dist/modules/ask/guess-bank.js');
const db = new MysqlService(new ConfigService(process.env));
try {
  const start = performance.now();
  const people = await loadGuessCatalogue(db, AbortSignal.timeout(60000));
  const apply = process.argv.includes('--apply');
  const prepared = apply ? await new GuessBankService(db).prepare(people, AbortSignal.timeout(60000)) : people;
  console.log(JSON.stringify({ mode: apply ? 'prepared' : 'read-only', eligible: people.length,
    easy: prepared.filter((p) => (apply ? p.game_difficulty : initialGuessDifficulty(p)) === 'easy').length,
    hard: prepared.filter((p) => (apply ? p.game_difficulty : initialGuessDifficulty(p)) === 'hard').length,
    note: apply ? 'Only missing game rows were inserted; existing difficulty feedback was preserved.' : 'Initial seed estimate only; existing feedback-adjusted levels are not included. No writes.',
    elapsedMs: Math.round(performance.now() - start), modelCalls: 0,
  }));
} finally { await db.onModuleDestroy(); }
