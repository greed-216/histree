import { BadRequestException } from '@nestjs/common';
import { createHash } from 'node:crypto';

import { uuid, visible } from './query-contracts';
import type { SqlReadPort } from './storage-port';
export class SourceRepository {
  constructor(private readonly db: SqlReadPort) {}
  async sourceText(sourceId: string) {
    if (!uuid.test(sourceId)) throw new BadRequestException('无效的来源地址');
    if (!this.db.enabled) return null;
    try {
      const rows = await this.db.rows(
        `SELECT t.source_id,t.archive_url,t.content,t.content_sha256 FROM source_text t
         JOIN source s ON s.id=t.source_id AND s.url=t.archive_url
         WHERE t.source_id=? AND EXISTS(SELECT 1 FROM fact_claim c WHERE c.source_id=s.id AND ${visible('fact_claim', 'c')}) LIMIT 1`,
        [sourceId],
      );
      return rows[0] || null;
    } catch (error) {
      // An older database can serve the rest of the source page before this migration.
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return null;
      throw error;
    }
  }
  async resolveSourceText(archive: string) {
    if (
      !/^https:\/\/github\.com\/greed-216\/histree\/blob\/[a-f0-9]{7,40}\/(?:content|resources\/(?:derived|originals))\/.+\.(?:txt|jsonl)(?:#L[1-9]\d*(?:-L[1-9]\d*)?)?$/.test(
        archive,
      ) ||
      archive.length > 2048
    )
      throw new BadRequestException('无效的存档地址');
    if (!this.db.enabled) return null;
    try {
      const rows = await this.db.rows(
        `SELECT t.source_id FROM source_text t JOIN source s ON s.id=t.source_id AND s.url=t.archive_url
         WHERE t.archive_url_sha256=? AND t.archive_url=? AND EXISTS(SELECT 1 FROM fact_claim c WHERE c.source_id=s.id AND ${visible('fact_claim', 'c')}) ORDER BY t.source_id LIMIT 1`,
        [createHash('sha256').update(archive).digest('hex'), archive],
      );
      return rows[0] || null;
    } catch (error) {
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return null;
      throw error;
    }
  }
}
