# Frontend

This directory contains the Next.js Kanban demo UI used by the MVP.

## Current Stack

- Next.js App Router (`src/app`)
- React + TypeScript
- Tailwind CSS v4
- `dnd-kit` for drag and drop
- Vitest + Testing Library for unit tests
- Playwright for end-to-end tests

## Core Areas

- `src/components/` Kanban board, columns, cards, and add-card form
- `src/lib/kanban.ts` board data model and card move helpers
- `tests/` Playwright e2e specs

## Part 3 Notes

- Frontend builds as static export (`next.config.ts` => `output: "export"`).
- Docker builds frontend assets and backend serves them at `/`.

## Part 4 Notes

- `AuthGate` controls login state on `/` by calling backend auth APIs.
- Board renders only when session is authenticated.
- Logout returns the user to the sign-in form.

## Part 7 Notes

- `KanbanBoard` now loads board state from `GET /api/board`.
- Board mutations persist via `PUT /api/board`.
- UI state remains persisted after browser reload.
