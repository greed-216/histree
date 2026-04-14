export interface Person {
  id: string;
  name: string;
  era: string;
  description: string;
}

export interface Event {
  id: string;
  title: string;
  time_start: number;
  time_end: number;
  description: string;
  dynasty: string;
  impact_level: number;
}

export type RelationshipType = 'enemy' | 'ally' | 'ruler' | 'cause-effect' | 'participant';

export interface Relationship {
  id: string;
  source: string; // id of Person or Event
  target: string; // id of Person or Event
  type: RelationshipType;
  description?: string;
}

export interface GraphData {
  nodes: Array<Person | Event>;
  links: Relationship[];
}
