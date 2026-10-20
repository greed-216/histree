import { Injectable, Optional } from '@nestjs/common';
import { createHash } from 'node:crypto';
import { MysqlService } from '../mysql/mysql.service';
import { GuessBankService, type GuessRating } from './guess-bank';
import type { GuessPerson } from './guess-catalogue';
import { GuessCharacterCatalogue } from './guess-character-catalogue';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { loadClueProfile } from './guess-clues';

type MaterialClaim = {
  id: string;
  kind: 'general_knowledge';
  claim_text: string;
  note: string;
  source: { title: string };
};
@Injectable()
export class GuessGameLibrary {
  constructor(
    private readonly db: MysqlService,
    private readonly bank: GuessBankService,
    private readonly sets: GuessClueSetsService,
    @Optional() characters?: GuessCharacterCatalogue,
  ) {
    this.characters = characters || new GuessCharacterCatalogue(db, bank);
  }
  private readonly characters: GuessCharacterCatalogue;
  async catalogue(signal: AbortSignal): Promise<GuessPerson[]> {
    const legacy = await this.characters.sync(signal);
    const activity = new Map(legacy.map((p) => [p.id, p.activity || []]));
    const people: GuessPerson[] = [];
    let cursor = '';
    while (true) {
      const page = await this.db.rows(
        `SELECT c.id,c.canonical_person_id,c.knowledge_revision,
    COALESCE(p.name,c.name) name,JSON_MERGE_PRESERVE(COALESCE(p.aliases,JSON_ARRAY()),c.aliases) aliases,
    COALESCE(p.courtesy_name,c.courtesy_name) courtesy_name,COALESCE(NULLIF(c.era,''),p.era) era,
    COALESCE(p.birth_year,c.birth_year) birth_year,COALESCE(p.death_year,c.death_year) death_year,
    COALESCE(NULLIF(c.description,''),p.description,'') description,p.tags,c.period_from,c.period_to,
    COALESCE(b.difficulty,c.question_difficulty) game_difficulty,COALESCE(b.revision,c.question_revision) game_revision,
    IF(b.person_id IS NULL,'character','bank') game_feedback
    FROM guess_character c LEFT JOIN person p ON p.id=c.canonical_person_id LEFT JOIN guess_bank b ON b.person_id=c.canonical_person_id
    WHERE c.enabled=1 AND (c.canonical_person_id IS NULL OR p.status='published') AND c.id>? ORDER BY c.id LIMIT 1000`,
        [cursor],
        signal,
      );
      for (const row of page) {
        const ranges = [...(activity.get(String(row.id)) || [])];
        people.push({ ...row, activity: ranges } as GuessPerson);
      }
      if (page.length < 1000) return people;
      const next = String(page[page.length - 1].id);
      if (next <= cursor) throw Error('Invalid shared game catalogue cursor');
      cursor = next;
    }
  }
  async material(person: GuessPerson, signal: AbortSignal) {
    const profile = await loadClueProfile(this.db, person.id, signal);
    // A new game-only hard character has no legacy source fallback. Prepare its shared cards once.
    const clues =
      (await this.sets.ready(profile, signal)) ||
      (person.canonical_person_id === null && person.game_difficulty === 'hard'
        ? await this.sets.ensure(profile, signal)
        : null);
    if (!clues) return null;
    const revision = createHash('sha256')
      .update(JSON.stringify([profile.revision, clues]))
      .digest('hex');
    const claims: Array<
      | MaterialClaim
      | {
          id: string;
          kind?: string;
          claim_text: string;
          note?: string;
          source?: { title: string };
          citation?: string;
        }
    > = clues.map((c, i) => ({
      id: `knowledge:${revision}:${i + 1}`,
      kind: 'general_knowledge',
      claim_text: c.explanation,
      note: '游戏通识资料卡，非本站已录入原文引文。',
      source: { title: '历史通识资料卡' },
    }));
    if (profile.person.canonical_person_id) {
      const original = await this.db
        .getClient()
        .rpc('content_page', {
          p_table: 'fact_claim',
          p_subject: 'person',
          p_subject_id: profile.person.canonical_person_id,
          p_page: 0,
          p_limit: 100,
        })
        .abortSignal(signal);
      if (original.error) throw new Error('Historical material unavailable');
      claims.push(
        ...(original.data?.items || []).filter(
          (c: { source?: { title?: string }; note?: string }) =>
            c.source?.title && c.note?.startsWith('原文：'),
        ),
      );
    }
    return {
      person: {
        ...profile.person,
        game_difficulty: person.game_difficulty,
        game_revision: person.game_revision,
        game_feedback: person.game_feedback,
      },
      claims,
    };
  }
  rate(
    input: {
      person: GuessPerson;
      claims: unknown[];
      revision: number;
      token: string;
      actor: string;
      rating: GuessRating;
      turns: number;
      hints: number;
      outcome: 'won' | 'revealed' | 'limit';
    },
    signal: AbortSignal,
  ) {
    const hash = (s: string) => createHash('sha256').update(s).digest('hex');
    return this.db.rateGuessCharacterQuestion(
      {
        person_id: input.person.id,
        revision: input.revision,
        knowledge_revision: input.person.knowledge_revision || 1,
        clue_revision: hash(JSON.stringify(input.claims)),
        actor_hash: hash(input.actor),
        game_hash: hash(input.token),
        rating: input.rating,
        guesses: input.turns,
        unlocked: input.hints + 1,
        outcome: input.outcome,
      },
      signal,
    );
  }
}

// Broad era labels are game categories, never verified activity/lifespan intervals.
export function matchesGameEra(
  person: GuessPerson,
  filters: { from?: number; to?: number },
) {
  const presets = new Set([
    '-3000:-221',
    '-221:220',
    '220:589',
    '589:907',
    '907:979',
    '960:1368',
    '1368:1912',
  ]);
  if (
    !presets.has(`${filters.from}:${filters.to}`) ||
    person.birth_year != null ||
    person.death_year != null ||
    (person.activity || []).length
  )
    return false;
  return (
    person.period_from != null &&
    person.period_to != null &&
    person.period_from <= filters.to! &&
    person.period_to >= filters.from!
  );
}
