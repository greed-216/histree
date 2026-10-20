import { GuessCharacterCatalogue } from './guess-character-catalogue';
import { GuessClueStore } from './guess-clue-store';
import { GuessGameLibrary } from './guess-game-library';
import { GuessBankService } from './guess-bank';
import { MysqlService } from '../mysql/mysql.service';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { loadGuessCatalogue } from './guess-catalogue';
jest.mock('./guess-catalogue', () => ({ loadGuessCatalogue: jest.fn() }));
it('synchronizes identities only in explicit preparation; both playable catalogues read without writes', async () => {
  const original = {
    id: '11111111-1111-4111-8111-111111111111',
    canonical_person_id: '11111111-1111-4111-8111-111111111111',
    name: '测试人物',
    activity: [],
  };
  let inserted = false;
  const db = {
    execute: jest.fn(async () => {
      inserted = true;
      return { affectedRows: 1 };
    }),
    rows: jest.fn(async (sql: string) =>
      sql.includes('FROM person_event') || !inserted ? [] : [original],
    ),
  };
  (loadGuessCatalogue as jest.Mock).mockResolvedValue([original]);
  const bank = { prepare: jest.fn(async () => [original]) };
  const characters = new GuessCharacterCatalogue(
    db as unknown as MysqlService,
    bank as unknown as GuessBankService,
  );
  const store = new GuessClueStore(db as unknown as MysqlService);
  const library = new GuessGameLibrary(
    db as unknown as MysqlService,
    bank as unknown as GuessBankService,
    {} as GuessClueSetsService,
  );
  expect(
    await store.candidates(
      { difficulty: 'easy' },
      AbortSignal.timeout(10000),
      true,
    ),
  ).toEqual([]);
  expect(await library.catalogue(AbortSignal.timeout(10000))).toEqual([]);
  expect(db.execute).not.toHaveBeenCalled();
  await characters.sync(AbortSignal.timeout(10000));
  const [cluePeople, questionPeople] = await Promise.all([
    store.candidates({ difficulty: 'easy' }, AbortSignal.timeout(10000)),
    library.catalogue(AbortSignal.timeout(10000)),
  ]);
  expect(cluePeople.map((p) => p.id)).toEqual(questionPeople.map((p) => p.id));
  expect(bank.prepare).toHaveBeenCalledTimes(1);
  expect(db.execute).toHaveBeenCalledTimes(1);
});
