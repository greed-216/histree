import type { Topic, EvidenceClaim } from '@histree/shared-types';
import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { SupabaseService } from '../supabase/supabase.service';
import { publicationStatus } from '../../common/publication';

const subjects = [
  'person',
  'event',
  'person_relationship',
  'person_event',
  'event_causality',
];
const tables = [...subjects, 'topic', 'source', 'fact_claim'];
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

@Injectable()
export class EditorialService {
  constructor(private readonly db: SupabaseService) {}

  async topics(slug?: string) {
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

  async evidence(subject: string, id: string) {
    if (!subjects.includes(subject) || !uuid.test(id))
      throw new BadRequestException('无效的出处对象');
    const { data, error } = await this.db
      .getClient()
      .from('fact_claim')
      .select('*, source:source_id(*)')
      .eq('status', 'published')
      .eq('subject_table', subject)
      .eq('subject_id', id);
    if (error) throw error;
    return (data ?? []) as EvidenceClaim[];
  }

  async list(table: string) {
    if (!tables.includes(table))
      throw new BadRequestException('无效的内容类型');
    const { data, error } = await this.db
      .getAdminClient()
      .from(table)
      .select('*')
      .order('created_at', { ascending: false });
    if (error) throw error;
    return (data ?? []) as Record<string, unknown>[];
  }

  async save(table: string, input: Record<string, unknown>, id?: string) {
    if (!['topic', 'source', 'fact_claim'].includes(table))
      throw new BadRequestException('无效的编辑类型');
    if (id && !uuid.test(id)) throw new BadRequestException('无效的记录 ID');
    const row = await this.validate(table, input);
    const db = this.db.getAdminClient().from(table);
    const { data, error } = await (
      id ? db.update(row).eq('id', id) : db.insert(row)
    )
      .select()
      .single<Record<string, unknown>>();
    if (error) throw error;
    return data;
  }

  async remove(table: string, id: string) {
    if (!['topic', 'source', 'fact_claim'].includes(table) || !uuid.test(id))
      throw new BadRequestException('无效的删除对象');
    if (table === 'source') {
      const { count, error } = await this.db
        .getAdminClient()
        .from('fact_claim')
        .select('id', { count: 'exact', head: true })
        .eq('source_id', id);
      if (error) throw error;
      if (count)
        throw new BadRequestException('这份资料仍有引用，请先调整引用');
    }
    const { error } = await this.db
      .getAdminClient()
      .from(table)
      .delete()
      .eq('id', id);
    if (error) throw error;
    return { id };
  }

  private async validate(table: string, input: Record<string, unknown>) {
    if (!input || typeof input !== 'object' || Array.isArray(input))
      throw new BadRequestException('无效的内容');
    const text = (key: string, required = false) => {
      const value = input[key];
      if (value != null && typeof value !== 'string')
        throw new BadRequestException(`${key} 必须是文本`);
      const result = typeof value === 'string' ? value.trim() : '';
      if (required && !result) throw new BadRequestException(`${key} 不能为空`);
      return result;
    };
    const status =
      table === 'source'
        ? undefined
        : (publicationStatus(input.status) ?? 'draft');
    if (table === 'source') {
      const url = text('url');
      if (url && !/^https?:\/\//i.test(url))
        throw new BadRequestException('资料链接须以 http 或 https 开头');
      const source_type = text('source_type', true);
      if (
        !['primary', 'reference', 'scholarship', 'digital', 'media'].includes(
          source_type,
        )
      )
        throw new BadRequestException('无效的资料类型');
      return {
        title: text('title', true),
        source_type,
        author: text('author'),
        edition: text('edition'),
        url,
        note: text('note'),
      };
    }
    if (table === 'topic') {
      const slug = text('slug', true);
      if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug))
        throw new BadRequestException('专题地址仅使用小写英文、数字和连字符');
      if (!Array.isArray(input.sections) || !input.sections.length)
        throw new BadRequestException('至少添加一个阅读章节');
      const sections: { heading: string; body: string; node_ids: string[] }[] =
        [];
      for (const value of input.sections as unknown[]) {
        if (!value || typeof value !== 'object' || Array.isArray(value))
          throw new BadRequestException('章节格式无效');
        const section = value as Record<string, unknown>;
        if (
          !section ||
          typeof section.heading !== 'string' ||
          !section.heading.trim() ||
          typeof section.body !== 'string' ||
          !Array.isArray(section.node_ids) ||
          section.node_ids.some(
            (v: unknown) => typeof v !== 'string' || !uuid.test(v),
          )
        )
          throw new BadRequestException('章节标题、正文或关联条目无效');
        const nodeIds = section.node_ids as string[];
        for (const node of nodeIds) {
          const [p, e] = await Promise.all(
            subjects
              .slice(0, 2)
              .map((t) =>
                this.db
                  .getAdminClient()
                  .from(t)
                  .select('id, status')
                  .eq('id', node)
                  .maybeSingle<{ id: string; status: string }>(),
              ),
          );
          if (p.error) throw p.error;
          if (e.error) throw e.error;
          const found = p.data ?? e.data;
          if (
            !found ||
            (status === 'published' && found.status !== 'published')
          )
            throw new BadRequestException('发布专题前，请先发布全部关联条目');
        }
        sections.push({
          heading: section.heading.trim(),
          body: section.body.trim(),
          node_ids: [...new Set(nodeIds)],
        });
      }
      return {
        slug,
        title: text('title', true),
        description: text('description', true),
        sections,
        status,
      };
    }
    const subject_table = text('subject_table', true);
    const subject_id = text('subject_id', true);
    if (!subjects.includes(subject_table) || !uuid.test(subject_id))
      throw new BadRequestException('无效的出处对象');
    const { data: subject, error: subjectError } = await this.db
      .getAdminClient()
      .from(subject_table)
      .select('id')
      .eq('id', subject_id)
      .maybeSingle();
    if (subjectError) throw subjectError;
    if (!subject) throw new BadRequestException('关联条目或关系不存在');
    const source_id = text('source_id', true);
    if (!uuid.test(source_id)) throw new BadRequestException('请选择来源');
    const { data: source, error: sourceError } = await this.db
      .getAdminClient()
      .from('source')
      .select('id')
      .eq('id', source_id)
      .maybeSingle();
    if (sourceError) throw sourceError;
    if (!source) throw new BadRequestException('来源不存在');
    return {
      subject_table,
      subject_id,
      source_id,
      field_path: text('field_path', true),
      claim_text: text('claim_text', true),
      citation: text('citation', true),
      note: text('note'),
      status,
    };
  }
}
