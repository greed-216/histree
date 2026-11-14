import type { IllustratedStory } from "../lib/stories";

/** Editorially resolved names only; anonymous fable characters remain plain text. */
export function StoryText({ text, story }: { text: string; story: IllustratedStory }) {
  const names = story.people.flatMap(person => [person.name, ...(person.aliases ?? [])].map(name => ({ name, person })));
  names.sort((a, b) => b.name.length - a.name.length);
  const parts = [];
  let start = 0, cursor = 0;
  while (cursor < text.length) {
    const match = names.find(item => text.startsWith(item.name, cursor));
    if (!match) { cursor++; continue; }
    if (cursor > start) parts.push(text.slice(start, cursor));
    parts.push(<a key={cursor} className="story-person-link" href={`/people/${match.person.id}`} target="_blank" rel="noopener noreferrer" aria-label={`了解${match.person.name}（新标签页）`}>{match.name}</a>);
    cursor += match.name.length;
    start = cursor;
  }
  if (start < text.length) parts.push(text.slice(start));
  return <>{parts}</>;
}
