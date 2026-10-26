import type { SqlReadPort } from './storage-port';
/** Database revision changes in the same transaction as content; failed loads are never cached. */
export class RevisionCache {
  private entries = new Map<
    string,
    { expires: number; value: Promise<unknown> }
  >();
  constructor(private readonly db: SqlReadPort) {}
  async revision() {
    try {
      return String(
        (
          await this.db.rows('SELECT revision FROM content_revision WHERE id=1')
        )[0]?.revision ?? '0',
      );
    } catch (error) {
      if ((error as { code?: string }).code === 'ER_NO_SUCH_TABLE')
        return 'legacy';
      throw error;
    }
  }
  async read<T>(key: string, load: () => Promise<T>): Promise<T> {
    const revision = await this.revision(),
      scope = revision + ':' + key,
      saved = this.entries.get(scope);
    if (saved && saved.expires > Date.now()) return saved.value as Promise<T>;
    const value = load();
    this.entries.set(scope, {
      value,
      expires: Date.now() + (revision === 'legacy' ? 5000 : 60000),
    });
    if (this.entries.size > 64)
      this.entries.delete(this.entries.keys().next().value!);
    try {
      return await value;
    } catch (error) {
      this.entries.delete(scope);
      throw error;
    }
  }
}
