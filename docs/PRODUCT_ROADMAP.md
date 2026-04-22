# Histree Product Roadmap

## Product North Star

Histree should become a source-aware history knowledge platform. Its core value is not to be another encyclopedia page, but to help readers see how people, institutions, geography, events, texts, and power structures change each other over time.

The product should treat data as the durable asset. Graphs, trees, timelines, maps, and institutional diagrams are different lenses over the same verified historical knowledge base.

## Method: The Four Keys

Deng Guangming's well-known "four keys" for studying Chinese history are usually summarized as:

- Chronology: 年代学
- Historical geography: 历史地理
- Official institutions: 职官制度
- Bibliography/catalogue studies: 目录学

For Histree, these should become product architecture, not just background theory:

- 目录学 becomes source discovery, citation, edition tracking, and "why do we know this?"
- 年代学 becomes comparable timelines for people, events, regimes, offices, and institutions.
- 历史地理 becomes maps, historical place-name changes, administrative regions, routes, and spatial scope.
- 职官制度 becomes institutional structure: office hierarchy, appointment routes, administrative levels, rank, authority, and operating rules.

The current person-event graph is closest to a catalogue-style entry point: it tells the reader what is related to what. The next stage must add source provenance, time, space, and institutional structure so the graph becomes historically intelligible rather than just visually connected.

Useful references for the framing:

- 中国社会科学网《中国社会科学报》, 方志远, "历史研究的六把钥匙", 2024-12-18.
- 北京大学新闻网, "邓广铭与二十世纪的宋代史学", notes Deng Guangming's 1956 "four keys" formulation.
- 中国青年报/中青在线, "一代宗师，北大教授邓广铭", discusses time, place, people, and the four keys.

## Data Model Roadmap

### 1. Sources and Bibliography

Every meaningful fact should eventually be traceable.

Core tables:

- `source`: book/article/database/webpage/archive item.
- `source_edition`: edition, publisher, year, volume, page range, URL, stable identifier.
- `citation`: exact reference target, quote, translation, note, confidence.
- `fact_claim`: typed claim linked to entity or edge, with source and confidence.
- `entity_source` and `edge_source`: lightweight links for MVP compatibility.

Initial source types:

- Primary sources: 正史、编年、出土文献、碑志、地方志、文集.
- Reference works: 辞典、历史地图集、职官表、年表.
- Modern scholarship: monographs, journal articles, edited volumes.
- Stable digital resources: CNKI/DOI metadata, 中国哲学书电子化计划, Wikidata as auxiliary, official museum/library pages.

Admin requirements:

- Every node and edge can attach one or more sources.
- Source note supports page/juan/chapter/entry fields.
- Mark source role: direct evidence, modern interpretation, disputed, image/media source.
- Show "unsourced" warnings before publishing.

### 2. Chronology

Time is not a single field. It needs uncertainty and comparison.

Core tables:

- `time_span`: start/end date, precision, calendar system, uncertainty note.
- `entity_time_span`: lifespan, reign, office tenure, campaign duration, event duration.
- `timeline_lane`: curated comparative lanes, such as "秦国", "赵国", "楚国", "思想文化".

Product views:

- Person lifespan and activity timeline.
- Event duration and phases.
- Side-by-side comparison of multiple people.
- State/dynasty timeline lanes.
- Time-filtered graph: show only nodes and edges active in a year or range.

Important details:

- Support BCE years.
- Support approximate dates: circa, before, after, range, disputed.
- Keep Chinese reign year / lunar date as source notation where available.

### 3. Historical Geography

Place must support historical names, modern coordinates, and changing administrative scope.

Core tables:

- `place`: canonical place, modern coordinate, current administrative location.
- `place_name`: historical names, period, language/script, source.
- `geo_region`: polygon or bounding box for states, commanderies, counties, routes, battle areas.
- `entity_place`: person's activity range, office location, exile route, campaign path, event location.

Product views:

- Event map with exact point and broader involved region.
- Person activity map across life phases.
- State/polity territorial map by time slice.
- Route maps for exile, campaigns, diplomatic missions, migration.
- Map-linked graph: clicking a place filters related people/events.

Data sources to evaluate:

- 谭其骧《中国历史地图集》 as a reference baseline, respecting copyright limits.
- CHGIS for historical GIS where usable.
- Harvard WorldMap / open historical GIS datasets where licensing permits.
- Wikidata/GeoNames only as auxiliary modern coordinates, never as final authority.
- Local gazetteers and specialized atlases for period-specific validation.

### 4. Offices, Institutions, and Social Structure

职官制度 should expand into the operating structure of society and state.

Core tables:

- `institution`: court, ministry, commandery, county, army, school, lineage, estate.
- `office`: office title, rank, parent office, jurisdiction, period, appointment rules.
- `office_tenure`: person, office, start/end, appointing authority, source.
- `rank_system`: rank, salary, privilege, civil/military category.
- `social_group`: ruler, aristocracy, scholar-official, military, commoner, slave, artisan, merchant, etc.

Product views:

- Institutional hierarchy tree.
- Career path timeline for a person.
- Office-holder list by period.
- "How the state works" diagrams for a dynasty or state.
- Relationship between office, geography, and events: who had authority where, when, and over whom.

Initial content suggestion:

- Start with Warring States states: ruler, ministers, generals, county/commandery prototypes, reform offices.
- Then Qin-Han: emperor, three excellencies/nine ministers, commandery-county system, military titles.
- Later add Tang/Song because source material and office systems are richer but more complex.

## Knowledge Graph Model

Core entities:

- Person: names, aliases, lifespan, era, state/dynasty, roles, biography, portraits.
- Event: title, time range, uncertainty, location, description, impact level, involved parties.
- Polity or organization: states, dynasties, families, armies, schools of thought.
- Place: historical place names, modern coordinates, confidence, alternate names.
- Office and institution: hierarchy, rank, jurisdiction, operating rules.
- Work or idea: texts, reforms, institutions, strategies, doctrines.
- Source: citation, author, title, edition, quote, reliability, URL or bibliographic info.

Core edges:

- Person to person: ruler-minister, ally, rival, teacher-student, kinship.
- Person to event: commander, reformer, ruler, envoy, victim, author, participant.
- Event to event: causes, enables, escalates, responds_to, resolves, precedes.
- Person/event to polity: rules, serves, attacks, reforms, defects_to.
- Person to office: holds, appointed_to, promoted_to, dismissed_from.
- Office to institution: belongs_to, reports_to, supervises.
- Entity or edge to source: supported_by, disputed_by.

## Presentation Roadmap

### Graph First

The graph page should become the main reading surface:

- Depth control: 1-hop, 2-hop, curated path.
- Edge filters: people, events, causality, political relations, offices, geography, sources.
- Timeline scrubber: show graph state at a year or range.
- Side panel: selected node details, citations, related paths, map preview.
- Layout modes: force graph, chronological tree, cause-effect chain, institution tree.

### Timeline View

Timeline should support comparison, not just listing:

- Put multiple people on one timeline.
- Overlay events, offices, states, reigns, reforms, wars.
- Support filters by state, region, office, source confidence.
- Show uncertainty visually, e.g. fuzzy ranges or dotted bars.

### Map View

Maps should explain spatial scope:

- Event point plus involved region.
- Person activity areas by phase.
- State borders by time slice.
- Campaign/diplomatic routes.
- Link map selection to graph and timeline filters.

### Institution View

Institution diagrams should explain structure:

- Hierarchy tree of offices.
- Career path through offices.
- Administrative layers from ruler to local society.
- Compare institutions across time: e.g. pre-Qin state structures vs Qin-Han bureaucracy.

### Source View

Every content panel should show provenance:

- "Sources" tab for each node and edge.
- Inline footnote markers for key claims.
- Source quality labels: primary source, reference work, modern scholarship, auxiliary dataset.
- Disputed claim display: show competing accounts rather than flattening disagreement.

## Admin Roadmap

### Stage 1: Graph Editing

- Add relationship CRUD: person-person, person-event, event-event.
- Add validation: no dangling edges, no duplicate edges, no self-causality.
- Add entity search and relationship creation from the graph canvas.

### Stage 2: Source Editing

- Add source library.
- Attach citations to entities and edges.
- Require source notes for published important claims.
- Add "unsourced / low confidence / disputed" review filters.

### Stage 3: Time and Place Editing

- Replace single year/location fields with structured time spans and places.
- Add precision and uncertainty.
- Add historical place-name aliases.
- Add map preview in editor.

### Stage 4: Institution Editing

- Add offices, institutions, ranks, jurisdictions.
- Add office tenure editor for people.
- Add institution tree editor and validation.

### Stage 5: Content Pipeline

- Import CSV/JSON for nodes, edges, sources, citations.
- Add review workflow for generated/imported data.
- Keep draft/published states and audit logs.

## Content Acquisition Plan

Start with curated, period-specific corpora:

1. Spring and Autumn / Warring States:
   `左传`, `国语`, `战国策`, `史记`, `资治通鉴` as source anchors, plus modern reference works.

2. Qin-Han transition:
   `史记`, `汉书`, `资治通鉴`, archaeological notes where applicable, maps and office references.

3. Late Eastern Han / Three Kingdoms:
   `三国志`, Pei Songzhi annotations, `后汉书`, `资治通鉴`.

Data workflow:

- Build a source bibliography first.
- Extract people/events/places/offices with source citations.
- Add edges only when source-supported or clearly marked as interpretive.
- Review by period, not by isolated entity.

## Engineering Iterations

### Iteration 1: Consistency and Seeds

- Make Explore, People, Events, Admin read from the same data.
- Add curated seed data for Spring and Autumn / Warring States.
- Upload portraits and media with source tracking.
- Add smoke tests for public pages and protected admin writes.

### Iteration 2: Source-Aware Schema

- Add source, citation, fact claim, entity-source, edge-source tables.
- Add confidence, status, slug, updated_at, created_by, updated_by.
- Show source panels on public pages.

### Iteration 3: Admin Relationship and Source Editing

- Add Admin panels for person relationships, event participation, event causality.
- Add source attachment to all node and edge forms.
- Add validation and review filters.

### Iteration 4: Timeline and Geography

- Add structured time spans.
- Add place and historical place-name model.
- Add timeline comparison page and map filters.

### Iteration 5: Institution System

- Add offices, institutions, ranks, tenures.
- Add institution tree and career timeline views.
- Start with Warring States and Qin-Han institutions.

## Immediate Next Step

Implement the source-aware schema and admin source library first. Without provenance, adding more data will create technical debt. After that, build relationship editing and structured time/place models so the graph can become a historically meaningful tree, timeline, and map system.
