import {
  applyDifficultyRating,
  type ClueFeedback,
  type ClueRatingResult,
} from '../ask/guess-difficulty';
import type {
  BankSeed,
  BankFeedback,
  BankRatingResult,
  BankRow,
} from '../ask/guess-bank';
import type { FeedbackRecord } from '../feedback/feedback.service';
import { createHash } from 'node:crypto';
import {
  BadRequestException,
  ConflictException,
  Injectable,
  OnModuleDestroy,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createPool, Pool, RowDataPacket } from 'mysql2/promise';

export type Row = Record<string, any>;
export type MysqlResult = {
  data: any;
  error: Error | null;
  count?: number | null;
};
export interface MysqlRequest extends PromiseLike<MysqlResult> {
  abortSignal(signal: AbortSignal): MysqlRequest;
}
export const tables = [
  'person',
  'event',
  'topic',
  'source',
  'fact_claim',
  'person_relationship',
  'person_event',
  'event_causality',
];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const id = (value: unknown) => {
  if (typeof value !== 'string' || !uuid.test(value))
    throw new Error('Invalid identifier');
  return value;
};
const integer = (
  value: unknown,
  fallback: number,
  min: number,
  max: number,
) => {
  const n = value == null ? fallback : Number(value);
  if (!Number.isInteger(n) || n < min || n > max)
    throw new Error('Invalid number');
  return n;
};
const year = (v: unknown) => (v == null ? null : integer(v, 0, -10000, 10000));
const fields: Record<string, string[]> = {
  person: ['name', 'aliases', 'era', 'faction', 'tags', 'description'],
  event: ['title', 'dynasty', 'tags', 'description'],
  topic: ['title', 'description'],
};
const body = (table: string, alias = 'r', biography = false) => {
  const text = [
    ...(fields[table] || []),
    ...(biography ? ['biography'] : []),
  ].map((f) =>
    ['aliases', 'tags'].includes(f)
      ? `COALESCE((SELECT GROUP_CONCAT(jt.value ORDER BY jt.ordinality SEPARATOR ' ') FROM JSON_TABLE(${alias}.\`${f}\`,'$[*]' COLUMNS(ordinality FOR ORDINALITY,value TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt),'')`
      : `COALESCE(${alias}.\`${f}\`,'')`,
  );
  return `LOWER(CONCAT_WS(' ',${text.join(',')}))`;
};
const pattern = (s: string) =>
  `%${s.toLowerCase().replace(/[!%_]/g, (c) => '!' + c)}%`;
export function visible(table: string, alias = 'r'): string {
  if (table === 'source') return 'TRUE';
  const base = `${alias}.status='published'`;
  const parent = (t: string, column: string) =>
    `EXISTS (SELECT 1 FROM \`${t}\` v WHERE v.id=${alias}.\`${column}\` AND v.status='published')`;
  if (table === 'person_relationship')
    return `${base} AND ${parent('person', 'person_a')} AND ${parent('person', 'person_b')}`;
  if (table === 'person_event')
    return `${base} AND ${parent('person', 'person_id')} AND ${parent('event', 'event_id')}`;
  if (table === 'event_causality')
    return `${base} AND ${parent('event', 'cause_event_id')} AND ${parent('event', 'effect_event_id')}`;
  if (table === 'fact_claim')
    return `${base} AND (${['person', 'event', 'person_relationship', 'person_event', 'event_causality'].map((t) => `(${alias}.subject_table='${t}' AND EXISTS(SELECT 1 FROM \`${t}\` subject WHERE subject.id=${alias}.subject_id AND ${visible(t, 'subject')}))`).join(' OR ')})`;
  return base;
}
const trim = (r: Row, kind?: string, length = 600) => {
  const result = { ...r };
  for (const k of [
    'biography',
    'historical_evaluation',
    'family',
    'social_relations',
    'references',
  ])
    delete result[k];
  if (['person', 'event', 'topic'].includes(kind || ''))
    result.description =
      r.description == null ? null : r.description.slice(0, length);
  if (kind === 'topic') {
    delete result.sections;
    result.section_count = r.sections?.length || 0;
  }
  if (kind === 'person' || kind === 'event') result.type = kind;
  return result;
};

@Injectable()
export class MysqlService implements OnModuleDestroy {
  readonly enabled: boolean;
  private pool?: Pool;
  constructor(private readonly config: ConfigService) {
    const backend = config.get('HISTREE_DATABASE');
    if (backend && backend !== 'mysql')
      throw new Error('Only MySQL is supported');
    this.enabled = true;
  }
  async saveFeedback(row: FeedbackRecord) {
    try {
      await this.connectionPool().execute(
        'INSERT INTO feedback(id,claim_id,source_id,page_path,context_label,message,email,request_sha256) VALUES(?,?,?,?,?,?,?,?)',
        [
          row.id,
          row.claim_id,
          row.source_id,
          row.page_path,
          row.context_label,
          row.message,
          row.email,
          row.request_sha256,
        ],
      );
    } catch (error) {
      if ((error as { code?: string }).code !== 'ER_DUP_ENTRY') throw error;
      const existing = await this.rows(
        'SELECT request_sha256 FROM feedback WHERE id=?',
        [row.id],
      );
      if (existing[0]?.request_sha256 !== row.request_sha256)
        throw new ConflictException('这条反馈已提交，请关闭后重新填写。');
    }
  }
  async seedGuessBank(seeds: BankSeed[], signal?: AbortSignal) {
    for (let offset = 0; offset < seeds.length; offset += 500) {
      signal?.throwIfAborted();
      const batch = seeds.slice(offset, offset + 500);
      if (
        batch.some(
          (seed) =>
            !uuid.test(seed.person_id) ||
            !['easy', 'hard'].includes(seed.difficulty),
        )
      )
        throw new BadRequestException('无效的游戏题库');
      const connection = await this.connectionPool().getConnection();
      const abort = () => connection.destroy();
      try {
        signal?.throwIfAborted();
        signal?.addEventListener('abort', abort, { once: true });
        await connection.execute(
          `INSERT INTO guess_bank(person_id,difficulty) VALUES ${batch.map(() => '(?,?)').join(',')} ON DUPLICATE KEY UPDATE person_id=person_id`,
          batch.flatMap((seed) => [seed.person_id, seed.difficulty]),
        );
        signal?.throwIfAborted();
      } finally {
        signal?.removeEventListener('abort', abort);
        connection.release();
      }
    }
  }

  async rateGuessPerson(
    input: BankFeedback,
    signal?: AbortSignal,
  ): Promise<BankRatingResult> {
    if (
      !uuid.test(input.person_id) ||
      !Number.isSafeInteger(input.revision) ||
      input.revision < 1 ||
      !/^[a-f0-9]{64}$/.test(input.actor_hash) ||
      !/^[a-f0-9]{64}$/.test(input.game_hash) ||
      !['easy', 'right', 'hard'].includes(input.rating) ||
      !Number.isInteger(input.turns) ||
      input.turns < 1 ||
      input.turns > 30 ||
      !Number.isInteger(input.hints) ||
      input.hints < 0 ||
      input.hints > 3
    )
      throw new BadRequestException('无效的难度反馈');
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      await connection.beginTransaction();
      const [rows] = await connection.execute<RowDataPacket[]>(
        'SELECT person_id,difficulty,revision,easy_votes,right_votes,hard_votes FROM guess_bank WHERE person_id=? FOR UPDATE',
        [input.person_id],
      );
      const row = rows[0] as BankRow & {
        easy_votes: number;
        right_votes: number;
        hard_votes: number;
      };
      if (!row) throw new BadRequestException('对应人物暂时无法反馈');
      // The bank row lock serializes deduplication and counter updates per person.
      const [existing] = await connection.execute<RowDataPacket[]>(
        'SELECT rating FROM guess_difficulty_feedback WHERE game_hash=? OR (person_id=? AND revision=? AND actor_hash=?) LIMIT 1',
        [input.game_hash, input.person_id, input.revision, input.actor_hash],
      );
      if (existing.length) {
        await connection.commit();
        return {
          person_id: row.person_id,
          difficulty: row.difficulty,
          revision: row.revision,
          rating: existing[0].rating as BankRatingResult['rating'],
          moved: false,
        };
      }
      await connection.execute(
        'INSERT INTO guess_difficulty_feedback(game_hash,person_id,revision,actor_hash,rating,turns,hints) VALUES(?,?,?,?,?,?,?)',
        [
          input.game_hash,
          input.person_id,
          input.revision,
          input.actor_hash,
          input.rating,
          input.turns,
          input.hints,
        ],
      );
      let moved = false;
      // Late feedback is retained but cannot vote in a newer classification round.
      if (row.revision === input.revision) {
        const change = applyDifficultyRating(
          row.difficulty,
          {
            easy: row.easy_votes,
            right: row.right_votes,
            hard: row.hard_votes,
          },
          input.rating,
        );
        const counts = change.counts;
        moved = change.moved;
        row.difficulty = change.difficulty;
        if (moved) row.revision++;
        await connection.execute(
          'UPDATE guess_bank SET difficulty=?,revision=?,easy_votes=?,right_votes=?,hard_votes=? WHERE person_id=?',
          [
            row.difficulty,
            row.revision,
            moved ? 0 : counts.easy,
            moved ? 0 : counts.right,
            moved ? 0 : counts.hard,
            input.person_id,
          ],
        );
      }
      signal?.throwIfAborted();
      await connection.commit();
      return {
        person_id: row.person_id,
        difficulty: row.difficulty,
        revision: row.revision,
        rating: input.rating,
        moved,
      };
    } catch (error) {
      await connection.rollback().catch(() => {});
      throw error;
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }

  rateGuessClue(
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    return this.rateGameCharacter('clue', input, signal);
  }
  rateGuessCharacterQuestion(
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    return this.rateGameCharacter('question', input, signal);
  }
  private async rateGameCharacter(
    mode: 'clue' | 'question',
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    if (
      !uuid.test(input.person_id) ||
      ![input.actor_hash, input.game_hash, input.clue_revision].every((v) =>
        /^[a-f0-9]{64}$/.test(v),
      ) ||
      !['easy', 'right', 'hard'].includes(input.rating) ||
      !['won', 'revealed', ...(mode === 'question' ? ['limit'] : [])].includes(
        input.outcome,
      ) ||
      !Number.isInteger(input.revision) ||
      input.revision < 1 ||
      !Number.isInteger(input.knowledge_revision) ||
      input.knowledge_revision < 1 ||
      !Number.isInteger(input.guesses) ||
      input.guesses < 0 ||
      input.guesses > 80 ||
      !Number.isInteger(input.unlocked) ||
      input.unlocked < 1 ||
      input.unlocked > 6 ||
      (input.guesses === 0 && input.unlocked === 1)
    )
      throw new BadRequestException('无效的难度反馈');
    const table =
      mode === 'clue' ? 'guess_clue_feedback' : 'guess_question_feedback';
    const columns =
      mode === 'clue'
        ? {
            difficulty: 'difficulty',
            revision: 'difficulty_revision',
            scope: 'vote_clue_revision',
            easy: 'easy_votes',
            right: 'right_votes',
            hard: 'hard_votes',
          }
        : {
            difficulty: 'question_difficulty',
            revision: 'question_revision',
            scope: 'question_vote_clue_revision',
            easy: 'question_easy_votes',
            right: 'question_right_votes',
            hard: 'question_hard_votes',
          };
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection(),
      abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      await connection.beginTransaction();
      const [rows] = await connection.execute<RowDataPacket[]>(
        `SELECT id,${columns.difficulty} difficulty,${columns.revision} difficulty_revision,knowledge_revision,${columns.scope} vote_clue_revision,${columns.easy} easy_votes,${columns.right} right_votes,${columns.hard} hard_votes,enabled FROM guess_character WHERE id=? FOR UPDATE`,
        [input.person_id],
      );
      const row = rows[0];
      if (!row || !row.enabled)
        throw new BadRequestException('对应人物暂时无法反馈');
      const [existing] = await connection.execute<RowDataPacket[]>(
        `SELECT rating FROM ${table} WHERE game_hash=? OR (person_id=? AND clue_revision=? AND difficulty_revision=? AND actor_hash=?) LIMIT 1`,
        [
          input.game_hash,
          input.person_id,
          input.clue_revision,
          input.revision,
          input.actor_hash,
        ],
      );
      if (existing.length) {
        await connection.commit();
        return {
          rating: existing[0].rating,
          difficulty: row.difficulty,
          revision: row.difficulty_revision,
          moved: false,
        };
      }
      await connection.execute(
        `INSERT INTO ${table}(game_hash,person_id,clue_revision,difficulty_revision,actor_hash,rating,guesses,unlocked,outcome) VALUES(?,?,?,?,?,?,?,?,?)`,
        [
          input.game_hash,
          input.person_id,
          input.clue_revision,
          input.revision,
          input.actor_hash,
          input.rating,
          input.guesses,
          input.unlocked,
          input.outcome,
        ],
      );
      let moved = false;
      // Votes belong to this clue set and classification round, not to the question game.
      if (
        row.difficulty_revision === input.revision &&
        row.knowledge_revision === input.knowledge_revision
      ) {
        const previous =
          row.vote_clue_revision === input.clue_revision
            ? {
                easy: row.easy_votes,
                right: row.right_votes,
                hard: row.hard_votes,
              }
            : { easy: 0, right: 0, hard: 0 };
        const change = applyDifficultyRating(
          row.difficulty,
          previous,
          input.rating,
        );
        moved = change.moved;
        row.difficulty = change.difficulty;
        if (moved) row.difficulty_revision++;
        await connection.execute(
          `UPDATE guess_character SET ${columns.difficulty}=?,${columns.revision}=?,${columns.scope}=?,${columns.easy}=?,${columns.right}=?,${columns.hard}=? WHERE id=?`,
          [
            row.difficulty,
            row.difficulty_revision,
            input.clue_revision,
            change.counts.easy,
            change.counts.right,
            change.counts.hard,
            input.person_id,
          ],
        );
      }
      signal?.throwIfAborted();
      await connection.commit();
      return {
        rating: input.rating,
        difficulty: row.difficulty,
        revision: row.difficulty_revision,
        moved,
      };
    } catch (error) {
      await connection.rollback().catch(() => {});
      throw error;
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }

  async sourceText(sourceId: string) {
    if (!uuid.test(sourceId)) throw new BadRequestException('无效的来源地址');
    if (!this.enabled) return null;
    try {
      const rows = await this.rows(
        `SELECT t.source_id,t.archive_url,t.content,t.content_sha256 FROM source_text t
         JOIN source s ON s.id=t.source_id AND s.url=t.archive_url
         WHERE t.source_id=? AND EXISTS(SELECT 1 FROM fact_claim c WHERE c.source_id=s.id AND ${visible('fact_claim', 'c')}) LIMIT 1`,
        [sourceId],
      );
      return rows[0] || null;
    } catch (error) {
      // An older database can serve the rest of the source page before this migration.
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return null;
      throw error;
    }
  }
  async resolveSourceText(archive: string) {
    if (
      !/^https:\/\/github\.com\/greed-216\/histree\/blob\/[a-f0-9]{7,40}\/(?:content|resources\/(?:derived|originals))\/.+\.(?:txt|jsonl)(?:#L[1-9]\d*(?:-L[1-9]\d*)?)?$/.test(
        archive,
      ) ||
      archive.length > 2048
    )
      throw new BadRequestException('无效的存档地址');
    if (!this.enabled) return null;
    try {
      const rows = await this.rows(
        `SELECT t.source_id FROM source_text t JOIN source s ON s.id=t.source_id AND s.url=t.archive_url
         WHERE t.archive_url_sha256=? AND t.archive_url=? AND EXISTS(SELECT 1 FROM fact_claim c WHERE c.source_id=s.id AND ${visible('fact_claim', 'c')}) ORDER BY t.source_id LIMIT 1`,
        [createHash('sha256').update(archive).digest('hex'), archive],
      );
      return rows[0] || null;
    } catch (error) {
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return null;
      throw error;
    }
  }
  private connectionPool() {
    if (!this.enabled) throw new Error('MySQL is disabled');
    if (!this.pool) {
      for (const key of [
        'MYSQL_HOST',
        'MYSQL_DATABASE',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
      ])
        if (!this.config.get(key))
          throw new Error('MySQL configuration is incomplete');
      const mode = this.config.get<string>('MYSQL_SSL_MODE') || 'disabled';
      if (!['disabled', 'require', 'verify-full'].includes(mode))
        throw new Error('Invalid TLS mode');
      this.pool = createPool({
        host: this.config.get('MYSQL_HOST'),
        port: integer(this.config.get('MYSQL_PORT'), 3306, 1, 65535),
        database: this.config.get('MYSQL_DATABASE'),
        user: this.config.get('MYSQL_USER'),
        password: this.config.get('MYSQL_PASSWORD'),
        charset: 'utf8mb4',
        timezone: 'Z',
        dateStrings: true,
        decimalNumbers: true,
        connectionLimit: 6,
        maxIdle: 6,
        idleTimeout: 60000,
        waitForConnections: true,
        queueLimit: 30,
        connectTimeout: 10000,
        ...(mode !== 'disabled'
          ? { ssl: { rejectUnauthorized: mode === 'verify-full' } }
          : {}),
        multipleStatements: false,
      });
    }
    return this.pool;
  }
  async execute(
    sql: string,
    args: any[] = [],
    signal?: AbortSignal,
  ): Promise<{ affectedRows: number }> {
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin');
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      const [result] = await connection.execute(sql, args);
      signal?.throwIfAborted();
      return {
        affectedRows: Number(
          (result as { affectedRows?: number }).affectedRows || 0,
        ),
      };
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
  async rows(
    sql: string,
    args: any[] = [],
    signal?: AbortSignal,
  ): Promise<Row[]> {
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin');
      await connection.query(
        "SET SESSION time_zone='+00:00', max_execution_time=10000,group_concat_max_len=65536",
      );
      const [result] = await connection.execute<RowDataPacket[]>(sql, args);
      signal?.throwIfAborted();
      return result.map((r) =>
        Object.fromEntries(
          Object.entries(r).map(([k, v]) => [
            k,
            k === 'created_at' && typeof v === 'string'
              ? v.replace(' ', 'T') + '+00:00'
              : v,
          ]),
        ),
      );
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
  async consumeQuota(actor: string, operation: 'ask' | 'guess' | 'session') {
    if (
      !/^(anon:[a-f0-9]{64}|user:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$/.test(
        actor,
      ) ||
      !['ask', 'guess', 'session'].includes(operation)
    )
      throw new Error('Invalid quota scope');
    const connection = await this.connectionPool().getConnection();
    try {
      await connection.query(
        "SET SESSION time_zone='+00:00',innodb_lock_wait_timeout=5",
      );
      await connection.beginTransaction();
      const [time] = await connection.query<RowDataPacket[]>(
        "SELECT DATE_FORMAT(UTC_TIMESTAMP(),'%Y-%m-%d %H:00:00') bucket",
      );
      const bucket = time[0].bucket;
      const actorCap =
          operation === 'ask' ? 10 : operation === 'guess' ? 80 : 1,
        globalCap =
          operation === 'ask' ? 200 : operation === 'guess' ? 1600 : 1000;
      // Lock global then actor in a fixed order. A rejected actor rolls back both debits.
      for (const [scope, cap] of [
        ['global', globalCap],
        [actor, actorCap],
      ] as const) {
        await connection.execute(
          'INSERT INTO ai_gateway_quota(actor,operation,bucket,used) VALUES(?,?,?,0) ON DUPLICATE KEY UPDATE used=used',
          [scope, operation, bucket],
        );
        const [rows] = await connection.execute<RowDataPacket[]>(
          'SELECT used FROM ai_gateway_quota WHERE actor=? AND operation=? AND bucket=? FOR UPDATE',
          [scope, operation, bucket],
        );
        if (rows[0].used >= cap) {
          await connection.rollback();
          return false;
        }
        await connection.execute(
          'UPDATE ai_gateway_quota SET used=used+1 WHERE actor=? AND operation=? AND bucket=?',
          [scope, operation, bucket],
        );
      }
      await connection.execute(
        'DELETE FROM ai_gateway_quota WHERE bucket < DATE_SUB(?,INTERVAL 2 HOUR)',
        [bucket],
      );
      await connection.commit();
      return true;
    } catch (error) {
      await connection.rollback();
      throw error;
    } finally {
      connection.release();
    }
  }
  async onModuleDestroy() {
    await this.pool?.end();
  }
  getClient() {
    return this.client();
  }
  client() {
    return {
      from: (table: string) => new MysqlQuery(this, table),
      rpc: (name: string, args: Row = {}) =>
        this.operation((s) => this.rpc(name, args, s)),
    };
  }
  operation(run: (signal?: AbortSignal) => Promise<any>): MysqlRequest {
    let signal: AbortSignal | undefined;
    const request: MysqlRequest = {
      abortSignal: (s: AbortSignal) => {
        signal = s;
        return request;
      },
      then: <TResult1 = MysqlResult, TResult2 = never>(
        resolve?:
          | ((value: MysqlResult) => TResult1 | PromiseLike<TResult1>)
          | null,
        reject?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null,
      ) =>
        run(signal)
          .then((data) => ({ data, error: null }))
          .catch(() => ({ data: null, error: new Error('公开资料查询失败') }))
          .then(resolve, reject),
    };
    return request;
  }
  async rpc(name: string, a: Row, signal?: AbortSignal): Promise<any> {
    if (name === 'content_page') return this.content(a, signal);
    if (name === 'entry_detail') return this.entry(id(a.p_id), signal);
    if (name === 'topic_detail')
      return (
        (
          await this.rows(
            `SELECT r.* FROM topic r WHERE ${visible('topic')} AND id=?`,
            [id(a.p_id)],
            signal,
          )
        )[0] || null
      );
    if (name === 'entry_context') return this.context(a, signal);
    if (name === 'graph_slice') return this.graph(a, signal);
    if (name === 'search_entries') return this.search(a, signal);
    if (name === 'ask_search') return this.askSearch(a, signal);
    if (name === 'timeline_overview') return this.timeline(signal);
    throw new Error('Unsupported public query');
  }
  async entry(value: string, signal?: AbortSignal) {
    for (const t of ['person', 'event']) {
      const r = await this.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id=?`,
        [value],
        signal,
      );
      if (r.length) return { ...r[0], type: t };
    }
    return null;
  }
  async labels(items: Row[], table: string, signal?: AbortSignal) {
    const ids = new Set<string>();
    for (const r of items)
      for (const f of [
        'person_a',
        'person_b',
        'person_id',
        'event_id',
        'cause_event_id',
        'effect_event_id',
        'source_id',
        'subject_id',
      ])
        if (r[f]) ids.add(r[f]);
    const labels: Row = {};
    if (!ids.size) return labels;
    for (const t of tables.filter((t) => t !== 'fact_claim' && t !== 'topic')) {
      const rs = await this.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id IN (${[...ids].map(() => '?').join(',')})`,
        [...ids],
        signal,
      );
      for (const r of rs)
        if (r.name || r.title) labels[r.id] = r.name || r.title;
      if (t === 'person_relationship')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.person_a] || '人物'} —${r.relation_type}→ ${labels[r.person_b] || '人物'}`;
      if (t === 'person_event')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.person_id] || '人物'} —${r.role}→ ${labels[r.event_id] || '事件'}`;
      if (t === 'event_causality')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.cause_event_id] || '事件'} → ${labels[r.effect_event_id] || '事件'}`;
    }
    return labels;
  }
  async content(a: Row, signal?: AbortSignal) {
    const t = a.p_table,
      size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    if (![...tables, 'nodes'].includes(t) || a.p_admin)
      throw new Error('Invalid public table');
    const q = String(a.p_query || '').trim();
    if (q.length > 200) throw new Error('Invalid query');
    const from = year(a.p_from),
      to = year(a.p_to);
    if (from !== null && to !== null && from > to)
      throw new Error('Invalid years');
    if (a.p_ids != null && (!Array.isArray(a.p_ids) || a.p_ids.length > 200))
      throw new Error('Invalid ids');
    if (t === 'source' && a.p_ids == null)
      throw new Error('Source list requires explicit ids');
    if (t === 'nodes') {
      const params: any[] = [],
        conditions = ["r.status='published'"];
      if (a.p_ids != null) {
        const ids = a.p_ids.map(id);
        conditions.push(
          ids.length ? `r.id IN (${ids.map(() => '?').join(',')})` : 'FALSE',
        );
        params.push(...ids);
      }
      let scope: string[] | null = null;
      if (a.p_topic != null) {
        if (typeof a.p_topic !== 'string' || a.p_topic.length > 200)
          throw new Error('Invalid topic');
        const topic = (
          await this.rows(
            "SELECT sections FROM topic WHERE slug=? AND status='published'",
            [a.p_topic],
            signal,
          )
        )[0];
        const sections = topic?.sections || [];
        scope =
          a.p_section == null
            ? [
                ...new Set<string>(
                  sections.flatMap((s: Row) => s.node_ids || []),
                ),
              ]
            : sections[integer(a.p_section, 0, 0, 100000)]?.node_ids || [];
        conditions.push(
          scope!.length
            ? `r.id IN (${scope!.map(() => '?').join(',')})`
            : 'FALSE',
        );
        params.push(...scope!);
      }
      if (q) {
        conditions.push(
          "LOWER(CONCAT_WS(' ',r.label,r.description,CAST(r.aliases AS CHAR),CAST(r.tags AS CHAR))) LIKE ? ESCAPE '!'",
        );
        params.push(pattern(q));
      }
      let order = 'r.created_at DESC,r.id';
      if (scope?.length && a.p_section != null) {
        order = `FIELD(r.id,${scope.map(() => '?').join(',')}),r.id`;
        params.push(...scope);
      }
      const matches = await this.rows(
        `SELECT r.id,r.kind FROM (SELECT id,status,created_at,'person' kind,name label,description,aliases,tags FROM person UNION ALL SELECT id,status,created_at,'event' kind,title label,description,NULL aliases,tags FROM event) r WHERE ${conditions.join(' AND ')} ORDER BY ${order} LIMIT ${size + 1} OFFSET ${size * page}`,
        params,
        signal,
      );
      const items: Row[] = [];
      for (const match of matches.slice(0, size)) {
        const r = (
          await this.rows(
            `SELECT * FROM \`${match.kind}\` WHERE id=? AND status='published'`,
            [match.id],
            signal,
          )
        )[0];
        if (r) items.push({ ...trim(r, match.kind), label: r.name || r.title });
      }
      return { items, has_more: matches.length > size, labels: {} };
    }
    const cond = [visible(t)],
      params: any[] = [];
    const add = (s: string, ...v: any[]) => {
      cond.push(s);
      params.push(...v);
    };
    if (a.p_ids != null) {
      const ids = a.p_ids.map(id);
      add(
        ids.length ? `r.id IN (${ids.map(() => '?').join(',')})` : 'FALSE',
        ...ids,
      );
    }
    let scope: string[] | null = null;
    if (a.p_topic != null) {
      if (typeof a.p_topic !== 'string' || a.p_topic.length > 200)
        throw new Error('Invalid topic');
      const topic = (
        await this.rows(
          "SELECT sections FROM topic WHERE slug=? AND status='published'",
          [a.p_topic],
          signal,
        )
      )[0];
      const sections = topic?.sections || [];
      scope =
        a.p_section == null
          ? [...new Set<string>(sections.flatMap((s: Row) => s.node_ids || []))]
          : sections[integer(a.p_section, 0, 0, 100000)]?.node_ids || [];
      add(
        scope!.length
          ? `r.id IN (${scope!.map(() => '?').join(',')})`
          : 'FALSE',
        ...scope!,
      );
    }
    if (t === 'topic' && a.p_node)
      add(
        "EXISTS(SELECT 1 FROM JSON_TABLE(r.sections,'$[*].node_ids[*]' COLUMNS(node CHAR(36) PATH '$')) jt WHERE jt.node=?)",
        id(a.p_node),
      );
    if (t === 'event') {
      if (a.p_person)
        add(
          "EXISTS(SELECT 1 FROM person_event pe JOIN person p ON p.id=pe.person_id AND p.status='published' WHERE pe.event_id=r.id AND pe.person_id=? AND pe.status='published')",
          id(a.p_person),
        );
      if (from !== null)
        add(
          '(r.start_year IS NULL OR COALESCE(r.end_year,r.start_year)>=?)',
          from,
        );
      if (to !== null) add('(r.start_year IS NULL OR r.start_year<=?)', to);
    }
    if (t === 'fact_claim')
      for (const [arg, column] of [
        ['p_subject', 'subject_table'],
        ['p_subject_id', 'subject_id'],
        ['p_source', 'source_id'],
        ['p_claim', 'id'],
      ])
        if (a[arg] != null)
          add(
            `r.\`${column}\`=?`,
            arg === 'p_subject' ? String(a[arg]) : id(a[arg]),
          );
    if (q) {
      if (fields[t]) add(`${body(t)} LIKE ? ESCAPE '!'`, pattern(q));
      else if (t === 'fact_claim')
        add(
          "LOWER(CONCAT_WS(' ',LEFT(r.claim_text,120),r.citation)) LIKE ? ESCAPE '!'",
          pattern(q),
        );
      else if (t === 'source')
        add("LOWER(CONCAT_WS(' ',r.title)) LIKE ? ESCAPE '!'", pattern(q));
      else {
        const endpoints: Record<string, string[]> = {
          person_relationship: [
            'person',
            'person_a',
            'person',
            'person_b',
            'relation_type',
          ],
          person_event: ['person', 'person_id', 'event', 'event_id', 'role'],
          event_causality: [
            'event',
            'cause_event_id',
            'event',
            'effect_event_id',
            '',
          ],
        };
        const [left, lc, right, rc, role] = endpoints[t];
        const label = `CONCAT_WS(' ',(SELECT ${left === 'person' ? 'name' : 'title'} FROM \`${left}\` WHERE id=r.\`${lc}\`),${role ? 'r.' + role : "''"},(SELECT ${right === 'person' ? 'name' : 'title'} FROM \`${right}\` WHERE id=r.\`${rc}\`),r.description)`;
        add(`LOWER(${label}) LIKE ? ESCAPE '!'`, pattern(q));
      }
    }
    let order =
      t === 'event'
        ? 'r.start_year IS NULL,r.start_year,r.id'
        : 'r.created_at DESC,r.id';
    if (t !== 'event' && scope && a.p_section != null && scope.length) {
      order = `FIELD(r.id,${scope.map(() => '?').join(',')}),r.id`;
      params.push(...scope);
    }
    const items = await this.rows(
      `SELECT r.* FROM \`${t}\` r WHERE ${cond.join(' AND ')} ORDER BY ${order} LIMIT ${size + 1} OFFSET ${page * size}`,
      params,
      signal,
    );
    const labels = await this.labels(items, t, signal);
    if (t === 'fact_claim' && items.length) {
      const sourceIds = [...new Set(items.map((r) => r.source_id))];
      const sources = await this.rows(
        `SELECT * FROM source WHERE id IN (${sourceIds.map(() => '?').join(',')})`,
        sourceIds,
        signal,
      );
      for (const r of items)
        r.source = sources.find((s) => s.id === r.source_id) || null;
    }
    return {
      items: items.slice(0, size).map((r) => ({
        ...trim(r, t),
        label:
          r.name ||
          r.title ||
          (t === 'fact_claim'
            ? r.claim_text.slice(0, 120)
            : t === 'person_relationship'
              ? `${labels[r.person_a] || '人物'} —${r.relation_type}→ ${labels[r.person_b] || '人物'}`
              : t === 'person_event'
                ? `${labels[r.person_id] || '人物'} —${r.role}→ ${labels[r.event_id] || '事件'}`
                : `${labels[r.cause_event_id] || '事件'} → ${labels[r.effect_event_id] || '事件'}`),
      })),
      has_more: items.length > size,
      labels,
    };
  }
  private incidentSql(t: string) {
    const config: Record<string, string[]> = {
      person_relationship: [
        'person_a',
        'person_b',
        'relation_type',
        'r.description',
      ],
      person_event: ['person_id', 'event_id', 'role', 'NULL'],
      event_causality: [
        'cause_event_id',
        'effect_event_id',
        "'causes'",
        'r.description',
      ],
    };
    const [source, target, type, description] = config[t];
    return `SELECT r.id,'${t}' subject_table,r.${source} source,r.${target} target,${type.startsWith("'") ? type : 'r.' + type} type,${description} description FROM \`${t}\` r WHERE ${visible(t)}`;
  }
  async context(a: Row, signal?: AbortSignal) {
    const value = id(a.p_id),
      center = await this.entry(value, signal);
    if (!center) return null;
    const size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    const edges = await this.rows(
      `SELECT * FROM (${['person_relationship', 'person_event', 'event_causality'].map((t) => this.incidentSql(t)).join(' UNION ALL ')}) edges WHERE source=? OR target=? ORDER BY subject_table,id LIMIT ${size + 1} OFFSET ${page * size}`,
      [value, value],
      signal,
    );
    const pageEdges = edges.slice(0, size),
      ids = [
        ...new Set<string>(pageEdges.flatMap((e) => [e.source, e.target])),
      ];
    const nodes = await this.nodes(ids, signal, false);
    return { center, nodes, edges: pageEdges, has_more: edges.length > size };
  }
  private async nodes(ids: string[], signal?: AbortSignal, compact = true) {
    if (!ids.length) return [];
    const nodes: Row[] = [];
    for (const t of ['person', 'event'])
      for (const r of await this.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id IN (${ids.map(() => '?').join(',')})`,
        ids,
        signal,
      ))
        nodes.push(
          compact
            ? this.graphNode(r, t)
            : t === 'person'
              ? { ...trim(r), references: r.references, type: t }
              : { ...r, type: t },
        );
    return nodes.sort((x, y) => x.id.localeCompare(y.id));
  }
  private graphNode(r: Row, t: string) {
    return t === 'person'
      ? {
          id: r.id,
          type: t,
          name: r.name,
          era: r.era,
          description: r.description?.slice(0, 600) ?? null,
        }
      : {
          id: r.id,
          type: t,
          title: r.title,
          start_year: r.start_year,
          end_year: r.end_year,
          description: r.description?.slice(0, 600) ?? null,
        };
  }
  async graph(a: Row, signal?: AbortSignal) {
    const value = id(a.p_id),
      entry = await this.entry(value, signal);
    if (!entry) return null;
    const depth = integer(a.p_depth, 1, 1, 2),
      mode = a.p_mode || 'people',
      from = year(a.p_from),
      to = year(a.p_to);
    if (
      !['people', 'events'].includes(mode) ||
      (from !== null && to !== null && from > to)
    )
      throw new Error('Invalid graph');
    const visited = new Set([value]),
      seen = new Set<string>(),
      edges: Row[] = [];
    let frontier = [value],
      truncated = false;
    for (let level = 0; level < depth && frontier.length; level++) {
      const t = mode === 'people' ? 'person_relationship' : 'person_event',
        args: any[] = [...frontier, ...frontier];
      let sql = `SELECT * FROM (${this.incidentSql(t)}) edges WHERE (source IN (${frontier.map(() => '?').join(',')}) OR target IN (${frontier.map(() => '?').join(',')}))`;
      if (mode === 'events' && (from !== null || to !== null)) {
        sql += ' AND EXISTS(SELECT 1 FROM event e WHERE e.id=edges.target';
        if (from !== null) {
          sql +=
            ' AND (e.start_year IS NULL OR COALESCE(e.end_year,e.start_year)>=?)';
          args.push(from);
        }
        if (to !== null) {
          sql += ' AND (e.start_year IS NULL OR e.start_year<=?)';
          args.push(to);
        }
        sql += ')';
      }
      if (seen.size) {
        sql += ` AND id NOT IN (${[...seen].map(() => '?').join(',')})`;
        args.push(...seen);
      }
      const candidates = await this.rows(
          sql + ' ORDER BY subject_table,id LIMIT 301',
          args,
          signal,
        ),
        next: string[] = [];
      if (candidates.length > 300) truncated = true;
      for (const e of candidates) {
        const fresh = [...new Set<string>([e.source, e.target])].filter(
          (v) => !visited.has(v),
        );
        if (edges.length >= 300 || visited.size + fresh.length > 120) {
          truncated = true;
          continue;
        }
        fresh.forEach((v) => {
          visited.add(v);
          next.push(v);
        });
        seen.add(e.id);
        edges.push(e);
      }
      frontier = next;
    }
    return {
      center: this.graphNode(entry, entry.type),
      nodes: await this.nodes([...visited], signal),
      edges,
      truncated,
      node_limit: 120,
      edge_limit: 300,
    };
  }
  async search(a: Row, signal?: AbortSignal) {
    const q = String(a.p_query || '')
        .trim()
        .toLowerCase(),
      kind = a.p_kind || 'all',
      size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    if (
      q.length > 200 ||
      !['all', 'person', 'event', 'topic', 'nodes'].includes(kind)
    )
      throw new Error('Invalid search');
    const parts: string[] = [],
      params: any[] = [];
    for (const t of ['person', 'event', 'topic']) {
      if (kind !== t && kind !== 'all' && !(kind === 'nodes' && t !== 'topic'))
        continue;
      const title = t === 'person' ? 'name' : 'title';
      const alias =
        t === 'person'
          ? "WHEN EXISTS(SELECT 1 FROM JSON_TABLE(r.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=?) THEN 1 "
          : '';
      parts.push(
        `SELECT r.id,'${t}' kind,r.${title} title,CASE WHEN LOWER(r.${title})=? THEN 0 ${alias}WHEN LOWER(r.${title}) LIKE ? ESCAPE '!' THEN 2 ELSE 3 END ranking FROM \`${t}\` r WHERE ${visible(t)} AND (?='' OR ${body(t)} LIKE ? ESCAPE '!')`,
      );
      params.push(q, ...(t === 'person' ? [q] : []), pattern(q), q, pattern(q));
    }
    const matches = await this.rows(
      `SELECT * FROM (${parts.join(' UNION ALL ')}) matches ORDER BY ranking,title COLLATE utf8mb4_0900_bin,kind,id LIMIT ${size + 1} OFFSET ${size * page}`,
      params,
      signal,
    );
    const items: Row[] = [];
    for (const m of matches.slice(0, size)) {
      const r = (
        await this.rows(
          `SELECT * FROM \`${m.kind}\` WHERE id=?`,
          [m.id],
          signal,
        )
      )[0];
      items.push(
        m.kind === 'person'
          ? {
              id: r.id,
              type: 'person',
              name: r.name,
              era: r.era,
              description: r.description?.slice(0, 300) ?? null,
              image_url: r.image_url,
            }
          : m.kind === 'event'
            ? {
                id: r.id,
                type: 'event',
                title: r.title,
                start_year: r.start_year,
                end_year: r.end_year,
                description: r.description?.slice(0, 300) ?? null,
                image_url: r.image_url,
              }
            : {
                id: r.id,
                type: 'topic',
                title: r.title,
                slug: r.slug,
                description: r.description?.slice(0, 300) ?? null,
              },
      );
    }
    return { items, has_more: matches.length > size };
  }
  async askSearch(a: Row, signal?: AbortSignal) {
    const keywords = a.p_keywords,
      kind = a.p_kind || 'all',
      from = year(a.p_from),
      to = year(a.p_to),
      offset = integer(a.p_offset, 0, 0, 10000);
    if (
      !Array.isArray(keywords) ||
      keywords.length < 1 ||
      keywords.length > 6 ||
      keywords.some(
        (k) => typeof k !== 'string' || !k.trim() || k.trim().length > 40,
      ) ||
      !['all', 'person', 'event', 'topic'].includes(kind) ||
      (from !== null && to !== null && from > to)
    )
      throw new Error('Invalid ask search');
    const terms = keywords.map((k: string) => ({
      term: k.trim().toLowerCase(),
      pattern: pattern(k.trim()),
    }));
    const entries = ['person', 'event', 'topic']
      .filter((t) => kind === 'all' || kind === t)
      .map(
        (t) =>
          `SELECT r.id,'${t}' kind,r.${t === 'person' ? 'name' : 'title'} label,${t === 'person' ? 'r.aliases' : 'NULL'} aliases,${t === 'person' ? 'r.birth_year' : t === 'event' ? 'r.start_year' : 'NULL'} start_year,${t === 'person' ? 'r.death_year' : t === 'event' ? 'COALESCE(r.end_year,r.start_year)' : 'NULL'} end_year,r.description,${body(t, 'r', t === 'person')} body FROM \`${t}\` r WHERE ${visible(t)}`,
      );
    const parameters: any[] = [JSON.stringify(terms)];
    let date = 'TRUE';
    if (from !== null || to !== null)
      date += ' AND (e.start_year IS NOT NULL OR e.end_year IS NOT NULL)';
    if (from !== null) {
      date += ' AND COALESCE(e.end_year,e.start_year)>=?';
      parameters.push(from);
    }
    if (to !== null) {
      date += ' AND COALESCE(e.start_year,e.end_year)<=?';
      parameters.push(to);
    }
    const sql = `WITH terms AS(SELECT term COLLATE utf8mb4_0900_bin term,pattern COLLATE utf8mb4_0900_bin pattern FROM JSON_TABLE(?,'$[*]' COLUMNS(term VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$.term',pattern VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$.pattern')) t), entries AS(${entries.join(' UNION ALL ')}), claim_hits AS(SELECT DISTINCT c.subject_id id,c.subject_table kind,t.term FROM terms t JOIN fact_claim c ON LOWER(CONCAT_WS(' ',c.claim_text,c.note)) LIKE t.pattern ESCAPE '!' WHERE c.status='published' AND c.subject_table IN ('person','event')), scored AS(SELECT e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,LEFT(e.description,1600) description,SUM(CASE WHEN LOWER(e.label)=t.term OR EXISTS(SELECT 1 FROM JSON_TABLE(e.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=t.term) THEN 10 WHEN LOWER(e.label) LIKE t.pattern ESCAPE '!' OR EXISTS(SELECT 1 FROM JSON_TABLE(e.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=t.term) THEN 5 ELSE 1 END) score FROM entries e CROSS JOIN terms t WHERE ${date} AND (e.body LIKE t.pattern ESCAPE '!' OR EXISTS(SELECT 1 FROM claim_hits h WHERE h.id=e.id AND h.kind=e.kind AND h.term=t.term)) GROUP BY e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,e.description) SELECT * FROM scored ORDER BY score DESC,id LIMIT 13 OFFSET ${offset}`;
    const rs = await this.rows(sql, parameters, signal);
    return {
      items: rs.slice(0, 12).map((r) => ({
        id: r.id,
        kind: r.kind,
        label: r.label,
        aliases: r.aliases,
        startYear: r.start_year,
        endYear: r.end_year,
        description: r.description,
        score: Number(r.score),
      })),
      nextOffset: rs.length > 12 ? offset + 12 : null,
      scope:
        '仅搜索已发布条目及其已录入引文；未搜索整部史书。年代筛选排除年代未知条目。',
    };
  }
  async timeline(signal?: AbortSignal) {
    const years = await this.rows(
      "SELECT start_year year,COUNT(*) count FROM event WHERE status='published' AND start_year IS NOT NULL GROUP BY start_year ORDER BY start_year",
      [],
      signal,
    );
    const highlights = await this.rows(
      "SELECT id,title,start_year FROM (SELECT id,title,start_year,ROW_NUMBER() OVER(PARTITION BY start_year ORDER BY COALESCE(impact_level,0) DESC,REGEXP_LIKE(title,'称帝|建立|灭亡|禅位|即位|政变|建国') DESC,id) ranking FROM event WHERE status='published' AND start_year IS NOT NULL) h WHERE ranking<=3 ORDER BY start_year,ranking",
      [],
      signal,
    );
    const stats = (
      await this.rows(
        "SELECT COUNT(*) total,COALESCE(SUM(start_year IS NULL),0) undated,MIN(start_year) `from`,MAX(GREATEST(start_year,COALESCE(end_year,start_year))) `to` FROM event WHERE status='published'",
        [],
        signal,
      )
    )[0];
    return {
      ...stats,
      years: years.map((y) => ({
        ...y,
        highlights: highlights
          .filter((h) => h.start_year === y.year)
          .map(({ id, title }) => ({ id, title })),
      })),
    };
  }
}

/** Bounded read adapter for the few remaining fluent public queries. No write methods. */
class MysqlQuery {
  private selection = '*';
  private conditions: string[] = [];
  private params: any[] = [];
  private orderings: string[] = [];
  private offset = 0;
  private size = 50;
  private cardinality = 'many';
  private counted = false;
  private signal?: AbortSignal;
  constructor(
    private db: MysqlService,
    private table: string,
  ) {
    if (!tables.includes(table)) throw new Error('Invalid table');
  }
  select(selection = '*', options?: { count?: string }) {
    if (
      selection !== '*' &&
      selection !== '*, source:source_id(*)' &&
      !/^[a-z_]+(,[a-z_]+)*$/.test(selection)
    )
      throw new Error('Invalid selection');
    this.selection = selection;
    this.counted = options?.count === 'exact';
    return this;
  }
  private column(c: string) {
    if (!/^[a-z_]+$/.test(c)) throw new Error('Invalid column');
    return `r.\`${c}\``;
  }
  eq(c: string, v: any) {
    this.conditions.push(this.column(c) + '=?');
    this.params.push(v);
    return this;
  }
  lte(c: string, v: any) {
    this.conditions.push(this.column(c) + '<=?');
    this.params.push(v);
    return this;
  }
  or(expression: string) {
    const m = expression.match(
      /^end_year\.gte\.(-?\d+),and\(end_year\.is\.null,start_year\.eq\.(-?\d+)\)$/,
    );
    if (!m || m[1] !== m[2]) throw new Error('Unsupported filter');
    this.conditions.push(
      '(r.end_year>=? OR (r.end_year IS NULL AND r.start_year=?))',
    );
    this.params.push(Number(m[1]), Number(m[1]));
    return this;
  }
  order(c: string, options?: { ascending?: boolean }) {
    this.orderings.push(
      this.column(c) + (options?.ascending === false ? ' DESC' : ' ASC'),
    );
    return this;
  }
  range(start: number, end: number) {
    this.offset = integer(start, 0, 0, 5000000);
    this.size = integer(end - start + 1, 20, 1, 51);
    return this;
  }
  single() {
    this.cardinality = 'single';
    return this;
  }
  maybeSingle() {
    this.cardinality = 'maybe';
    return this;
  }
  abortSignal(s: AbortSignal) {
    this.signal = s;
    return this;
  }
  then<TResult1 = MysqlResult, TResult2 = never>(
    resolve?: ((value: MysqlResult) => TResult1 | PromiseLike<TResult1>) | null,
    reject?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null,
  ): Promise<TResult1 | TResult2> {
    return this.run().then(resolve, reject);
  }
  private async run(): Promise<MysqlResult> {
    try {
      const projection = this.selection.includes('source:')
        ? 'r.*'
        : this.selection === '*'
          ? 'r.*'
          : this.selection
              .split(',')
              .map((c) => this.column(c))
              .join(',');
      const condition = [visible(this.table), ...this.conditions].join(' AND '),
        order = this.orderings.length ? this.orderings.join(',') : 'r.id';
      const rows = await this.db.rows(
        `SELECT ${projection} FROM \`${this.table}\` r WHERE ${condition} ORDER BY ${order} LIMIT ${this.size} OFFSET ${this.offset}`,
        this.params,
        this.signal,
      );
      if (this.selection.includes('source:'))
        for (const r of rows)
          r.source =
            (
              await this.db.rows(
                'SELECT * FROM source WHERE id=?',
                [r.source_id],
                this.signal,
              )
            )[0] || null;
      const count = this.counted
        ? Number(
            (
              await this.db.rows(
                `SELECT COUNT(*) count FROM \`${this.table}\` r WHERE ${condition}`,
                this.params,
                this.signal,
              )
            )[0].count,
          )
        : null;
      if (
        this.cardinality !== 'many' &&
        (rows.length > 1 || (this.cardinality === 'single' && !rows.length))
      )
        throw new Error('Unexpected cardinality');
      return {
        data: this.cardinality === 'many' ? rows : rows[0] || null,
        error: null,
        count,
      };
    } catch {
      return { data: null, error: new Error('公开资料查询失败'), count: null };
    }
  }
}
