import { createHash } from 'node:crypto';
import {
  readingLayout,
  readingRow,
  readingSection,
  verifiedHeaders,
} from './reading-layout';

const hash = (text: string) => createHash('sha256').update(text).digest('hex');

describe('Reading layout is independent of immutable text and evidence', () => {
  const data = readingLayout('shiji', '174f8dfa444c')!;
  const header = {
    id: 'shiji-174f8dfa444c-p002487',
    kind: 'table_row',
    content: '元前 \t紀年 \t大事紀。 \t相位。 \t將位。 \t御史大夫位。',
  };
  it('only decorates the bound book edition and section-volume pair', () => {
    expect(readingLayout('hanshu', '174f8dfa444c')).toBeNull();
    expect(readingLayout('shiji', 'new-edition')).toBeNull();
    expect(
      readingSection(
        { id: 'shiji-174f8dfa444c-s0014', volume: 13, title: '卷十三' },
        data,
      ),
    ).toMatchObject({
      title: '卷十三',
      display_title: '三代世表',
      division: 'biao',
    });
    expect(
      readingSection({ id: 'shiji-174f8dfa444c-s0014', volume: 14 }, data),
    ).not.toHaveProperty('display_title');
  });
  it('requires exact original bytes, kind and stable paragraph ID', () => {
    expect(hash(header.content)).toBe(
      data.paragraphs[header.id].content_sha256,
    );
    expect(readingRow(header, data)).toMatchObject({
      columns: 6,
      is_header: true,
    });
    expect(
      readingRow(
        { ...header, content: header.content.replace('相位', '將位') },
        data,
      ),
    ).toBeUndefined();
    expect(
      readingRow(
        { ...header, content: header.content.replaceAll('\t', ' ') },
        data,
      ),
    ).toBeUndefined();
    expect(readingRow({ ...header, kind: 'body' }, data)).toBeUndefined();
    expect(readingRow({ ...header, id: 'other' }, data)).toBeUndefined();
    expect(readingRow(header, data, 'other-section')).toBeUndefined();
  });
  it('never displays cached headers when the live original is missing or changed', () => {
    const id = data.paragraphs[header.id].table_id;
    expect(verifiedHeaders(data, [id], [header])[id]).toHaveLength(1);
    expect(verifiedHeaders(data, [id], [])).toEqual({});
    expect(
      verifiedHeaders(data, [id], [{ ...header, content: 'changed' }]),
    ).toEqual({});
  });
  it('keeps multi-paragraph physical rows and explicit merged columns', () => {
    const a = data.paragraphs['shiji-174f8dfa444c-p001413'];
    const b = data.paragraphs['shiji-174f8dfa444c-p001422'];
    expect([a.table_id, a.row_index]).toEqual([b.table_id, b.row_index]);
    expect(b.fragments[0][0]).toBe(15);
    expect(
      Object.values(data.tables).some((t) =>
        t.rows.some((row) => row.some((cell) => cell[1] > 1)),
      ),
    ).toBe(true);
  });
});
