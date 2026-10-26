import { Injectable, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { ContentRepository } from './content-repository';
import { FeedbackRepository } from './feedback-repository';
import { GameRepository } from './game-repository';
import { GraphRepository } from './graph-repository';
import { MysqlDatabase } from './mysql-database';
import { MysqlQuery } from './mysql-query';
import { MysqlRequest, MysqlResult, Row, id, visible } from './query-contracts';
import { QuotaRepository } from './quota-repository';
import { RevisionCache } from './revision-cache';
import { SearchRepository } from './search-repository';
import { SourceRepository } from './source-repository';
import { StructureRepository } from './structure-repository';
import { TimelineRepository } from './timeline-repository';
export { tables, visible } from './query-contracts';
export type { MysqlRequest, MysqlResult, Row } from './query-contracts';
@Injectable()
export class MysqlService implements OnModuleDestroy {
  readonly cache = new RevisionCache(this);
  readonly structure = new StructureRepository(this);
  private readonly database: MysqlDatabase;
  private readonly feedbackRepository = new FeedbackRepository(this);
  private readonly gameRepository = new GameRepository(this);
  private readonly sourceRepository = new SourceRepository(this);
  private readonly quotaRepository = new QuotaRepository(this);
  private readonly contentRepository = new ContentRepository(this);
  private readonly graphRepository = new GraphRepository(this);
  private readonly searchRepository = new SearchRepository(this);
  private readonly timelineRepository = new TimelineRepository(this);
  constructor(config: ConfigService) {
    this.database = new MysqlDatabase(config);
  }
  get enabled() {
    return this.database.enabled;
  }
  connectionPool() {
    return this.database.connectionPool();
  }
  rows(...args: Parameters<MysqlDatabase['rows']>) {
    return this.database.rows(...args);
  }
  execute(...args: Parameters<MysqlDatabase['execute']>) {
    return this.database.execute(...args);
  }
  onModuleDestroy() {
    return this.database.onModuleDestroy();
  }
  saveFeedback(...args: Parameters<FeedbackRepository['saveFeedback']>) {
    return this.feedbackRepository.saveFeedback(...args);
  }
  seedGuessBank(...args: Parameters<GameRepository['seedGuessBank']>) {
    return this.gameRepository.seedGuessBank(...args);
  }
  rateGuessPerson(...args: Parameters<GameRepository['rateGuessPerson']>) {
    return this.gameRepository.rateGuessPerson(...args);
  }
  rateGuessClue(...args: Parameters<GameRepository['rateGuessClue']>) {
    return this.gameRepository.rateGuessClue(...args);
  }
  rateGuessCharacterQuestion(
    ...args: Parameters<GameRepository['rateGuessCharacterQuestion']>
  ) {
    return this.gameRepository.rateGuessCharacterQuestion(...args);
  }
  sourceText(...args: Parameters<SourceRepository['sourceText']>) {
    return this.sourceRepository.sourceText(...args);
  }
  resolveSourceText(
    ...args: Parameters<SourceRepository['resolveSourceText']>
  ) {
    return this.sourceRepository.resolveSourceText(...args);
  }
  consumeQuota(...args: Parameters<QuotaRepository['consumeQuota']>) {
    return this.quotaRepository.consumeQuota(...args);
  }
  entry(...args: Parameters<ContentRepository['entry']>) {
    return this.contentRepository.entry(...args);
  }
  labels(...args: Parameters<ContentRepository['labels']>) {
    return this.contentRepository.labels(...args);
  }
  content(...args: Parameters<ContentRepository['content']>) {
    return this.contentRepository.content(...args);
  }
  context(...args: Parameters<GraphRepository['context']>) {
    return this.graphRepository.context(...args);
  }
  graph(...args: Parameters<GraphRepository['graph']>) {
    return this.graphRepository.graph(...args);
  }
  search(...args: Parameters<SearchRepository['search']>) {
    return this.searchRepository.search(...args);
  }
  askSearch(...args: Parameters<SearchRepository['askSearch']>) {
    return this.searchRepository.askSearch(...args);
  }
  timeline(...args: Parameters<TimelineRepository['timeline']>) {
    return this.timelineRepository.timeline(...args);
  }
  getClient() {
    return this.client();
  }
  client() {
    return {
      from: (table: string) => new MysqlQuery(this, table),
      rpc: (name: string, args: Row = {}) =>
        this.operation((s) => this.rpc(name, args, s)),
    };
  }
  operation(run: (signal?: AbortSignal) => Promise<any>): MysqlRequest {
    let signal: AbortSignal | undefined;
    const request: MysqlRequest = {
      abortSignal: (s: AbortSignal) => {
        signal = s;
        return request;
      },
      then: <TResult1 = MysqlResult, TResult2 = never>(
        resolve?:
          | ((value: MysqlResult) => TResult1 | PromiseLike<TResult1>)
          | null,
        reject?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null,
      ) =>
        run(signal)
          .then((data) => ({ data, error: null }))
          .catch(() => ({ data: null, error: new Error('公开资料查询失败') }))
          .then(resolve, reject),
    };
    return request;
  }
  async rpc(name: string, a: Row, signal?: AbortSignal): Promise<any> {
    if (name === 'content_page') return this.content(a, signal);
    if (name === 'entry_detail') return this.entry(id(a.p_id), signal);
    if (name === 'topic_detail')
      return (
        (
          await this.rows(
            `SELECT r.* FROM topic r WHERE ${visible('topic')} AND id=?`,
            [id(a.p_id)],
            signal,
          )
        )[0] || null
      );
    if (name === 'entry_context') return this.context(a, signal);
    if (name === 'graph_slice') return this.graph(a, signal);
    if (name === 'search_entries') return this.search(a, signal);
    if (name === 'ask_search') return this.askSearch(a, signal);
    if (name === 'timeline_overview') return this.timeline(signal);
    throw new Error('Unsupported public query');
  }
}
