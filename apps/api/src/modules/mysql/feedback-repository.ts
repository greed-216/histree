import { ConflictException } from '@nestjs/common';
import type { FeedbackRecord } from '../feedback/feedback.service';

import type { SqlWritePort } from './storage-port';
export class FeedbackRepository {
  constructor(private readonly db: SqlWritePort) {}
  async saveFeedback(row: FeedbackRecord) {
    try {
      await this.db
        .connectionPool()
        .execute(
          'INSERT INTO feedback(id,claim_id,source_id,page_path,context_label,message,email,request_sha256) VALUES(?,?,?,?,?,?,?,?)',
          [
            row.id,
            row.claim_id,
            row.source_id,
            row.page_path,
            row.context_label,
            row.message,
            row.email,
            row.request_sha256,
          ],
        );
    } catch (error) {
      if ((error as { code?: string }).code !== 'ER_DUP_ENTRY') throw error;
      const existing = await this.db.rows(
        'SELECT request_sha256 FROM feedback WHERE id=?',
        [row.id],
      );
      if (existing[0]?.request_sha256 !== row.request_sha256)
        throw new ConflictException('这条反馈已提交，请关闭后重新填写。');
    }
  }
}
