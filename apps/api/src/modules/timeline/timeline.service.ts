import { Injectable, Logger } from '@nestjs/common';
import type { Event } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class TimelineService {
  private readonly logger = new Logger(TimelineService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getTimeline(startYear: number, endYear: number): Promise<Event[]> {
    const supabase = this.supabaseService.getClient();

    try {
      let query = supabase
        .from('event')
        .select('*')
        .order('start_year', { ascending: true });

      if (!isNaN(startYear)) {
        query = query.gte('start_year', startYear);
      }
      
      if (!isNaN(endYear)) {
        query = query.lte('start_year', endYear);
      }

      const { data, error } = await query;

      if (error) {
        throw error;
      }

      return (data || []).map(e => ({ ...e, type: 'event' } as Event));
    } catch (err) {
      this.logger.error('Failed to fetch timeline from Supabase', err);
      throw err;
    }
  }
}
