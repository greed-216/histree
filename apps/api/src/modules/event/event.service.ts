import { readContentPage, validPage } from '../../common/pagination';
import { publicationStatus } from '../../common/publication';
import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type {
  EventDetail,
  Event,
  EntryContext,
  PageResult,
} from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class EventService {
  constructor(private supabaseService: SupabaseService) {}

  async getEvents(
    query: Record<string, string> = {},
  ): Promise<PageResult<Event>> {
    return readContentPage(this.supabaseService.getClient(), 'event', query);
  }

  async getEventDetail(eventId: string, page?: string): Promise<EventDetail> {
    const { data, error } = await this.supabaseService
      .getClient()
      .rpc('entry_context', { p_id: eventId, p_page: validPage(page) });
    if (error) throw error;
    const context = data as EntryContext | null;
    if (!context || context.center.type !== 'event')
      throw new NotFoundException('Event not found');
    const nodes = new Map(context.nodes.map((n) => [n.id, n]));
    return {
      ...context.center,
      related_people: context.edges
        .filter((e) => e.subject_table === 'person_event')
        .flatMap((e) => {
          const person = nodes.get(e.source);
          return person?.type === 'person' ? [{ person, role: e.type }] : [];
        }),
      cause_events: context.edges
        .filter(
          (e) => e.subject_table === 'event_causality' && e.target === eventId,
        )
        .flatMap((e) => {
          const event = nodes.get(e.source);
          return event?.type === 'event' ? [event] : [];
        }),
      effect_events: context.edges
        .filter(
          (e) => e.subject_table === 'event_causality' && e.source === eventId,
        )
        .flatMap((e) => {
          const event = nodes.get(e.target);
          return event?.type === 'event' ? [event] : [];
        }),
      has_more: context.has_more,
    };
  }

  async createEvent(payload: Partial<Event>): Promise<Event> {
    if (!payload.title?.trim()) {
      throw new BadRequestException('Event title is required');
    }

    const supabase = this.supabaseService.getAdminClient();
    const { data, error } = await supabase
      .from('event')
      .insert(this.toEventRow(payload))
      .select()
      .single();

    if (error) {
      throw error;
    }

    return { ...data, type: 'event' } as Event;
  }

  async updateEvent(id: string, payload: Partial<Event>): Promise<Event> {
    const supabase = this.supabaseService.getAdminClient();
    const { data, error } = await supabase
      .from('event')
      .update(this.toEventRow(payload))
      .eq('id', id)
      .select()
      .single();

    if (error || !data) {
      throw new NotFoundException('Event not found');
    }

    return { ...data, type: 'event' } as Event;
  }

  async deleteEvent(id: string): Promise<{ id: string }> {
    const supabase = this.supabaseService.getAdminClient();
    const { error } = await supabase.from('event').delete().eq('id', id);

    if (error) {
      throw error;
    }

    return { id };
  }

  private toEventRow(payload: Partial<Event>) {
    const { id: _id, type: _type, ...row } = payload;
    publicationStatus(row.status);
    return row;
  }
}
