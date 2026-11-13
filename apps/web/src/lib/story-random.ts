/** Select uniformly from the shelf, excluding the open story when another exists. */
export function pickRandomStory<T extends { slug: string }>(
  catalog: readonly T[], currentSlug?: string, random: () => number = Math.random,
): T | undefined {
  const alternatives = catalog.filter((story) => story.slug !== currentSlug);
  const candidates = alternatives.length ? alternatives : catalog;
  if (!candidates.length) return undefined;
  const value = random();
  // Clamp an injected generator's boundary values; Math.random itself is in [0, 1).
  const index = Math.min(candidates.length - 1, Math.max(0, Math.floor((Number.isFinite(value) ? value : 0) * candidates.length)));
  return candidates[index];
}
