import {
  BadRequestException,
  Injectable,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { createHash } from 'node:crypto';
import { MysqlService } from '../mysql/mysql.service';
import { visible } from '../mysql/query-contracts';
import {
  readingLayout,
  readingRow,
  readingSection,
  verifiedHeaders,
} from './reading-layout';

const key = (value: string) => {
  if (typeof value !== 'string' || !/^[a-z0-9][a-z0-9-]{0,127}$/.test(value))
    throw new BadRequestException('无效的史料地址');
  return value;
};
const pageIndex = (value: unknown) => {
  const n = Number(value || 0);
  if (!Number.isInteger(n) || n < 0 || n > 10000)
    throw new BadRequestException('无效的页码');
  return n;
};

@Injectable()
export class LibraryService {
  constructor(private readonly mysql: MysqlService) {}
  private async rows(sql: string, params: unknown[] = []) {
    if (!this.mysql.enabled)
      throw new ServiceUnavailableException('史料库暂时无法读取');
    return this.mysql.rows(sql, params);
  }
  async books() {
    return {
      items: await this.rows(
        "SELECT book_key,title,source_version,section_count,paragraph_count FROM library_book WHERE status='available' ORDER BY sort_order,book_key",
      ),
    };
  }
  async book(bookKey: string) {
    key(bookKey);
    const books = await this.rows(
      "SELECT book_key,title,source_version,section_count,paragraph_count FROM library_book WHERE book_key=? AND status='available'",
      [bookKey],
    );
    if (!books[0]) throw new NotFoundException('这部史书暂未收录');
    const sections = await this.rows(
      'SELECT id,title,volume,kind,has_issues FROM library_section WHERE book_key=? ORDER BY sort_order,id',
      [bookKey],
    );
    const coverage = await this.mysql.structure.optional(
      'SELECT c.* FROM library_review_coverage c JOIN library_book b ON b.book_key=c.book_key AND b.source_version=c.source_version WHERE c.book_key=? ORDER BY volume',
      [bookKey],
    );
    const layout = readingLayout(bookKey, books[0].source_version);
    return {
      book: { ...books[0], ...(layout ? { divisions: layout.divisions } : {}) },
      sections: sections.map((section) => readingSection(section, layout)),
      coverage,
    };
  }
  async section(
    bookKey: string,
    sectionId: string,
    options: { page?: string; paragraph?: string } = {},
  ) {
    key(bookKey);
    key(sectionId);
    let page = pageIndex(options.page);
    const books = await this.rows(
      "SELECT book_key,title,source_version FROM library_book WHERE book_key=? AND status='available'",
      [bookKey],
    );
    const sections = await this.rows(
      'SELECT id,title,volume,kind,has_issues,sort_order FROM library_section WHERE book_key=? AND id=?',
      [bookKey, sectionId],
    );
    if (!books[0] || !sections[0])
      throw new NotFoundException('这一卷章暂未收录');
    if (options.paragraph) {
      key(options.paragraph);
      const targets = await this.rows(
        'SELECT ordinal FROM library_paragraph WHERE id=? AND section_id=? AND book_key=?',
        [options.paragraph, sectionId, bookKey],
      );
      if (!targets[0]) throw new NotFoundException('这一段原文暂未收录');
      const before = await this.rows(
        'SELECT COUNT(*) AS total FROM library_paragraph WHERE section_id=? AND ordinal<?',
        [sectionId, targets[0].ordinal],
      );
      page = Math.floor(Number(before[0].total) / 40);
    }
    const paragraphs = await this.rows(
      `SELECT id,kind,content,ordinal FROM library_paragraph WHERE section_id=? ORDER BY ordinal LIMIT 41 OFFSET ${page * 40}`,
      [sectionId],
    );
    const previous = await this.rows(
      'SELECT id,title,volume FROM library_section WHERE book_key=? AND sort_order<? ORDER BY sort_order DESC LIMIT 1',
      [bookKey, sections[0].sort_order],
    );
    const next = await this.rows(
      'SELECT id,title,volume FROM library_section WHERE book_key=? AND sort_order>? ORDER BY sort_order LIMIT 1',
      [bookKey, sections[0].sort_order],
    );
    const reviews = await this.mysql.structure.optional(
      `SELECT * FROM library_paragraph_review WHERE paragraph_id IN (${paragraphs.map(() => '?').join(',') || 'NULL'})`,
      paragraphs.map((p) => p.id),
    );
    const layout = readingLayout(bookKey, books[0].source_version);
    const rowLayouts = new Map(
      paragraphs.slice(0, 40).map((p) => [p.id, readingRow(p, layout, sectionId)]),
    );
    const tableIds = [
      ...new Set(
        [...rowLayouts.values()]
          .map((row) => row?.table_id)
          .filter((id): id is string => Boolean(id)),
      ),
    ];
    const headerIds = layout
      ? [
          ...new Set(
            tableIds.flatMap((id) => layout.tables[id].header_paragraph_ids),
          ),
        ]
      : [];
    const headerRows = headerIds.length
      ? await this.rows(
          `SELECT id,kind,content,ordinal FROM library_paragraph WHERE book_key=? AND section_id=? AND id IN (${headerIds.map(() => '?').join(',')})`,
          [bookKey, sectionId, ...headerIds],
        )
      : [];
    const tableHeaders = layout
      ? verifiedHeaders(layout, tableIds, headerRows)
      : {};
    const reviewedParagraphs = paragraphs.slice(0, 40).map((p) => ({
      ...p,
      ...(rowLayouts.get(p.id) &&
      Object.hasOwn(tableHeaders, rowLayouts.get(p.id)!.table_id)
        ? { table_row: rowLayouts.get(p.id) }
        : {}),
      review:
        reviews.find(
          (r) =>
            r.paragraph_id === p.id &&
            r.content_sha256 ===
              createHash('sha256').update(String(p.content)).digest('hex'),
        ) ?? null,
    }));
    return {
      book: { ...books[0], ...(layout ? { divisions: layout.divisions } : {}) },
      section: readingSection(sections[0], layout),
      paragraphs: reviewedParagraphs,
      ...(tableIds.length ? { table_headers: tableHeaders } : {}),
      page,
      has_more: paragraphs.length > 40,
      previous: previous[0] ? readingSection(previous[0], layout) : null,
      next: next[0] ? readingSection(next[0], layout) : null,
    };
  }
  async search(query: string, bookKey?: string, pageValue?: string) {
    const q = query.trim();
    if (q.length < 2 || q.length > 80)
      throw new BadRequestException('请输入 2—80 个字进行检索');
    if (bookKey) key(bookKey);
    const page = pageIndex(pageValue);
    const pattern = '%' + q.replace(/[!%_]/g, (c) => '!' + c) + '%';
    // Literal substring semantics preserve original spellings, punctuation, % and _.
    // Scope/order indexes bound pagination; no unbounded COUNT or full text response.
    const rows = await this.rows(
      `SELECT p.id,p.book_key,p.section_id,p.content,b.title AS book_title,s.title AS section_title,s.volume
      FROM library_paragraph p JOIN library_book b ON b.book_key=p.book_key AND b.status='available'
      JOIN library_section s ON s.id=p.section_id
      WHERE p.kind IN ('body','annotation','table_row') AND p.content LIKE ? ESCAPE '!' ${bookKey ? 'AND p.book_key=?' : ''}
      ORDER BY b.sort_order,p.ordinal LIMIT 21 OFFSET ${page * 20}`,
      bookKey ? [pattern, bookKey] : [pattern],
    );
    return {
      query: q,
      page,
      has_more: rows.length > 20,
      items: rows.slice(0, 20).map((row) => {
        const content = String(row.content),
          index = content.indexOf(q),
          start = Math.max(0, index - 45);
        const { content: _content, ...location } = row;
        return {
          ...location,
          snippet:
            (start ? '…' : '') +
            content.slice(start, start + 180) +
            (content.length > start + 180 ? '…' : ''),
        };
      }),
    };
  }
  async links(
    bookKey: string,
    sectionId: string,
    paragraph: string,
    pageValue?: string,
  ) {
    key(bookKey);
    key(sectionId);
    key(paragraph);
    const page = pageIndex(pageValue);
    const rows = await this.rows(
      `SELECT c.id claim_id,c.subject_table,c.subject_id,c.claim_text,p.id paragraph_id,COALESCE(person.name,event.title,c.claim_text) label
      FROM library_paragraph p JOIN library_book b ON b.book_key=p.book_key AND b.status='available'
      JOIN library_source_link l ON l.paragraph_id=p.id
      JOIN source s ON s.id=l.source_id JOIN source_text st ON st.source_id=s.id AND st.archive_url=s.url AND st.archive_url_sha256=l.archive_url_sha256 AND st.content_sha256=l.snapshot_sha256
      JOIN fact_claim c ON c.source_id=s.id
      LEFT JOIN person ON c.subject_table='person' AND person.id=c.subject_id LEFT JOIN event ON c.subject_table='event' AND event.id=c.subject_id
      WHERE p.book_key=? AND p.section_id=? AND p.id=? AND ${visible('fact_claim', 'c')}
      ORDER BY c.id LIMIT 21 OFFSET ${page * 20}`,
      [bookKey, sectionId, paragraph],
    );
    return { items: rows.slice(0, 20), has_more: rows.length > 20 };
  }
  async sourceLocation(sourceId: string) {
    // The existing reader enforces public claim/endpoint visibility and current archive URL.
    const source = await this.mysql.sourceText(sourceId);
    if (!source) return null;
    try {
      const rows = await this.rows(
        `SELECT p.id AS paragraph_id,p.book_key,p.section_id FROM library_source_link l
        JOIN library_paragraph p ON p.id=l.paragraph_id JOIN library_book b ON b.book_key=p.book_key AND b.status='available'
        WHERE l.source_id=? AND l.archive_url_sha256=? AND l.snapshot_sha256=? LIMIT 1`,
        [
          sourceId,
          createHash('sha256').update(source.archive_url).digest('hex'),
          source.content_sha256,
        ],
      );
      return rows[0] || null;
    } catch (error) {
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return null;
      throw error;
    }
  }
}
