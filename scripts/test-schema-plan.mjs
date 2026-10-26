import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { schemaFiles, schemaStatements } from "./mysql-schema.mjs";
assert.deepEqual(
  schemaStatements(
    "increment.sql",
    "-- comment; stays a comment\nCREATE TABLE x(note TEXT DEFAULT 'a;b');\n/* also; a comment */ INSERT INTO x VALUES('c;d');",
  ),
  ["CREATE TABLE x(note TEXT DEFAULT 'a;b')", "INSERT INTO x VALUES('c;d')"],
);
for (const file of schemaFiles) {
  const statements = schemaStatements(
    file,
    await readFile(new URL("../" + file, import.meta.url), "utf8"),
  );
  assert(statements.length > 0);
  assert(
    statements.every((s) => /^(CREATE|INSERT)/i.test(s)),
    file,
  );
}
console.log(
  "PASS: schema comments and quoted delimiters remain intact across the ordered manifest",
);
