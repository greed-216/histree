import {
  Injectable,
  Optional,
  ServiceUnavailableException,
} from '@nestjs/common';
import { randomBytes } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { GuessAgentService } from './guess-agent.service';
import {
  GuessClueResearch,
  assessResearch,
  validateCheckedClues,
  UnsuitableGamePerson,
} from './guess-clue-research';
import { MysqlService } from '../mysql/mysql.service';
import { GuessClueStore } from './guess-clue-store';
import {
  loadClueProfile,
  validateClueSelection,
  validateCachedClues,
  type Clue,
  type ClueProfile,
} from './guess-clues';

function waitFor<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  signal.throwIfAborted();
  return new Promise((resolve, reject) => {
    const abort = () => reject(signal.reason);
    signal.addEventListener('abort', abort, { once: true });
    void promise
      .then(resolve, reject)
      .finally(() => signal.removeEventListener('abort', abort));
  });
}
@Injectable()
export class GuessClueSetsService {
  private readonly listeners = new Map<
    string,
    Set<(message: string) => void>
  >();
  private readonly stages = new Map<string, string>();
  private readonly pending = new Map<string, Promise<Clue[]>>();
  constructor(
    private readonly store: GuessClueStore,
    private readonly agent: GuessAgentService,
    private readonly db: MysqlService,
    @Optional() private readonly research?: GuessClueResearch,
  ) {}
  async ready(
    profile: ClueProfile,
    signal: AbortSignal,
  ): Promise<Clue[] | null> {
    const row = await this.store.find(profile, signal);
    return row?.status === 'ready'
      ? validateCachedClues(row.clues, profile)
      : null;
  }
  async ensure(
    profile: ClueProfile,
    signal: AbortSignal,
    progress?: (message: string) => void,
  ): Promise<Clue[]> {
    const hit = await this.ready(profile, signal);
    if (hit) return hit;
    const key = profile.person.id + ':' + profile.revision;
    if (!this.pending.has(key) && this.pending.size >= 32)
      throw new ServiceUnavailableException('线索准备较多，请稍后再试。');
    if (progress) {
      const listeners = this.listeners.get(key) || new Set();
      listeners.add(progress);
      this.listeners.set(key, listeners);
      progress(this.stages.get(key) || '正在为新人物准备六条线索…');
    }
    let work = this.pending.get(key);
    if (!work) {
      // The shared preparation survives one caller disconnecting, so its completed result can be reused.
      work = this.prepare(profile, AbortSignal.timeout(120000), (message) => {
        this.stages.set(key, message);
        this.listeners.get(key)?.forEach((listener) => listener(message));
      });
      this.pending.set(key, work);
      const owned = work;
      void work
        .finally(() => {
          if (this.pending.get(key) === owned) {
            this.pending.delete(key);
            this.stages.delete(key);
          }
        })
        .catch(() => {});
    }
    try {
      return await waitFor(work, signal);
    } finally {
      if (progress) this.listeners.get(key)?.delete(progress);
      if (!this.listeners.get(key)?.size) this.listeners.delete(key);
    }
  }
  private async prepare(
    profile: ClueProfile,
    signal: AbortSignal,
    progress: (message: string) => void,
  ): Promise<Clue[]> {
    const token = randomBytes(32).toString('hex');
    const row = await this.store.claim(profile, token, signal);
    if (row?.status === 'ready') return validateCachedClues(row.clues, profile);
    if (row?.lease_token !== token) {
      if (row?.status === 'failed')
        throw new ServiceUnavailableException(
          '这位人物的线索暂未准备好，请稍后重试。',
        );
      while (!signal.aborted) {
        await delay(750, undefined, { signal });
        const current = await this.store.find(profile, signal);
        if (current?.status === 'ready')
          return validateCachedClues(current.clues, profile);
        if (current?.status === 'failed')
          throw new ServiceUnavailableException('线索准备未完成，请稍后重试。');
      }
      signal.throwIfAborted();
    }
    let audit: Record<string, unknown> = {
      kind: 'general_knowledge',
      method: 'ai',
      prompt_version: 2,
      stage: 'generation',
    };
    try {
      let clues: Clue[];
      try {
        progress('正在整理人物经历，准备六条线索…');
        const raw = await this.agent.run(
          {
            task: 'clues',
            person: { name: profile.person.name, era: profile.person.era },
            count: 6,
            context: profile.person.description || '',
            aliases: profile.person.aliases || [],
            courtesy_name: profile.person.courtesy_name,
          },
          signal,
        );
        clues = validateClueSelection(raw, profile);
        if (this.research) {
          progress('正在复核人物经历与六条线索的辨识度…');
          const checked = await this.agent.run(
            {
              task: 'check_clues',
              person: profile.person,
              proposed: { clues },
            },
            signal,
          );
          audit = { ...audit, initialReview: checked };
          clues = validateCheckedClues(checked, profile);
        }
      } catch (error) {
        signal.throwIfAborted();
        if (!this.research) throw error;
        audit = {
          ...audit,
          stage: 'research',
          initialFailure:
            error instanceof Error
              ? error.message.slice(0, 200)
              : 'generation_failed',
        };
        progress('初次线索尚未通过，正在补查人物出处与史书原文…');
        const research = await this.research.collect(profile, signal);
        audit = { ...audit, research, checkedAt: new Date().toISOString() };
        if (!research.sources.length)
          throw new ServiceUnavailableException(
            '本次未取得可核对的补查资料，人物已保留待查。',
          );
        progress('正在核对补查资料，检查六条线索能否成立…');
        const raw = await this.agent.run(
          {
            task: 'research_clues',
            person: profile.person,
            count: 6,
            research,
          },
          signal,
        );
        audit = { ...audit, draftAssessment: raw };
        try {
          assessResearch(raw, profile, research);
        } catch (error) {
          audit = {
            ...audit,
            draftValidationFailure:
              error instanceof Error ? error.message : 'invalid_draft',
          };
        }
        progress('正在复核六条线索的独立性和人物辨识度…');
        const reviewed = await this.agent.run(
          {
            task: 'review_clues',
            person: profile.person,
            count: 6,
            research,
            proposed: raw,
          },
          signal,
        );
        const assessed = assessResearch(reviewed, profile, research);
        audit = { ...audit, assessment: assessed.assessment, reviewed: true };
        const current = await loadClueProfile(
          this.db,
          profile.person.id,
          signal,
        );
        if (current.revision !== profile.revision)
          throw new ServiceUnavailableException(
            '人物资料已更新，请重新准备线索。',
          );
        if (assessed.decision === 'unsuitable') {
          const changed = await this.store.disable(
            profile,
            token,
            audit,
            signal,
          );
          if (!changed.affectedRows)
            throw new ServiceUnavailableException(
              '人物资格已发生变化，请重新开局。',
            );
          throw new UnsuitableGamePerson();
        }
        clues = assessed.clues;
      }
      const current = await loadClueProfile(this.db, profile.person.id, signal);
      if (current.revision !== profile.revision)
        throw new ServiceUnavailableException(
          '人物资料已更新，请重新准备线索。',
        );
      if (
        (await this.store.complete(profile, token, clues, signal, audit))
          .affectedRows !== 1
      )
        throw new ServiceUnavailableException('线索保存未完成，请重试。');
      return clues;
    } catch (error) {
      await this.store
        .fail(profile, token, AbortSignal.timeout(5000), {
          ...audit,
          failure:
            error instanceof Error
              ? error.message.slice(0, 200)
              : 'preparation_failed',
        })
        .catch(() => {});
      throw error;
    }
  }
}
