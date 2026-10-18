# Part 1 Report: Research and Design

## Repository: https://github.com/AJP7521/prest-mental-health

Date: October 15, 2026

## Project purpose

The planned application supports short, structured mental-health skill exercises. Part 1 covers research and design; a working application is not required. This report documents the requirements and proposed design from `AGENTS.md` and `README.md`. External research and clinical validation have not yet been completed.

## Supported exercises

### Paced breathing

Guide the user through a 4-second inhale and a 6-second exhale, repeated for 60 seconds. This produces six complete breathing cycles and stays below the specified 90-second limit. Show the current breathing action with a simple animation and provide a persistent stop control.

### 5-4-3-2-1 grounding

Present one item at a time, preserving this sequence:

1. Five things the user can see.
2. Four things the user can feel.
3. Three things the user can hear.
4. Two things the user can smell.
5. One thing the user can taste.

The proposed interface lets the user advance at their own pace without requiring written responses. Stop and return controls remain available throughout.

## User experience

Users choose their preferred exercise from the skill-selection screen. During an exercise, the screen emphasizes the current action and avoids menus or large amounts of information. Completing an exercise is optional; model suggestions must never force participation.

Crisis-support access remains visible on every screen, including loading and error states, without depending on a menu, model response, or multiple navigation steps. The specification requires fictional support access for the prototype. Label it clearly as a demonstration so it does not imply a connection to real assistance.

## Proposed architecture

Development runs on localhost with separate `frontend/` and `backend/` directories.

| Component | Technology | Responsibilities |
| --- | --- | --- |
| Frontend | Vue | Navigation, skill selection, breathing animations, exercise progression, stop controls, crisis-support controls, and loading states |
| Backend | FastAPI | API routes, SQLite access, session records, skill history, conversation history, and error handling |
| Persistence | SQLite | Store fictional prototype records through the backend |

## Proposed session behavior

An exercise session can be active, completed, or stopped. Explicit user actions control starting and stopping; reaching the final exercise step marks completion. A stopped session must not be recorded as completed. If saving fails, the user should still be able to stop and return to skill selection.

Use synthetic data for development. Before implementation, define the minimum fields needed for session, skill, and conversation history, along with retention and deletion behavior. Do not commit credentials or identifiable health information.

## Current status and remaining work

The workspace currently contains project documentation. The frontend, backend, database, and automated tests are not yet implemented.

Remaining Part 1 work includes:

- Gathering and documenting research sources for the proposed exercises.
- Creating wireframes for selection, exercise, completion, stopped, loading, and error states.
- Defining API contracts and a minimal database schema.
- Reviewing accessibility, keyboard navigation, and reduced-motion behavior.
- Checking that every screen preserves stop or return controls where applicable and visible fictional support access.

## Verification

This report was checked against `AGENTS.md`, `README.md`, and the current workspace contents. No application tests were run because there is no application or test tooling yet.
