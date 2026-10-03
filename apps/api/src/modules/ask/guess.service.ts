import {
  BadRequestException,
  HttpException,
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { randomBytes, randomInt } from 'node:crypto';
import { z } from 'zod';
import { SupabaseService } from '../supabase/supabase.service';
import { GuessAgentService } from './guess-agent.service';

const filtersSchema = z
  .object({
    difficulty: z.number().int().min(1).max(5),
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
type Filters = z.infer<typeof filtersSchema>;
type Person = {
  id: string;
  name: string;
  aliases?: string[];
  courtesy_name?: string;
  era?: string;
  birth_year?: number;
  death_year?: number;
  description?: string;
  biography?: string;
  tags?: string[];
};
type Claim = {
  id: string;
  claim_text: string;
  note?: string;
  citation?: string;
  source?: { title: string };
};
type Turn = { text: string; answer: string; kind: 'question' | 'guess' };
type Game = {
  person: Person;
  context?: unknown;
  claims: Claim[];
  filters: Filters;
  turns: Turn[];
  hints: string[];
  expires: number;
  busy: boolean;
  outcome?: 'won' | 'revealed' | 'limit';
};
const labels = {
  yes: '是',
  no: '不是',
  unknown: '不清楚',
  mixed: '是，也不是',
  refuse: '请只问一个是非问题；猜姓名请使用“猜姓名”。',
};
export function normalizeGuess(text: string) {
  return text
    .normalize('NFKC')
    .replace(/[\s·・，。！？?!]/g, '')
    .toLocaleLowerCase();
}
// Reference anchors constrain the model's fame classification; absent names remain agent-assessed.
const anchors: Record<string, number> = Object.fromEntries(
  [
    [
      '李白 杜甫 李世民 曹操 刘邦 项羽 秦始皇 嬴政 武则天 孔子 孟子 诸葛亮 关羽 刘备 孙权 岳飞 朱元璋 李清照 苏轼 白居易',
      1,
    ],
    ['朱温 朱全忠 朱晃 李存勖 柴荣 石勒 苻坚 李克用 刘裕 王安石 赵匡胤', 2],
    ['王僧辩 刘琨 敬翔 李振 葛从周 王彦章', 3],
    ['孙泰 刘交', 4],
  ].flatMap(([names, tier]) =>
    String(names)
      .split(' ')
      .map((name) => [name, Number(tier)]),
  ),
);

@Injectable()
export class GuessService {
  private readonly games = new Map<string, Game>();
  private readonly quotas = new Map<string, { count: number; reset: number }>();
  private active = 0;
  constructor(
    private readonly db: SupabaseService,
    private readonly agent: GuessAgentService,
  ) {}
  status() {
    return { available: this.agent.available(), maxTurns: 30, maxHints: 3 };
  }
  private admit(ip: string) {
    if (!this.agent.available())
      throw new ServiceUnavailableException('猜人物服务尚未开放。');
    const now = Date.now();
    for (const [token, game] of this.games)
      if (!game.busy && game.expires < now) this.games.delete(token);
    for (const [key, quota] of this.quotas)
      if (quota.reset < now) this.quotas.delete(key);
    if (this.active >= 2)
      throw new HttpException('当前游戏请求较多，请稍后再试。', 429);
    const quota = this.quotas.get(ip) || { count: 0, reset: now + 3600000 };
    if (quota.count >= 80 || (!this.quotas.has(ip) && this.quotas.size >= 2048))
      throw new HttpException('已达到每小时游戏请求限额，请稍后再试。', 429);
    quota.count++;
    this.quotas.set(ip, quota);
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
  async start(body: unknown, ip: string, signal: AbortSignal) {
    const parsed = filtersSchema.safeParse(body);
    if (!parsed.success)
      throw new BadRequestException('请检查难度、年代和限定条件。');
    this.admit(ip);
    if (this.games.size >= 500)
      throw new HttpException('游戏会话较多，请稍后再试。', 429);
    this.active++;
    try {
      const filters = parsed.data;
      const people: Person[] = [];
      // Bound reads; fail explicitly if the corpus exceeds capacity rather than silently omitting older entries.
      for (let page = 0; page < 20; page++) {
        const result = await this.page('person', page, signal);
        people.push(...result.items);
        if (!result.has_more) break;
        if (page === 19)
          throw new ServiceUnavailableException(
            '人物库超过当前游戏候选容量，需扩展候选索引。',
          );
      }
      const candidates = people.filter((p) => {
        const tier = anchors[p.name];
        if (tier && tier !== filters.difficulty) return false;
        if (filters.from !== undefined || filters.to !== undefined) {
          const start = p.birth_year ?? p.death_year,
            end = p.death_year ?? p.birth_year;
          // Let the agent inspect descriptions for dated activity when lifespan is unknown.
          if (
            start !== undefined &&
            end !== undefined &&
            ((filters.from !== undefined && end < filters.from) ||
              (filters.to !== undefined && start > filters.to))
          )
            return false;
        }
        return true;
      });
      for (let i = candidates.length - 1; i > 0; i--) {
        const j = randomInt(i + 1);
        [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
      }
      const sample = [
        ...candidates.filter((p) => anchors[p.name] === filters.difficulty),
        ...candidates.filter((p) => !anchors[p.name]),
      ].slice(0, 120);
      if (!sample.length)
        throw new BadRequestException(
          '当前已发布人物中没有符合该难度和年代的候选。',
        );
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
      if (!eligible.length)
        throw new BadRequestException(
          '本次候选抽样没有可确认符合全部限定的人物，请放宽条件或重试。',
        );
      // Select uniformly among confirmed candidates; sparse evidence remains playable on very hard.
      while (eligible.length) {
        let person = eligible.splice(randomInt(eligible.length), 1)[0];
        const claims: Claim[] = [];
        const direct = await this.page('fact_claim', 0, signal, {
          p_subject: 'person',
          p_subject_id: person.id,
        });
        claims.push(
          ...direct.items.filter(
            (c) => c.source?.title && c.note?.startsWith('原文：'),
          ),
        );
        if (!claims.length) continue;
        const detail = await this.db
          .getClient()
          .rpc('entry_detail', { p_id: person.id })
          .abortSignal(signal);
        if (detail.error || !detail.data || detail.data.type !== 'person')
          continue;
        person = detail.data as Person;
        const related = await this.db
          .getClient()
          .rpc('entry_context', { p_id: person.id, p_page: 0, p_limit: 20 })
          .abortSignal(signal);
        if (related.error)
          throw new ServiceUnavailableException('人物关系暂时无法读取。');
        const context = related.data;
        for (const edge of (context?.edges || [])
          .filter((e: { subject_table: string }) =>
            ['person_relationship', 'person_event'].includes(e.subject_table),
          )
          .slice(0, 6)) {
          const result = await this.page('fact_claim', 0, signal, {
            p_subject: edge.subject_table,
            p_subject_id: edge.id,
          });
          claims.push(
            ...result.items
              .filter((c) => c.source?.title && c.note?.startsWith('原文：'))
              .slice(0, 5),
          );
        }
        const token = randomBytes(32).toString('hex');
        const game: Game = {
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
            person: {
              id: game.person.id,
              name: game.person.name,
              description: game.person.description,
            },
            evidence: game.claims.map((c) => ({
              id: c.id,
              claim: c.claim_text,
              note: c.note,
              title: c.source?.title,
              location: c.citation,
            })),
          }
        : {}),
    };
  }
  async act(body: unknown, ip: string, signal: AbortSignal) {
    const parsed = actionSchema.safeParse(body);
    if (!parsed.success) throw new BadRequestException('游戏请求格式不正确。');
    const { token, action, text } = parsed.data;
    const game = this.games.get(token);
    if (!game || game.expires < Date.now())
      throw new HttpException('游戏已过期，请重新开局。', 410);
    if (action === 'state') return this.view(game);
    this.admit(ip);
    if (game.busy) throw new HttpException('请等待本次操作完成。', 409);
    if (game.outcome) return this.view(game);
    game.busy = true;
    this.active++;
    try {
      if (action === 'reveal') game.outcome = 'revealed';
      else if (action === 'guess') {
        const names = [
          game.person.name,
          ...(game.person.aliases || []),
          game.person.courtesy_name,
        ].filter((n): n is string => !!n);
        const correct = names.some(
          (n) => normalizeGuess(n) === normalizeGuess(text!),
        );
        game.turns.push({
          text: text!,
          answer: correct ? '猜对了' : '不是',
          kind: 'guess',
        });
        if (correct) game.outcome = 'won';
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
              verdict: z.enum(['yes', 'no', 'unknown', 'mixed', 'refuse']),
              claims: z.array(z.string()).max(10),
            })
            .strict()
            .safeParse(raw);
          if (!result.success)
            throw new ServiceUnavailableException(
              '裁判未返回有效答案，请重试。',
            );
          const verdict =
            ['yes', 'no', 'mixed'].includes(result.data.verdict) &&
            !supported(result.data.claims)
              ? 'unknown'
              : result.data.verdict;
          // A refusal does not consume a turn; identity guesses only win through deterministic matching.
          if (verdict === 'refuse')
            return { ...this.view(game), notice: labels.refuse };
          game.turns.push({
            text: text!,
            answer: labels[verdict],
            kind: 'question',
          });
        } else {
          const result = z
            .object({
              text: z.string().max(80),
              claims: z.array(z.string()).max(10),
            })
            .strict()
            .safeParse(raw);
          const names = [
            game.person.name,
            ...(game.person.aliases || []),
            game.person.courtesy_name,
          ].filter((n): n is string => !!n);
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
