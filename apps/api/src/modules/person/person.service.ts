import { Injectable, Logger } from '@nestjs/common';
import type { Person } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class PersonService {
  private readonly logger = new Logger(PersonService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getPeople(): Promise<Person[]> {
    const supabase = this.supabaseService.getClient();

    try {
      const { data, error } = await supabase
        .from('person')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;

      return (data || []).map(p => ({ ...p, type: 'person' } as Person));
    } catch (err) {
      this.logger.error('Failed to fetch people', err);
      throw err;
    }
  }
}
