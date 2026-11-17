/** Local source fixture + actual LibraryService; no credentials or remote calls. */
import http from "node:http";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { createRequire } from "node:module";
import { resolve, extname } from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("..", import.meta.url));
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
const { LibraryService } = require("./dist/modules/library/library.service.js");
const raw = Array.from(
  await readFile(
    resolve(
      root,
      "resources/originals/twenty-four-histories/24明史-EPUB全文.txt",
    ),
    "utf8",
  ),
);
const corpus = gunzipSync(
  await readFile(
    resolve(
      root,
      "resources/derived/history-library/mingshi/paragraphs.jsonl.gz",
    ),
  ),
)
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse)
  .filter(
    (p) =>
      p.volume_candidate === 109 &&
      !p.flags.includes("editorial_navigation_heading"),
  );
const paragraphs = corpus.map((p, ordinal) => ({
  id: p.id,
  kind: p.kind,
  content: raw.slice(p.locator.char_start, p.locator.char_end).join(""),
  ordinal,
}));
const section = {
  id: corpus[0].section_id,
  title: "卷一百〇九 · 表第十 · 宰輔年表一",
  volume: 109,
  kind: "volume",
  has_issues: 0,
  sort_order: 0,
};
const book = {
  book_key: "mingshi",
  title: "明史",
  source_version: "2f603db3d81e",
  section_count: 1,
  paragraph_count: paragraphs.length,
};
const mysql = {
  enabled: true,
  structure: { optional: async () => [] },
  rows: async (sql, params = []) => {
    if (sql.includes("FROM library_book")) return [book];
    if (sql.includes("FROM library_section"))
      return sql.includes("sort_order<") || sql.includes("sort_order>")
        ? []
        : [section];
    if (sql.includes("SELECT ordinal FROM library_paragraph"))
      return paragraphs
        .filter((p) => p.id === params[0])
        .map((p) => ({ ordinal: p.ordinal }));
    if (sql.includes("COUNT(*) AS total"))
      return [
        { total: paragraphs.filter((p) => p.ordinal < params[1]).length },
      ];
    if (sql.includes("FROM library_paragraph") && sql.includes("id IN"))
      return paragraphs.filter((p) => params.slice(2).includes(p.id));
    if (sql.includes("FROM library_paragraph")) {
      const offset = Number(sql.match(/OFFSET (\d+)/)?.[1] || 0);
      return paragraphs.slice(offset, offset + 41);
    }
    return [];
  },
};
const service = new LibraryService(mysql);
const dist = resolve(root, "apps/web/dist");
const types = {
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
};
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://127.0.0.1");
    if (url.pathname.startsWith("/api/v1/")) {
      let result = { items: [] };
      if (url.pathname === "/api/v1/library") result = { items: [book] };
      else if (url.pathname === "/api/v1/library/mingshi")
        result = await service.book("mingshi");
      else if (url.pathname.includes("/sections/"))
        result = await service.section("mingshi", section.id, {
          page: url.searchParams.get("page") || undefined,
          paragraph: url.searchParams.get("paragraph") || undefined,
        });
      res.setHeader("Content-Type", "application/json");
      res.setHeader("X-Histree-Preview", "local-source-fixture");
      res.end(JSON.stringify(result));
      return;
    }
    const path = extname(url.pathname)
      ? resolve(dist, "." + url.pathname)
      : resolve(dist, "index.html");
    if (!path.startsWith(dist + "/")) throw Error("invalid path");
    res.setHeader(
      "Content-Type",
      path.endsWith("index.html")
        ? "text/html"
        : types[extname(path)] || "application/octet-stream",
    );
    res.end(await readFile(path));
  } catch (error) {
    res.statusCode = 500;
    res.end(String(error));
  }
});
server.listen(Number(process.env.PORT || 5199), "127.0.0.1", () =>
  console.log(
    "Ming table preview: http://127.0.0.1:" +
      (process.env.PORT || 5199) +
      "/library/mingshi/" +
      section.id,
  ),
);
