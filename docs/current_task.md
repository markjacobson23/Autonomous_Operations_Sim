# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 6 — Operator integration

## Objective

Expose Unity route progress, embodiment state, and blockage state through operator-facing surfaces without creating shadow truth.

This task is about making the browser/operator flow understand what Unity is doing and what it is reporting, while keeping Python as the only authority.

## Why this task exists

Phases 1–5 established:

- a canonical Python ↔ Unity bridge
- real simulator bootstrap
- explicit motion authority
- Unity route execution over backend-issued routes
- backend-visible route progress
- backend-visible embodiment and blockage state

The next required step is to make those states visible and usable to operators.

The system must now support:

- inspecting Unity-driven progress from operator-facing read models
- seeing embodiment/blockage state in live views
- keeping command and replay flows coherent while Unity handles embodiment
- avoiding any client-side interpretation layer that becomes competing truth

## In scope

- expose Unity route progress, embodiment status, and blockage status in operator-facing read models or bundle surfaces
- keep the browser/live surfaces grounded in Python-owned state
- make inspection surfaces coherent for:
  - current motion authority
  - route progress
  - embodiment state
  - blockage/exception details
- keep replay/live/read-model flow stable
- preserve existing command and session control behavior
- preserve Python-motion mode unchanged

## Out of scope

- do not redesign routing or dispatch
- do not redesign the world model
- do not implement major UI redesigns
- do not add a second bridge or second read-model authority
- do not move operator truth into Unity
- do not add advanced analytics or explanation systems yet
- do not remove compatibility paths unless trivially safe

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - route legality
  - task identity
  - command truth
  - session truth

- Operator-facing surfaces must consume Python-owned read models, not directly trust Unity as authority

- Unity-originated progress and embodiment signals must be visible only through backend-owned projections

- Replay/live/read-model flow must remain coherent across Python-motion and Unity-motion sessions

## Required backend behavior

### Operator-facing projections

The live/operator-facing surfaces should expose, in a coherent way:

- motion authority
- route-following status
- route progress
- embodiment state
- blockage or exception details when present

These should appear in operator-facing bundle/read-model structures rather than being isolated only inside Unity bootstrap surfaces.

### Inspection coherence

At minimum, an operator should be able to inspect a vehicle and determine:

- whether it is Python-motion or Unity-motion
- whether it has an active route
- whether it is progressing, blocked, complete, or otherwise exceptional
- what the current blockage or embodiment issue is, if any

## Unity-side expectations

If the Unity project is present in the workspace, Unity does not need major new behavior for this phase.

Only make tiny Unity changes if needed to keep the operator-facing/read-model flow aligned with the existing bridge.

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- `autonomous_ops_sim/live_app.py`
- `autonomous_ops_sim/unity_bridge.py`
- tests covering operator-facing live/read-model behavior
- minimal frontend/read-model projection glue if required
- tiny Unity adjustments only if strictly needed

## Files that must not be broadly rewritten

- world-model files
- routing/dispatch architecture
- unrelated simulation subsystems
- large frontend redesign files
- large Unity runtime changes

## Deliverables

1. Operator-facing read-model exposure of Unity progress/embodiment state
2. Coherent vehicle inspection data for Unity-motion sessions
3. Stable live/replay/read-model flow that remains Python-authoritative
4. Tests validating backend/operator-facing projection behavior
5. Existing Python-only and Python-motion paths still working

## Acceptance criteria

This task is complete when:

- operator-facing surfaces can show Unity route progress and embodiment state
- blockage/exception details are visible through backend-owned read models
- vehicle inspection is coherent in Unity-motion sessions
- the browser/live/read-model flow remains grounded in Python truth
- existing command/session behavior still works
- Python-motion mode still works unchanged

## Practical rule

Prefer:

- exposing backend-owned truth clearly
- small read-model extensions over UI churn
- coherence across clients
- reversible changes

Reject:

- Unity-owned operator truth
- direct client dependence on Unity-only state
- giant UI rewrites
- second competing read models