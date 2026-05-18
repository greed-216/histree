import { BadRequestException, ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import type {
  EventCausalityRelation,
  EventCausalityRelationInput,
  PersonEventRelation,
  PersonEventRelationInput,
  PersonRelationship,
  PersonRelationshipInput,
  RelationshipBundle,
} from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class RelationshipService {
  constructor(private readonly supabaseService: SupabaseService) {}

  async getRelationships(): Promise<RelationshipBundle> {
    const supabase = this.supabaseService.getClient();
    const [personRelationships, personEvents, eventCausalities] = await Promise.all([
      supabase.from('person_relationship').select('*').order('created_at', { ascending: false }),
      supabase.from('person_event').select('*').order('created_at', { ascending: false }),
      supabase.from('event_causality').select('*').order('created_at', { ascending: false }),
    ]);

    if (personRelationships.error) throw personRelationships.error;
    if (personEvents.error) throw personEvents.error;
    if (eventCausalities.error) throw eventCausalities.error;

    return {
      person_relationships: (personRelationships.data ?? []) as PersonRelationship[],
      person_events: (personEvents.data ?? []) as PersonEventRelation[],
      event_causalities: (eventCausalities.data ?? []) as EventCausalityRelation[],
    };
  }

  async createPersonRelationship(payload: PersonRelationshipInput): Promise<PersonRelationship> {
    const row = this.normalizePersonRelationship(payload);

    await Promise.all([this.ensurePerson(row.person_a), this.ensurePerson(row.person_b)]);
    await this.ensureNoPersonRelationshipDuplicate(row);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_relationship')
      .insert(row)
      .select()
      .single();

    if (error) throw error;
    return data as PersonRelationship;
  }

  async updatePersonRelationship(id: string, payload: Partial<PersonRelationshipInput>): Promise<PersonRelationship> {
    const row = this.normalizePersonRelationship(payload);

    await Promise.all([this.ensurePerson(row.person_a), this.ensurePerson(row.person_b)]);
    await this.ensureNoPersonRelationshipDuplicate(row, id);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_relationship')
      .update(row)
      .eq('id', id)
      .select()
      .single();

    if (error || !data) throw new NotFoundException('Person relationship not found');
    return data as PersonRelationship;
  }

  async deletePersonRelationship(id: string): Promise<{ id: string }> {
    const { error } = await this.supabaseService.getAdminClient().from('person_relationship').delete().eq('id', id);
    if (error) throw error;
    return { id };
  }

  async createPersonEvent(payload: PersonEventRelationInput): Promise<PersonEventRelation> {
    const row = this.normalizePersonEvent(payload);

    await Promise.all([this.ensurePerson(row.person_id), this.ensureEvent(row.event_id)]);
    await this.ensureNoPersonEventDuplicate(row);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_event')
      .insert(row)
      .select()
      .single();

    if (error) throw error;
    return data as PersonEventRelation;
  }

  async updatePersonEvent(id: string, payload: Partial<PersonEventRelationInput>): Promise<PersonEventRelation> {
    const row = this.normalizePersonEvent(payload);

    await Promise.all([this.ensurePerson(row.person_id), this.ensureEvent(row.event_id)]);
    await this.ensureNoPersonEventDuplicate(row, id);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_event')
      .update(row)
      .eq('id', id)
      .select()
      .single();

    if (error || !data) throw new NotFoundException('Person-event relation not found');
    return data as PersonEventRelation;
  }

  async deletePersonEvent(id: string): Promise<{ id: string }> {
    const { error } = await this.supabaseService.getAdminClient().from('person_event').delete().eq('id', id);
    if (error) throw error;
    return { id };
  }

  async createEventCausality(payload: EventCausalityRelationInput): Promise<EventCausalityRelation> {
    const row = this.normalizeEventCausality(payload);

    await Promise.all([this.ensureEvent(row.cause_event_id), this.ensureEvent(row.effect_event_id)]);
    await this.ensureNoEventCausalityDuplicate(row);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('event_causality')
      .insert(row)
      .select()
      .single();

    if (error) throw error;
    return data as EventCausalityRelation;
  }

  async updateEventCausality(
    id: string,
    payload: Partial<EventCausalityRelationInput>,
  ): Promise<EventCausalityRelation> {
    const row = this.normalizeEventCausality(payload);

    await Promise.all([this.ensureEvent(row.cause_event_id), this.ensureEvent(row.effect_event_id)]);
    await this.ensureNoEventCausalityDuplicate(row, id);

    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('event_causality')
      .update(row)
      .eq('id', id)
      .select()
      .single();

    if (error || !data) throw new NotFoundException('Event causality not found');
    return data as EventCausalityRelation;
  }

  async deleteEventCausality(id: string): Promise<{ id: string }> {
    const { error } = await this.supabaseService.getAdminClient().from('event_causality').delete().eq('id', id);
    if (error) throw error;
    return { id };
  }

  private normalizePersonRelationship(payload: Partial<PersonRelationshipInput>): PersonRelationshipInput {
    const person_a = payload.person_a?.trim();
    const person_b = payload.person_b?.trim();
    const relation_type = payload.relation_type?.trim();

    if (!person_a || !person_b || !relation_type) {
      throw new BadRequestException('person_a, person_b, and relation_type are required');
    }

    if (person_a === person_b) {
      throw new BadRequestException('A person relationship must connect two different people');
    }

    return {
      person_a,
      person_b,
      relation_type,
      description: this.optionalText(payload.description),
    };
  }

  private normalizePersonEvent(payload: Partial<PersonEventRelationInput>): PersonEventRelationInput {
    const person_id = payload.person_id?.trim();
    const event_id = payload.event_id?.trim();
    const role = payload.role?.trim();

    if (!person_id || !event_id || !role) {
      throw new BadRequestException('person_id, event_id, and role are required');
    }

    return { person_id, event_id, role };
  }

  private normalizeEventCausality(payload: Partial<EventCausalityRelationInput>): EventCausalityRelationInput {
    const cause_event_id = payload.cause_event_id?.trim();
    const effect_event_id = payload.effect_event_id?.trim();

    if (!cause_event_id || !effect_event_id) {
      throw new BadRequestException('cause_event_id and effect_event_id are required');
    }

    if (cause_event_id === effect_event_id) {
      throw new BadRequestException('An event cannot cause itself');
    }

    return {
      cause_event_id,
      effect_event_id,
      description: this.optionalText(payload.description),
    };
  }

  private optionalText(value: string | undefined): string | undefined {
    const trimmed = value?.trim();
    return trimmed || undefined;
  }

  private async ensurePerson(id: string): Promise<void> {
    const { data, error } = await this.supabaseService.getAdminClient().from('person').select('id').eq('id', id).maybeSingle();
    if (error) throw error;
    if (!data) throw new NotFoundException(`Person not found: ${id}`);
  }

  private async ensureEvent(id: string): Promise<void> {
    const { data, error } = await this.supabaseService.getAdminClient().from('event').select('id').eq('id', id).maybeSingle();
    if (error) throw error;
    if (!data) throw new NotFoundException(`Event not found: ${id}`);
  }

  private async ensureNoPersonRelationshipDuplicate(row: PersonRelationshipInput, currentId?: string): Promise<void> {
    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_relationship')
      .select('id')
      .eq('person_a', row.person_a)
      .eq('person_b', row.person_b)
      .eq('relation_type', row.relation_type)
      .maybeSingle();

    if (error) throw error;
    if (data && data.id !== currentId) {
      throw new ConflictException('Duplicate person relationship');
    }
  }

  private async ensureNoPersonEventDuplicate(row: PersonEventRelationInput, currentId?: string): Promise<void> {
    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('person_event')
      .select('id')
      .eq('person_id', row.person_id)
      .eq('event_id', row.event_id)
      .eq('role', row.role)
      .maybeSingle();

    if (error) throw error;
    if (data && data.id !== currentId) {
      throw new ConflictException('Duplicate person-event relation');
    }
  }

  private async ensureNoEventCausalityDuplicate(row: EventCausalityRelationInput, currentId?: string): Promise<void> {
    const { data, error } = await this.supabaseService
      .getAdminClient()
      .from('event_causality')
      .select('id')
      .eq('cause_event_id', row.cause_event_id)
      .eq('effect_event_id', row.effect_event_id)
      .maybeSingle();

    if (error) throw error;
    if (data && data.id !== currentId) {
      throw new ConflictException('Duplicate event causality');
    }
  }
}
