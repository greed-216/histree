import type { GuessDifficulty, GuessRating } from './guess-bank';
export type DifficultyCounts = Record<GuessRating, number>;
export function applyDifficultyRating(
  difficulty: GuessDifficulty,
  previous: DifficultyCounts,
  rating: GuessRating,
) {
  const counts = { ...previous };
  counts[rating]++;
  const total = counts.easy + counts.right + counts.hard;
  const contrary = difficulty === 'easy' ? counts.hard : counts.easy;
  const moved = total >= 12 && contrary * 4 >= total * 3;
  return {
    moved,
    difficulty: moved
      ? ((difficulty === 'easy' ? 'hard' : 'easy') as GuessDifficulty)
      : difficulty,
    counts: moved ? { easy: 0, right: 0, hard: 0 } : counts,
  };
}
export type ClueFeedback = {
  person_id: string;
  revision: number;
  knowledge_revision: number;
  clue_revision: string;
  actor_hash: string;
  game_hash: string;
  rating: GuessRating;
  guesses: number;
  unlocked: number;
  outcome: 'won' | 'revealed' | 'limit';
};
export type ClueRatingResult = {
  rating: GuessRating;
  difficulty: GuessDifficulty;
  revision: number;
  moved: boolean;
};
