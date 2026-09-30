import {
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { exploreRequest } from '@histree/shared-types';
import type { EntryContext } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';
import { validPage } from '../../common/pagination';
@Injectable()
export class GraphService {
  constructor(private readonly supabaseService: SupabaseService) {}
  async getGraph(id: string, page?: string): Promise<EntryContext> {
    try {
      exploreRequest(`/entry/${id}`);
    } catch {
      throw new BadRequestException('无效条目');
    }
    const { data, error } = await this.supabaseService
      .getClient()
      .rpc('entry_context', { p_id: id, p_page: validPage(page) });
    if (error) throw error;
    if (!data) throw new NotFoundException('Node not found');
    return data;
  }
}
