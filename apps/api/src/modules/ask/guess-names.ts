import { guessIdentityVariants } from './guess-identity';
import type { GuessPerson as Person } from './guess-catalogue';
export function normalizeGuess(text: string) {
  return text
    .normalize('NFKC')
    .replace(/[\s·・，。！？?!]/g, '')
    .toLocaleLowerCase();
}
// Registered identities and user-confirmed common forms; never infer a win from a substring.
export function guessNames(person: Person) {
  const common: Record<string, string[]> = {
    李存勖: ['李亚子'],
    李白: ['李太白'],
  };
  return [
    person.name,
    ...guessIdentityVariants(person.name),
    ...(person.aliases || []),
    person.courtesy_name,
    ...(common[person.name] || []),
  ].filter((name): name is string => !!name);
}
export function directGuess(text: string) {
  const value = normalizeGuess(text);
  // Only anchored affirmative guess forms. A name inside a fact question or a negation cannot win.
  const match = value.match(
    /^(?:(?:我猜|我觉得|我认为|答案)(?:是)?|你是不是|你是|你叫|是不是|会不会是|应该是|是)?(.+?)(?:吗|么|吧|对吗)?$/u,
  );
  return match?.[1] || value;
}
