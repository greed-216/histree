import type { VersionedReadPort } from './storage-port';
export class TimelineRepository {
  constructor(private readonly db: VersionedReadPort) {}
  async summary() {
    return this.db.cache.read('timeline-summary', async () => {
      const years = await this.db.rows(
        "SELECT start_year year,COUNT(*) count FROM event WHERE status='published' AND start_year IS NOT NULL GROUP BY start_year ORDER BY start_year",
      );
      const [stats] = await this.db.rows(
        "SELECT COUNT(*) total,COALESCE(SUM(start_year IS NULL),0) undated,MIN(start_year) `from`,MAX(GREATEST(start_year,COALESCE(end_year,start_year))) `to` FROM event WHERE status='published'",
      );
      return { ...stats, years };
    });
  }
  async highlights(value: number) {
    return this.db.cache.read('year-highlights:' + value, async () => ({
      items: await this.db.rows(
        "SELECT id,title FROM event WHERE status='published' AND start_year=? ORDER BY COALESCE(impact_level,0) DESC,REGEXP_LIKE(title,'称帝|建立|灭亡|禅位|即位|政变|建国') DESC,id LIMIT 3",
        [value],
      ),
    }));
  }
  async timeline(signal?: AbortSignal) {
    const years = await this.db.rows(
      "SELECT start_year year,COUNT(*) count FROM event WHERE status='published' AND start_year IS NOT NULL GROUP BY start_year ORDER BY start_year",
      [],
      signal,
    );
    const highlights = await this.db.rows(
      "SELECT id,title,start_year FROM (SELECT id,title,start_year,ROW_NUMBER() OVER(PARTITION BY start_year ORDER BY COALESCE(impact_level,0) DESC,REGEXP_LIKE(title,'称帝|建立|灭亡|禅位|即位|政变|建国') DESC,id) ranking FROM event WHERE status='published' AND start_year IS NOT NULL) h WHERE ranking<=3 ORDER BY start_year,ranking",
      [],
      signal,
    );
    const stats = (
      await this.db.rows(
        "SELECT COUNT(*) total,COALESCE(SUM(start_year IS NULL),0) undated,MIN(start_year) `from`,MAX(GREATEST(start_year,COALESCE(end_year,start_year))) `to` FROM event WHERE status='published'",
        [],
        signal,
      )
    )[0];
    return {
      ...stats,
      years: years.map((y) => ({
        ...y,
        highlights: highlights
          .filter((h) => h.start_year === y.year)
          .map(({ id, title }) => ({ id, title })),
      })),
    };
  }
}
