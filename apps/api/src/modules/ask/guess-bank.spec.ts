import { GuessBankService, initialGuessDifficulty } from './guess-bank';
import { guessNames } from './guess-names';
import { MysqlService } from '../mysql/mysql.service';
import type { GuessPerson } from './guess-catalogue';

describe('Prepared guess bank', () => {
  it('seeds only missing people and never overwrites feedback-adjusted levels', async () => {
    const saved = new Map([
      ['p1', { person_id: 'p1', difficulty: 'hard', revision: 2 }],
    ]);
    const rows = jest.fn((_sql: string, ids: string[]) =>
      Promise.resolve(
        ids.flatMap((id) => (saved.has(id) ? [saved.get(id)!] : [])),
      ),
    );
    const seedGuessBank = jest.fn(
      (seeds: Array<{ person_id: string; difficulty: string }>) => {
        for (const seed of seeds)
          if (!saved.has(seed.person_id))
            saved.set(seed.person_id, { ...seed, revision: 1 });
        return Promise.resolve();
      },
    );
    const bank = new GuessBankService({
      rows,
      seedGuessBank,
    } as unknown as MysqlService);
    const people: GuessPerson[] = [
      { id: 'p1', name: '曹操' },
      { id: 'p2', name: '未分类人物' },
    ];
    const prepared = await bank.prepare(people, new AbortController().signal);
    expect(seedGuessBank).toHaveBeenCalledWith(
      [{ person_id: 'p2', difficulty: 'hard' }],
      expect.any(AbortSignal),
    );
    expect(prepared[0].game_difficulty).toBe('hard');
    expect(prepared[0].game_revision).toBe(2);
    expect(people[0]).not.toHaveProperty('game_revision');
    await bank.prepare(people, new AbortController().signal);
    expect(seedGuessBank).toHaveBeenCalledTimes(1);
  });
  it('recognizes reviewed identity qualifiers and aliases without merging homonyms', () => {
    for (const name of [
      '李世民（李渊子）',
      '杨广（杨坚子）',
      '杨坚（杨忠子）',
      '高长恭（齐兰陵王）',
      '秦王政',
      '项籍',
      '孟轲',
      '武曌',
      '祖冲之',
    ]) {
      expect(initialGuessDifficulty({ id: 'p', name })).toBe('easy');
    }
    for (const name of [
      '杨广（杨亮子）',
      '杨广（上邽人）',
      '徐庶（王敬则参军）',
      '谢安（下邳募兵者）',
      '李世民（身份待考）',
      '孔子（西秦征西将军）',
    ]) {
      expect(initialGuessDifficulty({ id: 'p', name })).toBe('hard');
    }
  });
  it('accepts reviewed short answers while keeping genuine homonyms separate', () => {
    expect(guessNames({ id: 'p', name: '李世民（李渊子）' })).toEqual(
      expect.arrayContaining(['李世民', '唐太宗']),
    );
    expect(guessNames({ id: 'p', name: '杨广（杨亮子）' })).not.toContain(
      '杨广',
    );
    expect(guessNames({ id: 'p', name: '秦王政' })).toContain('秦始皇');
  });
  it('uses editorial seeds only as initial game settings', () => {
    expect(initialGuessDifficulty({ id: 'p', name: '曹操' })).toBe('easy');
    expect(initialGuessDifficulty({ id: 'p', name: '荀彧' })).toBe('easy');
    expect(initialGuessDifficulty({ id: 'p', name: '刘交' })).toBe('hard');
    expect(initialGuessDifficulty({ id: 'p', name: '未分类人物' })).toBe(
      'hard',
    );
  });
});
