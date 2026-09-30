import { readContentPage } from '../../common/pagination';
import { publicationStatus } from '../../common/publication';
import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type { Person, PageResult } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class PersonService {
  constructor(private supabaseService: SupabaseService) {}

  async getPeople(
    query: Record<string, string> = {},
  ): Promise<PageResult<Person>> {
    return readContentPage(this.supabaseService.getClient(), 'person', query);
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
    publicationStatus(row.status);
    return row;
  }
}
