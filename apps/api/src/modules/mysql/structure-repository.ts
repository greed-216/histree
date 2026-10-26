import {
  legacyEvidence,
  personReading,
  type EvidenceStructure,
} from '@histree/shared-types';
import { createHash } from 'node:crypto';
import type { Row } from './query-contracts';
import { claimFingerprintSql, visible } from './query-contracts';
import type { SqlReadPort } from './storage-port';
export class StructureRepository {
  constructor(private readonly db: SqlReadPort) {}
  async optional(sql: string, args: unknown[] = []) {
    try {
      return await this.db.rows(sql, args);
    } catch (error) {
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE') return [];
      throw error;
    }
  }
  async enrich(items: Row[], kind: string): Promise<Row[]> {
    if (!items.length) return items;
    if (kind === 'person')
      return items.map((row) => ({
        ...row,
        reading: personReading(row.description),
      }));
    if (kind === 'event') {
      const datings = await this.optional(
        `SELECT d.id,d.event_id,d.earliest_year,d.latest_year,d.precision_kind AS \`precision\`,d.era_key,d.basis,d.claim_id,d.review_state
    FROM event_dating d JOIN fact_claim c ON c.id=d.claim_id JOIN source basis_source ON basis_source.id=c.source_id WHERE d.event_id IN (${items.map(() => '?').join(',')})
    AND d.review_state='reviewed' AND d.claim_sha256=${claimFingerprintSql('c', 'basis_source')} AND c.subject_table='event' AND c.subject_id=d.event_id AND ${visible('fact_claim', 'c')} ORDER BY d.id`,
        items.map((r) => r.id),
      );
      return items.map((row) => ({
        ...row,
        datings: datings.filter((d) => d.event_id === row.id),
      }));
    }
    if (kind !== 'fact_claim') return items;
    const data = await this.optional(
      `SELECT * FROM claim_structure WHERE claim_id IN (${items.map(() => '?').join(',')})`,
      items.map((r) => r.id),
    );
    const locations = await this.optional(
      `SELECT l.source_id,p.id paragraph_id,p.book_key,p.section_id,b.source_version FROM library_source_link l
   JOIN source s ON s.id=l.source_id JOIN source_text t ON t.source_id=s.id AND t.archive_url=s.url AND t.content_sha256=l.snapshot_sha256 AND t.archive_url_sha256=l.archive_url_sha256
   JOIN library_paragraph p ON p.id=l.paragraph_id JOIN library_book b ON b.book_key=p.book_key AND b.status='available'
   WHERE l.source_id IN (${items.map(() => '?').join(',')})`,
      items.map((r) => r.source_id ?? ''),
    );
    const relations = await this.optional(
      `SELECT cr.claim_id,owner_claim.subject_table owner_table,owner_claim.subject_id owner_id,other.id related_claim_id,other.subject_table,other.subject_id,cr.relation_kind,cr.note
      FROM claim_relation cr JOIN fact_claim owner_claim ON owner_claim.id=cr.claim_id JOIN source owner_source ON owner_source.id=owner_claim.source_id
      JOIN fact_claim other ON other.id=cr.related_claim_id JOIN source other_source ON other_source.id=other.source_id
      WHERE (cr.claim_id IN (${items.map(() => '?').join(',')}) OR cr.related_claim_id IN (${items.map(() => '?').join(',')})) AND cr.review_state='reviewed'
      AND cr.claim_sha256=${claimFingerprintSql('owner_claim', 'owner_source')} AND cr.related_sha256=${claimFingerprintSql('other', 'other_source')}
      AND ${visible('fact_claim', 'owner_claim')} AND ${visible('fact_claim', 'other')} ORDER BY cr.id`,
      [...items.map((row) => row.id), ...items.map((row) => row.id)],
    );
    return items.map((row) => {
      const stored = data.find(
        (s) =>
          s.claim_id === row.id &&
          s.note_sha256 ===
            createHash('sha256')
              .update(row.note ?? '')
              .digest('hex'),
      );
      const evidence: EvidenceStructure = stored
        ? {
            quote: stored.quote_text,
            review: stored.review_note,
            review_state: stored.review_state,
            origin: 'structured',
          }
        : legacyEvidence(row.note);
      const location = locations.find((l) => l.source_id === row.source_id);
      if (location)
        evidence.location = location as EvidenceStructure['location'];
      evidence.related_claims = relations.flatMap((r) =>
        r.claim_id === row.id
          ? [r]
          : r.related_claim_id === row.id
            ? [
                {
                  ...r,
                  related_claim_id: r.claim_id,
                  subject_table: r.owner_table,
                  subject_id: r.owner_id,
                },
              ]
            : [],
      ) as EvidenceStructure['related_claims'];
      return { ...row, evidence };
    });
  }
}
