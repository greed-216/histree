# Histree Product Roadmap

## Product North Star

Histree should become a source-aware history knowledge platform. The core value is not a prettier encyclopedia page; it is helping users see how people, states, institutions, wars, reforms, ideas, and geography change each other over time.

The product should treat data as the durable asset and graph/timeline/map views as different lenses over the same knowledge graph.

## Data Strategy

### 1. Knowledge Model

Core entities:

- Person: names, aliases, lifespan, era, state/dynasty, roles, biography, portraits.
- Event: title, time range, uncertainty, location, description, impact level, involved parties.
- Polity or Organization: states, dynasties, families, armies, schools of thought.
- Place: historical place names, modern coordinates, confidence, alternate names.
- Work or Idea: texts, reforms, institutions, strategies, doctrines.
- Source: citation, author, title, quote, reliability, URL or bibliographic info.

Core edges:

- Person to person: ruler-minister, ally, rival, teacher-student, kinship.
- Person to event: commander, reformer, ruler, envoy, victim, author, participant.
- Event to event: causes, enables, escalates, responds_to, resolves, precedes.
- Person/event to polity: rules, serves, attacks, reforms, defects_to.
- Entity to source: supported_by, disputed_by.

### 2. Data Quality Workflow

- Every important node and edge should eventually have at least one source.
- Add confidence fields for uncertain dates, locations, and causality.
- Separate draft and published data.
- Keep audit metadata: created_by, updated_by, reviewed_by, reviewed_at.
- Use stable IDs or slugs so graph links remain shareable.

### 3. Initial Content Plan

Start with dense, connected periods instead of trying to cover all history shallowly:

- Spring and Autumn / Warring States: reforms, hegemonies, diplomacy, wars.
- Qin-Han transition: unification, collapse, Chu-Han contention, early Han institutions.
- Late Eastern Han / Three Kingdoms: warlord networks, campaigns, regime formation.

For each period, build curated “paths”:

- Reform path: 管仲改革 -> 商鞅变法 -> 秦制扩张.
- Hegemony path: 齐桓公 -> 晋文公 -> 楚庄王 -> 吴越争霸.
- Unification path: 合纵连横 -> 长平之战 -> 秦灭六国.

## Presentation Strategy

### 1. Graph First

The graph page should become the main reading surface:

- Depth control: 1-hop, 2-hop, curated path.
- Edge filters: people, events, causality, political relations, military relations.
- Timeline scrubber: show graph state at a year or range.
- Side panel: selected node details, citations, related paths, map preview.
- Layout modes: force graph, chronological tree, cause-effect chain.

### 2. Tree Views

Use tree layouts when the question has direction:

- Event causality tree: causes above, consequences below.
- Political succession tree: rulers, states, dynasties.
- Influence tree: ideas, reforms, texts, institutional inheritance.
- Campaign tree: battles, commanders, locations, outcomes.

### 3. Timeline and Map

Timeline and map should not be separate “nice extras.” They should filter the graph:

- Drag a year range to dim unrelated nodes.
- Click a location to show events and actors there.
- Compare two periods or two states side by side.

### 4. Admin UX

Admin should be a graph editor, not a table editor:

- Left: entity search and filters.
- Center: editable graph canvas.
- Right: structured inspector for node/edge fields.
- Inline source attachment.
- Relationship creation by dragging from one node to another.
- Data validation warnings before publish.

## Engineering Iterations

### Iteration 1: Consistency and Seeds

- Make Explore, People, Events, Admin read from the same API-backed data.
- Add curated seed data for Spring and Autumn / Warring States.
- Add smoke tests for public pages and protected admin writes.

### Iteration 2: Admin Graph Editing

- Add API endpoints for person relationships, person-event roles, and event causality.
- Add Admin tabs or split panes for relationships.
- Add validation: no dangling edges, no duplicate edges, no self-causality.

### Iteration 3: Source-Aware Schema

- Add `source`, `entity_source`, and `edge_source` tables.
- Add confidence, status, slug, updated_at, created_by, updated_by.
- Add RLS policies for draft vs published data.

### Iteration 4: Graph Presentation

- Rebuild GraphPage with controls for depth, filters, layout mode, and timeline range.
- Add tree layout for causality and succession.
- Add shareable graph URLs with query params.

### Iteration 5: Content Production

- Create a data import format: CSV/JSON for nodes, edges, and sources.
- Add review workflow for generated or imported data.
- Build curated collections for one historical period at a time.

## Immediate Next Step

Build relationship management in Admin. Without edge editing, Histree cannot really become a graph knowledge platform; it will remain a list of people and events with hidden links.
