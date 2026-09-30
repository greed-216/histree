/** One parser for API requests and the static site's anonymous Supabase path. */
export function exploreRequest(
  path: string,
): {
  name: "search_entries" | "graph_slice" | "entry_detail";
  args: Record<string, string | number | null>;
} | null {
  const url = new URL(path, "https://histree.local");
  const number = (
    key: string,
    fallback: number | null,
    min: number,
    max: number,
  ) => {
    const raw = url.searchParams.get(key);
    if (raw === null || raw === "") return fallback;
    const value = Number(raw);
    if (!Number.isInteger(value) || value < min || value > max)
      throw new Error(`Invalid ${key}`);
    return value;
  };
  if (url.pathname.startsWith("/entry/")) {
    const id = url.pathname.slice("/entry/".length);
    if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        id,
      )
    )
      throw new Error("Invalid entry");
    return { name: "entry_detail", args: { p_id: id } };
  }
  if (url.pathname === "/search") {
    const query = (url.searchParams.get("q") ?? "").trim();
    const kind = url.searchParams.get("kind") ?? "all";
    if (
      query.length > 200 ||
      !["all", "person", "event", "topic", "nodes"].includes(kind)
    )
      throw new Error("Invalid search parameters");
    return {
      name: "search_entries",
      args: {
        p_query: query,
        p_kind: kind,
        p_page: number("page", 0, 0, 100000),
        p_limit: number("limit", 20, 1, 50),
      },
    };
  }
  if (url.pathname.startsWith("/graph-slice/")) {
    const id = url.pathname.slice("/graph-slice/".length);
    const mode = url.searchParams.get("mode") ?? "people";
    const from = number("from", null, -10000, 10000),
      to = number("to", null, -10000, 10000);
    if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        id,
      ) ||
      !["people", "events"].includes(mode) ||
      (from !== null && to !== null && from > to)
    )
      throw new Error("Invalid graph parameters");
    return {
      name: "graph_slice",
      args: {
        p_id: id,
        p_mode: mode,
        p_depth: number("depth", 1, 1, 2),
        p_from: from,
        p_to: to,
      },
    };
  }
  return null;
}
