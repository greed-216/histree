import {
  BadRequestException,
  HttpException,
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { createHash, randomBytes, randomInt } from 'node:crypto';
import { z } from 'zod';
import { MysqlService } from '../mysql/mysql.service';
import { guessNames, normalizeGuess, directGuess } from './guess-names';
import { GuessAgentService } from './guess-agent.service';
import { GuessClueStore } from './guess-clue-store';
import { GuessClueSetsService } from './guess-clue-sets.service';
import type { GuessRating } from './guess-bank';
import { loadClueProfile, type Clue, type ClueProfile } from './guess-clues';

const filtersSchema = z
  .object({
    difficulty: z.enum(['easy', 'hard']),
    from: z.number().int().min(-3000).max(2100).optional(),
    to: z.number().int().min(-3000).max(2100).optional(),
  })
  .strict()
  .refine((f) => f.from === undefined || f.to === undefined || f.from <= f.to);
const actionSchema = z
  .object({
    token: z.string().regex(/^[a-f0-9]{64}$/),
    action: z.enum(['state', 'guess', 'hint', 'reveal']),
    text: z.string().trim().min(1).max(100).optional(),
    expectedUnlocked: z.number().int().min(1).max(6).optional(),
  })
  .strict()
  .refine((a) => a.action !== 'guess' || !!a.text)
  .refine((a) => a.action !== 'hint' || a.expectedUnlocked !== undefined);
const ratingSchema = z
  .object({
    token: z.string().regex(/^[a-f0-9]{64}$/),
    rating: z.enum(['easy', 'right', 'hard']),
  })
  .strict();
type Filters = z.infer<typeof filtersSchema>;
type Game = {
  owner: string;
  profile: ClueProfile;
  filters: Filters;
  clues: Clue[];
  unlocked: number;
  guesses: Array<{ text: string; correct: boolean }>;
  outcome: 'won' | 'revealed' | null;
  expires: number;
  busy: boolean;
  rating?: GuessRating;
};

@Injectable()
export class GuessClueGameService {
  private readonly games = new Map<string, Game>();
  private readonly recent = new Map<string, string[]>();
  constructor(
    private readonly db: MysqlService,
    private readonly store: GuessClueStore,
    private readonly sets: GuessClueSetsService,
    private readonly agent: GuessAgentService,
  ) {}
  async status(signal: AbortSignal) {
    try {
      return {
        available: this.agent.available(),
        preparedPeople: (await this.store.readyPeople(signal)).size,
      };
    } catch {
      return { available: false, preparedPeople: 0 };
    }
  }
  private view(game: Game) {
    const visible = game.outcome
      ? game.clues
      : game.clues.slice(0, game.unlocked);
    return {
      filters: game.filters,
      clues: visible.map((c) => c.text),
      unlocked: game.unlocked,
      total: game.clues.length,
      guesses: game.guesses,
      outcome: game.outcome,
      ...(game.outcome
        ? {
            ratingEligible: game.guesses.length > 0 || game.unlocked > 1,
            rating: game.rating || null,
            person: {
              id: game.profile.person.canonical_person_id,
              name: game.profile.person.name,
              description: game.profile.person.description,
            },
            evidence: game.clues.map((c) => ({
              clue: c.text,
              explanation: c.explanation,
              kind: 'general_knowledge' as const,
              title: '历史通识线索',
            })),
          }
        : {}),
    };
  }
  async start(
    body: unknown,
    actor: string,
    signal: AbortSignal,
    progress: (message: string) => void = () => {},
  ) {
    const parsed = filtersSchema.safeParse(body);
    if (!parsed.success) throw new BadRequestException('请检查难度和年代。');
    if (!this.agent.available())
      throw new ServiceUnavailableException('线索游戏尚未开放。');
    const now = Date.now();
    for (const [token, g] of this.games)
      if (!g.busy && g.expires < now) this.games.delete(token);
    if (this.games.size >= 500)
      throw new HttpException('游戏会话较多，请稍后再试。', 429);
    const filters = parsed.data;
    progress('正在抽选符合难度和年代的人物…');
    let candidates = await this.store.candidates(filters, signal, true);
    const ready = await this.store.readyPeople(signal);
    candidates = candidates.filter((p) => ready.has(p.id));
    if (!candidates.length)
      throw new BadRequestException(
        '已准备的题库中暂无符合该难度和年代的人物，请换个条件。',
      );
    const history = this.recent.get(actor) || [];
    const fresh = candidates.filter((p) => !history.includes(p.id));
    if (fresh.length) candidates = fresh;
    for (let i = candidates.length - 1; i > 0; i--) {
      const j = randomInt(i + 1);
      [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
    }
    // Gameplay only reads prepared sets. Content preparation belongs to the batch job.
    for (const person of candidates.slice(0, 20)) {
      signal.throwIfAborted();
      let profile: ClueProfile;
      try {
        profile = await loadClueProfile(this.db, person.id, signal);
      } catch (error) {
        if (error instanceof BadRequestException) continue;
        throw error;
      }
      if (
        profile.person.game_difficulty &&
        profile.person.game_difficulty !== filters.difficulty
      )
        continue;
      progress('正在读取已准备的六条线索…');
      const clues = await this.sets.ready(profile, signal);
      if (!clues) continue;
      const token = randomBytes(32).toString('hex');
      const game: Game = {
        owner: actor,
        profile,
        filters,
        clues,
        unlocked: 1,
        guesses: [],
        outcome: null,
        expires: Date.now() + 3600000,
        busy: false,
      };
      this.games.set(token, game);
      if (this.recent.size >= 2048 && !this.recent.has(actor))
        this.recent.delete(this.recent.keys().next().value!);
      this.recent.set(actor, [...history.slice(-4), person.id]);
      return { token, ...this.view(game) };
    }
    throw new ServiceUnavailableException(
      '人物资料更新后，线索需要重新准备，请稍后再试。',
    );
  }
  async feedback(body: unknown, actor: string, signal: AbortSignal) {
    const parsed = ratingSchema.safeParse(body);
    if (!parsed.success) throw new BadRequestException('请选择本局难度感受。');
    const { token, rating } = parsed.data,
      game = this.games.get(token);
    if (game && game.owner !== actor)
      throw new HttpException('无权访问此游戏。', 403);
    if (!game || game.expires < Date.now())
      throw new HttpException('游戏已过期，请重新开局。', 410);
    if (!game.outcome || (!game.guesses.length && game.unlocked === 1))
      throw new BadRequestException(
        '猜过名字或看过下一条线索，并揭晓后才能评价难度。',
      );
    if (game.busy) throw new HttpException('请等待本次操作完成。', 409);
    if (game.rating) return this.view(game);
    game.busy = true;
    try {
      const current = await loadClueProfile(
        this.db,
        game.profile.person.id,
        signal,
      );
      if (current.revision !== game.profile.revision)
        throw new HttpException('人物资料已更新，请重新开局。', 410);
      const hash = (v: string) => createHash('sha256').update(v).digest('hex');
      const result = await this.store.rate(
        {
          person_id: game.profile.person.id,
          revision: game.profile.person.difficulty_revision || 1,
          knowledge_revision: game.profile.person.knowledge_revision || 1,
          clue_revision: hash(
            JSON.stringify([game.profile.revision, game.clues]),
          ),
          actor_hash: hash(actor),
          game_hash: hash(token),
          rating,
          guesses: game.guesses.length,
          unlocked: game.unlocked,
          outcome: game.outcome,
        },
        signal,
      );
      game.rating = result.rating;
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
    if (!parsed.success)
      throw new BadRequestException('线索游戏请求格式不正确。');
    const a = parsed.data,
      game = this.games.get(a.token);
    if (game && game.owner !== actor)
      throw new HttpException('无权访问此游戏。', 403);
    if (!game || game.expires < Date.now())
      throw new HttpException('游戏已过期，请重新开局。', 410);
    if (game.busy) throw new HttpException('请等待本次操作完成。', 409);
    game.busy = true;
    try {
      let current: ClueProfile;
      try {
        current = await loadClueProfile(
          this.db,
          game.profile.person.id,
          signal,
        );
      } catch (error) {
        if (error instanceof BadRequestException) {
          this.games.delete(a.token);
          throw new HttpException('人物资料已更新，请重新开局。', 410);
        }
        throw error;
      }

      if (current.revision !== game.profile.revision) {
        this.games.delete(a.token);
        throw new HttpException('人物资料已更新，请重新开局。', 410);
      }
      if (a.action === 'state' || game.outcome) return this.view(game);
      if (a.action === 'reveal') game.outcome = 'revealed';
      else if (a.action === 'hint') {
        if ((a.expectedUnlocked ?? 0) > game.unlocked)
          throw new BadRequestException('线索进度不匹配，请刷新恢复。');
        // Duplicate/retried unlocks return the same progress, never two extra clues.
        if (
          a.expectedUnlocked === game.unlocked &&
          game.unlocked < game.clues.length
        )
          game.unlocked++;
      } else {
        if (game.guesses.length >= 80)
          throw new HttpException('本局提交较多，请稍后继续或揭晓答案。', 429);
        const correct = guessNames(game.profile.person).some(
          (n) => normalizeGuess(n) === directGuess(a.text!),
        );
        game.guesses.push({ text: a.text!, correct });
        if (correct) game.outcome = 'won';
      }
      return this.view(game);
    } finally {
      game.busy = false;
    }
  }
}
