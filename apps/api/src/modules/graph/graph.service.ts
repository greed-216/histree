import { Injectable, Logger } from '@nestjs/common';
import type { GraphData, Person, Event, Relationship } from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Injectable()
export class GraphService {
  private readonly logger = new Logger(GraphService.name);

  constructor(private supabaseService: SupabaseService) {}

  async getDemoGraphData(): Promise<GraphData> {
    const supabase = this.supabaseService.getClient();

    try {
      // Fetch all people
      const { data: peopleData, error: peopleErr } = await supabase
        .from('people')
        .select('id, name, era, description');
      
      if (peopleErr) throw peopleErr;

      // Fetch all events
      const { data: eventsData, error: eventsErr } = await supabase
        .from('events')
        .select('id, title, time_start, time_end, description, dynasty, impact_level');
      
      if (eventsErr) throw eventsErr;

      // Fetch all relationships
      const { data: relData, error: relErr } = await supabase
        .from('relationships')
        .select('id, source, target, type, description');
      
      if (relErr) throw relErr;

      const nodes: Array<Person | Event> = [
        ...(peopleData as Person[] || []),
        ...(eventsData as Event[] || [])
      ];

      return {
        nodes,
        links: relData as Relationship[] || []
      };
    } catch (err) {
      this.logger.error('Failed to fetch graph data from Supabase', err);
      // Fallback mock data if DB isn't ready
      return { nodes: [], links: [] };
    }
  }
}
