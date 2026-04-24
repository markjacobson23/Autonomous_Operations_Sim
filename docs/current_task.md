# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 7 — Replay and analysis groundwork

## Objective

Add a backend-owned replay/analysis surface for Unity-influenced runs so operators and future tools can inspect what happened after or during a run without relying on Unity as a source of truth.

This task is about creating a minimal but real replay/analysis foundation, not a full analytics platform.

## Why this task exists

Phases 1–6 established:

- a canonical Python ↔ Unity bridge
- explicit motion authority
- backend-owned route progress and embodiment state
- operator-facing read models grounded in Python truth

The next useful extension is to make run history inspectable as a coherent replay/analysis surface.

The system must now support:

- understanding what happened during a Unity-motion run
- reconstructing route progress and embodiment events from backend-owned history
- viewing a stable replay/analysis summary without inventing new authority

## In scope

- add a backend-owned replay/analysis surface derived from existing Python-owned history
- expose route progress history and embodiment/blockage history in a structured replay/analysis record
- include enough session/run metadata to understand what happened
- make the replay/analysis surface available through the live bundle or a closely related backend-owned surface
- preserve current operator/live behavior
- preserve Python-motion mode unchanged

## Out of scope

- do not redesign routing or dispatch
- do not redesign the world model
- do not implement full timeline scrubbers or major frontend replay UI
- do not add sensors or ML/AI runtime features yet
- do not create a second source of truth
- do not move replay authority into Unity
- do not do a broad analytics/dashboard rewrite

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - route legality
  - task identity
  - command truth
  - session truth
  - replay/analysis truth

- Replay/analysis must be derived from backend-owned state and history, not from Unity-local memory

- The canonical Python ↔ Unity bridge remains singular
- Replay data may consume Unity-originated signals only after they have been ingested into Python-owned runtime state

## Required backend behavior

### Replay/analysis projection

The backend should expose a replay/analysis record that includes, at minimum:

- session/run identity
- motion authority
- route progress history
- embodiment/blockage history
- notable vehicle-level events or state transitions where already derivable
- counts or summaries useful for operator understanding

### Vehicle-level analysis

At minimum, a vehicle-level analysis record should allow a user or future tool to determine:

- whether a vehicle was under Python or Unity motion authority
- whether it completed its route
- whether it became blocked
- what blockage/exception state occurred
- what progress history is known from backend-owned records

## Frontend expectations

If frontend/operator code is touched, keep changes minimal.

Allowed frontend work:
- parse the replay/analysis surface
- expose a small operator-facing summary or inspection view if helpful

Do not turn this into a major replay UI build.

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- `autonomous_ops_sim/live_app.py`
- `autonomous_ops_sim/unity_bridge.py`
- tests covering replay/analysis projection behavior
- minimal frontend adapter/read-model glue if needed

## Files that must not be broadly rewritten

- world-model files
- routing/dispatch architecture
- unrelated simulation subsystems
- large frontend redesign files
- large Unity runtime changes

## Deliverables

1. A backend-owned replay/analysis surface
2. Vehicle-level route/embodiment history projection
3. Stable replay/analysis data for Unity-motion sessions
4. Tests validating replay/analysis projection behavior
5. Existing Python-only, Python-motion, and operator-read-model paths still working

## Acceptance criteria

This task is complete when:

- a backend-owned replay/analysis surface exists
- Unity-originated route/embodiment history is visible only through Python-owned records
- a vehicle’s route completion/blockage history can be inspected coherently
- current live/operator flows still work
- Python remains the only authority

## Practical rule

Prefer:

- backend-owned replay truth
- small structured projections
- incremental inspection value
- reversible changes

Reject:

- Unity-owned replay truth
- giant replay UI rewrites
- analytics sprawl
- second competing histories