import type { Pool } from 'mysql2/promise';
import type { Row } from './query-contracts';
/** Domain queries know only the capabilities they consume, not Nest or the compatibility facade. */
export interface SqlReadPort {
  readonly enabled: boolean;
  rows(sql: string, args?: unknown[], signal?: AbortSignal): Promise<Row[]>;
}
export interface SqlWritePort extends SqlReadPort {
  connectionPool(): Pool;
  execute(
    sql: string,
    args?: unknown[],
    signal?: AbortSignal,
  ): Promise<{ affectedRows: number }>;
}
export interface StructurePort {
  optional(sql: string, args?: unknown[]): Promise<Row[]>;
  enrich(items: Row[], kind: string): Promise<Row[]>;
}
export interface CachePort {
  revision(): Promise<string>;
  read<T>(key: string, load: () => Promise<T>): Promise<T>;
}
export interface StructuredReadPort extends SqlReadPort {
  structure: StructurePort;
}
export interface EntryReadPort extends SqlReadPort {
  entry(id: string, signal?: AbortSignal): Promise<Row | null>;
}
export interface VersionedReadPort extends SqlReadPort {
  cache: CachePort;
}
export interface ReadModelPort extends StructuredReadPort, VersionedReadPort {}
