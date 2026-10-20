import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  makeClueProfile,
  validateCachedClues,
  CLUE_VERSION,
  type CluePerson,
  type Clue,
} from './guess-clues';
// Content integrity only. This does not establish historical accuracy.
const directory = resolve(__dirname, '../../../../../games/guess');
const pack = JSON.parse(
  readFileSync(resolve(directory, 'starter-clues.json'), 'utf8'),
) as {
  characters: CluePerson[];
  entries: Array<{
    person_id: string;
    profile_revision: string;
    generator_version: number;
    clues: Clue[];
  }>;
};
const characters = JSON.parse(
  readFileSync(resolve(directory, 'characters.json'), 'utf8'),
) as CluePerson[];
describe('Starter clue content integrity', () => {
  it('has at least sixty reusable characters, a complete set for each and both difficulty levels', () => {
    expect(pack.characters.length).toBeGreaterThanOrEqual(60);
    expect(new Set(pack.characters.map((p) => p.id)).size).toBe(
      pack.characters.length,
    );
    expect(new Set(pack.entries.map((p) => p.person_id)).size).toBe(
      pack.characters.length,
    );
    expect(new Set(characters.map((p) => p.id))).toEqual(
      new Set(pack.characters.map((p) => p.id)),
    );
    expect(
      new Set(
        pack.characters.map(
          (p) => (p as CluePerson & { difficulty: string }).difficulty,
        ),
      ),
    ).toEqual(new Set(['easy', 'hard']));
  });
  it('uses current profile fingerprints, keeps future identities out of clues and preserves explicit canonical mappings', () => {
    for (const person of pack.characters) {
      const profile = makeClueProfile(person),
        entry = pack.entries.find((e) => e.person_id === person.id)!;
      expect(entry.generator_version).toBe(CLUE_VERSION);
      expect(entry.profile_revision).toBe(profile.revision);
      expect(validateCachedClues(entry.clues, profile)).toHaveLength(6);
      if (person.canonical_person_id)
        expect(person.id).toBe(person.canonical_person_id);
      if (person.period_from != null && person.period_to != null)
        expect(person.period_from).toBeLessThanOrEqual(person.period_to);
    }
  });
});

it('covers every easy identity from the original game-bank preparation manifest', () => {
  const manifest = JSON.parse(
    readFileSync(resolve(directory, 'preparation-manifest.json'), 'utf8'),
  ) as { legacy_easy: number; legacy_easy_ids: string[] };
  expect(manifest.legacy_easy_ids).toHaveLength(manifest.legacy_easy);
  for (const id of manifest.legacy_easy_ids) {
    expect(characters.find((p) => p.id === id)?.canonical_person_id).toBe(id);
    expect(characters.find((p) => p.id === id)).toMatchObject({
      difficulty: 'easy',
    });
    expect(pack.entries.find((e) => e.person_id === id)?.clues).toHaveLength(6);
  }
});
