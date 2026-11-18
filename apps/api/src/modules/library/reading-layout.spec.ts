import { createHash } from 'node:crypto';
import {
  readingLayout,
  readingRow,
  readingSection,
  verifiedHeaders,
  verifiedTableContexts,
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
  it('binds Ming year carry-over to live original text and the correct section', () => {
    const ming = readingLayout('mingshi', '2f603db3d81e')!;
    const id = 'mingshi-2f603db3d81e-p018057';
    const source = {
      id,
      kind: 'table_row',
      content:
        '太祖洪武元年戊申\t中書令 時中書及都督府議倣元制，設中書令，太子為之。太祖曰：「吾子年未長，學未充，更事未多。所宜尊禮師傅，講習經傳，博通古今，識達機宜。他日軍國重務，皆令啟聞，何必作中書令乎？」遂不設。',
    };
    expect(readingRow(source, ming)?.calendar_year).toBe(1368);
    expect(
      verifiedTableContexts(ming, [id], [source], 'mingshi-2f603db3d81e-s0110')[
        id
      ],
    ).toBeDefined();
    expect(
      verifiedTableContexts(
        ming,
        [id],
        [{ ...source, content: 'changed' }],
        'mingshi-2f603db3d81e-s0110',
      ),
    ).toEqual({});
    expect(verifiedTableContexts(ming, [id], [source], 'other')).toEqual({});
    expect(readingLayout('mingshi', 'different')).toBeNull();
  });
  it('preserves seven-office positions after missing EPUB empty cells', () => {
    const ming = readingLayout('mingshi', '2f603db3d81e')!;
    const source = {
      id: 'mingshi-2f603db3d81e-p019148',
      kind: 'table_row',
      content:
        '李冕七月，侍郎試。十月為江西布政司試參政。\t趙本去年十一月任，以後無考。\t呂宗藝去年十一月任，以後無考。\t薛祥二月任。\t安然正月任，五月致仕。',
    };
    const row = readingRow(source, ming, 'mingshi-2f603db3d81e-s0112');
    expect(row).toMatchObject({ columns: 8, calendar_year: 1380 });
    expect(
      ming.tables[ming.paragraphs[source.id].table_id].rows[
        ming.paragraphs[source.id].row_index
      ].map((cell) => cell[0]),
    ).toEqual([3, 4, 5, 6, 7]);
    expect(
      readingRow(
        { ...source, content: source.content.replace('趙本', '趙某') },
        ming,
      ),
    ).toBeUndefined();
    expect(
      readingRow(source, ming, 'mingshi-2f603db3d81e-s0113'),
    ).toBeUndefined();
  });
});
