import { normalizeGuess, guessNames, directGuess } from './guess-names';
import { GuessGameLibrary, matchesGameEra } from './guess-game-library';
import {
  BadRequestException,
  HttpException,
  Injectable,
  Optional,
  OnModuleInit,
  OnModuleDestroy,
  ServiceUnavailableException,
} from '@nestjs/common';
import { createHash, randomBytes, randomInt } from 'node:crypto';
import { z } from 'zod';
import { MysqlService } from '../mysql/mysql.service';
import { GuessAgentService } from './guess-agent.service';
import { judgeEraQuestion } from './guess-era';
import {
  GuessBankService,
  guessCatalogueRevision,
  legacyGuessTiers as anchors,
  type GuessRating,
} from './guess-bank';
import {
  loadGuessCatalogue,
  matchesGuessYears,
  type GuessPerson as Person,
} from './guess-catalogue';

const filtersSchema = z
  .object({
    // Numeric tiers remain accepted for older clients; new games use two modes.
    difficulty: z.union([
      z.enum(['easy', 'hard']),
      z.number().int().min(1).max(5),
    ]),
    from: z.number().int().min(-3000).max(2100).optional(),
    to: z.number().int().min(-3000).max(2100).optional(),
    identity: z.string().trim().max(80).default(''),
    gender: z.enum(['any', 'male', 'female']).default('any'),
    custom: z.string().trim().max(200).default(''),
  })
  .strict()
  .refine(
    (x) => x.from === undefined || x.to === undefined || x.from <= x.to,
    '年代起点不得晚于终点',
  );
const actionSchema = z
  .object({
    token: z.string().regex(/^[a-f0-9]{64}$/),
    action: z.enum(['state', 'question', 'guess', 'hint', 'reveal']),
    text: z.string().trim().min(1).max(400).optional(),
  })
  .strict()
  .refine((x) => !['question', 'guess'].includes(x.action) || !!x.text);
const ratingSchema = z
  .object({
    token: z.string().regex(/^[a-f0-9]{64}$/),
    rating: z.enum(['easy', 'right', 'hard']),
  })
  .strict();
type Filters = z.infer<typeof filtersSchema>;
type Catalogue = { people: Person[]; revision: string };
type Claim = {
  id: string;
  kind?: string;
  claim_text: string;
  note?: string;
  citation?: string;
  source?: { title: string };
};
type Turn = { text: string; answer: string; kind: 'question' | 'guess' };
type Game = {
  owner: string;
  person: Person;
  context?: unknown;
  claims: Claim[];
  filters: Filters;
  turns: Turn[];
  hints: string[];
  expires: number;
  busy: boolean;
  outcome?: 'won' | 'revealed' | 'limit';
  bankRevision?: number;
  rating?: GuessRating;
};
const labels = {
  yes: '是',
  no: '不是',
  unknown: '不清楚',
  mixed: '是，也不是',
  refuse: '请问一个是非问题，或提出一个人物名字；不能直接索要答案或候选名单。',
};
export { normalizeGuess, guessNames, directGuess } from './guess-names';
@Injectable()
export class GuessService implements OnModuleInit, OnModuleDestroy {
  private readonly games = new Map<string, Game>();
  private readonly quotas = new Map<string, { count: number; reset: number }>();
  private active = 0;
  private catalogueCache?: {
    expires: number;
    promise: Promise<Catalogue>;
  };
  private readonly candidatePools = new Map<string, Promise<Person[]>>();
  private refreshTimer?: ReturnType<typeof setInterval>;
  private refreshing = false;
  constructor(
    private readonly db: MysqlService,
    private readonly agent: GuessAgentService,
    private readonly bank: GuessBankService,
    @Optional() private readonly library?: GuessGameLibrary,
  ) {}
  onModuleInit() {
    if (!this.agent.available()) return;
    void this.catalogue().catch(() => {});
    this.refreshTimer = setInterval(() => void this.refreshCatalogue(), 240000);
    this.refreshTimer.unref();
  }
  onModuleDestroy() {
    clearInterval(this.refreshTimer);
  }
  private async refreshCatalogue() {
    if (this.refreshing || !this.agent.available()) return;
    this.refreshing = true;
    const previous = this.catalogueCache;
    try {
      const people = await this.loadCatalogue(AbortSignal.timeout(60000));
      // Keep serving the current pool while loading; swap only a complete successful snapshot.
      if (this.catalogueCache === previous) {
        this.catalogueCache = {
          expires: Date.now() + 300000,
          promise: Promise.resolve({
            people,
            revision: guessCatalogueRevision(people),
          }),
        };
      }
    } catch {
      /* Retain the last snapshot within its existing TTL; foreground retry after expiry. */
    } finally {
      this.refreshing = false;
    }
  }
  private waitShared<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
    signal.throwIfAborted();
    return new Promise((resolve, reject) => {
      const abort = () => reject(signal.reason);
      signal.addEventListener('abort', abort, { once: true });
      promise
        .then(resolve, reject)
        .finally(() => signal.removeEventListener('abort', abort));
    });
  }
  private catalogue() {
    if (this.catalogueCache && this.catalogueCache.expires > Date.now())
      return this.catalogueCache.promise;
    const promise = this.loadCatalogue(AbortSignal.timeout(60000)).then(
      (people) => ({ people, revision: guessCatalogueRevision(people) }),
    );
    this.catalogueCache = { expires: Date.now() + 300000, promise };
    void promise.catch(() => {
      if (this.catalogueCache?.promise === promise)
        this.catalogueCache = undefined;
    });
    return promise;
  }
  private async loadCatalogue(signal: AbortSignal) {
    try {
      if (this.library) return await this.library.catalogue(signal);
      return await this.bank.prepare(
        await loadGuessCatalogue(this.db, signal),
        signal,
      );
    } catch {
      throw new ServiceUnavailableException('游戏题库暂未准备好，请稍后重试。');
    }
  }

  private async pool(
    filters: Filters,
    catalogue: Catalogue,
    signal: AbortSignal,
  ) {
    // Default setup is entirely deterministic: no model, worker startup or AI cache miss.
    if (
      typeof filters.difficulty === 'string' &&
      !filters.identity &&
      filters.gender === 'any' &&
      !filters.custom
    ) {
      const eligible = catalogue.people.filter(
        (p) =>
          p.game_difficulty === filters.difficulty &&
          (matchesGuessYears(p, filters) ||
            (!!this.library && matchesGameEra(p, filters))),
      );
      if (!eligible.length)
        throw new BadRequestException(
          '已准备的题库中暂无符合该难度和年代的人物，请调整条件。',
        );
      return eligible;
    }
    // Unchanged snapshots share advanced screening even across periodic refreshes.
    const key = JSON.stringify([catalogue.revision, filters]);
    let pending = this.candidatePools.get(key);
    if (!pending) {
      if (this.candidatePools.size >= 128)
        this.candidatePools.delete(this.candidatePools.keys().next().value!);
      pending = this.selectCandidates(
        filters,
        catalogue.people,
        AbortSignal.timeout(120000),
      );
      this.candidatePools.set(key, pending);
      const owned = pending;
      void pending.catch(() => {
        if (this.candidatePools.get(key) === owned)
          this.candidatePools.delete(key);
      });
    }
    // Per-game removals must never mutate the shared pool.
    return [...(await this.waitShared(pending, signal))];
  }
  status() {
    return { available: this.agent.available(), maxTurns: 30, maxHints: 3 };
  }
  private admit(actor: string) {
    if (!this.agent.available())
      throw new ServiceUnavailableException('猜人物服务尚未开放。');
    const now = Date.now();
    for (const [token, game] of this.games)
      if (!game.busy && game.expires < now) this.games.delete(token);
    for (const [key, quota] of this.quotas)
      if (quota.reset < now) this.quotas.delete(key);
    if (this.active >= 2)
      throw new HttpException('当前游戏请求较多，请稍后再试。', 429);
    const quota = this.quotas.get(actor) || { count: 0, reset: now + 3600000 };
    if (
      quota.count >= 80 ||
      (!this.quotas.has(actor) && this.quotas.size >= 2048)
    )
      throw new HttpException('已达到每小时游戏请求限额，请稍后再试。', 429);
    quota.count++;
    this.quotas.set(actor, quota);
  }
  private async page(
    table: string,
    page: number,
    signal: AbortSignal,
    extra = {},
  ) {
    const { data, error } = await this.db
      .getClient()
      .rpc('content_page', {
        p_table: table,
        p_page: page,
        p_limit: 50,
        p_admin: false,
        ...extra,
      })
      .abortSignal(signal);
    if (error || !data)
      throw new ServiceUnavailableException('已发布资料暂时无法读取。');
    return data as { items: Array<Person & Claim>; has_more: boolean };
  }
  private async selectCandidates(
    filters: Filters,
    people: Person[],
    signal: AbortSignal,
  ) {
    const acceptsTier = (tier: number) =>
      filters.difficulty === 'easy'
        ? tier <= 2
        : filters.difficulty === 'hard'
          ? tier >= 3
          : tier === filters.difficulty;
    const candidates = people.filter(
      (p) =>
        (typeof filters.difficulty === 'string'
          ? p.game_difficulty === filters.difficulty
          : !anchors[p.name] || acceptsTier(anchors[p.name])) &&
        (matchesGuessYears(p, filters) ||
          (!!this.library && matchesGameEra(p, filters))),
    );
    for (let i = candidates.length - 1; i > 0; i--) {
      const j = randomInt(i + 1);
      [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
    }
    const ordered = [
      ...candidates.filter(
        (p) => anchors[p.name] && acceptsTier(anchors[p.name]),
      ),
      ...candidates.filter((p) => !anchors[p.name]),
    ];
    if (!ordered.length)
      throw new BadRequestException(
        '当前已发布人物中没有符合该难度和年代的候选。',
      );
    // Try another disjoint sample when restrictive conditions leave the first
    // empty. Bound model work to three batches under the shared selection timeout.
    for (
      let offset = 0;
      offset < Math.min(ordered.length, 360);
      offset += 120
    ) {
      const sample = ordered.slice(offset, offset + 120);
      const selection = z
        .object({ ids: z.array(z.string()).max(120) })
        .strict()
        .safeParse(
          await this.agent.run(
            {
              task: 'select',
              filters,
              candidates: sample.map((p) => ({
                ...p,
                description: p.description?.slice(0, 600),
                fixedDifficulty: anchors[p.name],
              })),
            },
            signal,
          ),
        );
      if (!selection.success)
        throw new ServiceUnavailableException('人物筛选未完成，请重试。');
      const eligible = sample.filter((p) => selection.data.ids.includes(p.id));
      if (eligible.length) return eligible;
    }
    throw new BadRequestException(
      '本次候选抽样没有可确认符合全部限定的人物，请放宽条件或重试。',
    );
  }
  async start(body: unknown, actor: string, signal: AbortSignal) {
    const parsed = filtersSchema.safeParse(body);
    if (!parsed.success)
      throw new BadRequestException('请检查难度、年代和限定条件。');
    this.admit(actor);
    if (this.games.size >= 500)
      throw new HttpException('游戏会话较多，请稍后再试。', 429);
    this.active++;
    try {
      const filters = parsed.data;
      const catalogue = await this.waitShared(this.catalogue(), signal);
      const eligible = await this.pool(filters, catalogue, signal);
      // Select uniformly among confirmed candidates, then revalidate publication and evidence.
      while (eligible.length) {
        let person = eligible.splice(randomInt(eligible.length), 1)[0];
        const bankRevision = person.game_revision;
        const prepared = await this.library?.material(person, signal);
        if (prepared) {
          const token = randomBytes(32).toString('hex');
          const game: Game = {
            owner: actor,
            person: prepared.person,
            claims: prepared.claims,
            filters,
            turns: [],
            hints: [],
            expires: Date.now() + 3600000,
            busy: false,
            bankRevision,
          };
          this.games.set(token, game);
          return { token, ...this.view(game) };
        }
        if (person.canonical_person_id === null) continue;

        const claims: Claim[] = [];
        const [direct, detail, related] = await Promise.all([
          this.page('fact_claim', 0, signal, {
            p_subject: 'person',
            p_subject_id: person.id,
          }),
          this.db
            .getClient()
            .rpc('entry_detail', { p_id: person.id })
            .abortSignal(signal),
          this.db
            .getClient()
            .rpc('entry_context', { p_id: person.id, p_page: 0, p_limit: 20 })
            .abortSignal(signal),
        ]);
        claims.push(
          ...direct.items.filter(
            (c) => c.source?.title && c.note?.startsWith('原文：'),
          ),
        );
        if (
          !claims.length ||
          detail.error ||
          !detail.data ||
          detail.data.type !== 'person'
        )
          continue;
        person = detail.data as Person;
        if (related.error)
          throw new ServiceUnavailableException('人物关系暂时无法读取。');
        const context = related.data;
        const edges = (context?.edges || [])
          .filter((e: { subject_table: string }) =>
            ['person_relationship', 'person_event'].includes(e.subject_table),
          )
          .slice(0, 6);
        const relatedClaims = await Promise.all(
          edges.map((edge: { subject_table: string; id: string }) =>
            this.page('fact_claim', 0, signal, {
              p_subject: edge.subject_table,
              p_subject_id: edge.id,
            }),
          ),
        );
        for (const result of relatedClaims) {
          claims.push(
            ...result.items
              .filter(
                (c: Claim) => c.source?.title && c.note?.startsWith('原文：'),
              )
              .slice(0, 5),
          );
        }
        const token = randomBytes(32).toString('hex');
        const game: Game = {
          owner: actor,
          bankRevision,
          person,
          context,
          claims,
          filters,
          turns: [],
          hints: [],
          expires: Date.now() + 3600000,
          busy: false,
        };
        this.games.set(token, game);
        return { token, ...this.view(game) };
      }
      throw new BadRequestException(
        '本次符合限定的候选尚无可回溯原文，无法开局。请调整条件或重试。',
      );
    } finally {
      this.active--;
    }
  }
  private view(game: Game) {
    return {
      filters: game.filters,
      turns: game.turns,
      hints: game.hints,
      outcome: game.outcome || null,
      remaining: 30 - game.turns.length,
      ...(game.outcome
        ? {
            ratingEligible: game.turns.length > 0 && !!game.bankRevision,
            rating: game.rating || null,
            person: {
              id:
                game.person.canonical_person_id === undefined
                  ? game.person.id
                  : game.person.canonical_person_id,
              name: game.person.name,
              description: game.person.description,
            },
            evidence: game.claims.map((c) => ({
              id: c.id,
              kind: c.kind || 'source',
              claim: c.claim_text,
              note: c.note,
              title: c.source?.title,
              location: c.citation,
            })),
          }
        : {}),
    };
  }
  async feedback(body: unknown, actor: string, signal: AbortSignal) {
    const parsed = ratingSchema.safeParse(body);
    if (!parsed.success) throw new BadRequestException('请选择本局难度感受。');
    const game = this.games.get(parsed.data.token);
    if (game && game.owner !== actor)
      throw new HttpException('无权访问此游戏。', 403);
    if (!game || game.expires < Date.now())
      throw new HttpException('游戏已过期，请重新开局。', 410);
    if (!game.outcome || !game.turns.length || !game.bankRevision)
      throw new BadRequestException('完成至少一次对答并揭晓后，才能评价难度。');
    if (game.busy) throw new HttpException('请等待本次操作完成。', 409);
    if (game.rating) return this.view(game);
    game.busy = true;
    try {
      const result =
        game.person.game_feedback === 'character' && this.library
          ? await this.library.rate(
              {
                person: game.person,
                claims: game.claims,
                revision: game.bankRevision,
                token: parsed.data.token,
                actor,
                rating: parsed.data.rating,
                turns: game.turns.length,
                hints: game.hints.length,
                outcome: game.outcome,
              },
              signal,
            )
          : await this.bank.rate(
              {
                person_id: game.person.id,
                revision: game.bankRevision,
                actor_hash: createHash('sha256').update(actor).digest('hex'),
                game_hash: createHash('sha256')
                  .update(parsed.data.token)
                  .digest('hex'),
                rating: parsed.data.rating,
                turns: game.turns.length,
                hints: game.hints.length,
              },
              signal,
            );
      game.rating = result.rating;
      if (result.moved || result.revision !== game.bankRevision) {
        // A new level is used by future games only. No active game is changed.
        this.catalogueCache = undefined;
      }
      return this.view(game);
    } catch (error) {
      if (error instanceof HttpException) throw error;
      throw new ServiceUnavailableException('难度反馈未能保存，请重试。');
    } finally {
      game.busy = false;
    }
  }

  async act(body: unknown, actor: string, signal: AbortSignal) {
    const parsed = actionSchema.safeParse(body);
    if (!parsed.success) throw new BadRequestException('游戏请求格式不正确。');
    const { token, action, text } = parsed.data;
    const game = this.games.get(token);
    if (game && game.owner !== actor)
      throw new HttpException('无权访问此游戏。', 403);
    if (!game || game.expires < Date.now())
      throw new HttpException('游戏已过期，请重新开局。', 410);
    if (action === 'state') return this.view(game);
    this.admit(actor);
    if (game.busy) throw new HttpException('请等待本次操作完成。', 409);
    if (game.outcome) return this.view(game);
    game.busy = true;
    this.active++;
    try {
      const eraVerdict =
        action === 'question'
          ? judgeEraQuestion(text!, game.person.era)
          : undefined;
      if (action === 'reveal') game.outcome = 'revealed';
      else if (
        action === 'guess' ||
        (action === 'question' &&
          guessNames(game.person).some(
            (name) => normalizeGuess(name) === directGuess(text!),
          ))
      ) {
        const correct = guessNames(game.person).some(
          (name) => normalizeGuess(name) === directGuess(text!),
        );
        game.turns.push({
          text: text!,
          answer: correct ? '猜对了' : '不是',
          kind: 'guess',
        });
        if (correct) game.outcome = 'won';
      } else if (eraVerdict !== undefined) {
        game.turns.push({
          text: text!,
          answer: labels[eraVerdict],
          kind: 'question',
        });
      } else {
        if (action === 'hint' && game.hints.length >= 3)
          throw new BadRequestException('本局的三个提示已用完。');
        const input = {
          task: action,
          person: {
            ...game.person,
            biography: game.person.biography?.slice(0, 6000),
          },
          context: game.context,
          claims: game.claims.map((c) => ({
            ...c,
            claim_text: c.claim_text.slice(0, 800),
            note: c.note?.slice(0, 3000),
          })),
          history: game.turns,
          difficulty: game.filters.difficulty,
          question: text,
          level: game.hints.length + 1,
          previousHints: game.hints,
        };
        const raw = await this.agent.run(input, signal);
        const supported = (ids: string[]) =>
          ids.length > 0 &&
          ids.every((id) => game.claims.some((c) => c.id === id));
        if (action === 'question') {
          const result = z
            .object({
              verdict: z.enum([
                'yes',
                'no',
                'unknown',
                'mixed',
                'refuse',
                'guess',
              ]),
              name: z.string().trim().min(1).max(100).optional(),
              claims: z.array(z.string()).max(10),
            })
            .strict()
            .safeParse(raw);
          if (!result.success)
            throw new ServiceUnavailableException(
              '裁判未返回有效答案，请重试。',
            );
          if (result.data.verdict === 'guess') {
            const name = result.data.name;
            if (!name || directGuess(text!) !== normalizeGuess(name))
              throw new ServiceUnavailableException(
                '未能确认你提出的人物名字，请重试。',
              );
            const correct = guessNames(game.person).some(
              (n) => normalizeGuess(n) === normalizeGuess(name),
            );
            game.turns.push({
              text: text!,
              answer: correct ? '猜对了' : '不是',
              kind: 'guess',
            });
            if (correct) game.outcome = 'won';
          } else {
            const verdict =
              ['yes', 'no', 'mixed'].includes(result.data.verdict) &&
              !supported(result.data.claims)
                ? 'unknown'
                : result.data.verdict;
            if (verdict === 'refuse')
              return { ...this.view(game), notice: labels.refuse };
            game.turns.push({
              text: text!,
              answer: labels[verdict],
              kind: 'question',
            });
          }
        } else {
          const result = z
            .object({
              text: z.string().max(80),
              claims: z.array(z.string()).max(10),
            })
            .strict()
            .safeParse(raw);
          const names = guessNames(game.person);
          if (
            !result.success ||
            !result.data.text ||
            game.hints.includes(result.data.text) ||
            !supported(result.data.claims) ||
            names.some((n) =>
              normalizeGuess(result.data.text).includes(normalizeGuess(n)),
            ) ||
            /https?:|<|\]\(|\\u|[A-Za-z]/.test(result.data.text)
          )
            return {
              ...this.view(game),
              notice: '当前资料不足以提供安全、有据的新提示；未消耗提示次数。',
            };
          game.hints.push(result.data.text);
        }
      }
      if (!game.outcome && game.turns.length >= 30) game.outcome = 'limit';
      return this.view(game);
    } finally {
      game.busy = false;
      this.active--;
    }
  }
}
