import { LibraryService } from './library.service';
import type { MysqlService } from '../mysql/mysql.service';

describe('Library request boundaries', () => {
  function fixture(enabled = true) {
    const mysql = { enabled, rows: jest.fn().mockResolvedValue([]), sourceText: jest.fn().mockResolvedValue(null) };
    return { mysql, service: new LibraryService(mysql as unknown as MysqlService) };
  }
  it('rejects invalid search and paging before querying', async () => {
    const { service, mysql } = fixture();
    for (const args of [['字'], ['字'.repeat(81)], ['关键词', 'bad/../book'], ['关键词', undefined, '-1'], ['关键词', undefined, '1.5']]) await expect(service.search(args[0]!, args[1], args[2])).rejects.toMatchObject({ status: 400 });
    expect(mysql.rows).not.toHaveBeenCalled();
  });
  it('does not expose unknown books or mixed book-section paths', async () => {
    const { service } = fixture();
    await expect(service.book('missing-book')).rejects.toMatchObject({ status: 404 });
    await expect(service.section('shiji', 'other-book-s0001')).rejects.toMatchObject({ status: 404 });
  });
  it('keeps hidden sources and old schemas from producing a false book link', async () => {
    const { service, mysql } = fixture();
    expect(await service.sourceLocation('source')).toBeNull();
    expect(mysql.rows).not.toHaveBeenCalled();
    mysql.sourceText.mockResolvedValue({ archive_url: 'https://example.test/archive', content_sha256: 'test' } as never);
    mysql.rows.mockRejectedValue({ code: 'ER_NO_SUCH_TABLE' });
    expect(await service.sourceLocation('source')).toBeNull();
    mysql.rows.mockRejectedValue(new Error('database failure'));
    await expect(service.sourceLocation('source')).rejects.toThrow('database failure');
  });
  it('fails visibly when no reading backend is configured', async () => {
    await expect(fixture(false).service.books()).rejects.toMatchObject({ status: 503 });
  });
});
