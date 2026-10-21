import { Injectable } from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';
import type { ClueFeedback } from './guess-difficulty';
import { CLUE_VERSION, type Clue, type ClueProfile } from './guess-clues';

export type ClueCacheRow = {
  status: 'generating' | 'ready' | 'failed';
  lease_token: string | null;
  clues: unknown;
  provenance?: unknown;
};
@Injectable()
export class GuessClueStore {
  constructor(private readonly db: MysqlService) {}
  async candidates(
    filters: { difficulty: 'easy' | 'hard'; from?: number; to?: number },
    signal: AbortSignal,
    preparedOnly = false,
  ) {
    const result: Array<{ id: string }> = [];
    let cursor = '';
    while (true) {
      const args: Array<string | number> = [filters.difficulty, cursor];
      let years = '';
      if (filters.from !== undefined || filters.to !== undefined) {
        const from = filters.from ?? -3000,
          to = filters.to ?? 2100;
        years = ` AND ((COALESCE(p.birth_year,c.birth_year,p.death_year,c.death_year)<=?
          AND COALESCE(p.death_year,c.death_year,p.birth_year,c.birth_year)>=?)
          OR (c.period_from<=? AND c.period_to>=?)
          OR EXISTS(SELECT 1 FROM person_event pe JOIN event e ON e.id=pe.event_id
            WHERE pe.person_id=c.canonical_person_id AND pe.status='published' AND e.status='published'
            AND COALESCE(e.start_year,e.end_year)<=? AND COALESCE(e.end_year,e.start_year)>=?))`;
        args.push(to, from, to, from, to, from);
      }
      const page = await this.db.rows(
        `SELECT c.id FROM guess_character c
        LEFT JOIN person p ON p.id=c.canonical_person_id
        WHERE c.enabled=1 AND (c.canonical_person_id IS NULL OR p.status='published')
        AND c.difficulty=? AND c.id>? ${years}
        ${preparedOnly ? `AND EXISTS(SELECT 1 FROM guess_clue_set s WHERE s.person_id=c.id AND s.status='ready' AND s.generator_version=${CLUE_VERSION})` : ''}
        ORDER BY c.id LIMIT 1000`,
        args,
        signal,
      );
      result.push(...(page as Array<{ id: string }>));
      if (page.length < 1000) return result;
      const next = String(page[page.length - 1].id);
      if (next <= cursor) throw new Error('Invalid clue catalogue cursor');
      cursor = next;
    }
  }
  rate(input: ClueFeedback, signal: AbortSignal) {
    return this.db.rateGuessClue(input, signal);
  }
  async readyPeople(signal: AbortSignal): Promise<Set<string>> {
    const rows = await this.db.rows(
      `SELECT DISTINCT s.person_id FROM guess_clue_set s
       JOIN guess_character c ON c.id=s.person_id
       LEFT JOIN person p ON p.id=c.canonical_person_id
       WHERE s.status='ready' AND s.generator_version=? AND c.enabled=1
       AND (c.canonical_person_id IS NULL OR p.status='published')`,
      [CLUE_VERSION],
      signal,
    );
    return new Set(rows.map((r) => r.person_id as string));
  }
  async find(
    profile: ClueProfile,
    signal: AbortSignal,
  ): Promise<ClueCacheRow | null> {
    const rows = await this.db.rows(
      `SELECT status,lease_token,clues,provenance FROM guess_clue_set WHERE person_id=? AND profile_revision=? AND generator_version=?`,
      [profile.person.id, profile.revision, CLUE_VERSION],
      signal,
    );
    return (rows[0] as ClueCacheRow) || null;
  }
  async claim(profile: ClueProfile, token: string, signal: AbortSignal) {
    const args = [profile.person.id, profile.revision, CLUE_VERSION];
    await this.db.execute(
      `INSERT IGNORE INTO guess_clue_set(person_id,profile_revision,generator_version,status,lease_token,lease_until)
       VALUES(?,?,?,'generating',?,DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 150 SECOND))`,
      [...args, token],
      signal,
    );
    await this.db.execute(
      `UPDATE guess_clue_set SET status='generating',lease_token=?,lease_until=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 150 SECOND),retry_after=NULL
       WHERE person_id=? AND profile_revision=? AND generator_version=? AND
       ((status='generating' AND lease_until<UTC_TIMESTAMP(6)) OR (status='failed' AND retry_after<=UTC_TIMESTAMP(6)))`,
      [token, ...args],
      signal,
    );
    return this.find(profile, signal);
  }
  async complete(
    profile: ClueProfile,
    token: string,
    clues: Clue[],
    signal: AbortSignal,
    provenance: Record<string, unknown> = {
      kind: 'general_knowledge',
      method: 'ai',
      prompt_version: CLUE_VERSION,
    },
  ) {
    return this.db.execute(
      `UPDATE guess_clue_set SET status='ready',clues=?,provenance=?,lease_token=NULL,lease_until=NULL,retry_after=NULL
       WHERE person_id=? AND profile_revision=? AND generator_version=? AND status='generating' AND lease_token=?`,
      [
        JSON.stringify(clues),
        JSON.stringify(provenance),
        profile.person.id,
        profile.revision,
        CLUE_VERSION,
        token,
      ],
      signal,
    );
  }
  async fail(
    profile: ClueProfile,
    token: string,
    signal: AbortSignal,
    provenance: Record<string, unknown> = {},
  ) {
    await this.db.execute(
      `UPDATE guess_clue_set SET status='failed',provenance=?,lease_token=NULL,lease_until=NULL,retry_after=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 60 SECOND)
       WHERE person_id=? AND profile_revision=? AND generator_version=? AND status='generating' AND lease_token=?`,
      [
        JSON.stringify(provenance),
        profile.person.id,
        profile.revision,
        CLUE_VERSION,
        token,
      ],
      signal,
    );
  }
  async disable(
    profile: ClueProfile,
    token: string,
    provenance: Record<string, unknown>,
    signal: AbortSignal,
  ) {
    return this.db.execute(
      `UPDATE guess_clue_set s JOIN guess_character c ON c.id=s.person_id
      SET c.enabled=0,s.status='failed',s.provenance=?,s.lease_token=NULL,s.lease_until=NULL,s.retry_after=NULL
      WHERE s.person_id=? AND s.profile_revision=? AND s.generator_version=? AND s.status='generating' AND s.lease_token=? AND c.enabled=1 AND c.knowledge_revision=?`,
      [
        JSON.stringify(provenance),
        profile.person.id,
        profile.revision,
        CLUE_VERSION,
        token,
        profile.person.knowledge_revision || 1,
      ],
      signal,
    );
  }
}
