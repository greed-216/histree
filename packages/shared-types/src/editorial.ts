/** Evidence structure is additive: legacy note bytes remain authoritative. */
export type ReviewState = "recorded" | "deferred" | "unparsed";
export interface EvidenceStructure {
  quote: string;
  review: string;
  review_state: ReviewState;
  origin: "structured" | "legacy";
  related_claims?: Array<{
    related_claim_id: string;
    subject_table: string;
    subject_id: string;
    relation_kind: "corroborates" | "conflicts" | "identity_candidate";
    note: string;
  }>;
  location?: {
    book_key: string;
    section_id: string;
    paragraph_id: string;
    source_version?: string;
  };
}
export function legacyEvidence(note?: string | null): EvidenceStructure {
  const raw = note ?? "",
    marker = "；核对说明：",
    end = raw.indexOf(marker);
  if (!raw.startsWith("原文：") || end < 0)
    return {
      quote: "",
      review: raw,
      review_state: "unparsed",
      origin: "legacy",
    };
  const review = raw.slice(end + marker.length);
  return {
    quote: raw.slice(3, end),
    review,
    review_state: /待考|待核|存疑|未决|暂不归并/.test(review)
      ? "deferred"
      : "recorded",
    origin: "legacy",
  };
}
export interface PersonReading {
  summary: string;
  identity_notes: string[];
  review_state: "deferred" | "none";
}
export function personReading(description?: string | null): PersonReading {
  const text = description ?? "";
  // Split only explicit editorial clauses, never a negated historical action.
  const marker =
    /(?:未与[^。；]{0,80}(?:同名|强合|归并)|与前卷[^。；]{0,100}(?:同名|候选)|与[^，,。；]{0,100}(?:无明确桥|缺[^，,。；]{0,12}桥)[^，,。；]{0,20}(?:暂分|先分|分列)|未证[^，,。；]{0,80}同名[^，,。；]{0,20}|暂保候选|身份(?:尚)?待考|(?:同名|身份)[^。；]{0,60}(?:待核|存疑))/;
  const summary: string[] = [],
    identity_notes: string[] = [];
  for (const sentence of text.match(/[^。；]+[。；]?/g) ?? []) {
    const match = marker.exec(sentence);
    if (!match) {
      summary.push(sentence);
      continue;
    }
    let start = match.index;
    while (start > 0 && /[，,\s]/.test(sentence[start - 1])) start--;
    if (start) summary.push(sentence.slice(0, start) + "。");
    identity_notes.push(sentence.slice(match.index));
  }
  return {
    summary: summary.join(""),
    identity_notes,
    review_state: identity_notes.length ? "deferred" : "none",
  };
}
export type DatingPrecision =
  | "year"
  | "approximate"
  | "range"
  | "relative"
  | "era"
  | "unknown";
export interface EventDating {
  id: string;
  event_id: string;
  earliest_year: number | null;
  latest_year: number | null;
  precision: DatingPrecision;
  era_key?: string | null;
  basis: string;
  claim_id: string;
  review_state: "proposed" | "reviewed";
}
export function validateDating(value: EventDating) {
  if (
    [value.id, value.event_id, value.claim_id].some(
      (id) =>
        !/^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/i.test(
          id ?? "",
        ),
    )
  )
    throw new Error("Dating needs stable UUIDs");
  if (!value.basis?.trim() || !value.claim_id || !value.event_id)
    throw new Error("Dating requires traceable evidence");
  if (
    !["year", "approximate", "range", "relative", "era", "unknown"].includes(
      value.precision,
    )
  )
    throw new Error("Invalid dating precision");
  for (const year of [value.earliest_year, value.latest_year])
    if (
      year !== null &&
      (!Number.isInteger(year) || year === 0 || Math.abs(year) > 10000)
    )
      throw new Error("Invalid dating year");
  if (
    value.earliest_year !== null &&
    value.latest_year !== null &&
    value.earliest_year > value.latest_year
  )
    throw new Error("Reversed dating bounds");
  if (
    ["year", "range", "approximate"].includes(value.precision) &&
    (value.earliest_year === null || value.latest_year === null)
  )
    throw new Error("Dating interval needs both bounds");
  if (value.precision === "year" && value.earliest_year !== value.latest_year)
    throw new Error("Exact year needs equal bounds");
  if (
    value.precision === "unknown" &&
    (value.earliest_year !== null || value.latest_year !== null)
  )
    throw new Error("Unknown dating cannot assert bounds");
  if (value.precision === "era" && !value.era_key)
    throw new Error("Era dating needs an era");
  if (!["proposed", "reviewed"].includes(value.review_state))
    throw new Error("Invalid dating review state");
  return value;
}
export interface ReviewCoverage {
  book_key: string;
  source_version: string;
  volume: number;
  reviewed: number;
  published: number;
  no_new: number;
  deferred: number;
  audit_sha256: string;
}
export interface ReadingLink {
  paragraph_id: string;
  claim_id: string;
  subject_table: string;
  subject_id: string;
  label: string;
  claim_text: string;
}
