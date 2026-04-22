export interface Person {
  id: string;
  name: string;
  courtesy_name?: string;
  aliases?: string[];
  era?: string;
  faction?: string;
  native_place?: string;
  birth_year?: number;
  death_year?: number;
  description?: string;
  biography?: string;
  historical_evaluation?: string;
  tags?: string[];
  family?: Array<{
    name: string;
    relation: string;
    note?: string;
  }>;
  social_relations?: Array<{
    person_id?: string;
    name: string;
    relation: string;
    note?: string;
  }>;
  image_url?: string;
  type: 'person';
}

export interface Event {
  id: string;
  title: string;
  start_year?: number;
  end_year?: number;
  dynasty?: string;
  description?: string;
  impact_level?: number;
  tags?: string[];
  phases?: Array<{
    title: string;
    start_year?: number;
    end_year?: number;
    description?: string;
  }>;
  image_url?: string;
  location_lat?: number;
  location_lng?: number;
  location_name?: string;
  type: 'event';
}

export interface Edge {
  source: string; // id of node
  target: string; // id of node
  type: string; // enemy / ally / participated / causes / etc.
  description?: string;
}

export interface GraphResponse {
  center: Person | Event;
  nodes: Array<Person | Event>;
  edges: Edge[];
}

export interface EventDetail extends Event {
  related_people: {
    person: Person;
    role: string;
  }[];
  cause_events: Event[];
  effect_events: Event[];
}

export interface Source {
  id: string;
  title: string;
  source_type: 'primary' | 'reference' | 'scholarship' | 'digital' | 'media';
  author?: string;
  edition?: string;
  url?: string;
  note?: string;
}

export interface FactClaim {
  id: string;
  subject_table: string;
  subject_id: string;
  field_path: string;
  claim_text: string;
  source_id?: string;
  citation?: string;
  confidence?: number;
  note?: string;
}
