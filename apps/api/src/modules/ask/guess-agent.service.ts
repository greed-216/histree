import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { fork } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

@Injectable()
export class GuessAgentService {
  private active = 0;
  constructor(private readonly config: ConfigService) {}
  available() {
    return (
      this.config.get('HISTREE_ASK_ENABLED') === 'true' &&
      !!this.config.get('DEEPSEEK_API_KEY')
    );
  }
  async run(input: unknown, signal: AbortSignal): Promise<unknown> {
    if (!this.available())
      throw new ServiceUnavailableException('猜人物服务尚未开放。');
    if (this.active >= 2)
      throw new ServiceUnavailableException('当前游戏请求较多，请稍后再试。');
    this.active++;
    let directory: string | undefined;
    const combined = AbortSignal.any([signal, AbortSignal.timeout(120000)]);
    try {
      combined.throwIfAborted();
      directory = await mkdtemp(join(tmpdir(), 'histree-guess-'));
      return await new Promise((accept, reject) => {
        const child = fork(
          resolve(__dirname, '../../../dsh/guess-worker.mjs'),
          [],
          {
            detached: process.platform !== 'win32',
            stdio: ['ignore', 'ignore', 'ignore', 'ipc'],
            env: {
              PATH: process.env.PATH,
              HOME: directory,
              TMPDIR: directory,
              DSH_HOME: directory,
              HISTREE_MODEL:
                this.config.get<string>('HISTREE_MODEL') || 'deepseek-flash',
              DEEPSEEK_API_KEY: this.config.get<string>('DEEPSEEK_API_KEY'),
            },
          },
        );
        let result: unknown;
        let failure: Error | undefined;
        const kill = () => {
          try {
            if (process.platform !== 'win32' && child.pid)
              process.kill(-child.pid, 'SIGKILL');
            else child.kill('SIGKILL');
          } catch {
            /* exited */
          }
        };
        const abort = () => {
          failure = new Error('请求取消或超时');
          kill();
        };
        combined.addEventListener('abort', abort, { once: true });
        child.on('message', (message: { type: string; data?: unknown }) => {
          if (message.type === 'result') result = message.data;
          if (message.type === 'error') {
            failure = new Error('游戏 Agent 未完成');
            kill();
          }
        });
        child.once('error', (error) => {
          failure = error;
          kill();
        });
        child.once('close', () => {
          combined.removeEventListener('abort', abort);
          kill();
          if (failure || result === undefined)
            reject(failure || new Error('游戏 Agent 未完成'));
          else accept(result);
        });
        if (combined.aborted) abort();
        else child.send(JSON.parse(JSON.stringify(input)));
      });
    } catch {
      throw new ServiceUnavailableException('本次游戏请求未完成，请稍后重试。');
    } finally {
      this.active--;
      if (directory) await rm(directory, { recursive: true, force: true });
    }
  }
}
