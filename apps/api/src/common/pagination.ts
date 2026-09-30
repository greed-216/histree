import { BadRequestException } from '@nestjs/common';
import type { SupabaseClient } from '@supabase/supabase-js';
import { contentRequest, pageNumber } from '@histree/shared-types';
export async function readContentPage(
  client: SupabaseClient,
  table: string,
  query: Record<string, string> = {},
  admin = false,
) {
  let args: ReturnType<typeof contentRequest>;
  try {
    args = contentRequest(
      `/catalog/${table}?${new URLSearchParams(query)}`,
      admin,
    );
  } catch {
    throw new BadRequestException('查询参数无效');
  }
  const { data, error } = await client.rpc('content_page', args);
  if (error) throw error;
  return data;
}
export function validPage(value?: string) {
  try {
    return pageNumber(value);
  } catch {
    throw new BadRequestException('分页参数无效');
  }
}
