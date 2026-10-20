// Offline preparation only. Fresh SDK sessions preserve per-person and review isolation.
import { DeepSeekHarness } from '@deepseek-ai/dsh-sdk-client';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { guessPrompt, guessMaxTokens } from './guess-worker.mjs';
const allowed = new Set([
  'clues',
  'check_clues',
  'research_clues',
  'review_clues',
]);
export class PreparedClueAgent {
  slots = new Map();
  owned = new Set();
  closed = false;
  stats = {
    runtimeStarts: 0,
    requests: 0,
    active: 0,
    maxActive: 0,
    sessions: 0,
  };
  constructor(options = {}) {
    this.options = options;
  }
  available() {
    return (
      !this.closed &&
      this.options.enabled !== false &&
      !!(this.options.apiKey || process.env.DEEPSEEK_API_KEY)
    );
  }
  async create(task) {
    const directory = await mkdtemp(join(tmpdir(), 'histree-clue-batch-'));
    const slot = { task, directory, active: 0, uses: 0, retired: false };
    const env = {
      PATH: process.env.PATH,
      HOME: directory,
      TMPDIR: directory,
      DSH_HOME: directory,
      DEEPSEEK_API_KEY: this.options.apiKey || process.env.DEEPSEEK_API_KEY,
      DSH_SYSTEM_PROMPT: guessPrompt(task),
      ...(this.options.baseUrl
        ? { DEEPSEEK_BASE_URL: this.options.baseUrl }
        : {}),
    };
    slot.harness = new DeepSeekHarness({
      profile: 'sdk-minimal',
      patches: [fileURLToPath(new URL('./guess.patch.yml', import.meta.url))],
      cwd: directory,
      processCwd: directory,
      dshHome: directory,
      provider: 'deepseek-official',
      model:
        this.options.model || process.env.HISTREE_MODEL || 'deepseek-flash',
      maxTokens: guessMaxTokens(task),
      initializeTimeoutMs: 30000,
      env,
    });
    this.owned.add(slot);
    this.stats.runtimeStarts++;
    try {
      await slot.harness.start();
      return slot;
    } catch {
      await this.dispose(slot);
      throw new Error('批量模型运行环境未能启动');
    }
  }
  async acquire(task) {
    let promise = this.slots.get(task);
    if (!promise) {
      promise = this.create(task);
      this.slots.set(task, promise);
    }
    let slot;
    try {
      slot = await promise;
    } catch (error) {
      if (this.slots.get(task) === promise) this.slots.delete(task);
      throw error;
    }
    if (slot.retired || slot.uses >= (this.options.recycleAfter || 128)) {
      slot.retired = true;
      if (this.slots.get(task) === promise) this.slots.delete(task);
      if (!slot.active) await this.dispose(slot);
      return this.acquire(task);
    }
    return slot;
  }
  async dispose(slot) {
    if (slot.disposing) return slot.disposing;
    slot.retired = true;
    slot.disposing = (async () => {
      await slot.harness.close();
      await rm(slot.directory, { recursive: true, force: true });
      this.owned.delete(slot);
    })();
    return slot.disposing;
  }
  async run(input, signal) {
    signal.throwIfAborted();
    if (!this.available() || !allowed.has(input.task))
      throw new Error('批量线索任务不可用');
    const slot = await this.acquire(input.task);
    signal.throwIfAborted();
    slot.active++;
    slot.uses++;
    this.stats.requests++;
    this.stats.sessions++;
    this.stats.active++;
    this.stats.maxActive = Math.max(this.stats.maxActive, this.stats.active);
    // Closing a failed/aborted shared runtime rejects every owned activity; none can be saved silently.
    const abort = () => {
      void this.dispose(slot).catch(() => {});
    };
    signal.addEventListener('abort', abort, { once: true });
    try {
      const result = await slot.harness
        .run(`按系统规则执行以下任务数据：\n${JSON.stringify(input)}`)
        .catch(async (error) => {
          await this.dispose(slot);
          throw error;
        });
      signal.throwIfAborted();
      return JSON.parse(
        (result.finalResponse || '')
          .trim()
          .replace(/^```(?:json)?\s*/, '')
          .replace(/\s*```$/, ''),
      );
    } catch {
      if (signal.aborted) signal.throwIfAborted();
      throw new Error('批量模型未完成有效输出');
    } finally {
      signal.removeEventListener('abort', abort);
      slot.active--;
      this.stats.active--;
      if (slot.retired && !slot.active) await this.dispose(slot);
    }
  }
  metrics() {
    return { ...this.stats, runtimes: this.owned.size };
  }
  async close() {
    this.closed = true;
    await Promise.allSettled([...this.slots.values()]);
    const results = await Promise.allSettled(
      [...this.owned].map((slot) => this.dispose(slot)),
    );
    const failed = results.find((result) => result.status === 'rejected');
    if (failed) throw new Error('批量运行进程清理未完成');
  }
}
