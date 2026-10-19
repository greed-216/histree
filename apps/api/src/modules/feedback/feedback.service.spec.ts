import { FeedbackService } from './feedback.service';
import type { MysqlService } from '../mysql/mysql.service';
const id = '11111111-1111-4111-8111-111111111111';
const valid = { id, page_path: '/learn', message: '希望补充这一段的相关原文。' };

describe('Feedback submission', () => {
  function fixture(enabled = true) {
    const mysql = { enabled, rows: jest.fn(), saveFeedback: jest.fn().mockResolvedValue(undefined) };
    return { mysql, service: new FeedbackService(mysql as unknown as MysqlService) };
  }
  it('accepts anonymous feedback without email and only acknowledges a saved record', async () => {
    const { mysql, service } = fixture();
    expect(await service.submit(valid, 'reader')).toEqual({ received: true });
    expect(mysql.saveFeedback).toHaveBeenCalledWith(expect.objectContaining({ message: valid.message, email: null, context_label: '网站反馈' }));
    mysql.saveFeedback.mockRejectedValue(new Error('private database diagnostics'));
    await expect(service.submit(valid, 'reader')).rejects.toMatchObject({ status: 503 });
  });
  it('rejects invalid input before querying or writing', async () => {
    const { mysql, service } = fixture();
    for (const body of [null, [], { ...valid, email: 'invalid' }, { ...valid, message: '' }, { ...valid, page_path: '//external.example' }]) await expect(service.submit(body, 'reader')).rejects.toMatchObject({ status: 400 });
    expect(mysql.rows).not.toHaveBeenCalled();
    expect(mysql.saveFeedback).not.toHaveBeenCalled();
  });
  it('does not pretend success on an unconfigured backend', async () => {
    await expect(fixture(false).service.submit(valid, 'reader')).rejects.toMatchObject({ status: 503 });
  });
  it('rejects hidden claims and binds context to the published record', async () => {
    const { mysql, service } = fixture();
    mysql.rows.mockResolvedValueOnce([]);
    await expect(service.submit({ ...valid, claim_id: id }, 'reader')).rejects.toMatchObject({ status: 400 });
    mysql.rows.mockResolvedValueOnce([{ source_id: null, claim_text: '实际引用内容' }]);
    await service.submit({ ...valid, claim_id: id, context_label: '伪造标题' }, 'reader');
    expect(mysql.saveFeedback).toHaveBeenCalledWith(expect.objectContaining({ context_label: '实际引用内容', claim_id: id }));
  });
});
