import { GuessService } from './guess.service';
import { GuessGameLibrary, matchesGameEra } from './guess-game-library';
import { MysqlService } from '../mysql/mysql.service';
import { GuessBankService } from './guess-bank';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { GuessAgentService } from './guess-agent.service';
const person = {
  id: '11111111-1111-4111-8111-111111111111',
  canonical_person_id: null,
  name: '李白',
  aliases: ['李太白'],
  era: '唐',
  game_difficulty: 'easy' as const,
  game_revision: 1,
  knowledge_revision: 1,
  game_feedback: 'character' as const,
};
const claim = {
  id: 'knowledge:test:1',
  kind: 'general_knowledge',
  claim_text: '李白是唐代诗人，写过《将进酒》。',
  note: '游戏通识资料卡，非本站已录入原文引文。',
  source: { title: '历史通识资料卡' },
};
describe('Both guess modes share character identity and prepared knowledge', () => {
  it('opens a question game for a person without a canonical record or source; never consults the legacy source gate', async () => {
    const db = {
      getClient: jest.fn(() => {
        throw Error('No canonical source exists');
      }),
    };
    const agent = {
      available: () => true,
      run: jest.fn(async () => ({ verdict: 'yes', claims: [claim.id] })),
    };
    const library = {
      catalogue: jest.fn(async () => [person]),
      material: jest.fn(async () => ({ person, claims: [claim] })),
      rate: jest.fn(async () => ({
        rating: 'right',
        revision: 1,
        moved: false,
      })),
    };
    const bank = { prepare: jest.fn(), rate: jest.fn() };
    const service = new GuessService(
      db as unknown as MysqlService,
      agent as unknown as GuessAgentService,
      bank as unknown as GuessBankService,
      library as unknown as GuessGameLibrary,
    );
    const signal = AbortSignal.timeout(10000),
      start = await service.start({ difficulty: 'easy' }, 'owner', signal);
    expect(start).not.toHaveProperty('person');
    expect(agent.run).not.toHaveBeenCalled();
    expect(db.getClient).not.toHaveBeenCalled();
    const answer = await service.act(
      { token: start.token, action: 'question', text: '你写过诗吗？' },
      'owner',
      signal,
    );
    expect(answer.turns[0].answer).toBe('是');
    expect(agent.run.mock.calls[0]).toBeDefined();
    const end = await service.act(
      { token: start.token, action: 'guess', text: '李太白' },
      'owner',
      signal,
    );
    expect(end.outcome).toBe('won');
    expect(end.person?.id).toBeNull();
    expect(end.evidence?.[0].kind).toBe('general_knowledge');
    expect(
      (
        await service.feedback(
          { token: start.token, rating: 'right' },
          'owner',
          signal,
        )
      ).rating,
    ).toBe('right');
    expect(library.rate).toHaveBeenCalledTimes(1);
    expect(bank.rate).not.toHaveBeenCalled();
  });
});

it('uses era categories only for broad presets and never turns them into activity intervals', () => {
  const p = { ...person, period_from: 1644, period_to: 1912 };
  expect(matchesGameEra(p, { from: 1368, to: 1912 })).toBe(true);
  expect(matchesGameEra(p, { from: 1800, to: 1810 })).toBe(false);
  expect(
    matchesGameEra(
      { ...p, birth_year: 1640, death_year: 1715 },
      { from: 1368, to: 1912 },
    ),
  ).toBe(false);
});

it('prepares missing knowledge for a game-only hard person and reuses it across modes', async () => {
  const hard = { ...person, game_difficulty: 'hard' as const };
  const db = { rows: jest.fn(async () => [hard]), getClient: jest.fn() };
  const clues = [
    {
      text: '我曾留下闻名后世的诗篇。',
      explanation: '李白写过《将进酒》等诗篇。',
    },
  ];
  let cached = false;
  const sets = {
    ready: jest.fn(async () => (cached ? clues : null)),
    ensure: jest.fn(async () => {
      cached = true;
      return clues;
    }),
  };
  const library = new GuessGameLibrary(
    db as unknown as MysqlService,
    {} as GuessBankService,
    sets as unknown as GuessClueSetsService,
  );
  expect(
    (await library.material(hard, AbortSignal.timeout(10000)))?.claims[0].kind,
  ).toBe('general_knowledge');
  await library.material(hard, AbortSignal.timeout(10000));
  expect(sets.ensure).toHaveBeenCalledTimes(1);
  expect(db.getClient).not.toHaveBeenCalled();
});
