import { GuessService } from './guess.service';
import { GuessAgentService } from './guess-agent.service';
import { SupabaseService } from '../supabase/supabase.service';
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
function make() {
  const agent = {
    available: jest.fn(() => true),
    run: jest.fn().mockResolvedValue({ ids: [person.id] }),
  };
  const rpc = jest.fn((name: string, args: { p_table: string }) => ({
    abortSignal: () =>
      Promise.resolve({
        data:
          name === 'entry_detail'
            ? { ...person, type: 'person' }
            : name === 'entry_context'
              ? { edges: [], nodes: [] }
              : {
                  items: args.p_table === 'person' ? [person] : [claim],
                  has_more: false,
                },
        error: null,
      }),
  }));
  const service = new GuessService(
    { getClient: () => ({ rpc }) } as unknown as SupabaseService,
    agent as unknown as GuessAgentService,
  );
  return { service, agent, rpc };
}
const signal = new AbortController().signal;
const filters = { difficulty: 2 };
describe('Guess game privacy and lifecycle', () => {
  it('refreshes the catalogue in the background before expiry and rebuilds screening for the new snapshot', async () => {
    jest.useFakeTimers();
    const { service, agent, rpc } = make();
    try {
      await service.start(filters, 'a', signal);
      service.onModuleInit();
      jest.advanceTimersByTime(240000);
      for (let i = 0; i < 20; i++) await Promise.resolve();
      await service.start(filters, 'a', signal);
      expect(agent.run).toHaveBeenCalledTimes(2);
      expect(
        rpc.mock.calls.filter(
          ([name, args]) =>
            name === 'content_page' && args.p_table === 'person',
        ),
      ).toHaveLength(2);
    } finally {
      service.onModuleDestroy();
      jest.useRealTimers();
    }
  });
  it('reuses candidate reads and screening but creates independent games with fresh evidence', async () => {
    const { service, agent, rpc } = make();
    const first = await service.start(filters, 'a', signal);
    const second = await service.start(filters, 'a', signal);
    expect(first.token).not.toBe(second.token);
    expect(second).not.toHaveProperty('person');
    expect(agent.run).toHaveBeenCalledTimes(1);
    expect(
      rpc.mock.calls.filter(
        ([name, args]) => name === 'content_page' && args.p_table === 'person',
      ),
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
    const { service, agent, rpc } = make();
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
      expect(agent.run).toHaveBeenCalledTimes(2);
      expect(
        rpc.mock.calls.filter(
          ([name, args]) =>
            name === 'content_page' && args.p_table === 'person',
        ),
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
  it('reads candidates beyond the first 1000 published people', async () => {
    const { service, rpc } = make();
    const original = rpc.getMockImplementation()!;
    rpc.mockImplementation((name, args) => {
      if (name === 'content_page' && args.p_table === 'person') {
        const page = (args as { p_page?: number }).p_page ?? 0;
        return {
          abortSignal: () =>
            Promise.resolve({
              data: { items: page === 20 ? [person] : [], has_more: page < 20 },
              error: null,
            }),
        };
      }
      return original(name, args);
    });
    const started = await service.start(filters, 'a', signal);
    expect(started.token).toMatch(/^[a-f0-9]{64}$/);
    expect(rpc).toHaveBeenCalledWith(
      'content_page',
      expect.objectContaining({
        p_table: 'person',
        p_page: 20,
        p_admin: false,
      }),
    );
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
      expect.objectContaining({ p_table: 'person', p_admin: false }),
    );
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
