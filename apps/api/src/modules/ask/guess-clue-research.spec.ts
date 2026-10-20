import {
  assessResearch,
  GuessClueResearch,
  UnsuitableGamePerson,
  type Research,
} from './guess-clue-research';
import { makeClueProfile } from './guess-clues';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { GuessClueStore } from './guess-clue-store';
import { GuessAgentService } from './guess-agent.service';
import { MysqlService } from '../mysql/mysql.service';
const person = {
  id: '11111111-1111-4111-8111-111111111111',
  canonical_person_id: '11111111-1111-4111-8111-111111111111',
  name: '合成甲',
  aliases: [],
  era: '唐',
  description: '合成测试人物',
  knowledge_revision: 1,
};
const profile = makeClueProfile(person),
  signal = () => AbortSignal.timeout(10000);
const quotes = [
  '合成甲生于某地，后来离开故乡。',
  '合成甲曾在地方担任官职。',
  '合成甲与一位著名诗人共事。',
  '合成甲参与了某次地方防守。',
  '合成甲留下描写山川的作品。',
  '合成甲的代表作品被后人传读。',
];
const texts = [
  '我出生于一处地方，后来离开家乡。',
  '我曾经担任过地方官职。',
  '我与一位知名诗人共同任职。',
  '我参与过一次地方的防守。',
  '我曾留下描写山川的作品。',
  '我的代表作品仍被后人传读。',
];
const research: Research = {
  complete: true,
  issues: [],
  sources: [
    {
      id: 'claim:one',
      title: '合成史料',
      location: '测试卷',
      text: quotes.join('\n'),
      identityLinked: true,
    },
  ],
};
const ready = {
  decision: 'ready',
  clues: texts.map((text, i) => ({
    text,
    angle: [
      'origin',
      'identity',
      'relationship',
      'experience',
      'work',
      'legacy',
    ][i],
    explanation: quotes[i],
    evidence: [{ sourceId: 'claim:one', quote: quotes[i] }],
  })),
};
const unsuitable = {
  decision: 'unsuitable',
  reason: '仅能确认一次短暂活动，缺少可辨认的六项事实。',
  identity: { sourceId: 'claim:one', quote: quotes[0] },
  facts: [{ sourceId: 'claim:one', quote: quotes[0] }],
};
function chain() {
  let cached: unknown;
  const store = {
    find: jest.fn(async () => cached || null),
    claim: jest.fn(async () => ({
      status: 'generating',
      lease_token: 'owned',
    })),
    complete: jest.fn(async (_p, _token, clues) => {
      cached = { status: 'ready', clues };
      return { affectedRows: 1 };
    }),
    disable: jest.fn(async () => ({ affectedRows: 2 })),
    fail: jest.fn(async () => {}),
  };
  // Capture the actual random lease token, rather than bypassing ownership.
  store.claim.mockImplementation(async (_p?: unknown, token?: string) => ({
    status: 'generating',
    lease_token: token || 'owned',
  }));
  const agent = {
    run: jest
      .fn<Promise<unknown>, unknown[]>()
      .mockResolvedValueOnce({ unavailable: true })
      .mockResolvedValueOnce(ready)
      .mockResolvedValueOnce(ready),
  };
  const db = { rows: jest.fn(async () => [person]) };
  const collect = { collect: jest.fn(async () => research) };
  const create = () =>
    new GuessClueSetsService(
      store as unknown as GuessClueStore,
      agent as unknown as GuessAgentService,
      db as unknown as MysqlService,
      collect as unknown as GuessClueResearch,
    );
  return { store, agent, db, collect, create };
}
describe('Six-clue preparation with actual source research', () => {
  it('keeps six clues and rejects invented quotes, wrong identity and incomplete surveys', () => {
    expect(assessResearch(ready, profile, research).decision).toBe('ready');
    expect(() =>
      assessResearch(
        {
          ...ready,
          clues: ready.clues.map((c) => ({ ...c, angle: 'experience' })),
        },
        profile,
        research,
      ),
    ).toThrow('同一角度');
    const invented = structuredClone(ready);
    invented.clues[0].evidence[0].quote = '不存在于原文的虚构引用';
    expect(() => assessResearch(invented, profile, research)).toThrow('引用');
    expect(() =>
      assessResearch(unsuitable, profile, { ...research, complete: false }),
    ).toThrow('覆盖');
    expect(() =>
      assessResearch(unsuitable, profile, {
        ...research,
        sources: research.sources.map((s) => ({ ...s, identityLinked: false })),
      }),
    ).toThrow('身份');
    expect(() =>
      assessResearch(
        {
          ...unsuitable,
          identity: { sourceId: 'claim:one', quote: quotes[0].slice(3) },
        },
        profile,
        research,
      ),
    ).toThrow('身份');
    expect(() =>
      assessResearch(
        { decision: 'uncertain', reason: '同名人物尚未分清' },
        profile,
        research,
      ),
    ).toThrow('待查');
    expect(() =>
      assessResearch(
        { ...ready, clues: ready.clues.slice(0, 5) },
        profile,
        research,
      ),
    ).toThrow('校验');
  });
  it('checks six distinct fact angles even when the initial generation succeeds', async () => {
    const m = chain();
    const checked = {
      clues: ready.clues.map(({ angle, text, explanation }) => ({
        angle,
        text,
        explanation,
      })),
    };
    m.agent.run
      .mockReset()
      .mockResolvedValueOnce({
        clues: checked.clues.map(({ text, explanation }) => ({
          text,
          explanation,
        })),
      })
      .mockResolvedValueOnce(checked);
    expect((await m.create().ensure(profile, signal())).length).toBe(6);
    expect(m.agent.run.mock.calls[1][0]).toMatchObject({ task: 'check_clues' });
    expect(m.collect.collect).not.toHaveBeenCalled();
    expect(m.store.complete.mock.calls[0][4]).toMatchObject({
      initialReview: checked,
    });
  });
  it('researches after an unavailable response, saves evidence, then reuses after restart without more model calls', async () => {
    const m = chain(),
      progress: string[] = [];
    expect(
      (await m.create().ensure(profile, signal(), (v) => progress.push(v)))
        .length,
    ).toBe(6);
    expect(m.collect.collect).toHaveBeenCalledTimes(1);
    expect(m.agent.run).toHaveBeenCalledTimes(3);
    expect(m.agent.run.mock.calls[1][0]).toMatchObject({
      task: 'research_clues',
      research,
    });
    expect(m.store.complete.mock.calls[0][4]).toMatchObject({
      stage: 'research',
      assessment: { decision: 'ready' },
    });
    expect(progress.join(' ')).toContain('补查');
    await m.create().ensure(profile, signal());
    expect(m.agent.run).toHaveBeenCalledTimes(3);
    expect(m.store.disable).not.toHaveBeenCalled();
  });
  it('only disables after a referenced insufficient-facts assessment and preserves an audit', async () => {
    const m = chain();
    m.agent.run
      .mockReset()
      .mockResolvedValueOnce({ unavailable: true })
      .mockResolvedValueOnce(unsuitable)
      .mockResolvedValueOnce(unsuitable);
    await expect(m.create().ensure(profile, signal())).rejects.toBeInstanceOf(
      UnsuitableGamePerson,
    );
    expect(m.store.disable.mock.calls[0][2]).toMatchObject({
      research,
      assessment: unsuitable,
    });
    expect(m.store.complete).not.toHaveBeenCalled();
  });
  it('independently reviews a six-line draft and can reject padding instead of saving it', async () => {
    const m = chain();
    m.agent.run
      .mockReset()
      .mockResolvedValueOnce({ unavailable: true })
      .mockResolvedValueOnce(ready)
      .mockResolvedValueOnce(unsuitable);
    await expect(m.create().ensure(profile, signal())).rejects.toBeInstanceOf(
      UnsuitableGamePerson,
    );
    expect(m.agent.run.mock.calls[2][0]).toMatchObject({
      task: 'review_clues',
      proposed: ready,
    });
    expect(m.store.disable.mock.calls[0][2]).toMatchObject({
      draftAssessment: ready,
      assessment: unsuitable,
      reviewed: true,
    });
    expect(m.store.complete).not.toHaveBeenCalled();
  });
  it('still independently reviews an invalid draft and saves only the repaired assessment', async () => {
    const m = chain();
    const invalid = { decision: 'ready', clues: [] };
    m.agent.run
      .mockReset()
      .mockResolvedValueOnce({ unavailable: true })
      .mockResolvedValueOnce(invalid)
      .mockResolvedValueOnce(ready);
    expect(await m.create().ensure(profile, signal())).toHaveLength(6);
    expect(m.agent.run.mock.calls[2][0]).toMatchObject({
      task: 'review_clues',
      proposed: invalid,
    });
    expect(m.store.complete.mock.calls[0][4]).toMatchObject({
      draftAssessment: invalid,
      draftValidationFailure: expect.any(String),
      assessment: ready,
    });
    expect(m.store.disable).not.toHaveBeenCalled();
  });
  it('does not disable on retrieval outage, uncertain identity, invalid output, transport failure or profile change', async () => {
    for (const failure of [
      'retrieval',
      'identity',
      'invalid',
      'transport',
      'updated',
    ]) {
      const m = chain();
      if (failure === 'retrieval')
        m.collect.collect.mockResolvedValue({
          ...research,
          sources: [],
          complete: false,
          issues: ['book_library_unavailable'],
        });
      if (failure === 'identity')
        m.agent.run
          .mockReset()
          .mockResolvedValueOnce({ unavailable: true })
          .mockResolvedValueOnce({
            ...unsuitable,
            identity: { sourceId: 'claim:one', quote: quotes[0].slice(3) },
          });
      if (failure === 'invalid')
        m.agent.run
          .mockReset()
          .mockResolvedValueOnce({ unavailable: true })
          .mockResolvedValueOnce({ decision: 'ready', clues: [] })
          .mockResolvedValueOnce({ decision: 'ready', clues: [] });
      if (failure === 'transport')
        m.agent.run
          .mockReset()
          .mockRejectedValue(new Error('provider unavailable'));
      if (failure === 'updated')
        m.db.rows.mockResolvedValue([{ ...person, knowledge_revision: 2 }]);
      await expect(m.create().ensure(profile, signal())).rejects.toThrow();
      expect(m.store.disable).not.toHaveBeenCalled();
      expect(m.store.complete).not.toHaveBeenCalled();
    }
  });
  it('reads unstructured book text as well as published claims and marks partial searches unsafe for disabling', async () => {
    const read = jest.fn().mockResolvedValue({
      data: {
        items: [
          { id: 'one', claim_text: quotes[0], note: '原文：' + quotes[0] },
        ],
        has_more: false,
      },
      error: null,
    });
    const db = {
      getClient: () => ({ rpc: () => ({ abortSignal: read }) }),
      rows: jest.fn(async () => [
        {
          id: 'paragraph',
          content: quotes.join('\n'),
          book_title: '合成史书',
          section_title: '卷一',
          book_key: 'test',
          section_id: 'one',
        },
      ]),
    };
    const result = await new GuessClueResearch(
      db as unknown as MysqlService,
    ).collect(profile, signal());
    expect(result.complete).toBe(true);
    expect(result.sources).toHaveLength(2);
    await new GuessClueResearch(db as unknown as MysqlService).collect(
      makeClueProfile({ ...person, aliases: ['王右军'] }),
      signal(),
    );
    expect(db.rows.mock.calls.at(-1)?.[1]).toEqual(
      expect.arrayContaining(['%王右军%']),
    );
    db.rows.mockRejectedValueOnce(new Error('table unavailable'));
    expect(
      (
        await new GuessClueResearch(db as unknown as MysqlService).collect(
          profile,
          signal(),
        )
      ).complete,
    ).toBe(false);
  });
});
