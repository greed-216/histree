import {
  loadGuessCatalogue,
  matchesGuessYears,
  GuessPerson,
} from './guess-catalogue';
import { MysqlService } from '../mysql/mysql.service';

describe('Published guess catalogue', () => {
  it('reads a corpus larger than the old 10,000 limit without losing or duplicating people', async () => {
    const records = Array.from({ length: 15022 }, (_, i) => ({
      id: String(i + 1).padStart(36, '0'),
      name: `人物${i}`,
    }));
    const rows = jest.fn((sql: string, args: string[]) =>
      Promise.resolve(
        sql.includes('FROM person p')
          ? records.filter((p) => p.id > args[0]).slice(0, 1000)
          : [],
      ),
    );
    const result = await loadGuessCatalogue(
      { rows } as unknown as MysqlService,
      new AbortController().signal,
    );
    expect(result.map((p) => p.id)).toEqual(records.map((p) => p.id));
    expect(
      rows.mock.calls.filter(([sql]) => sql.includes('FROM person p')),
    ).toHaveLength(16);
  });
  it('stops a cancelled refresh without returning a partial catalogue', async () => {
    const controller = new AbortController();
    controller.abort(new Error('cancelled'));
    const rows = jest.fn();
    await expect(
      loadGuessCatalogue(
        { rows } as unknown as MysqlService,
        controller.signal,
      ),
    ).rejects.toThrow('cancelled');
    expect(rows).not.toHaveBeenCalled();
  });
  it('uses real activity intervals without turning null dates or gaps into a lifespan', () => {
    const person: GuessPerson = {
      id: 'p',
      name: '测试',
      birth_year: null,
      death_year: null,
      activity: [
        { from: -403, to: -400 },
        { from: 900, to: 907 },
      ],
    };
    expect(matchesGuessYears(person, { from: 900, to: 960 })).toBe(true);
    expect(matchesGuessYears(person, { from: -401, to: -401 })).toBe(true);
    expect(matchesGuessYears(person, { from: 0, to: 800 })).toBe(false);
    expect(matchesGuessYears({ ...person, activity: [] }, { from: 0 })).toBe(
      false,
    );
    expect(matchesGuessYears({ ...person, activity: [] }, {})).toBe(true);
    expect(
      matchesGuessYears(
        { ...person, activity: [], birth_year: 850, death_year: 910 },
        { from: 900 },
      ),
    ).toBe(true);
    expect(
      matchesGuessYears(
        { ...person, activity: [], death_year: 910 },
        { to: 900 },
      ),
    ).toBe(false);
  });
});
