import { Injectable } from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';
import { GuessBankService } from './guess-bank';
import { loadGuessCatalogue, type GuessPerson } from './guess-catalogue';

// Both modes and the batch preparer synchronize the same stable identity directory.
// This never generates clues or overwrites either mode's feedback-adjusted tier.
@Injectable()
export class GuessCharacterCatalogue {
  private pending?: Promise<GuessPerson[]>;
  private expires = 0;
  constructor(
    private readonly db: MysqlService,
    private readonly bank: GuessBankService,
  ) {}
  async sync(signal: AbortSignal): Promise<GuessPerson[]> {
    signal.throwIfAborted();
    if (!this.pending || Date.now() >= this.expires) {
      const work = this.refresh(AbortSignal.timeout(60000));
      this.pending = work;
      this.expires = Date.now() + 240000;
      void work.catch(() => {
        if (this.pending === work) this.pending = undefined;
      });
    }
    const work = this.pending;
    return new Promise((resolve, reject) => {
      const abort = () => reject(signal.reason);
      signal.addEventListener('abort', abort, { once: true });
      if (signal.aborted) abort();
      void work
        .then(resolve, reject)
        .finally(() => signal.removeEventListener('abort', abort));
    });
  }
  private async refresh(signal: AbortSignal) {
    const people = await this.bank.prepare(
      await loadGuessCatalogue(this.db, signal),
      signal,
    );
    await this.db.execute(
      `INSERT IGNORE INTO guess_character(id,canonical_person_id,name,aliases,courtesy_name,era,birth_year,death_year,description,difficulty,question_difficulty)
       SELECT p.id,p.id,p.name,COALESCE(p.aliases,JSON_ARRAY()),p.courtesy_name,p.era,p.birth_year,p.death_year,COALESCE(p.description,''),b.difficulty,b.difficulty
       FROM guess_bank b JOIN person p ON p.id=b.person_id WHERE p.status='published'`,
      [],
      signal,
    );
    return people;
  }
}
