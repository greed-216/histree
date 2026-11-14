import catalog from "../data/stories.json";

export interface StoryPanel {
  number: number;
  title: string;
  crop: { x: number; y: number; width: number; height: number };
  alt: string;
  caption: string;
}

export interface IllustratedStory {
  slug: string;
  title: string;
  description: string;
  readingMinutes: number;
  people: { name: string; id: string; aliases?: string[] }[];
  sourceLinks: { label: string; url: string }[];
  introduction: { title: string; text: string };
  afterword: {
    title: string;
    paragraphs: string[];
    takeaway: { title: string; text: string };
    sourceNote: string;
  };
  image: { url: string; width: number; height: number; sha256: string };
  panels: StoryPanel[];
}

export const stories: IllustratedStory[] = catalog.stories;
export const storyBySlug = (slug?: string) => stories.find((story) => story.slug === slug);
