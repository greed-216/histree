import type { Event } from "@histree/shared-types";
import data from "../data/ancient-stories.json";

export type AncientStory = (typeof data.chapters)[number]["stories"][number];
export const ancientStoriesPath = `/catalog/event?ids=${data.chapters.flatMap((chapter) => chapter.stories.map((story) => story.event_id)).join(",")}&limit=50`;

export function ancientStoryChapter(id: string) {
  return data.chapters.find((chapter) => chapter.id === id);
}

/** The API supplies published records; the reviewed navigation supplies reading order only. */
export function ancientStoryEvents(id: string, events: Event[] = []) {
  const published = new Map(events.map((event) => [event.id, event]));
  return (ancientStoryChapter(id)?.stories ?? []).flatMap((story) => {
    const event = published.get(story.event_id);
    return event ? [{ ...story, event }] : [];
  });
}

export function ancientStorySource(story: AncientStory) {
  const source = story.source;
  return `/library/shiji/${source.section_id}?paragraph=${source.paragraph_id}&claim=${source.claim_id}#paragraph-${source.paragraph_id}`;
}
