import { GuessService } from './guess.service';
import { GuessAgentService } from './guess-agent.service';
import { MysqlService } from '../mysql/mysql.service';
import { GuessBankService, initialGuessDifficulty } from './guess-bank';
import type { GuessPerson } from './guess-catalogue';
const person = {
  id: '11111111-1111-4111-8111-111111111111',
  name: '朱温',
  aliases: ['朱全忠'],
  era: '五代',
  description: '有史料的测试人物',
};
const claim = {
  id: 'c1',
  claim_text: '测试事实',
  note: '原文：测试原文。；核对说明：测试',
  source: { title: '测试史书' },
  citation: '测试定位',
};
function make(target = person, evidence = claim) {
  const agent = {
    available: jest.fn(() => true),
    run: jest
      .fn<Promise<unknown>, [unknown, AbortSignal]>()
      .mockResolvedValue({ ids: [target.id] }),
  };
  const rpc = jest.fn((name: string, args: { p_table: string }) => ({
    abortSignal: () =>
      Promise.resolve({
        data:
          name === 'entry_detail'
            ? { ...target, type: 'person' }
            : name === 'entry_context'
              ? { edges: [], nodes: [] }
              : {
                  items: args.p_table === 'person' ? [target] : [evidence],
                  has_more: false,
                },
        error: null,
      }),
  }));
  const rows = jest.fn<Promise<unknown[]>, [string]>((sql) =>
    Promise.resolve(sql.includes('FROM person p') ? [{ ...target }] : []),
  );
  const bank = {
    prepare: jest.fn((people: GuessPerson[]) =>
      Promise.resolve(
        people.map((p) => ({
          ...p,
          game_difficulty: initialGuessDifficulty(p),
          game_revision: 1,
        })),
      ),
    ),
    rate: jest.fn().mockResolvedValue({
      person_id: target.id,
      difficulty: 'hard',
      revision: 1,
      rating: 'hard',
      moved: false,
    }),
  };
  const service = new GuessService(
    { rows, getClient: () => ({ rpc }) } as unknown as MysqlService,
    agent as unknown as GuessAgentService,
    bank as unknown as GuessBankService,
  );
  return { service, agent, rpc, rows, bank };
}
const signal = new AbortController().signal;
const filters = { difficulty: 2 };
describe('Guess game privacy and lifecycle', () => {
  it.each([
    ['你是宋以及宋以前的么？', 'yes', '是'],
    ['你的生活时期不晚于宋代吗？', 'yes', '是'],
    ['你是宋以前的人吗？', 'yes', '是'],
    ['你是宋以后的人吗？', 'no', '不是'],
    ['你不是宋朝人吗？', 'yes', '是'],
    ['你不曾生活在宋或更早时期吗？', 'no', '不是'],
    ['你整个生平都在五代吗？', 'unknown', '不清楚'],
    ['你是李白的兄弟吗？', 'unknown', '不清楚'],
    ['你姓朱吗？', 'yes', '是'],
  ])(
    'forwards the whole complex proposition once and preserves the verdict: %s',
    async (text, verdict, answer) => {
      const { service, agent } = make();
      const { token } = await service.start(
        { difficulty: 'easy' },
        'a',
        signal,
      );
      expect(agent.run).not.toHaveBeenCalled();
      agent.run.mockResolvedValueOnce({
        verdict,
        claims: verdict === 'unknown' ? [] : ['c1'],
      });
      const result = await service.act(
        { token, action: 'question', text },
        'a',
        signal,
      );
      expect(agent.run).toHaveBeenCalledTimes(1);
      expect(agent.run.mock.calls[0][0]).toMatchObject({
        task: 'question',
        question: text,
        person: { name: person.name },
        claims: [{ id: 'c1', note: claim.note }],
      });
      expect(agent.run.mock.calls[0][1]).toBe(signal);
      expect(result.turns).toEqual([{ text, answer, kind: 'question' }]);
      expect(result.remaining).toBe(29);
      expect(result.outcome).toBeNull();
      expect(result).not.toHaveProperty('person');
      expect(result).not.toHaveProperty('evidence');
      expect(JSON.stringify(result)).not.toContain(person.name);
    },
  );

  it('rejects a single-call judge trying to win with one of several proposed names', async () => {
    const { service, agent } = make();
    const { token } = await service.start({ difficulty: 'easy' }, 'a', signal);
    agent.run.mockResolvedValueOnce({
      verdict: 'guess',
      name: '朱温',
      claims: [],
    });
    await expect(
      service.act(
        {
          token,
          action: 'question',
          text: '你是朱温还是曹操？',
        },
        'a',
        signal,
      ),
    ).rejects.toThrow('确认');
    const state = await service.act({ token, action: 'state' }, 'a', signal);
    expect(state.remaining).toBe(30);
    expect(state.outcome).toBeNull();
    expect(state).not.toHaveProperty('person');
  });

  it('answers the reported era variants consistently without requiring lifespan dates or a model verdict', async () => {
    const wang = {
      ...person,
      name: '王羲之',
      aliases: [],
      era: '晋',
      description: '王导从子，348年劝殷浩荀羡勿与桓温构隙。',
    };
    const { service, agent } = make(wang, {
      ...claim,
      claim_text: '所引记载中的人物对应王羲之。',
      note: '原文：羲之，导之从子也。；核对说明：身份由本段官号、称谓、已核连续上下文确认。',
    });
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockClear();
    for (const text of [
      '你是秦汉时期的人么',
      '你是秦汉年代的人么？',
      '你活跃在秦汉时期吗？',
      '你是活跃在三国时期的人么？',
    ]) {
      const result = await service.act(
        { token, action: 'question', text },
        'a',
        signal,
      );
      expect(result.turns.at(-1)?.answer).toBe('不是');
      expect(result).not.toHaveProperty('person');
      expect(result).not.toHaveProperty('evidence');
      expect(JSON.stringify(result)).not.toContain('王羲之');
    }
    const result = await service.act(
      { token, action: 'question', text: '你是晋朝的人吗？' },
      'a',
      signal,
    );
    expect(result.turns.at(-1)?.answer).toBe('是');
    expect(result.remaining).toBe(25);
    expect(agent.run).not.toHaveBeenCalled();
  });

  it('keeps era questions unknown when the published era is missing', async () => {
    const { service, agent } = make({ ...person, era: '' });
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockResolvedValueOnce({ verdict: 'unknown', claims: [] });
    const result = await service.act(
      { token, action: 'question', text: '你是秦汉时期的人么' },
      'a',
      signal,
    );
    expect(result.turns[0].answer).toBe('不清楚');
    expect(agent.run).toHaveBeenLastCalledWith(
      expect.objectContaining({ task: 'question' }),
      signal,
    );
  });

  it.each([
    ['easy', '曹操'],
    ['easy', '朱温'],
    ['hard', '刘琨'],
    ['hard', '刘交'],
  ])('merges fame tiers into %s for %s', async (difficulty, name) => {
    const { service, agent } = make({ ...person, name });
    const started = await service.start({ difficulty }, 'a', signal);
    expect(started.filters.difficulty).toBe(difficulty);
    expect(started).not.toHaveProperty('person');
    expect(agent.run).not.toHaveBeenCalled();
  });
  it('never calls the model for ordinary starts, including after a new preparation', async () => {
    const { service, agent, bank } = make();
    agent.run.mockRejectedValue(new Error('The model must not be called'));
    const start = await service
      .start({ difficulty: 'easy', from: 900, to: 960 }, 'a', signal)
      .catch(() => null);
    expect(start).toBeNull(); // No known years: do not widen the requested era.
    const first = await service.start({ difficulty: 'easy' }, 'a', signal);
    const second = await service.start({ difficulty: 'easy' }, 'a', signal);
    expect(first.token).not.toBe(second.token);
    const now = jest.spyOn(Date, 'now').mockReturnValue(Date.now() + 300001);
    try {
      await service.start({ difficulty: 'easy' }, 'a', signal);
    } finally {
      now.mockRestore();
    }
    expect(bank.prepare).toHaveBeenCalledTimes(2);
    expect(agent.run).not.toHaveBeenCalled();
  });
  it('uses feedback-adjusted difficulty instead of a fixed name anchor for new games', async () => {
    const { service, bank, agent } = make();
    bank.prepare.mockImplementation((people) =>
      Promise.resolve(
        people.map((p) => ({
          ...p,
          game_difficulty: 'hard' as const,
          game_revision: 2,
        })),
      ),
    );
    await service.start({ difficulty: 'hard' }, 'a', signal);
    await expect(
      service.start({ difficulty: 'easy' }, 'a', signal),
    ).rejects.toThrow('暂无符合');
    expect(agent.run).not.toHaveBeenCalled();
  });
  it('accepts feedback only after a played, owned, revealed game and keeps it on refresh', async () => {
    const { service, bank } = make();
    const started = await service.start({ difficulty: 'easy' }, 'a', signal);
    expect(started).not.toHaveProperty('ratingEligible');
    await expect(
      service.feedback({ token: started.token, rating: 'hard' }, 'a', signal),
    ).rejects.toThrow('揭晓');
    await expect(
      service.feedback(
        { token: started.token, rating: 'hard' },
        'other',
        signal,
      ),
    ).rejects.toThrow('无权');
    await service.act(
      { token: started.token, action: 'question', text: '朱温' },
      'a',
      signal,
    );
    const rated = await service.feedback(
      { token: started.token, rating: 'hard' },
      'a',
      signal,
    );
    expect(rated.rating).toBe('hard');
    expect(rated.ratingEligible).toBe(true);
    await service.feedback(
      { token: started.token, rating: 'easy' },
      'a',
      signal,
    );
    expect(bank.rate).toHaveBeenCalledTimes(1);
    expect(bank.rate).toHaveBeenCalledWith(
      expect.objectContaining({
        person_id: person.id,
        revision: 1,
        turns: 1,
        hints: 0,
      }),
      signal,
    );
    expect(
      (
        await service.act(
          { token: started.token, action: 'state' },
          'a',
          signal,
        )
      ).rating,
    ).toBe('hard');
  });
  it('refreshes a changed level after an idempotent retry that discovers an earlier commit', async () => {
    const { service, bank, agent } = make();
    const game = await service.start({ difficulty: 'easy' }, 'a', signal);
    await service.act(
      { token: game.token, action: 'guess', text: '朱温' },
      'a',
      signal,
    );
    bank.rate.mockResolvedValueOnce({
      person_id: person.id,
      difficulty: 'hard',
      revision: 2,
      rating: 'hard',
      moved: false,
    });
    bank.prepare.mockImplementation((people) =>
      Promise.resolve(
        people.map((p) => ({
          ...p,
          game_difficulty: 'hard' as const,
          game_revision: 2,
        })),
      ),
    );
    await service.feedback({ token: game.token, rating: 'hard' }, 'a', signal);
    await service.start({ difficulty: 'hard' }, 'a', signal);
    expect(bank.prepare).toHaveBeenCalledTimes(2);
    expect(
      (await service.act({ token: game.token, action: 'state' }, 'a', signal))
        .filters.difficulty,
    ).toBe('easy');
    expect(agent.run).not.toHaveBeenCalled();
  });
  it('refuses ratings after a reveal without play, and lets a failed save be retried', async () => {
    const { service, bank } = make();
    const empty = await service.start({ difficulty: 'easy' }, 'a', signal);
    await service.act({ token: empty.token, action: 'reveal' }, 'a', signal);
    await expect(
      service.feedback({ token: empty.token, rating: 'hard' }, 'a', signal),
    ).rejects.toThrow('至少一次');
    const played = await service.start({ difficulty: 'easy' }, 'a', signal);
    await service.act(
      { token: played.token, action: 'guess', text: '朱温' },
      'a',
      signal,
    );
    bank.rate.mockRejectedValueOnce(new Error('offline'));
    await expect(
      service.feedback({ token: played.token, rating: 'hard' }, 'a', signal),
    ).rejects.toThrow('未能保存');
    expect(
      (
        await service.feedback(
          { token: played.token, rating: 'hard' },
          'a',
          signal,
        )
      ).rating,
    ).toBe('hard');
  });
  it('keeps easy anchors out of hard games and respects recorded activity for null lifespans', async () => {
    const { service, rows } = make();
    rows.mockImplementation((sql: string) =>
      Promise.resolve(
        sql.includes('FROM person p')
          ? [{ ...person, birth_year: null, death_year: null }]
          : [{ person_id: person.id, start_year: 900, end_year: 907 }],
      ),
    );
    await expect(
      service.start({ difficulty: 'hard' }, 'a', signal),
    ).rejects.toThrow('暂无符合');
    const started = await service.start(
      { difficulty: 'easy', from: 900, to: 960 },
      'a',
      signal,
    );
    expect(started.token).toHaveLength(64);
    await expect(
      service.start({ difficulty: 'easy', from: 1368, to: 1644 }, 'a', signal),
    ).rejects.toThrow('暂无符合');
  });
  it('tries a disjoint sample after an empty model selection without accepting foreign IDs', async () => {
    const { service, agent, rows } = make();
    const candidates = Array.from({ length: 121 }, (_, i) => ({
      ...person,
      id: `p${i}`,
      name: `测试人物${i}`,
    }));
    rows.mockImplementation((sql: string) =>
      Promise.resolve(sql.includes('FROM person p') ? candidates : []),
    );
    agent.run.mockImplementation((input) => {
      const call = agent.run.mock.calls.length;
      const batch = (input as { candidates: typeof candidates }).candidates;
      return Promise.resolve({ ids: call === 1 ? ['foreign'] : [batch[0].id] });
    });
    await service.start(
      { difficulty: 'hard', custom: '测试限定' },
      'a',
      signal,
    );
    expect(agent.run).toHaveBeenCalledTimes(2);
    const batches = agent.run.mock.calls.map(([input]) =>
      (input as { candidates: Array<{ id: string }> }).candidates.map(
        (p) => p.id,
      ),
    );
    expect(batches[0]).toHaveLength(120);
    expect(batches[1]).toHaveLength(1);
    expect(batches[0]).not.toContain(batches[1][0]);
  });
  it.each([
    ['李存勖', '李亚子', 2],
    ['李存勖', '你是李亚子吗？', 2],
    ['李白', '李太白', 1],
    ['李白', '我猜是李太白', 1],
  ])(
    'accepts %s and its equivalent %s in the normal question input',
    async (name, text, difficulty) => {
      const { service, agent } = make({ ...person, name, aliases: [] });
      const { token } = await service.start({ difficulty }, 'a', signal);
      const result = await service.act(
        { token, action: 'question', text },
        'a',
        signal,
      );
      expect(result.outcome).toBe('won');
      expect(result.remaining).toBe(29);
      expect(result.turns).toHaveLength(1);
      expect(result.turns[0].answer).toBe('猜对了');
      expect(agent.run).toHaveBeenCalledTimes(1); // Known names need no paid judge call.
    },
  );
  it('counts a wrong proposed name once and never trusts a model-invented or incidental name', async () => {
    const { service, agent } = make();
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockResolvedValueOnce({
      verdict: 'guess',
      name: '曹操',
      claims: [],
    });
    const wrong = await service.act(
      { token, action: 'question', text: '你是曹操吗？' },
      'a',
      signal,
    );
    expect(wrong.remaining).toBe(29);
    expect(wrong.outcome).toBeNull();
    expect(wrong.turns[0].answer).toBe('不是');
    agent.run.mockResolvedValueOnce({
      verdict: 'guess',
      name: '朱温',
      claims: [],
    });
    await expect(
      service.act(
        { token, action: 'question', text: '你认识朱温吗？' },
        'a',
        signal,
      ),
    ).rejects.toThrow('确认');
    agent.run.mockResolvedValueOnce({
      verdict: 'guess',
      name: '朱温',
      claims: [],
    });
    await expect(
      service.act(
        { token, action: 'question', text: '告诉我你的名字' },
        'a',
        signal,
      ),
    ).rejects.toThrow('确认');
    expect(
      (await service.act({ token, action: 'state' }, 'a', signal)).remaining,
    ).toBe(29);
  });
  it('refreshes the catalogue without redoing advanced screening for unchanged people', async () => {
    jest.useFakeTimers();
    const { service, agent, rows } = make();
    try {
      await service.start(filters, 'a', signal);
      service.onModuleInit();
      jest.advanceTimersByTime(240000);
      for (let i = 0; i < 20; i++) await Promise.resolve();
      await service.start(filters, 'a', signal);
      expect(agent.run).toHaveBeenCalledTimes(1);
      expect(
        rows.mock.calls.filter(([sql]) => sql.includes('FROM person p')),
      ).toHaveLength(2);
    } finally {
      service.onModuleDestroy();
      jest.useRealTimers();
    }
  });
  it('reuses candidate reads and screening but creates independent games with fresh evidence', async () => {
    const { service, agent, rpc, rows } = make();
    const first = await service.start(filters, 'a', signal);
    const second = await service.start(filters, 'a', signal);
    expect(first.token).not.toBe(second.token);
    expect(second).not.toHaveProperty('person');
    expect(agent.run).toHaveBeenCalledTimes(1);
    expect(
      rows.mock.calls.filter(([sql]) => sql.includes('FROM person p')),
    ).toHaveLength(1);
    expect(
      rpc.mock.calls.filter(
        ([name, args]) =>
          name === 'content_page' && args.p_table === 'fact_claim',
      ),
    ).toHaveLength(2);
    await service.start(
      { ...filters, custom: 'another restriction' },
      'a',
      signal,
    );
    expect(agent.run).toHaveBeenCalledTimes(2);
  });
  it('refreshes expired candidates and never opens a cached person without current published evidence', async () => {
    const { service, agent, rpc, rows } = make();
    await service.start(filters, 'a', signal);
    const original = rpc.getMockImplementation()!;
    rpc.mockImplementation((name, args) =>
      name === 'content_page' && args.p_table === 'fact_claim'
        ? {
            abortSignal: () =>
              Promise.resolve({
                data: { items: [], has_more: false },
                error: null,
              }),
          }
        : original(name, args),
    );
    await expect(service.start(filters, 'a', signal)).rejects.toThrow(
      '尚无可回溯原文',
    );
    expect(agent.run).toHaveBeenCalledTimes(1);
    rpc.mockImplementation(original);
    const now = jest.spyOn(Date, 'now').mockReturnValue(Date.now() + 300001);
    try {
      await service.start(filters, 'a', signal);
      expect(agent.run).toHaveBeenCalledTimes(1);
      expect(
        rows.mock.calls.filter(([sql]) => sql.includes('FROM person p')),
      ).toHaveLength(2);
    } finally {
      now.mockRestore();
    }
  });
  it('evicts a failed screening and shares pending screening without letting one cancellation abort the other game', async () => {
    const { service, agent } = make();
    agent.run.mockRejectedValueOnce(new Error('offline'));
    await expect(service.start(filters, 'a', signal)).rejects.toThrow(
      'offline',
    );
    let complete!: (value: unknown) => void;
    agent.run.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          complete = resolve;
        }),
    );
    const controller = new AbortController();
    const first = service.start(filters, 'a', controller.signal);
    const cancelled = expect(first).rejects.toThrow('cancelled');
    const second = service.start(filters, 'b', signal);
    for (let i = 0; i < 20 && !complete; i++) await Promise.resolve();
    expect(complete).toBeDefined();
    controller.abort(new Error('cancelled'));
    await cancelled;
    complete({ ids: [person.id] });
    expect((await second).token).toMatch(/^[a-f0-9]{64}$/);
    expect(agent.run).toHaveBeenCalledTimes(2);
  });
  it('keeps identity and evidence server-side until a deterministic guess wins', async () => {
    const { service } = make();
    const started = await service.start(filters, 'a', signal);
    expect(started.token).toMatch(/^[a-f0-9]{64}$/);
    expect(JSON.stringify(started)).not.toContain(person.name);
    expect(started).not.toHaveProperty('person');
    expect(started).not.toHaveProperty('evidence');
    const wrong = await service.act(
      { token: started.token, action: 'guess', text: '朱' },
      'a',
      signal,
    );
    expect(wrong.outcome).toBeNull();
    expect(wrong.remaining).toBe(29);
    const won = await service.act(
      { token: started.token, action: 'guess', text: ' 朱全忠 ' },
      'a',
      signal,
    );
    expect(won.outcome).toBe('won');
    expect(won.person?.id).toBe(person.id);
    expect(won.evidence?.[0].title).toBe('测试史书');
  });
  it('rejects free-form model output, unsupported claims, and identity-bearing hints', async () => {
    const { service, agent } = make();
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockResolvedValueOnce({ verdict: 'yes', claims: ['foreign'] });
    const unsupported = await service.act(
      { token, action: 'question', text: '你是皇帝吗' },
      'a',
      signal,
    );
    expect(unsupported.turns[0].answer).toBe('不清楚');
    expect(unsupported).not.toHaveProperty('person');
    agent.run.mockResolvedValueOnce({
      verdict: 'yes',
      claims: ['c1'],
      answer: '我是朱温',
    });
    await expect(
      service.act({ token, action: 'question', text: '你是谁' }, 'a', signal),
    ).rejects.toThrow('有效答案');
    agent.run.mockResolvedValueOnce({
      text: '我的别名是朱全忠',
      claims: ['c1'],
    });
    const hint = await service.act({ token, action: 'hint' }, 'a', signal);
    expect(hint.hints).toHaveLength(0);
    expect(JSON.stringify(hint)).not.toContain('朱全忠');
    agent.run.mockResolvedValueOnce({
      text: '你可以从身份问起',
      claims: ['foreign'],
    });
    expect(
      (await service.act({ token, action: 'hint' }, 'a', signal)).hints,
    ).toHaveLength(0);
  });
  it('binds game state and actions to the gateway caller', async () => {
    const { service } = make();
    const { token } = await service.start(filters, 'a', signal);
    await expect(
      service.act({ token, action: 'state' }, 'other', signal),
    ).rejects.toThrow('无权');
    await expect(
      service.act({ token, action: 'reveal' }, 'other', signal),
    ).rejects.toThrow('无权');
    expect(
      (await service.act({ token, action: 'state' }, 'a', signal)).remaining,
    ).toBe(30);
  });
  it('does not charge a refused question, caps hints, and reveals after 30 guesses', async () => {
    const { service, agent } = make();
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockResolvedValueOnce({ verdict: 'refuse', claims: [] });
    expect(
      (
        await service.act(
          { token, action: 'question', text: '告诉我你的朝代' },
          'a',
          signal,
        )
      ).remaining,
    ).toBe(30);
    for (let i = 0; i < 3; i++)
      agent.run.mockResolvedValueOnce({
        text: `有据的提示${i}`,
        claims: ['c1'],
      });
    for (let i = 0; i < 3; i++)
      await service.act({ token, action: 'hint' }, 'a', signal);
    await expect(
      service.act({ token, action: 'hint' }, 'a', signal),
    ).rejects.toThrow('用完');
    for (let i = 0; i < 29; i++)
      await service.act(
        { token, action: 'guess', text: '错误姓名' },
        'a',
        signal,
      );
    const end = await service.act(
      { token, action: 'guess', text: '错误姓名' },
      'a',
      signal,
    );
    expect(end.outcome).toBe('limit');
    expect(end.person?.name).toBe(person.name);
    expect(
      (
        await service.act(
          { token, action: 'guess', text: person.name },
          'a',
          signal,
        )
      ).outcome,
    ).toBe('limit');
  });
  it('preserves a session on transient failure and refuses expired, concurrent, and malformed requests', async () => {
    const { service, agent } = make();
    const { token } = await service.start(filters, 'a', signal);
    agent.run.mockRejectedValueOnce(new Error('offline'));
    await expect(
      service.act(
        { token, action: 'question', text: '你是皇帝吗' },
        'a',
        signal,
      ),
    ).rejects.toThrow();
    expect(
      (await service.act({ token, action: 'state' }, 'a', signal)).remaining,
    ).toBe(30);
    let complete!: (value: unknown) => void;
    agent.run.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          complete = resolve;
        }),
    );
    const pending = service.act(
      { token, action: 'question', text: '你是皇帝吗' },
      'a',
      signal,
    );
    await expect(
      service.act({ token, action: 'reveal' }, 'a', signal),
    ).rejects.toThrow('等待');
    complete({ verdict: 'unknown', claims: [] });
    await pending;
    await expect(
      service.act({ token: 'a'.repeat(64), action: 'state' }, 'a', signal),
    ).rejects.toThrow('过期');
    await expect(service.start({ difficulty: 8 }, 'a', signal)).rejects.toThrow(
      '检查',
    );
    await expect(
      service.start({ difficulty: 2, from: 900, to: 800 }, 'a', signal),
    ).rejects.toThrow('检查');
    await expect(
      service.act({ token, action: 'guess' }, 'a', signal),
    ).rejects.toThrow('格式');
  });
  it('never silently changes difficulty or accepts a model-selected ID outside the candidate pool', async () => {
    const { service, agent } = make();
    await expect(service.start({ difficulty: 1 }, 'a', signal)).rejects.toThrow(
      '没有符合',
    );
    agent.run.mockResolvedValueOnce({ ids: ['foreign'] });
    await expect(service.start(filters, 'a', signal)).rejects.toThrow('抽样');
  });
  it('only accepts anonymous published reads and requires a source snapshot before opening a round', async () => {
    const { service, rpc } = make();
    await service.start(filters, 'a', signal);
    expect(rpc).toHaveBeenCalledWith(
      'content_page',
      expect.objectContaining({
        p_table: 'fact_claim',
        p_admin: false,
        p_subject: 'person',
        p_subject_id: person.id,
      }),
    );
  });
  it('does not open a game without original-source evidence and expires active sessions', async () => {
    const missing = make();
    missing.rpc.mockImplementation(
      (name: string, args: { p_table: string }) => ({
        abortSignal: () =>
          Promise.resolve({
            data:
              name === 'content_page'
                ? {
                    items:
                      args.p_table === 'person'
                        ? [person]
                        : [{ ...claim, note: '没有原文的说明' }],
                    has_more: false,
                  }
                : null,
            error: null,
          }),
      }),
    );
    await expect(missing.service.start(filters, 'a', signal)).rejects.toThrow(
      '尚无可回溯原文',
    );
    const { service } = make();
    const { token } = await service.start(filters, 'a', signal);
    const now = jest.spyOn(Date, 'now').mockReturnValue(Date.now() + 3600001);
    try {
      await expect(
        service.act({ token, action: 'state' }, 'a', signal),
      ).rejects.toThrow('过期');
    } finally {
      now.mockRestore();
    }
  });
});
