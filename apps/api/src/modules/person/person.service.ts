import { BadRequestException, Injectable, Logger, NotFoundException } from '@nestjs/common';
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

  async createPerson(payload: Partial<Person>): Promise<Person> {
    if (!payload.name?.trim()) {
      throw new BadRequestException('Person name is required');
    }

    const supabase = this.supabaseService.getAdminClient();
    const { data, error } = await supabase
      .from('person')
      .insert(this.toPersonRow(payload))
      .select()
      .single();

    if (error) {
      throw error;
    }

    return { ...data, type: 'person' } as Person;
  }

  async updatePerson(id: string, payload: Partial<Person>): Promise<Person> {
    const supabase = this.supabaseService.getAdminClient();
    const { data, error } = await supabase
      .from('person')
      .update(this.toPersonRow(payload))
      .eq('id', id)
      .select()
      .single();

    if (error || !data) {
      throw new NotFoundException('Person not found');
    }

    return { ...data, type: 'person' } as Person;
  }

  async deletePerson(id: string): Promise<{ id: string }> {
    const supabase = this.supabaseService.getAdminClient();
    const { error } = await supabase.from('person').delete().eq('id', id);

    if (error) {
      throw error;
    }

    return { id };
  }

  private toPersonRow(payload: Partial<Person>) {
    const { id: _id, type: _type, ...row } = payload;
    return row;
  }
}
