# Histree Refactor Plan

## Current Product Shape

Histree is a graph-first history explorer. The public experience lets users browse people, events, and relationship graphs. The private admin experience edits core historical entities and uploads images through Supabase Storage.

The current stack is:

- Web: React, Vite, Tailwind, D3, React Leaflet, Supabase client auth.
- API: NestJS, Supabase JS client, public graph/timeline/person/event endpoints, one protected upload endpoint.
- Data: Supabase Postgres tables for people, events, person relationships, person-event participation, event causality, user roles, and image/location fields.

## Main Problems

- Authorization is split across the browser, Supabase RLS, and one hand-written upload check. The browser can directly write to database tables, which makes permission behavior hard to audit.
- `user_roles` existed without RLS, so role data could be exposed through the public Supabase API.
- The web app treated any logged-in session as an admin in the navigation.
- Graph and detail services perform multiple sequential queries and do not consistently check Supabase errors.
- Admin only supports people and events. Relationships, event participation, causality, publishing state, sources, and review workflow are missing.
- UI is mostly MVP cards and tables. It lacks a clear information architecture, dense graph controls, search/filtering, and responsive admin workflows.
- Types are handwritten interfaces rather than generated or validated contracts.

## Target Architecture

1. API owns all writes.
   Public read endpoints can remain open. Admin writes, uploads, role management, and future moderation should go through NestJS guards and service methods.

2. Supabase RLS remains the final safety layer.
   Public tables allow read. Admin mutations require role checks. Role tables allow users to read only their own role, and admins to manage roles.

3. Data model becomes source-aware.
   Add citations/sources, confidence, aliases, tags, time ranges with uncertainty, geo confidence, created/updated metadata, and optional publish status.

4. Frontend uses a small API layer.
   Components should not know endpoint URLs or auth-header mechanics. React pages should deal in domain operations.

5. Admin becomes a graph editor.
   Manage entities and edges together: person-person relationships, event participation, event causality, media, locations, source notes, and draft/published state.

## Delivery Phases

### Phase 1: Stabilize

- Centralize frontend API calls.
- Fix admin role display and upload auth.
- Harden `user_roles` RLS.
- Add NestJS auth/admin guards and move admin mutations behind API endpoints.
- Add basic DTO validation and consistent HTTP errors.
- Add smoke tests for public graph reads and admin upload/write denial.

### Phase 2: Data Model

- Add `updated_at`, `created_by`, `updated_by`, `status`, `slug`, aliases, tags, source tables, and edge uniqueness constraints.
- Normalize relationship types into enums or lookup tables.
- Add indexes for graph expansion queries.
- Replace seed-only MVP data with migration-safe seed scripts.

### Phase 3: Product UX

- Redesign public layout around search, timeline, map, and graph modes.
- Add graph controls: depth, relation filters, layout reset, node search, edge legend, and selected path view.
- Redesign directories with search, dynasty filters, year ranges, and image-first cards.
- Redesign admin as a split-pane editor with entity forms and relationship panels.

### Phase 4: Quality

- Generate shared database/API types.
- Add API unit tests and e2e tests against a local Supabase fixture.
- Add frontend component tests for auth states and admin denial.
- Add CI scripts for lint, typecheck, build, and tests.

## Immediate Next Implementation

The next concrete engineering slice should move person/event CRUD from direct Supabase browser calls into NestJS admin endpoints guarded by a shared admin guard. After that, add relationship management so the admin panel can actually maintain the graph, not just isolated nodes.
