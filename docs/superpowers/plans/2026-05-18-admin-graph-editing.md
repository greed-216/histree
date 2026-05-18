# Admin Graph Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first usable admin graph editor for person relationships, event participation, and event causality.

**Architecture:** Keep person and event node CRUD as-is. Add a focused NestJS `relationships` module that owns edge listing, creation, update, deletion, duplicate checks, dangling edge checks, and public/admin-safe DTO shaping. Extend shared types so the frontend can use typed relationship rows, then add a third admin tab that edits all three edge kinds with existing `apiFetch` auth mechanics.

**Tech Stack:** NestJS, Supabase JS, React, Vite, TypeScript, `@histree/shared-types`.

---

### Task 1: Shared Relationship Contracts

**Files:**
- Modify: `packages/shared-types/src/index.ts`

- [x] **Step 1: Define three row types and payload types**

Add `PersonRelationship`, `PersonEventRelation`, `EventCausalityRelation`, and corresponding input aliases that omit `id` and `created_at`.

- [x] **Step 2: Type-check dependents**

Run: `pnpm --filter web build`

Expected: Existing build should still compile, or fail only on unrelated pre-existing issues.

### Task 2: Relationship API

**Files:**
- Create: `apps/api/src/modules/relationship/relationship.module.ts`
- Create: `apps/api/src/modules/relationship/relationship.controller.ts`
- Create: `apps/api/src/modules/relationship/relationship.service.ts`
- Modify: `apps/api/src/app.module.ts`
- Test: `apps/api/src/modules/relationship/relationship.service.spec.ts`

- [x] **Step 1: Write failing service tests**

Test duplicate person relationships, self-event causality rejection, and missing endpoint row validation.

- [x] **Step 2: Run test to verify red**

Run: `pnpm --filter api test -- relationship.service.spec.ts`

Expected: FAIL because the module/service do not exist.

- [x] **Step 3: Implement the minimal relationship service and controller**

Expose:
- `GET /api/v1/relationships`
- `POST /api/v1/relationships/person-relationships`
- `PATCH /api/v1/relationships/person-relationships/:id`
- `DELETE /api/v1/relationships/person-relationships/:id`
- `POST /api/v1/relationships/person-events`
- `PATCH /api/v1/relationships/person-events/:id`
- `DELETE /api/v1/relationships/person-events/:id`
- `POST /api/v1/relationships/event-causalities`
- `PATCH /api/v1/relationships/event-causalities/:id`
- `DELETE /api/v1/relationships/event-causalities/:id`

- [x] **Step 4: Run tests to verify green**

Run: `pnpm --filter api test -- relationship.service.spec.ts`

Expected: PASS.

### Task 3: Admin Relationship Tab

**Files:**
- Modify: `apps/web/src/pages/AdminPage.tsx`

- [x] **Step 1: Add relationship state and loaders**

Load people, events, and relationship bundle together after admin verification.

- [x] **Step 2: Add the third tab**

Add `关系` tab with compact forms and tables for the three edge types.

- [x] **Step 3: Add save/delete handlers**

Use authenticated `apiFetch` calls to the new relationship endpoints.

- [x] **Step 4: Build frontend**

Run: `pnpm --filter web build`

Expected: PASS.

### Task 4: Smoke Coverage

**Files:**
- Modify: `scripts/e2e-smoke.mjs`

- [x] **Step 1: Add anonymous-write denial checks**

Check anonymous POSTs to all three relationship create endpoints return `401`.

- [x] **Step 2: Run available verification**

Run:
- `pnpm --filter api test -- relationship.service.spec.ts`
- `pnpm --filter web build`

Expected: both pass.
