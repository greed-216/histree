import type { Person, Event } from "@histree/shared-types";
export type Entry = Person | Event;
export const entryTitle = (n: Entry) =>
  n.type === "person" ? n.name : n.title;
export const entryPath = (n: Entry) =>
  `/${n.type === "person" ? "people" : "events"}/${n.id}`;
export function safeUrl(url?: string) {
  return url && /^https?:\/\//i.test(url) ? url : undefined;
}
