import {
  BadRequestException,
  Body,
  Controller,
  NotFoundException,
  Param,
  Post,
} from '@nestjs/common';
import { z } from 'zod';
import { MysqlService } from './mysql.service';
const identifier = z.string().uuid(),
  year = z.number().int().min(-10000).max(10000).nullable().optional();
const schemas: Record<string, z.ZodTypeAny> = {
  entry_detail: z.object({ p_id: identifier }).strict(),
  topic_detail: z.object({ p_id: identifier }).strict(),
  entry_context: z
    .object({
      p_id: identifier,
      p_page: z.number().int().min(0).max(100000).optional(),
      p_limit: z.number().int().min(1).max(50).optional(),
    })
    .strict(),
  ask_search: z
    .object({
      p_keywords: z.array(z.string().trim().min(1).max(40)).min(1).max(6),
      p_kind: z.enum(['all', 'person', 'event', 'topic']).optional(),
      p_from: year,
      p_to: year,
      p_offset: z.number().int().min(0).max(10000).optional(),
    })
    .strict(),
  content_page: z
    .object({
      p_table: z.enum(['person', 'event', 'topic', 'nodes', 'fact_claim']),
      p_page: z.number().int().min(0).max(100000).optional(),
      p_limit: z.number().int().min(1).max(50).optional(),
      p_admin: z.literal(false).optional(),
      p_subject: z
        .enum([
          'person',
          'event',
          'person_relationship',
          'person_event',
          'event_causality',
        ])
        .nullable()
        .optional(),
      p_subject_id: identifier.nullable().optional(),
    })
    .strict(),
};
/** Worker receives only these public read operations, never database credentials. */
@Controller('api/v1/read')
export class MysqlReadController {
  constructor(private readonly mysql: MysqlService) {}
  @Post(':name') async read(
    @Param('name') name: string,
    @Body() body: unknown,
  ) {
    if (!this.mysql.enabled || !schemas[name])
      throw new NotFoundException('接口不存在');
    const parsed = schemas[name].safeParse(body);
    if (!parsed.success) throw new BadRequestException('查询参数无效');
    if (
      parsed.data.p_from != null &&
      parsed.data.p_to != null &&
      parsed.data.p_from > parsed.data.p_to
    )
      throw new BadRequestException('年代参数无效');
    return this.mysql.rpc(name, parsed.data, AbortSignal.timeout(15000));
  }
}
