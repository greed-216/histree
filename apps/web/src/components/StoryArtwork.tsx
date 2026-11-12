import { useId, useState } from "react";
import type { IllustratedStory, StoryPanel } from "../lib/stories";

/** Show an exact viewport of the approved sheet; the source artwork stays intact. */
export function StoryArtwork({ image, panel }: { image: IllustratedStory["image"]; panel: StoryPanel }) {
  const titleId = useId();
  const clipId = useId();
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  if (failed) return <div className="story-image-error" role="status">
    <p>图片暂时没能翻开。</p>
    <button type="button" onClick={(event) => { event.preventDefault(); event.stopPropagation(); setAttempt((value) => value + 1); setFailed(false); }}>再试一下</button>
  </div>;

  return <svg className="story-artwork" width="500" height="310"
    viewBox={`${panel.crop.x} ${panel.crop.y} ${panel.crop.width} ${panel.crop.height}`}
    preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby={titleId}>
    <title id={titleId}>{panel.alt}</title>
    <defs><clipPath id={clipId}><rect x={panel.crop.x} y={panel.crop.y} width={panel.crop.width} height={panel.crop.height} /></clipPath></defs>
    <image clipPath={`url(#${clipId})`} key={attempt} href={image.url} width={image.width} height={image.height}
      onError={() => setFailed(true)} />
  </svg>;
}
