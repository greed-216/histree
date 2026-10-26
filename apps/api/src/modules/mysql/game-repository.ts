import { BadRequestException } from '@nestjs/common';
import { RowDataPacket } from 'mysql2/promise';
import type {
  BankFeedback,
  BankRatingResult,
  BankRow,
  BankSeed,
} from '../ask/guess-bank';
import {
  applyDifficultyRating,
  type ClueFeedback,
  type ClueRatingResult,
} from '../ask/guess-difficulty';

import { uuid } from './query-contracts';
import type { SqlWritePort } from './storage-port';
export class GameRepository {
  constructor(private readonly db: SqlWritePort) {}
  async seedGuessBank(seeds: BankSeed[], signal?: AbortSignal) {
    for (let offset = 0; offset < seeds.length; offset += 500) {
      signal?.throwIfAborted();
      const batch = seeds.slice(offset, offset + 500);
      if (
        batch.some(
          (seed) =>
            !uuid.test(seed.person_id) ||
            !['easy', 'hard'].includes(seed.difficulty),
        )
      )
        throw new BadRequestException('无效的游戏题库');
      const connection = await this.db.connectionPool().getConnection();
      const abort = () => connection.destroy();
      try {
        signal?.throwIfAborted();
        signal?.addEventListener('abort', abort, { once: true });
        await connection.execute(
          `INSERT INTO guess_bank(person_id,difficulty) VALUES ${batch.map(() => '(?,?)').join(',')} ON DUPLICATE KEY UPDATE person_id=person_id`,
          batch.flatMap((seed) => [seed.person_id, seed.difficulty]),
        );
        signal?.throwIfAborted();
      } finally {
        signal?.removeEventListener('abort', abort);
        connection.release();
      }
    }
  }
  async rateGuessPerson(
    input: BankFeedback,
    signal?: AbortSignal,
  ): Promise<BankRatingResult> {
    if (
      !uuid.test(input.person_id) ||
      !Number.isSafeInteger(input.revision) ||
      input.revision < 1 ||
      !/^[a-f0-9]{64}$/.test(input.actor_hash) ||
      !/^[a-f0-9]{64}$/.test(input.game_hash) ||
      !['easy', 'right', 'hard'].includes(input.rating) ||
      !Number.isInteger(input.turns) ||
      input.turns < 1 ||
      input.turns > 30 ||
      !Number.isInteger(input.hints) ||
      input.hints < 0 ||
      input.hints > 3
    )
      throw new BadRequestException('无效的难度反馈');
    signal?.throwIfAborted();
    const connection = await this.db.connectionPool().getConnection();
    const abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      await connection.beginTransaction();
      const [rows] = await connection.execute<RowDataPacket[]>(
        'SELECT person_id,difficulty,revision,easy_votes,right_votes,hard_votes FROM guess_bank WHERE person_id=? FOR UPDATE',
        [input.person_id],
      );
      const row = rows[0] as BankRow & {
        easy_votes: number;
        right_votes: number;
        hard_votes: number;
      };
      if (!row) throw new BadRequestException('对应人物暂时无法反馈');
      // The bank row lock serializes deduplication and counter updates per person.
      const [existing] = await connection.execute<RowDataPacket[]>(
        'SELECT rating FROM guess_difficulty_feedback WHERE game_hash=? OR (person_id=? AND revision=? AND actor_hash=?) LIMIT 1',
        [input.game_hash, input.person_id, input.revision, input.actor_hash],
      );
      if (existing.length) {
        await connection.commit();
        return {
          person_id: row.person_id,
          difficulty: row.difficulty,
          revision: row.revision,
          rating: existing[0].rating as BankRatingResult['rating'],
          moved: false,
        };
      }
      await connection.execute(
        'INSERT INTO guess_difficulty_feedback(game_hash,person_id,revision,actor_hash,rating,turns,hints) VALUES(?,?,?,?,?,?,?)',
        [
          input.game_hash,
          input.person_id,
          input.revision,
          input.actor_hash,
          input.rating,
          input.turns,
          input.hints,
        ],
      );
      let moved = false;
      // Late feedback is retained but cannot vote in a newer classification round.
      if (row.revision === input.revision) {
        const change = applyDifficultyRating(
          row.difficulty,
          {
            easy: row.easy_votes,
            right: row.right_votes,
            hard: row.hard_votes,
          },
          input.rating,
        );
        const counts = change.counts;
        moved = change.moved;
        row.difficulty = change.difficulty;
        if (moved) row.revision++;
        await connection.execute(
          'UPDATE guess_bank SET difficulty=?,revision=?,easy_votes=?,right_votes=?,hard_votes=? WHERE person_id=?',
          [
            row.difficulty,
            row.revision,
            moved ? 0 : counts.easy,
            moved ? 0 : counts.right,
            moved ? 0 : counts.hard,
            input.person_id,
          ],
        );
      }
      signal?.throwIfAborted();
      await connection.commit();
      return {
        person_id: row.person_id,
        difficulty: row.difficulty,
        revision: row.revision,
        rating: input.rating,
        moved,
      };
    } catch (error) {
      await connection.rollback().catch(() => {});
      throw error;
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
  rateGuessClue(
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    return this.rateGameCharacter('clue', input, signal);
  }
  rateGuessCharacterQuestion(
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    return this.rateGameCharacter('question', input, signal);
  }
  private async rateGameCharacter(
    mode: 'clue' | 'question',
    input: ClueFeedback,
    signal?: AbortSignal,
  ): Promise<ClueRatingResult> {
    if (
      !uuid.test(input.person_id) ||
      ![input.actor_hash, input.game_hash, input.clue_revision].every((v) =>
        /^[a-f0-9]{64}$/.test(v),
      ) ||
      !['easy', 'right', 'hard'].includes(input.rating) ||
      !['won', 'revealed', ...(mode === 'question' ? ['limit'] : [])].includes(
        input.outcome,
      ) ||
      !Number.isInteger(input.revision) ||
      input.revision < 1 ||
      !Number.isInteger(input.knowledge_revision) ||
      input.knowledge_revision < 1 ||
      !Number.isInteger(input.guesses) ||
      input.guesses < 0 ||
      input.guesses > 80 ||
      !Number.isInteger(input.unlocked) ||
      input.unlocked < 1 ||
      input.unlocked > 6 ||
      (input.guesses === 0 && input.unlocked === 1)
    )
      throw new BadRequestException('无效的难度反馈');
    const table =
      mode === 'clue' ? 'guess_clue_feedback' : 'guess_question_feedback';
    const columns =
      mode === 'clue'
        ? {
            difficulty: 'difficulty',
            revision: 'difficulty_revision',
            scope: 'vote_clue_revision',
            easy: 'easy_votes',
            right: 'right_votes',
            hard: 'hard_votes',
          }
        : {
            difficulty: 'question_difficulty',
            revision: 'question_revision',
            scope: 'question_vote_clue_revision',
            easy: 'question_easy_votes',
            right: 'question_right_votes',
            hard: 'question_hard_votes',
          };
    signal?.throwIfAborted();
    const connection = await this.db.connectionPool().getConnection(),
      abort = () => connection.destroy();
    try {
      signal?.throwIfAborted();
      signal?.addEventListener('abort', abort, { once: true });
      await connection.query('SET SESSION innodb_lock_wait_timeout=5');
      await connection.beginTransaction();
      const [rows] = await connection.execute<RowDataPacket[]>(
        `SELECT id,${columns.difficulty} difficulty,${columns.revision} difficulty_revision,knowledge_revision,${columns.scope} vote_clue_revision,${columns.easy} easy_votes,${columns.right} right_votes,${columns.hard} hard_votes,enabled FROM guess_character WHERE id=? FOR UPDATE`,
        [input.person_id],
      );
      const row = rows[0];
      if (!row || !row.enabled)
        throw new BadRequestException('对应人物暂时无法反馈');
      const [existing] = await connection.execute<RowDataPacket[]>(
        `SELECT rating FROM ${table} WHERE game_hash=? OR (person_id=? AND clue_revision=? AND difficulty_revision=? AND actor_hash=?) LIMIT 1`,
        [
          input.game_hash,
          input.person_id,
          input.clue_revision,
          input.revision,
          input.actor_hash,
        ],
      );
      if (existing.length) {
        await connection.commit();
        return {
          rating: existing[0].rating,
          difficulty: row.difficulty,
          revision: row.difficulty_revision,
          moved: false,
        };
      }
      await connection.execute(
        `INSERT INTO ${table}(game_hash,person_id,clue_revision,difficulty_revision,actor_hash,rating,guesses,unlocked,outcome) VALUES(?,?,?,?,?,?,?,?,?)`,
        [
          input.game_hash,
          input.person_id,
          input.clue_revision,
          input.revision,
          input.actor_hash,
          input.rating,
          input.guesses,
          input.unlocked,
          input.outcome,
        ],
      );
      let moved = false;
      // Votes belong to this clue set and classification round, not to the question game.
      if (
        row.difficulty_revision === input.revision &&
        row.knowledge_revision === input.knowledge_revision
      ) {
        const previous =
          row.vote_clue_revision === input.clue_revision
            ? {
                easy: row.easy_votes,
                right: row.right_votes,
                hard: row.hard_votes,
              }
            : { easy: 0, right: 0, hard: 0 };
        const change = applyDifficultyRating(
          row.difficulty,
          previous,
          input.rating,
        );
        moved = change.moved;
        row.difficulty = change.difficulty;
        if (moved) row.difficulty_revision++;
        await connection.execute(
          `UPDATE guess_character SET ${columns.difficulty}=?,${columns.revision}=?,${columns.scope}=?,${columns.easy}=?,${columns.right}=?,${columns.hard}=? WHERE id=?`,
          [
            row.difficulty,
            row.difficulty_revision,
            input.clue_revision,
            change.counts.easy,
            change.counts.right,
            change.counts.hard,
            input.person_id,
          ],
        );
      }
      signal?.throwIfAborted();
      await connection.commit();
      return {
        rating: input.rating,
        difficulty: row.difficulty,
        revision: row.difficulty_revision,
        moved,
      };
    } catch (error) {
      await connection.rollback().catch(() => {});
      throw error;
    } finally {
      signal?.removeEventListener('abort', abort);
      connection.release();
    }
  }
}
