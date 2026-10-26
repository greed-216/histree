import { RowDataPacket } from 'mysql2/promise';

import type { SqlWritePort } from './storage-port';
export class QuotaRepository {
  constructor(private readonly db: SqlWritePort) {}
  async consumeQuota(actor: string, operation: 'ask' | 'guess' | 'session') {
    if (
      !/^(anon:[a-f0-9]{64}|user:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$/.test(
        actor,
      ) ||
      !['ask', 'guess', 'session'].includes(operation)
    )
      throw new Error('Invalid quota scope');
    const connection = await this.db.connectionPool().getConnection();
    try {
      await connection.query(
        "SET SESSION time_zone='+00:00',innodb_lock_wait_timeout=5",
      );
      await connection.beginTransaction();
      const [time] = await connection.query<RowDataPacket[]>(
        "SELECT DATE_FORMAT(UTC_TIMESTAMP(),'%Y-%m-%d %H:00:00') bucket",
      );
      const bucket = time[0].bucket;
      const actorCap =
          operation === 'ask' ? 10 : operation === 'guess' ? 80 : 1,
        globalCap =
          operation === 'ask' ? 200 : operation === 'guess' ? 1600 : 1000;
      // Lock global then actor in a fixed order. A rejected actor rolls back both debits.
      for (const [scope, cap] of [
        ['global', globalCap],
        [actor, actorCap],
      ] as const) {
        await connection.execute(
          'INSERT INTO ai_gateway_quota(actor,operation,bucket,used) VALUES(?,?,?,0) ON DUPLICATE KEY UPDATE used=used',
          [scope, operation, bucket],
        );
        const [rows] = await connection.execute<RowDataPacket[]>(
          'SELECT used FROM ai_gateway_quota WHERE actor=? AND operation=? AND bucket=? FOR UPDATE',
          [scope, operation, bucket],
        );
        if (rows[0].used >= cap) {
          await connection.rollback();
          return false;
        }
        await connection.execute(
          'UPDATE ai_gateway_quota SET used=used+1 WHERE actor=? AND operation=? AND bucket=?',
          [scope, operation, bucket],
        );
      }
      await connection.execute(
        'DELETE FROM ai_gateway_quota WHERE bucket < DATE_SUB(?,INTERVAL 2 HOUR)',
        [bucket],
      );
      await connection.commit();
      return true;
    } catch (error) {
      await connection.rollback();
      throw error;
    } finally {
      connection.release();
    }
  }
}
