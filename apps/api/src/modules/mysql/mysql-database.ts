import { OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createPool, Pool, RowDataPacket } from 'mysql2/promise';

import { integer, Row } from './query-contracts';
export class MysqlDatabase implements OnModuleDestroy {
  readonly enabled = true;
  private pool?: Pool;
  constructor(private readonly config: ConfigService) {
    const backend = config.get('HISTREE_DATABASE');
    if (backend && backend !== 'mysql')
      throw new Error('Only MySQL is supported');
  }
  connectionPool() {
    if (!this.enabled) throw new Error('MySQL is disabled');
    if (!this.pool) {
      for (const key of [
        'MYSQL_HOST',
        'MYSQL_DATABASE',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
      ])
        if (!this.config.get(key))
          throw new Error('MySQL configuration is incomplete');
      const mode = this.config.get<string>('MYSQL_SSL_MODE') || 'disabled';
      if (!['disabled', 'require', 'verify-full'].includes(mode))
        throw new Error('Invalid TLS mode');
      this.pool = createPool({
        host: this.config.get('MYSQL_HOST'),
        port: integer(this.config.get('MYSQL_PORT'), 3306, 1, 65535),
        database: this.config.get('MYSQL_DATABASE'),
        user: this.config.get('MYSQL_USER'),
        password: this.config.get('MYSQL_PASSWORD'),
        charset: 'utf8mb4',
        timezone: 'Z',
        dateStrings: true,
        decimalNumbers: true,
        connectionLimit: 6,
        maxIdle: 6,
        idleTimeout: 60000,
        waitForConnections: true,
        queueLimit: 30,
        connectTimeout: 10000,
        ...(mode !== 'disabled'
          ? { ssl: { rejectUnauthorized: mode === 'verify-full' } }
          : {}),
        multipleStatements: false,
      });
    }
    return this.pool;
  }
  async execute(
    sql: string,
    args: any[] = [],
    signal?: AbortSignal,
  ): Promise<{ affectedRows: number }> {
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin');
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      const [result] = await connection.execute(sql, args);
      signal?.throwIfAborted();
      return {
        affectedRows: Number(
          (result as { affectedRows?: number }).affectedRows || 0,
        ),
      };
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
  async rows(
    sql: string,
    args: any[] = [],
    signal?: AbortSignal,
  ): Promise<Row[]> {
    signal?.throwIfAborted();
    const connection = await this.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET NAMES utf8mb4 COLLATE utf8mb4_0900_bin');
      await connection.query(
        "SET SESSION time_zone='+00:00', max_execution_time=10000,group_concat_max_len=65536",
      );
      const [result] = await connection.execute<RowDataPacket[]>(sql, args);
      signal?.throwIfAborted();
      return result.map((r) =>
        Object.fromEntries(
          Object.entries(r).map(([k, v]) => [
            k,
            k === 'created_at' && typeof v === 'string'
              ? v.replace(' ', 'T') + '+00:00'
              : v,
          ]),
        ),
      );
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
  async onModuleDestroy() {
    await this.pool?.end();
  }
}
