/** Native year-context regression. Disposable loopback MySQL only. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import { createHash } from "node:crypto";
const require = createRequire(
  new URL("../apps/api/package.json", import.meta.url),
);
const { ConfigService } = require("@nestjs/config");
const { MysqlService } = require("./dist/modules/mysql/mysql.service.js");
const { LibraryService } = require("./dist/modules/library/library.service.js");
assert(["localhost", "127.0.0.1"].includes(process.env.MYSQL_HOST));
assert.match(process.env.MYSQL_DATABASE ?? "", /^histree_test_[a-z0-9_]+$/);
const db = new MysqlService(new ConfigService(process.env));
const service = new LibraryService(db);
const sha = (text) => createHash("sha256").update(text).digest("hex");
const volume = Number(process.env.MING_TABLE_VOLUME ?? 109);
assert([109, 110, 111, 112].includes(volume));
const layout = JSON.parse(
  await readFile(
    new URL(
      volume === 109
        ? "../apps/api/src/data/mingshi-reading-layout.json"
        : "../apps/api/src/data/mingshi-office-reading-layout.json",
      import.meta.url,
    ),
    "utf8",
  ),
);
const source = Array.from(
  await readFile(
    new URL(
      "../resources/originals/twenty-four-histories/24明史-EPUB全文.txt",
      import.meta.url,
    ),
    "utf8",
  ),
);
const rows = gunzipSync(
  await readFile(
    new URL(
      "../resources/derived/history-library/mingshi/paragraphs.jsonl.gz",
      import.meta.url,
    ),
  ),
)
  .toString()
  .trim()
  .split("\n")
  .map(JSON.parse)
  .filter(
    (p) =>
      p.volume_candidate === volume &&
      !p.flags.includes("editorial_navigation_heading"),
  );
const section = rows[0].section_id;
const asset = sha("native-mingshi-year-context-owned-fixture");
const tables = {
  library_book: "book_key",
  library_asset: "id",
  library_section: "id",
  library_paragraph: "id",
};
const baseline = {};
let owned = false;
try {
  for (const [table, key] of Object.entries(tables))
    baseline[table] = new Set(
      (await db.rows(`SELECT ${key} AS k FROM ${table}`)).map((r) => r.k),
    );
  assert(!baseline.library_book.has("mingshi"));
  assert(!baseline.library_asset.has(asset));
  assert(!baseline.library_section.has(section));
  assert(rows.every((p) => !baseline.library_paragraph.has(p.id)));
  owned = true;
  await db.execute(
    "INSERT INTO library_book VALUES('mingshi','明史隔离阅读夹具',?,0,1,?,?,JSON_OBJECT(),'available')",
    [layout.source_version, rows.length, sha("fixture")],
  );
  await db.execute(
    "INSERT INTO library_asset VALUES(?, 'synthetic-ming-context.txt', ?)",
    [asset, sha("fixture")],
  );
  await db.execute(
    "INSERT INTO library_section VALUES(?,'mingshi',0,'宰辅年表一',109,'volume',0,JSON_OBJECT())",
    [section],
  );
  for (const [ordinal, p] of rows.entries()) {
    const a = p.locator.char_start,
      b = p.locator.char_end,
      content = source.slice(a, b).join("");
    assert.equal(sha(content), p.locator.raw_excerpt_sha256);
    await db.execute(
      "INSERT INTO library_paragraph VALUES(?,?,?,?,?,?,?,?,?,?,JSON_ARRAY())",
      [
        p.id,
        "mingshi",
        section,
        ordinal,
        p.kind,
        content,
        sha(content),
        asset,
        a,
        b,
      ],
    );
  }
  const first = await service.section("mingshi", section);
  const sample = {
    109: ["p018062", 1368, 5],
    110: ["p018609", 1522, 2],
    111: ["p019148", 1380, 8],
    112: ["p019790", 1522, 8],
  }[volume];
  const sampleRow = first.paragraphs.find((p) =>
    p.id.endsWith(sample[0]),
  ).table_row;
  assert.equal(sampleRow.calendar_year, sample[1]);
  assert.equal(sampleRow.columns, sample[2]);
  const cut = Array.from(
    { length: Math.ceil(rows.length / 40) },
    (_, page) => page,
  ).find((page) => {
    const slice = rows.slice(page * 40, (page + 1) * 40);
    return slice.some((p) =>
      layout.paragraphs[p.id]?.context_cells?.some(
        (c) => !slice.some((q) => q.id === c.paragraph_id),
      ),
    );
  });
  assert(cut > 0);
  const page = await service.section("mingshi", section, { page: String(cut) });
  const dependent = page.paragraphs.find(
    (p) => p.table_row?.context_cells?.length,
  );
  assert(dependent);
  const owner = dependent.table_row.context_cells[0].paragraph_id;
  assert(page.table_contexts[owner]);
  assert.equal(
    sha(page.table_contexts[owner].content),
    layout.paragraphs[owner].content_sha256,
  );
  await db.execute(
    "UPDATE library_paragraph SET content='changed',content_sha256=? WHERE id=?",
    [sha("changed"), owner],
  );
  const changed = await service.section("mingshi", section, {
    page: String(cut),
  });
  assert(!changed.table_contexts[owner]);
  assert(!changed.paragraphs.find((p) => p.id === dependent.id).table_row);
  await db.execute(
    "UPDATE library_book SET source_version='different' WHERE book_key='mingshi'",
  );
  assert(
    (await service.section("mingshi", section)).paragraphs.every(
      (p) => !p.table_row,
    ),
  );
  console.log(
    JSON.stringify({
      native_mysql: true,
      book: "mingshi",
      volume,
      year_carry_over: true,
      edited_context_fails_closed: true,
      production_env_reads: 0,
    }),
  );
} finally {
  if (owned) {
    for (const p of rows)
      await db.execute("DELETE FROM library_paragraph WHERE id=?", [p.id]);
    await db.execute("DELETE FROM library_section WHERE id=?", [section]);
    await db.execute("DELETE FROM library_asset WHERE id=?", [asset]);
    await db.execute("DELETE FROM library_book WHERE book_key='mingshi'");
    for (const [table, key] of Object.entries(tables))
      assert.deepEqual(
        new Set(
          (await db.rows(`SELECT ${key} AS k FROM ${table}`)).map((r) => r.k),
        ),
        baseline[table],
      );
  }
  await db.onModuleDestroy();
}
