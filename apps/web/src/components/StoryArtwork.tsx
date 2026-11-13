import { useEffect, useId, useRef, useState } from "react";
import type { IllustratedStory, StoryPanel } from "../lib/stories";

/** Show an exact viewport of the approved sheet; the source artwork stays intact. */
export function StoryArtwork({ image, panel, lazy = false }: { image: IllustratedStory["image"]; panel: StoryPanel; lazy?: boolean }) {
  const titleId = useId();
  const clipId = useId();
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [ready, setReady] = useState(() => !lazy || typeof IntersectionObserver === "undefined");
  const artwork = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (ready || !artwork.current) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) { setReady(true); observer.disconnect(); }
    }, { rootMargin: "200px" });
    observer.observe(artwork.current);
    return () => observer.disconnect();
  }, [ready]);

  if (failed) return <div className="story-image-error" role="status">
    <p>图片暂时没能翻开。</p>
    <button type="button" onClick={(event) => { event.preventDefault(); event.stopPropagation(); setAttempt((value) => value + 1); setFailed(false); }}>再试一下</button>
  </div>;

  return <svg ref={artwork} className="story-artwork" width={panel.crop.width} height={panel.crop.height}
    viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
    preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby={titleId}>
    <title id={titleId}>{panel.alt}</title>
    <defs><clipPath id={clipId}><rect x={panel.crop.x} y={panel.crop.y} width={panel.crop.width} height={panel.crop.height} /></clipPath></defs>
    {ready && <image clipPath={`url(#${clipId})`} key={attempt} href={image.url} width={image.width} height={image.height}
      onError={() => setFailed(true)} />}
  </svg>;
}
