const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function pageNumber(value: unknown, fallback = 0, maximum = 100000) {
  if (value === undefined || value === null || value === "") return fallback;
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0 || number > maximum)
    throw new Error("Invalid page");
  return number;
}
export function contentRequest(path: string, admin = false) {
  const url = new URL(path, "https://histree.local");
  const query = url.searchParams;
  const table = url.pathname.split("/")[2];
  if (
    ![
      "person",
      "event",
      "nodes",
      "topic",
      "source",
      "fact_claim",
      "person_relationship",
      "person_event",
      "event_causality",
    ].includes(table)
  )
    throw new Error("Invalid table");
  const id = (key: string) => {
    const value = query.get(key);
    if (value && !uuid.test(value)) throw new Error(`Invalid ${key}`);
    return value || null;
  };
  const year = (key: string) => {
    const value = query.get(key);
    if (value === null || value === "") return null;
    const number = Number(value);
    if (!Number.isInteger(number) || Math.abs(number) > 10000)
      throw new Error("Invalid year");
    return number;
  };
  const from = year("from"),
    to = year("to"),
    q = query.get("q")?.trim() ?? "";
  if (q.length > 200 || (from !== null && to !== null && from > to))
    throw new Error("Invalid query");
  const ids = query.has("ids")
    ? (query.get("ids") || "").split(",").filter(Boolean)
    : null;
  if (ids && (ids.length > 200 || ids.some((value) => !uuid.test(value))))
    throw new Error("Invalid ids");
  const limit = pageNumber(query.get("limit"), 20, 50);
  if (limit < 1) throw new Error("Invalid limit");
  return {
    p_table: table,
    p_page: pageNumber(query.get("page")),
    p_limit: limit,
    p_query: q,
    p_admin: admin,
    p_ids: ids,
    p_topic: query.get("topic"),
    p_section: query.has("section") ? pageNumber(query.get("section")) : null,
    p_person: id("person"),
    p_from: from,
    p_to: to,
    p_subject: query.get("subject"),
    p_subject_id: id("subject_id"),
    p_source: id("source"),
    p_claim: id("claim"),
    p_node: id("node"),
  };
}
