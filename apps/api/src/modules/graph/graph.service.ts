import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import type { GraphResponse, Person, Event, Edge } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class GraphService {
  private readonly logger = new Logger(GraphService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getPersonGraph(personId: string): Promise<GraphResponse> {
    const supabase = this.supabaseService.getClient();

    try {
      // 1. Get the target person
      const { data: mainPerson, error: mainErr } = await supabase
        .from('person')
        .select('*')
        .eq('id', personId)
        .single();
      
      if (mainErr || !mainPerson) {
        throw new NotFoundException('Person not found');
      }

      // 2. Get relationships where person is A or B
      const { data: relsA } = await supabase
        .from('person_relationship')
        .select('person_b, relation_type, description')
        .eq('person_a', personId);
        
      const { data: relsB } = await supabase
        .from('person_relationship')
        .select('person_a, relation_type, description')
        .eq('person_b', personId);

      const relatedPersonIds = new Set<string>();
      const edges: Edge[] = [];

      relsA?.forEach(r => {
        relatedPersonIds.add(r.person_b);
        edges.push({ source: personId, target: r.person_b, type: r.relation_type, description: r.description });
      });

      relsB?.forEach(r => {
        relatedPersonIds.add(r.person_a);
        edges.push({ source: r.person_a, target: personId, type: r.relation_type, description: r.description });
      });

      // 3. Get events this person is involved in
      const { data: personEvents } = await supabase
        .from('person_event')
        .select('event_id, role')
        .eq('person_id', personId);

      const relatedEventIds = new Set<string>();
      personEvents?.forEach(pe => {
        relatedEventIds.add(pe.event_id);
        edges.push({ source: personId, target: pe.event_id, type: pe.role });
      });

      // 4. Fetch the related persons and events details
      let peopleData: any[] = [];
      if (relatedPersonIds.size > 0) {
        const { data } = await supabase.from('person').select('*').in('id', Array.from(relatedPersonIds));
        peopleData = data || [];
      }

      let eventsData: any[] = [];
      if (relatedEventIds.size > 0) {
        const { data } = await supabase.from('event').select('*').in('id', Array.from(relatedEventIds));
        eventsData = data || [];
      }

      // 5. Get causalities among these events
      if (relatedEventIds.size > 0) {
        const { data: causalities } = await supabase
          .from('event_causality')
          .select('cause_event_id, effect_event_id, description')
          .in('cause_event_id', Array.from(relatedEventIds))
          .in('effect_event_id', Array.from(relatedEventIds));
        
        causalities?.forEach(c => {
          edges.push({ source: c.cause_event_id, target: c.effect_event_id, type: 'causes', description: c.description });
        });
      }

      // 6. Build the final nodes array
      const nodes: Array<Person | Event> = [
        { ...mainPerson, type: 'person' } as Person,
        ...peopleData.map(p => ({ ...p, type: 'person' } as Person)),
        ...eventsData.map(e => ({ ...e, type: 'event' } as Event))
      ];

      return { nodes, edges };
    } catch (err) {
      this.logger.error('Failed to fetch graph data from Supabase', err);
      throw err;
    }
  }
}
