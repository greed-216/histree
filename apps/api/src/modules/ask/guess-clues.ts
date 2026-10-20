import { createHash } from 'node:crypto';
import {
  BadRequestException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { z } from 'zod';
import { MysqlService } from '../mysql/mysql.service';
import { guessNames, normalizeGuess } from './guess-names';
import type { GuessPerson } from './guess-catalogue';

// A game character may exist before its historical record is ingested.
export const CLUE_VERSION = 2;
export type CluePerson = GuessPerson & {
  canonical_person_id: string | null;
  knowledge_revision?: number;
  difficulty_revision?: number;
  period_from?: number | null;
  period_to?: number | null;
};
export type Clue = { text: string; explanation: string };
export type ClueProfile = { person: CluePerson; revision: string };
export function makeClueProfile(person: CluePerson): ClueProfile {
  const revision = createHash('sha256')
    .update(
      JSON.stringify({
        version: CLUE_VERSION,
        id: person.id,
        canonical: person.canonical_person_id,
        name: person.name,
        aliases: [...new Set(person.aliases || [])].sort(),
        courtesy_name: person.courtesy_name || null,
        era: person.era || null,
        description: person.description || '',
        birth_year: person.birth_year ?? null,
        death_year: person.death_year ?? null,
        period_from: person.period_from ?? null,
        period_to: person.period_to ?? null,
        knowledge_revision: person.knowledge_revision || 1,
      }),
    )
    .digest('hex');
  return { person, revision };
}
export async function loadClueProfile(
  db: MysqlService,
  personId: string,
  signal: AbortSignal,
): Promise<ClueProfile> {
  const rows = await db.rows(
    `SELECT c.id,c.canonical_person_id,c.knowledge_revision,c.difficulty_revision,c.difficulty game_difficulty,
    COALESCE(p.name,c.name) name,JSON_MERGE_PRESERVE(COALESCE(p.aliases,JSON_ARRAY()),c.aliases) aliases,
    COALESCE(p.courtesy_name,c.courtesy_name) courtesy_name,COALESCE(NULLIF(c.era,''),p.era) era,
    c.period_from,c.period_to,
    COALESCE(p.birth_year,c.birth_year) birth_year,COALESCE(p.death_year,c.death_year) death_year,
    COALESCE(NULLIF(c.description,''),p.description,'') description
    FROM guess_character c LEFT JOIN person p ON p.id=c.canonical_person_id
    WHERE c.id=? AND c.enabled=1 AND (c.canonical_person_id IS NULL OR p.status='published')`,
    [personId],
    signal,
  );
  if (!rows[0])
    throw new BadRequestException('这位人物已暂停出题，请重新开局。');
  return makeClueProfile(rows[0] as CluePerson);
}
const clueSchema = z
  .object({
    text: z.string().trim().min(6).max(100),
    explanation: z.string().trim().min(8).max(240),
  })
  .strict();
export function validateClueSelection(
  raw: unknown,
  profile: ClueProfile,
): Clue[] {
  if (
    raw &&
    typeof raw === 'object' &&
    'unavailable' in raw &&
    raw.unavailable === true
  )
    throw new ServiceUnavailableException(
      '这位人物暂时没有足够可靠的线索，请换一位。',
    );
  const parsed = z
    .object({ clues: z.array(clueSchema).length(6) })
    .strict()
    .safeParse(raw);
  if (!parsed.success)
    throw new ServiceUnavailableException('线索未能完成校验，请稍后重试。');
  const names = guessNames(profile.person)
    .map(normalizeGuess)
    .filter((n) => n.length >= 2);
  const seen = new Set<string>();
  for (const clue of parsed.data.clues) {
    const text = normalizeGuess(clue.text);
    if (names.some((n) => text.includes(n)))
      throw new ServiceUnavailableException(
        '线索提前透露了人物姓名，请重新准备。',
      );
    if (seen.has(text) || /https?:|[<>]|人物姓名|答案是/.test(clue.text))
      throw new ServiceUnavailableException('线索重复或格式无效，请重新准备。');
    seen.add(text);
  }
  return parsed.data.clues;
}
export function validateCachedClues(
  raw: unknown,
  profile: ClueProfile,
): Clue[] {
  return validateClueSelection({ clues: raw }, profile);
}
