# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 2 — Real simulator bootstrap

## Objective

Build on the existing Phase 1 HTTP/JSON Unity bridge so Unity can consume a clearer real-simulator bootstrap and instantiate a minimal runtime scene from backend truth.

This task is about improving and stabilizing the bootstrap contract, not about implementing motion authority switching, full route execution, advanced physics, sensors, or AI runtime features.

## Why this task exists

Phase 1 proved the bridge seam:
- Python can serve a Unity bootstrap payload
- Unity telemetry can be ingested by Python
- Python authority was preserved

Phase 2 exists to make that bridge more usable for real Unity integration:
- the bootstrap should be more clearly derived from real simulator/runtime surfaces
- the payload should be easier for Unity to consume as a minimal scene/runtime description
- stable identity and backend-owned intent should remain explicit

## In scope

- tighten the Unity-facing bootstrap contract
- keep the contract versioned and explicit
- ensure the bootstrap is clearly derived from real simulator/runtime surfaces
- preserve stable vehicle identity mapping
- preserve pending route or target intent projection
- include enough world/topology/geometry context for Unity to instantiate a basic runtime scene
- if the Unity project is available in the workspace, implement the minimum bootstrap consumer there

## Out of scope

- do not remove or break Python motion
- do not switch motion authority yet
- do not move routing, dispatch, or command legality into Unity
- do not redesign the world model
- do not add WebSockets or gRPC yet
- do not add ML-Agents, sensors, or advanced physics behavior yet
- do not create a Unity-only source of truth
- do not implement full route following unless a tiny amount is strictly needed for bootstrap validation

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - task identity
  - routing legality
  - command truth
  - session truth

- Unity may consume and embody simulator state, but must not become the source of operational truth

- The bridge must continue using one canonical Python ↔ Unity path rather than introducing a second competing bridge

- The bootstrap should remain a backend-derived projection, not a standalone Unity-only data model

## Bootstrap requirements

The Phase 2 bootstrap should include at least:

- metadata/schema version
- authority fields
- session/runtime identity
- real world/topology data derived from backend surfaces
- render/world-form geometry usable for minimal Unity instantiation
- runtime vehicle snapshot
- stable vehicle identity mapping
- pending route/target intents
- bridge endpoint or contract info if still useful

The payload should be simulator-shaped and easy to consume, but should not duplicate or replace backend truth ownership.

## Telemetry expectations

The existing telemetry path should remain intact.

Telemetry should continue to support at least:
- vehicle id
- x/y/z position
- speed
- timestamp

If already supported safely, continue allowing:
- heading/rotation
- nearest node id or current edge id

Phase 2 is not about expanding telemetry deeply; it is about making the bootstrap more usable.

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- Python live/session bridge or API surface
- serialization / payload building
- tests or validation coverage
- Unity bootstrap consumer code, if the Unity project is available
- docs only if needed to clarify the contract

## Files that must not be broadly rewritten

- static world model files
- routing/dispatch architecture
- command semantics
- unrelated frontend/operator workflow files
- unrelated simulation subsystems

## Deliverables

1. A clearer Phase 2 Unity bootstrap contract
2. A Python implementation path that serves the Phase 2 bootstrap
3. Stable backend-owned vehicle identity mapping
4. Tests or validation showing the bootstrap is real-simulator-derived and stable
5. If Unity project is present, a minimal bootstrap consumer that instantiates placeholder runtime objects from the payload

## Acceptance criteria

This task is complete when:

- the Unity bootstrap is clearly derived from real simulator/runtime surfaces
- the payload is sufficient for minimal Unity scene/runtime instantiation
- stable vehicle identities are preserved
- pending route or target intent remains backend-owned and visible
- the existing Python-only path still works
- Python authority is preserved throughout

## Practical rule

Prefer:
- additive seams
- explicit contracts
- reversible changes
- fallback-safe behavior
- one canonical bridge path

Reject:
- giant rewrites
- Unity-owned operational truth
- client-side shadow state
- premature transport complexity
- a second bridge contract that competes with the first