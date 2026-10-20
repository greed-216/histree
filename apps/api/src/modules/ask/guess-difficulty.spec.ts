import { applyDifficultyRating } from './guess-difficulty';
describe('Shared difficulty consensus rule', () => {
  it('requires twelve votes and at least 75 percent contrary ratings', () => {
    expect(
      applyDifficultyRating('easy', { easy: 0, right: 0, hard: 10 }, 'hard')
        .moved,
    ).toBe(false);
    expect(
      applyDifficultyRating('easy', { easy: 0, right: 3, hard: 8 }, 'hard'),
    ).toEqual({
      moved: true,
      difficulty: 'hard',
      counts: { easy: 0, right: 0, hard: 0 },
    });
    expect(
      applyDifficultyRating('easy', { easy: 0, right: 4, hard: 7 }, 'hard')
        .moved,
    ).toBe(false);
  });
  it('also moves hard to easy, and does not mutate existing counters', () => {
    const previous = { easy: 11, right: 0, hard: 0 };
    expect(applyDifficultyRating('hard', previous, 'easy').difficulty).toBe(
      'easy',
    );
    expect(previous.easy).toBe(11);
    expect(applyDifficultyRating('easy', previous, 'right').moved).toBe(false);
  });
});
