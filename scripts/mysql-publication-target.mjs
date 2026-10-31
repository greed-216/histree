import assert from "node:assert/strict";
import { createHash } from "node:crypto";

/** Same host/port/schema JSON contract as MysqlContentStore; account guard stays separate. */
export function mysqlPublicationTargetFingerprint(env) {
  assert(typeof env.MYSQL_HOST === "string" && typeof env.MYSQL_DATABASE === "string");
  const rawPort = env.MYSQL_PORT ?? "3306";
  assert(/^\d+$/.test(String(rawPort)), "Invalid MySQL port");
  const port = Number(rawPort);
  assert(Number.isInteger(port) && port > 0 && port <= 65535, "Invalid MySQL port");
  const json = JSON.stringify([env.MYSQL_HOST, port, env.MYSQL_DATABASE])
    .replace(/[\u007f-\uffff]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
  return createHash("sha256").update(json).digest("hex");
}
