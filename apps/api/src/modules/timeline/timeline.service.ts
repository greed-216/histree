import { Injectable } from '@nestjs/common';
import { SupabaseService } from '../supabase/supabase.service';
import { readContentPage } from '../../common/pagination';
@Injectable()
export class TimelineService {
  constructor(private readonly supabaseService: SupabaseService) {}
  getTimeline(query: Record<string, string> = {}) {
    const { start, end, ...rest } = query;
    return readContentPage(this.supabaseService.getClient(), 'event', {
      ...rest,
      ...(start ? { from: start } : {}),
      ...(end ? { to: end } : {}),
    });
  }
}
