export interface Person {
  id: string;
  name: string;
  era?: string;
  birth_year?: number;
  death_year?: number;
  description?: string;
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
  type: 'event';
}

export interface Edge {
  source: string; // id of node
  target: string; // id of node
  type: string; // enemy / ally / participated / causes / etc.
  description?: string;
}

export interface GraphResponse {
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
