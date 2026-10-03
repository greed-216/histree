import {
  BadRequestException,
  HttpException,
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { fork } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve, join } from 'node:path';
import { z } from 'zod';
import { SupabaseService } from '../supabase/supabase.service';

const bodySchema = z
  .object({
    question: z.string().trim().min(2).max(800),
    conversation: z
      .string()
      .regex(/^[a-f0-9]{64}$/)
      .optional(),
    context: z
      .object({ kind: z.enum(['person', 'event']), id: z.string().uuid() })
      .strict()
      .optional(),
  })
  .strict();
type AskBody = z.infer<typeof bodySchema>;
type Conversation = {
  owner: string;
  history: Array<{ question: string; answer: string }>;
  expires: number;
  busy: boolean;
};
type WorkerMessage = {
  type: string;
  message?: string;
  answer?: string;
  [key: string]: unknown;
};

@Injectable()
export class AskService {
  private readonly conversations = new Map<string, Conversation>();
  private readonly requests = new Map<
    string,
    { count: number; reset: number }
  >();
  private active = 0;
  constructor(
    private readonly config: ConfigService,
    _db: SupabaseService,
  ) {}

  status() {
    return {
      available:
        this.config.get('HISTREE_ASK_ENABLED') === 'true' &&
        !!this.config.get('DEEPSEEK_API_KEY'),
      scope: '已发布人物、事件、关系及其已录入史料引用',
      maxTurns: 6,
    };
  }

  reserve(body: unknown, actor: string) {
    if (!this.status().available)
      throw new ServiceUnavailableException(
        '史料问答尚未开放，请先使用普通搜索。',
      );
    const parsed = bodySchema.safeParse(body);
    if (!parsed.success)
      throw new BadRequestException('请输入 2–800 字的问题，或重新开始对话。');
    const now = Date.now();
    for (const [key, value] of this.conversations)
      if (!value.busy && value.expires < now) this.conversations.delete(key);
    for (const [key, value] of this.requests)
      if (value.reset < now) this.requests.delete(key);
    const existing = parsed.data.conversation;
    const conversation = existing
      ? this.conversations.get(existing)
      : undefined;
    if (existing && !conversation)
      throw new HttpException('对话已过期，请开始新对话。', 410);
    if (conversation && conversation.owner !== actor)
      throw new HttpException('无权访问此对话。', 403);
    if (conversation?.busy)
      throw new HttpException('请等待当前问题完成。', 409);
    if (conversation && conversation.history.length >= 6)
      throw new HttpException('本次对话已达 6 轮，请开始新对话。', 409);
    if (this.active >= 2)
      throw new HttpException('当前提问较多，请稍后再试。', 429);
    const quota = this.requests.get(actor) || {
      count: 0,
      reset: now + 3600000,
    };
    if (
      quota.count >= 10 ||
      (!this.requests.has(actor) && this.requests.size >= 2048) ||
      (!existing && this.conversations.size >= 1000)
    )
      throw new HttpException('已达到提问限额，请稍后再试。', 429);
    quota.count++;
    this.requests.set(actor, quota);
    const token = existing || randomBytes(32).toString('hex');
    const session = conversation || {
      owner: actor,
      history: [],
      expires: now + 1800000,
      busy: false,
    };
    session.busy = true;
    session.expires = now + 1800000;
    this.conversations.set(token, session);
    this.active++;
    return { input: parsed.data, token, session };
  }

  async run(
    ticket: { input: AskBody; token: string; session: Conversation },
    signal: AbortSignal,
    emit: (event: WorkerMessage) => void,
  ) {
    let directory: string | undefined;
    const deadline = AbortSignal.timeout(120000);
    const combined = AbortSignal.any([signal, deadline]);
    try {
      emit({ type: 'conversation', conversation: ticket.token });
      emit({ type: 'status', message: '正在准备已发布资料检索…' });
      combined.throwIfAborted();
      const url = this.config.get<string>('SUPABASE_URL');
      const anonKey = this.config.get<string>('SUPABASE_ANON_KEY');
      if (!url || !anonKey)
        throw new Error('Public query configuration is missing');
      const data = { mode: 'remote', url, anonKey };
      directory = await mkdtemp(join(tmpdir(), 'histree-ask-'));
      const snapshot = join(directory, 'published.json');
      const retrieved = join(directory, 'retrieved.txt');
      await writeFile(snapshot, JSON.stringify(data), { mode: 0o600 });
      await writeFile(retrieved, '', { mode: 0o600 });
      await writeFile(`${retrieved}.json`, '[]', { mode: 0o600 });
      const files = resolve(__dirname, '../../../dsh');
      const answer = await new Promise<WorkerMessage>((accept, reject) => {
        const child = fork(join(files, 'worker.mjs'), [], {
          detached: process.platform !== 'win32',
          stdio: ['ignore', 'ignore', 'inherit', 'ipc'],
          env: {
            PATH: process.env.PATH,
            HOME: directory,
            TMPDIR: directory,
            NODE_ENV: 'production',
            DSH_HOME: directory,
            HISTREE_SNAPSHOT: snapshot,
            HISTREE_RETRIEVED: retrieved,
            HISTREE_MODEL:
              this.config.get<string>('HISTREE_MODEL') || 'deepseek-flash',
            DEEPSEEK_API_KEY: this.config.get<string>('DEEPSEEK_API_KEY'),
          },
        });
        let result: WorkerMessage | undefined;
        let failure: Error | undefined;
        const kill = () => {
          try {
            if (process.platform !== 'win32' && child.pid)
              process.kill(-child.pid, 'SIGKILL');
            else child.kill('SIGKILL');
          } catch {
            /* Already exited. */
          }
        };
        const abort = () => {
          failure = new Error('请求已取消或超时');
          kill();
        };
        combined.addEventListener('abort', abort, { once: true });
        child.on('message', (message: WorkerMessage) => {
          if (message.type === 'status') emit(message);
          if (message.type === 'result') result = message;
          if (message.type === 'error') failure = new Error(message.message);
        });
        child.once('error', (error) => {
          failure = error;
          kill();
        });
        child.once('close', () => {
          combined.removeEventListener('abort', abort);
          kill(); // Reap any remaining descendants even if the worker exited early.
          if (failure || !result)
            reject(failure || new Error('问答服务未正常完成'));
          else accept(result);
        });
        if (combined.aborted) abort();
        else
          child.send({
            question: ticket.input.question,
            context: ticket.input.context,
            history: ticket.session.history,
          });
      });
      if (combined.aborted) return;
      ticket.session.history.push({
        question: ticket.input.question,
        answer: String(answer.answer),
      });
      ticket.session.expires = Date.now() + 1800000;
      emit(answer);
    } catch {
      if (!signal.aborted)
        emit({
          type: 'error',
          message: deadline.aborted
            ? '检索用时过长，已停止本次请求，请缩小问题范围后重试。'
            : '本次问答未能完成，请稍后重试。你仍可使用普通搜索查看资料。',
        });
    } finally {
      ticket.session.busy = false;
      this.active--;
      if (directory) await rm(directory, { recursive: true, force: true });
    }
  }
}
