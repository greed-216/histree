import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import type { EventDetail, Person, Event } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class EventService {
  private readonly logger = new Logger(EventService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getEventDetail(eventId: string): Promise<EventDetail> {
    const supabase = this.supabaseService.getClient();

    try {
      // 1. Get event basic info
      const { data: event, error } = await supabase
        .from('event')
        .select('*')
        .eq('id', eventId)
        .single();

      if (error || !event) {
        throw new NotFoundException('Event not found');
      }

      // 2. Get related people
      const { data: personEvents } = await supabase
        .from('person_event')
        .select('role, person_id')
        .eq('event_id', eventId);

      let related_people: any[] = [];
      if (personEvents && personEvents.length > 0) {
        const personIds = personEvents.map(pe => pe.person_id);
        const { data: peopleData } = await supabase.from('person').select('*').in('id', personIds);
        
        related_people = personEvents.map(pe => {
          const p = peopleData?.find(p => p.id === pe.person_id);
          return {
            role: pe.role,
            person: { ...p, type: 'person' } as Person
          };
        });
      }

      // 3. Get cause events
      const { data: causeCausalities } = await supabase
        .from('event_causality')
        .select('cause_event_id')
        .eq('effect_event_id', eventId);

      let cause_events: Event[] = [];
      if (causeCausalities && causeCausalities.length > 0) {
        const causeIds = causeCausalities.map(c => c.cause_event_id);
        const { data: causeData } = await supabase.from('event').select('*').in('id', causeIds);
        cause_events = (causeData || []).map(e => ({ ...e, type: 'event' } as Event));
      }

      // 4. Get effect events
      const { data: effectCausalities } = await supabase
        .from('event_causality')
        .select('effect_event_id')
        .eq('cause_event_id', eventId);

      let effect_events: Event[] = [];
      if (effectCausalities && effectCausalities.length > 0) {
        const effectIds = effectCausalities.map(c => c.effect_event_id);
        const { data: effectData } = await supabase.from('event').select('*').in('id', effectIds);
        effect_events = (effectData || []).map(e => ({ ...e, type: 'event' } as Event));
      }

      return {
        ...event,
        type: 'event',
        related_people,
        cause_events,
        effect_events,
      };

    } catch (err) {
      this.logger.error('Failed to fetch event detail from Supabase', err);
      throw err;
    }
  }
}
