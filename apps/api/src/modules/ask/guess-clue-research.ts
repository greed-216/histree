import { Converter } from 'opencc-js';
import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { z } from 'zod';
import { MysqlService } from '../mysql/mysql.service';
import { validateClueSelection, type ClueProfile } from './guess-clues';

export type ResearchSource = {
  id: string;
  title: string;
  location: string;
  text: string;
  identityLinked: boolean;
};
export type Research = {
  sources: ResearchSource[];
  complete: boolean;
  issues: string[];
};
const toTraditional = Converter({ from: 'cn', to: 't' }) as (
  text: string,
) => string;
const toSimplified = Converter({ from: 't', to: 'cn' }) as (
  text: string,
) => string;
const angleSchema = z.enum([
  'era',
  'origin',
  'identity',
  'lifespan',
  'relationship',
  'experience',
  'work',
  'legacy',
]);
function validateAngles(clues: Array<{ angle: string }>) {
  const counts = new Map<string, number>();
  for (const clue of clues)
    counts.set(clue.angle, (counts.get(clue.angle) || 0) + 1);
  if (counts.size < 3 || [...counts.values()].some((count) => count > 2))
    throw new ServiceUnavailableException(
      '线索集中在同一角度，尚不能组成六条独立提示。',
    );
}
export function validateCheckedClues(raw: unknown, profile: ClueProfile) {
  const parsed = z
    .object({
      clues: z
        .array(
          z
            .object({
              angle: angleSchema,
              text: z.string(),
              explanation: z.string(),
            })
            .strict(),
        )
        .length(6),
    })
    .strict()
    .safeParse(raw);
  if (!parsed.success)
    throw new ServiceUnavailableException('初次线索复核未通过，需要补查。');
  validateAngles(parsed.data.clues);
  return validateClueSelection(
    {
      clues: parsed.data.clues.map(({ text, explanation }) => ({
        text,
        explanation,
      })),
    },
    profile,
  );
}
const reference = z
  .object({
    sourceId: z.string().max(150),
    quote: z.string().trim().min(4).max(500),
  })
  .strict();
const assessment = z.discriminatedUnion('decision', [
  z
    .object({
      decision: z.literal('ready'),
      clues: z
        .array(
          z
            .object({
              angle: angleSchema,
              text: z.string(),
              explanation: z.string(),
              evidence: z.array(reference).min(1).max(4),
            })
            .strict(),
        )
        .length(6),
    })
    .strict(),
  z
    .object({
      decision: z.literal('unsuitable'),
      reason: z.string().min(8).max(400),
      identity: reference,
      facts: z.array(reference).max(5),
    })
    .strict(),
  z
    .object({
      decision: z.literal('uncertain'),
      reason: z.string().min(1).max(400),
    })
    .strict(),
]);
export class UnsuitableGamePerson extends ServiceUnavailableException {
  constructor() {
    super('这位人物补查后仍缺少可辨认的六条事实，已退出两个模式的游戏题库。');
  }
}
export function assessResearch(
  raw: unknown,
  profile: ClueProfile,
  research: Research,
) {
  const parsed = assessment.safeParse(raw);
  if (!parsed.success)
    throw new ServiceUnavailableException('补查结果未通过校验，人物保留待查。');
  const cited = (ref: z.infer<typeof reference>) => {
    const source = research.sources.find((s) => s.id === ref.sourceId);
    if (!source || !source.text.includes(ref.quote))
      throw new ServiceUnavailableException('补查引用无法核对，人物保留待查。');
    return source;
  };
  const result = parsed.data;
  if (result.decision === 'ready') {
    validateAngles(result.clues);
    result.clues.forEach((c) => c.evidence.forEach(cited));
    return {
      decision: 'ready' as const,
      clues: validateClueSelection(
        {
          clues: result.clues.map(({ text, explanation }) => ({
            text,
            explanation,
          })),
        },
        profile,
      ),
      assessment: result,
    };
  }
  if (result.decision === 'unsuitable') {
    const source = cited(result.identity);
    const name = profile.person.name.replace(/[（(].*$/, '');
    if (
      !research.complete ||
      !source.identityLinked ||
      !toSimplified(result.identity.quote).includes(toSimplified(name))
    )
      throw new ServiceUnavailableException(
        '资料覆盖或人物身份尚未确认，人物保留待查。',
      );
    result.facts.forEach(cited);
    return { decision: 'unsuitable' as const, assessment: result };
  }
  throw new ServiceUnavailableException('补查尚不能确认人物资料，已保留待查。');
}

@Injectable()
export class GuessClueResearch {
  constructor(private readonly db: MysqlService) {}
  async collect(profile: ClueProfile, signal: AbortSignal): Promise<Research> {
    const sources: ResearchSource[] = [],
      issues: string[] = [];
    let complete = true;
    // Query the complete public book library, including text not yet turned into people/facts.
    const allNames = [
      ...new Set([
        profile.person.name.replace(/[（(].*$/, ''),
        ...(profile.person.aliases || []).filter(
          (n) => !/(?:帝|王|公|侯|皇后)$/.test(n),
        ),
      ]),
    ].filter((n) => n.length >= 2);
    const names = allNames.slice(0, 2);
    if (allNames.length > names.length) complete = false;
    if (profile.person.canonical_person_id) {
      try {
        const result = await this.db
          .getClient()
          .rpc('content_page', {
            p_table: 'fact_claim',
            p_subject: 'person',
            p_subject_id: profile.person.canonical_person_id,
            p_page: 0,
            p_limit: 50,
            p_admin: false,
          })
          .abortSignal(signal);
        if (result.error || !result.data) throw Error('claims');
        const data = result.data as {
          items: Array<{
            id: string;
            claim_text: string;
            note?: string;
            citation?: string;
            source?: { title?: string };
          }>;
          has_more?: boolean;
        };
        complete &&= !data.has_more;
        for (const row of data.items)
          if (row.note?.startsWith('原文：')) {
            if (`${row.claim_text}\n${row.note}`.length > 5000)
              complete = false;
            sources.push({
              id: `claim:${row.id}`,
              title: row.source?.title || '已发布人物出处',
              location: row.citation || row.id,
              text: `${row.claim_text}\n${row.note}`.slice(0, 5000),
              identityLinked: true,
            });
          }
      } catch {
        signal.throwIfAborted();
        complete = false;
        issues.push('published_evidence_unavailable');
      }
    }
    const variants = [
      ...new Set(
        names.flatMap((name) => [
          name,
          toTraditional(name),
          toSimplified(name),
        ]),
      ),
    ];
    if (variants.length) {
      try {
        const patterns = variants.map(
          (name) => '%' + name.replace(/[!%_]/g, (c) => '!' + c) + '%',
        );
        const rows = await this.db.rows(
          `SELECT /*+ MAX_EXECUTION_TIME(5000) */ p.id,p.content,p.book_key,p.section_id,b.title book_title,s.title section_title
          FROM library_paragraph p JOIN library_book b ON b.book_key=p.book_key AND b.status='available'
          JOIN library_section s ON s.id=p.section_id
          WHERE p.kind IN ('body','annotation','table_row') AND (${patterns.map(() => "p.content LIKE ? ESCAPE '!'").join(' OR ')}) LIMIT 31`,
          patterns,
          signal,
        );
        if (rows.length > 30) complete = false;
        for (const row of rows.slice(0, 30)) {
          const id = `library:${row.id}`;
          if (sources.some((s) => s.id === id)) continue;
          const full = String(row.content);
          if (full.length > 6000) complete = false;
          sources.push({
            id,
            title: String(row.book_title),
            location: `${row.book_key}/${row.section_id}/${row.id} · ${row.section_title}`,
            text: full.slice(0, 6000),
            identityLinked: false,
          });
        }
      } catch {
        signal.throwIfAborted();
        complete = false;
        issues.push('book_library_unavailable');
      }
    }
    // A direct published identity anchor prevents matching a same-named person in another era.
    // Library-only matches can produce clues, but can never automatically disable a person.
    const maxChars = 42000;
    let used = 0;
    const bounded = sources.filter((source) => {
      used += source.text.length;
      if (used > maxChars) {
        complete = false;
        return false;
      }
      return true;
    });
    if (!bounded.length) complete = false;
    return { sources: bounded, complete, issues };
  }
}
