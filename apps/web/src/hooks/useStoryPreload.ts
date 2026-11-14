import { useEffect, useRef } from "react";
import type { StoryPanel } from "../lib/stories";
import { createStoryPreloader, storyPreloadUrls } from "../lib/story-preload";

function loadImage(url: string) {
  return new Promise<void>((resolve, reject) => {
    const image = new Image();
    image.fetchPriority = "low";
    image.onload = () => { image.onload = image.onerror = null; resolve(); };
    image.onerror = () => { image.onload = image.onerror = null; reject(new Error("Image preload failed")); };
    image.src = url;
  });
}

export function useStoryPreload(panels: readonly StoryPanel[], page: number) {
  const preloader = useRef<ReturnType<typeof createStoryPreloader> | null>(null);
  useEffect(() => {
    const instance = createStoryPreloader(loadImage, 2);
    preloader.current = instance;
    return () => { instance.dispose(); preloader.current = null; };
  }, [panels]);
  useEffect(() => { preloader.current?.warm(storyPreloadUrls(panels, page)); }, [panels, page]);
}
