import { BadRequestException, HttpException, Injectable, ServiceUnavailableException } from '@nestjs/common';
import { createHash } from 'node:crypto';
import { MysqlService, visible } from '../mysql/mysql.service';

export interface FeedbackRecord {
  id: string;
  claim_id: string | null;
  source_id: string | null;
  page_path: string;
  context_label: string;
  message: string;
  email: string | null;
  request_sha256: string;
}
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

@Injectable()
export class FeedbackService {
  private readonly attempts = new Map<string, { count: number; until: number }>();
  constructor(private readonly mysql: MysqlService) {}

  async submit(input: unknown, actor: string) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) throw new BadRequestException('请填写反馈内容。');
    const body = input as Record<string, unknown>;
    const text = (key: string, max: number, min = 0) => {
      const value = body[key];
      if (value == null && min === 0) return '';
      if (typeof value !== 'string' || value.trim().length < min || value.length > max) throw new BadRequestException('反馈内容或联系方式格式不正确。');
      return value.trim();
    };
    const id = text('id', 36, 36), message = text('message', 3000, 5);
    const email = text('email', 254), page = text('page_path', 1024, 1);
    const claimId = text('claim_id', 36), sourceId = text('source_id', 36);
    if (!uuid.test(id) || (claimId && !uuid.test(claimId)) || (sourceId && !uuid.test(sourceId))) throw new BadRequestException('反馈关联的内容无效。');
    if (!page.startsWith('/') || page.startsWith('//') || /[\s\\\u0000-\u001f]/.test(page)) throw new BadRequestException('反馈页面地址无效。');
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new BadRequestException('请填写有效的邮箱，或留空。');
    if (!this.mysql.enabled) throw new ServiceUnavailableException('反馈功能暂时无法使用，请稍后再试。');
    const now = Date.now();
    for (const [key, value] of this.attempts) if (value.until <= now) this.attempts.delete(key);
    // Bound anonymous public writes without storing visitor addresses in feedback records.
    const key = createHash('sha256').update(actor || 'unknown').digest('hex');
    const quota = this.attempts.get(key) || { count: 0, until: now + 3600000 };
    if (quota.count >= 10 || (!this.attempts.has(key) && this.attempts.size >= 4096)) throw new HttpException('提交较频繁，请稍后再试。', 429);
    quota.count++;
    this.attempts.set(key, quota);
    try {
      let source = sourceId || null, label = '网站反馈';
      if (claimId) {
        const rows = await this.mysql.rows(`SELECT c.claim_text,c.source_id FROM fact_claim c WHERE c.id=? AND ${visible('fact_claim', 'c')} LIMIT 1`, [claimId]);
        if (!rows[0] || (sourceId && rows[0].source_id !== sourceId)) throw new BadRequestException('对应的内容暂时无法反馈，请刷新页面。');
        source = rows[0].source_id || null;
        label = String(rows[0].claim_text).slice(0, 500);
      } else if (sourceId) {
        const rows = await this.mysql.rows(`SELECT s.title FROM source s WHERE s.id=? AND EXISTS(SELECT 1 FROM fact_claim c WHERE c.source_id=s.id AND ${visible('fact_claim', 'c')}) LIMIT 1`, [sourceId]);
        if (!rows[0]) throw new BadRequestException('对应的来源暂时无法反馈，请刷新页面。');
        label = String(rows[0].title).slice(0, 500);
      }
      const normalized = { claim_id: claimId || null, source_id: source, page_path: page, message, email: email || null };
      const request_sha256 = createHash('sha256').update(JSON.stringify(normalized)).digest('hex');
      await this.mysql.saveFeedback({ id, ...normalized, context_label: label, request_sha256 });
      return { received: true };
    } catch (error) {
      if (error instanceof HttpException) throw error;
      throw new ServiceUnavailableException('反馈未能保存，请稍后重试。');
    }
  }
}
