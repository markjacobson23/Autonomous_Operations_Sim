# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 1 — Contract and bridge

## Objective

Implement the first simulator-shaped Python ↔ Unity bridge using HTTP/JSON.

This task is about proving the contract end to end, not about building full physics, sensors, or a final Unity runtime.

## Why this task exists

The project direction is now:

- Python remains authoritative for operational and simulator truth
- Unity becomes the embodied runtime layer
- motion authority must become explicit instead of implicit

Before any deeper Unity work, the codebase needs a clean round-trip bridge:
- Python sends bootstrap / target or route intent
- Unity consumes it
- Unity reports telemetry back

## In scope

- define the initial Unity-facing bootstrap payload
- define the initial telemetry payload
- add or document the Python endpoint surface for bootstrap + telemetry
- preserve stable vehicle identity between Python and Unity
- keep the contract versioned and explicit
- keep transport simple: HTTP/JSON first

## Out of scope

- do not remove or break Python motion
- do not move routing or dispatch logic into Unity
- do not redesign the world model
- do not add WebSockets or gRPC yet
- do not add ML-Agents, sensors, or advanced physics behavior yet
- do not create a Unity-only source of truth

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - task identity
  - routing legality
  - command truth
  - session truth

- Unity may execute motion, but only as a client/runtime layer under Python authority

- The bridge must not invent a separate data model that conflicts with existing backend bundle concepts

## Initial payload requirements

### Bootstrap payload

The initial bootstrap payload should be simulator-shaped and include at least:

- metadata/schema version
- runtime vehicle snapshot
- pending target or route intent
- enough world/topology context for Unity to instantiate basic runtime objects

A minimal acceptable form is a backend-derived projection, not a throwaway one-field JSON forever.

### Telemetry payload

The initial telemetry payload should include at least:

- vehicle id
- x/y/z position
- speed
- timestamp

If easy and safe to include now, also allow:
- heading/rotation
- nearest node id or current edge id

## Allowed files to change

Only the minimum files needed for the bridge slice.

Expected categories:
- Python live/session bridge or API surface
- serialization / payload building
- tests or validation coverage
- docs only if needed to clarify the contract

## Files that must not be broadly rewritten

- static world model files
- routing/dispatch architecture
- unrelated frontend/operator workflow files
- unrelated simulation subsystems

## Deliverables

1. A defined bootstrap contract
2. A defined telemetry contract
3. A minimal Python implementation path for serving and receiving them
4. Stable vehicle identity mapping
5. Clear notes or tests showing how the round trip is expected to work

## Acceptance criteria

This task is complete when:

- Python can provide a Unity-consumable bootstrap payload
- Unity can be expected to consume the payload without relying on ad hoc one-off fields
- Unity can send telemetry back in a stable format
- the bridge preserves Python authority
- the work does not break the existing Python-only path

## Practical rule

Prefer:
- additive seams
- explicit contracts
- reversible changes
- fallback-safe behavior

Reject:
- giant rewrites
- Unity-owned operational truth
- client-side shadow state
- premature complexity