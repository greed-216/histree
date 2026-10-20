import { ServiceUnavailableException } from '@nestjs/common';
import {
  makeClueProfile,
  validateClueSelection,
  validateCachedClues,
  type CluePerson,
  type Clue,
} from './guess-clues';
import { GuessClueGameService } from './guess-clue-game.service';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { GuessClueStore, type ClueCacheRow } from './guess-clue-store';
import { GuessAgentService } from './guess-agent.service';
import { MysqlService } from '../mysql/mysql.service';
const person: CluePerson = {
  id: '11111111-1111-4111-8111-111111111111',
  canonical_person_id: null,
  name: '测试甲',
  aliases: ['甲先生'],
  courtesy_name: '子甲',
  era: '唐',
  description: '',
  knowledge_revision: 1,
};
const clues: Clue[] = [
  '我曾离开家乡，远赴另一座城市。',
  '我在地方任职，也与友人来往。',
  '我留下过被后人阅读的作品。',
  '我的一位好友以诗歌闻名。',
  '我的作品描写过山川与河流。',
  '我最出名的一篇作品描写了故乡。',
].map((text) => ({ text, explanation: '仅供独立测试使用的合成通识解释。' }));
const profile = () => makeClueProfile(person),
  signal = () => AbortSignal.timeout(10000);
function memory() {
  const rows = new Map<string, ClueCacheRow>(),
    key = (p: ReturnType<typeof profile>) => p.person.id + ':' + p.revision;
  const store = {
    rate: jest.fn(async (input: { rating: 'easy' | 'right' | 'hard' }) => ({
      rating: input.rating,
      difficulty: 'easy',
      revision: 1,
      moved: false,
    })),
    candidates: jest.fn(async () => [{ id: person.id }]),
    readyPeople: jest.fn(async () => new Set([person.id])),
    find: jest.fn(
      async (p: ReturnType<typeof profile>) => rows.get(key(p)) || null,
    ),
    claim: jest.fn(async (p: ReturnType<typeof profile>, token: string) => {
      if (!rows.has(key(p)))
        rows.set(key(p), {
          status: 'generating',
          lease_token: token,
          clues: null,
        });
      return rows.get(key(p))!;
    }),
    complete: jest.fn(
      async (p: ReturnType<typeof profile>, token: string, values: Clue[]) => {
        if (rows.get(key(p))?.lease_token !== token) return { affectedRows: 0 };
        rows.set(key(p), { status: 'ready', lease_token: null, clues: values });
        return { affectedRows: 1 };
      },
    ),
    fail: jest.fn(async (p: ReturnType<typeof profile>, token: string) => {
      if (rows.get(key(p))?.lease_token === token)
        rows.set(key(p), { status: 'failed', lease_token: null, clues: null });
    }),
  };
  const db = { rows: jest.fn(async () => [person]) };
  const agent = {
    available: () => true,
    run: jest.fn(async () => ({ clues })),
  };
  const create = () =>
    new GuessClueSetsService(
      store as unknown as GuessClueStore,
      agent as unknown as GuessAgentService,
      db as unknown as MysqlService,
    );
  const sets = {
    ready: jest.fn(async () => clues),
    ensure: jest.fn(async () => clues),
  };
  const game = () =>
    new GuessClueGameService(
      db as unknown as MysqlService,
      store as unknown as GuessClueStore,
      sets as unknown as GuessClueSetsService,
      agent as unknown as GuessAgentService,
    );
  return { rows, store, db, agent, create, sets, game };
}
describe('Reusable historical general-knowledge clues', () => {
  it('supports a game-only person with no ingested description or claims', () => {
    const p = profile();
    expect(p.person.canonical_person_id).toBeNull();
    expect(validateClueSelection({ clues }, p)).toEqual(clues);
    expect(validateCachedClues(clues, p)).toEqual(clues);
    expect(
      makeClueProfile({ ...person, knowledge_revision: 2 }).revision,
    ).not.toBe(p.revision);
    expect(makeClueProfile({ ...person, aliases: ['甲某'] }).revision).not.toBe(
      p.revision,
    );
  });
  it('allows calligraphy and works even if the site profile only describes a political event', () => {
    const p = makeClueProfile({
      ...person,
      name: '王羲之',
      aliases: ['王右军'],
      courtesy_name: '逸少',
      description: '曾劝两人勿与桓温构隙。',
    });
    const values = clues.map((c, i) => ({
      ...c,
      text:
        i === 4
          ? '我的书法对后世产生了深远影响。'
          : i === 5
            ? '我留下了被誉为天下第一行书的《兰亭集序》。'
            : c.text,
    }));
    expect(validateClueSelection({ clues: values }, p)).toEqual(values);
  });
  it('rejects early identity leaks, duplicate clues, incomplete sets and invented source fields', () => {
    for (const text of [
      '我是测试甲，曾经远行。',
      '我字子甲，曾经远行。',
      '大家称我为甲先生。',
    ])
      expect(() =>
        validateClueSelection(
          { clues: clues.map((c, i) => (i ? c : { ...c, text })) },
          profile(),
        ),
      ).toThrow('透露');
    expect(() =>
      validateClueSelection(
        { clues: [...clues.slice(0, 5), clues[0]] },
        profile(),
      ),
    ).toThrow('重复');
    expect(() =>
      validateClueSelection({ clues: clues.slice(0, 5) }, profile()),
    ).toThrow('校验');
    expect(() =>
      validateClueSelection(
        { clues: clues.map((c) => ({ ...c, claimId: 'fabricated' })) },
        profile(),
      ),
    ).toThrow('校验');
  });
  it('prepares once for concurrent callers and reuses durable results after a restart', async () => {
    const m = memory(),
      s = m.create(),
      p = profile();
    const [a, b] = await Promise.all([
      s.ensure(p, signal()),
      s.ensure(p, signal()),
    ]);
    expect(a).toEqual(b);
    expect(m.agent.run).toHaveBeenCalledTimes(1);
    expect(await m.create().ensure(p, signal())).toEqual(a);
    expect(m.agent.run).toHaveBeenCalledTimes(1);
    expect(m.agent.run.mock.calls[0]).toBeDefined();
  });
  it('coordinates separate instances through the shared persistence lease', async () => {
    const m = memory();
    const [a, b] = await Promise.all([
      m.create().ensure(profile(), signal()),
      m.create().ensure(profile(), signal()),
    ]);
    expect(a).toEqual(b);
    expect(m.agent.run).toHaveBeenCalledTimes(1);
  });
  it('does not store invalid model output; the retry cooldown prevents repeated calls', async () => {
    const m = memory();
    m.agent.run.mockResolvedValue({ clues: [] });
    await expect(m.create().ensure(profile(), signal())).rejects.toThrow(
      '校验',
    );
    expect(m.store.complete).not.toHaveBeenCalled();
    expect(m.store.fail).toHaveBeenCalledTimes(1);
    await expect(m.create().ensure(profile(), signal())).rejects.toThrow(
      '稍后',
    );
    expect(m.agent.run).toHaveBeenCalledTimes(1);
  });
  it('does not save obsolete results if the game identity changes during generation', async () => {
    const m = memory();
    m.agent.run.mockImplementation(async () => {
      m.db.rows.mockResolvedValue([{ ...person, knowledge_revision: 2 }]);
      return { clues };
    });
    await expect(m.create().ensure(profile(), signal())).rejects.toThrow(
      '已更新',
    );
    expect(m.store.complete).not.toHaveBeenCalled();
  });
  it('lets shared preparation finish after one player disconnects', async () => {
    const m = memory(),
      s = m.create();
    let resolve!: (v: { clues: Clue[] }) => void;
    m.agent.run.mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    const c = new AbortController(),
      a = s.ensure(profile(), c.signal),
      b = s.ensure(profile(), signal());
    await new Promise((r) => setTimeout(r, 5));
    c.abort();
    await expect(a).rejects.toThrow();
    resolve({ clues });
    expect(await b).toEqual(clues);
    expect(m.store.complete).toHaveBeenCalledTimes(1);
  });
});
describe('Clue game privacy and incremental reveal', () => {
  it('returns only the first clue; guesses do not reveal identity or extra clues', async () => {
    const m = memory(),
      g = m.game(),
      start = await g.start({ difficulty: 'easy' }, 'a', signal());
    expect(start.clues).toEqual([clues[0].text]);
    expect(start).not.toHaveProperty('person');
    expect(start).not.toHaveProperty('evidence');
    const serialized = JSON.stringify(start);
    for (const hidden of [
      person.name,
      person.id,
      '子甲',
      clues[1].text,
      clues[0].explanation,
    ])
      expect(serialized).not.toContain(hidden);
    const wrong = await g.act(
      { token: start.token, action: 'guess', text: '另一个人' },
      'a',
      signal(),
    );
    expect(wrong.outcome).toBeNull();
    expect(wrong.unlocked).toBe(1);
    expect(m.agent.run).not.toHaveBeenCalled();
  });
  it('unlocks once per operation, restores progress and checks ownership', async () => {
    const g = memory().game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal()),
      hint = { token: s.token, action: 'hint', expectedUnlocked: 1 };
    expect((await g.act(hint, 'a', signal())).unlocked).toBe(2);
    expect((await g.act(hint, 'a', signal())).unlocked).toBe(2);
    expect(
      (await g.act({ token: s.token, action: 'state' }, 'a', signal())).clues,
    ).toHaveLength(2);
    await expect(
      g.act({ ...hint, expectedUnlocked: 5 }, 'a', signal()),
    ).rejects.toThrow('进度');
    await expect(
      g.act({ token: s.token, action: 'hint' }, 'a', signal()),
    ).rejects.toThrow('格式');
    await expect(
      g.act({ token: s.token, action: 'state' }, 'b', signal()),
    ).rejects.toThrow('无权');
  });
  it('accepts aliases and reveals explanations with no fabricated historical links', async () => {
    const g = memory().game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal());
    const won = await g.act(
      { token: s.token, action: 'guess', text: '甲先生' },
      'a',
      signal(),
    );
    expect(won.outcome).toBe('won');
    expect(won.unlocked).toBe(1);
    expect(won.clues).toHaveLength(6);
    expect(won.person?.id).toBeNull();
    expect(won.person?.name).toBe(person.name);
    expect(won.evidence?.[0]).toMatchObject({
      kind: 'general_knowledge',
      explanation: clues[0].explanation,
    });
    expect(won.evidence?.[0]).not.toHaveProperty('id');
  });
  it('refuses chosen targets and AI questions, invalidates sessions after identity edits', async () => {
    const m = memory(),
      g = m.game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal());
    await expect(
      g.start({ difficulty: 'easy', person_id: person.id }, 'a', signal()),
    ).rejects.toThrow('检查');
    await expect(
      g.act(
        { token: s.token, action: 'question', text: '你是谁' },
        'a',
        signal(),
      ),
    ).rejects.toThrow('格式');
    m.db.rows.mockResolvedValue([{ ...person, knowledge_revision: 2 }]);
    await expect(
      g.act({ token: s.token, action: 'state' }, 'a', signal()),
    ).rejects.toThrow('已更新');
  });
  it('opens easy only from prepared caches, while hard prepares on first use', async () => {
    const m = memory(),
      g = m.game();
    m.store.readyPeople.mockResolvedValue(new Set());
    await expect(
      g.start({ difficulty: 'easy' }, 'a', signal()),
    ).rejects.toThrow('尚未准备');
    expect(m.sets.ensure).not.toHaveBeenCalled();
    expect(
      (await g.start({ difficulty: 'hard' }, 'a', signal())).clues,
    ).toHaveLength(1);
    expect(m.sets.ensure).toHaveBeenCalledTimes(1);
  });
});

describe('Clue difficulty feedback', () => {
  it('requires engagement and an ended game, and keeps rating private before the end', async () => {
    const m = memory(),
      g = m.game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal());
    expect(s).not.toHaveProperty('rating');
    await expect(
      g.feedback({ token: s.token, rating: 'hard' }, 'a', signal()),
    ).rejects.toThrow('揭晓后');
    const end = await g.act(
      { token: s.token, action: 'reveal' },
      'a',
      signal(),
    );
    expect(end.ratingEligible).toBe(false);
    await expect(
      g.feedback({ token: s.token, rating: 'hard' }, 'a', signal()),
    ).rejects.toThrow('揭晓后');
    expect(m.store.rate).not.toHaveBeenCalled();
  });
  it('accepts a rating after revealing hints, deduplicates retries and restores the result', async () => {
    const m = memory(),
      g = m.game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal());
    await g.act(
      { token: s.token, action: 'hint', expectedUnlocked: 1 },
      'a',
      signal(),
    );
    await g.act({ token: s.token, action: 'reveal' }, 'a', signal());
    await expect(
      g.feedback({ token: s.token, rating: 'hard' }, 'other', signal()),
    ).rejects.toThrow('无权');
    expect(
      (await g.feedback({ token: s.token, rating: 'hard' }, 'a', signal()))
        .rating,
    ).toBe('hard');
    expect(
      (await g.feedback({ token: s.token, rating: 'easy' }, 'a', signal()))
        .rating,
    ).toBe('hard');
    expect(m.store.rate).toHaveBeenCalledTimes(1);
    expect(m.store.rate.mock.calls[0][0]).toMatchObject({
      guesses: 0,
      unlocked: 2,
      outcome: 'revealed',
      revision: 1,
    });
    expect(
      (await g.act({ token: s.token, action: 'state' }, 'a', signal())).rating,
    ).toBe('hard');
  });
  it('does not mark an unsaved vote as saved and allows an explicit retry', async () => {
    const m = memory(),
      g = m.game(),
      s = await g.start({ difficulty: 'easy' }, 'a', signal());
    await g.act(
      { token: s.token, action: 'guess', text: '甲先生' },
      'a',
      signal(),
    );
    m.store.rate.mockRejectedValueOnce(new Error('database unavailable'));
    await expect(
      g.feedback({ token: s.token, rating: 'right' }, 'a', signal()),
    ).rejects.toThrow('未能保存');
    expect(
      (await g.feedback({ token: s.token, rating: 'right' }, 'a', signal()))
        .rating,
    ).toBe('right');
  });
});

it('falls back to a prepared hard target when a newly drawn person lacks reliable knowledge', async () => {
  const m = memory();
  const other = { ...person, id: '22222222-2222-4222-8222-222222222222' };
  m.store.candidates.mockResolvedValue([{ id: person.id }, { id: other.id }]);
  m.store.readyPeople.mockResolvedValue(new Set([other.id]));
  m.db.rows.mockImplementation(async (_sql: string, args: unknown[]) => [
    { ...(args[0] === person.id ? person : other), game_difficulty: 'hard' },
  ]);
  m.sets.ensure.mockImplementation(async (p) => {
    if (p.person.id === person.id)
      throw new ServiceUnavailableException('没有足够可靠的线索');
    return clues;
  });
  const shuffle = jest
    .spyOn(
      jest.requireActual('node:crypto') as { randomInt(max: number): number },
      'randomInt',
    )
    .mockImplementation((max) => max - 1);
  try {
    const game = await m
      .game()
      .start({ difficulty: 'hard' }, 'fallback-player', signal());
    expect(game.clues).toHaveLength(1);
    expect(m.sets.ensure.mock.calls.map(([p]) => p.person.id)).toEqual([
      person.id,
      other.id,
    ]);
  } finally {
    shuffle.mockRestore();
  }
});
