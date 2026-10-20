import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { randomBytes } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { GuessAgentService } from './guess-agent.service';
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
  private readonly pending = new Map<string, Promise<Clue[]>>();
  constructor(
    private readonly store: GuessClueStore,
    private readonly agent: GuessAgentService,
    private readonly db: MysqlService,
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
  async ensure(profile: ClueProfile, signal: AbortSignal): Promise<Clue[]> {
    const hit = await this.ready(profile, signal);
    if (hit) return hit;
    const key = profile.person.id + ':' + profile.revision;
    let work = this.pending.get(key);
    if (!work) {
      if (this.pending.size >= 32)
        throw new ServiceUnavailableException('线索准备较多，请稍后再试。');
      // The shared preparation survives one caller disconnecting, so its completed result can be reused.
      work = this.prepare(profile, AbortSignal.timeout(120000));
      this.pending.set(key, work);
      const owned = work;
      void work
        .finally(() => {
          if (this.pending.get(key) === owned) this.pending.delete(key);
        })
        .catch(() => {});
    }
    return waitFor(work, signal);
  }
  private async prepare(
    profile: ClueProfile,
    signal: AbortSignal,
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
    try {
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
      const clues = validateClueSelection(raw, profile);
      const current = await loadClueProfile(this.db, profile.person.id, signal);
      if (current.revision !== profile.revision)
        throw new ServiceUnavailableException(
          '人物资料已更新，请重新准备线索。',
        );
      if (
        (await this.store.complete(profile, token, clues, signal))
          .affectedRows !== 1
      )
        throw new ServiceUnavailableException('线索保存未完成，请重试。');
      return clues;
    } catch (error) {
      await this.store
        .fail(profile, token, AbortSignal.timeout(5000))
        .catch(() => {});
      throw error;
    }
  }
}
