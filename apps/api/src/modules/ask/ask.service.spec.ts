import { AskService } from './ask.service';
import { ConfigService } from '@nestjs/config';
import { SupabaseService } from '../supabase/supabase.service';

describe('Ask admission', () => {
  const make = (enabled = true) => new AskService(new ConfigService({ HISTREE_ASK_ENABLED: String(enabled), DEEPSEEK_API_KEY: 'test' }), {} as SupabaseService);
  it('does not admit requests when disabled or malformed', () => {
    expect(() => make(false).reserve({ question: '你好' }, 'a')).toThrow();
    expect(() => make().reserve({ question: 'x'.repeat(801) }, 'a')).toThrow();
    expect(() => make().reserve({ question: '你好', context: { kind: 'person', id: '../private' } }, 'a')).toThrow();
  });
  it('issues unguessable conversation tokens and rejects unknown or concurrent sessions', () => {
    const service = make();
    const first = service.reserve({ question: '朱温是谁' }, 'a');
    const second = service.reserve({ question: '敬翔是谁' }, 'b');
    expect(first.token).toMatch(/^[a-f0-9]{64}$/);
    expect(first.token).not.toBe(second.token);
    expect(() => service.reserve({ question: '朱温是谁', conversation: first.token }, 'a')).toThrow('等待');
    expect(() => service.reserve({ question: '朱温是谁', conversation: 'a'.repeat(64) }, 'a')).toThrow('过期');
    expect(() => service.reserve({ question: '朱温是谁' }, 'c')).toThrow('较多');
  });
  it('bounds followup history and releases admission after cancellation', async () => {
    const service = make();
    const first = service.reserve({ question: '朱温是谁' }, 'a');
    // No database is supplied: failure must still release the slot and session lock.
    await service.run(first, AbortSignal.abort(), () => {});
    expect(first.session.busy).toBe(false);
    first.session.history = Array.from({ length: 6 }, () => ({ question: '问', answer: '答' }));
    expect(() => service.reserve({ question: '继续问', conversation: first.token }, 'a')).toThrow('6 轮');
    expect(() => service.reserve({ question: '重新问' }, 'b')).not.toThrow();
  });
});
