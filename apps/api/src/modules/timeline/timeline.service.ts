import { timelineYear, pageNumber } from '@histree/shared-types';
import { BadRequestException, Injectable } from '@nestjs/common';
import { SupabaseService } from '../supabase/supabase.service';
import { readContentPage } from '../../common/pagination';
@Injectable()
export class TimelineService {
  constructor(private readonly supabaseService: SupabaseService) {}
  async getOverview() {
    const { data, error } = await this.supabaseService.getClient().rpc('timeline_overview');
    if (error) throw error;
    return data;
  }
  async getTimeline(query: Record<string, string> = {}) {
    if (query.year !== undefined) {
      let year: number, page: number;
      try { year = timelineYear(query.year); page = pageNumber(query.page); }
      catch { throw new BadRequestException('无效的时间图参数'); }
      const { data, error } = await this.supabaseService.getClient().from('event').select('*')
        .eq('status', 'published').lte('start_year', year)
        .or(`end_year.gte.${year},and(end_year.is.null,start_year.eq.${year})`)
        .order('start_year').order('id').range(page * 20, page * 20 + 20);
      if (error) throw error;
      return { items: (data ?? []).slice(0, 20), has_more: (data?.length ?? 0) > 20 };
    }
    const { start, end, ...rest } = query;
    return readContentPage(this.supabaseService.getClient(), 'event', {
      ...rest,
      ...(start ? { from: start } : {}),
      ...(end ? { to: end } : {}),
    });
  }
}
