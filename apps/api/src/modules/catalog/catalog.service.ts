import { readContentPage } from '../../common/pagination';
import type { Topic } from '@histree/shared-types';
import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';

const subjects = [
  'person',
  'event',
  'person_relationship',
  'person_event',
  'event_causality',
];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

@Injectable()
export class CatalogService {
  constructor(private readonly db: MysqlService) {}

  async topics(slug?: string, options: Record<string, string> = {}) {
    if (!slug) return readContentPage(this.db.getClient(), 'topic', options);
    let query = this.db
      .getClient()
      .from('topic')
      .select('*')
      .eq('status', 'published')
      .order('created_at');
    if (slug) query = query.eq('slug', slug);
    const { data, error } = await query;
    if (error) throw error;
    if (slug && !data?.length)
      throw new NotFoundException('专题尚未发布或不存在');
    const topics = (data ?? []) as Topic[];
    return slug ? topics[0] : topics;
  }

  async source(id: string, page = 0) {
    if (!uuid.test(id) || !Number.isInteger(page) || page < 0 || page > 100000)
      throw new BadRequestException('无效的来源地址');
    const client = this.db.getClient();
    const [source, claims] = await Promise.all([
      client.from('source').select('*').eq('id', id).single(),
      client
        .from('fact_claim')
        .select('*, source:source_id(*)', { count: 'exact' })
        .eq('status', 'published')
        .eq('source_id', id)
        .order('id')
        .range(page * 50, page * 50 + 49),
    ]);
    if (source.error) throw source.error;
    if (claims.error) throw claims.error;
    return {
      source: source.data,
      claims: claims.data ?? [],
      count: claims.count ?? 0,
    };
  }

  async evidence(
    subject: string,
    id: string,
    options: Record<string, string> = {},
  ) {
    if (!subjects.includes(subject) || !uuid.test(id))
      throw new BadRequestException('无效的出处对象');
    return readContentPage(this.db.getClient(), 'fact_claim', {
      ...options,
      subject,
      subject_id: id,
    });
  }

}
