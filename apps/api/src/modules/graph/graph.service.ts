import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import type { GraphResponse, Person, Event, Edge } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class GraphService {
  private readonly logger = new Logger(GraphService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getGraph(id: string): Promise<GraphResponse> {
    const supabase = this.supabaseService.getClient();

    try {
      // 1. Check if person
      let centerNode: any = null;
      let centerType: 'person' | 'event' = 'person';
      
      const { data: personData } = await supabase.from('person').select('*').eq('id', id).single();
      if (personData) {
        centerNode = { ...personData, type: 'person' };
        centerType = 'person';
      } else {
        const { data: eventData } = await supabase.from('event').select('*').eq('id', id).single();
        if (eventData) {
          centerNode = { ...eventData, type: 'event' };
          centerType = 'event';
        } else {
          throw new NotFoundException('Node not found');
        }
      }

      const relatedPersonIds = new Set<string>();
      const relatedEventIds = new Set<string>();
      const edges: Edge[] = [];

      if (centerType === 'person') {
        relatedPersonIds.add(id);
        
        // relationships
        const { data: relsA } = await supabase.from('person_relationship').select('person_b, relation_type, description').eq('person_a', id);
        const { data: relsB } = await supabase.from('person_relationship').select('person_a, relation_type, description').eq('person_b', id);
        
        relsA?.forEach(r => { relatedPersonIds.add(r.person_b); edges.push({ source: id, target: r.person_b, type: r.relation_type, description: r.description }); });
        relsB?.forEach(r => { relatedPersonIds.add(r.person_a); edges.push({ source: r.person_a, target: id, type: r.relation_type, description: r.description }); });

        // events
        const { data: personEvents } = await supabase.from('person_event').select('event_id, role').eq('person_id', id);
        personEvents?.forEach(pe => { relatedEventIds.add(pe.event_id); edges.push({ source: id, target: pe.event_id, type: pe.role }); });
      } else {
        relatedEventIds.add(id);

        // people in this event
        const { data: eventPeople } = await supabase.from('person_event').select('person_id, role').eq('event_id', id);
        eventPeople?.forEach(ep => { relatedPersonIds.add(ep.person_id); edges.push({ source: ep.person_id, target: id, type: ep.role }); });

        // causalities where event is cause
        const { data: effects } = await supabase.from('event_causality').select('effect_event_id, description').eq('cause_event_id', id);
        effects?.forEach(e => { relatedEventIds.add(e.effect_event_id); edges.push({ source: id, target: e.effect_event_id, type: 'causes', description: e.description }); });

        // causalities where event is effect
        const { data: causes } = await supabase.from('event_causality').select('cause_event_id, description').eq('effect_event_id', id);
        causes?.forEach(c => { relatedEventIds.add(c.cause_event_id); edges.push({ source: c.cause_event_id, target: id, type: 'causes', description: c.description }); });
      }

      // Fetch the related details
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

      // For related events, let's also fetch causalities among THEM to make graph richer
      if (relatedEventIds.size > 0) {
        const { data: causalities } = await supabase
          .from('event_causality')
          .select('cause_event_id, effect_event_id, description')
          .in('cause_event_id', Array.from(relatedEventIds))
          .in('effect_event_id', Array.from(relatedEventIds));
        
        causalities?.forEach(c => {
          // Avoid duplicate edge
          const exists = edges.some(e => e.source === c.cause_event_id && e.target === c.effect_event_id);
          if (!exists) {
            edges.push({ source: c.cause_event_id, target: c.effect_event_id, type: 'causes', description: c.description });
          }
        });
      }

      const nodes: Array<Person | Event> = [
        ...peopleData.map(p => ({ ...p, type: 'person' } as Person)),
        ...eventsData.map(e => ({ ...e, type: 'event' } as Event))
      ];

      return { center: centerNode, nodes, edges };
    } catch (err) {
      this.logger.error('Failed to fetch graph data', err);
      throw err;
    }
  }
}
