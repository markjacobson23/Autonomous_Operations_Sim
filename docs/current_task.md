# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 5 — Terrain and physics embodiment

## Objective

Make Unity route execution physically meaningful enough to surface operationally relevant outcomes back to Python.

This task is about introducing the first terrain/physics embodiment seam, not about full realism.

## Why this task exists

Phases 1–4 established:

- a canonical Python ↔ Unity bridge
- real simulator bootstrap
- explicit motion authority
- Unity-side route execution over backend-issued routes
- backend-visible route progress and completion

The next required step is to make Unity execution produce physically meaningful outcomes rather than pure placeholder kinematic movement.

The system must now support:

- terrain-aware or scene-aware movement constraints
- basic collision or blockage detection
- backend-visible exception/blockage signals
- operational consequences that remain Python-owned

## In scope

- add a minimal terrain/physics embodiment layer to the Unity route-following path
- introduce basic collision or blockage detection for Unity-controlled vehicles
- report blockage/exception state back through the canonical telemetry bridge
- expose backend-visible embodiment status through the canonical Unity bridge state
- keep Unity movement simple but no longer purely abstract waypoint motion
- preserve route-following behavior from Phase 4
- preserve Python-motion mode unchanged

## Out of scope

- do not redesign routing or dispatch
- do not move route legality into Unity
- do not implement advanced vehicle dynamics
- do not implement realistic tire/suspension/traction simulation
- do not add ML-Agents, sensors, or advanced autonomy logic
- do not introduce a second reporting channel
- do not redesign the world model
- do not remove Python fallback behavior

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - route legality
  - task identity
  - command truth
  - session truth

- Unity may surface physically meaningful execution outcomes, but must not become the source of operational truth

- Terrain/physics effects must feed back into Python through the canonical bridge

- Unity must not invent new operational states that bypass backend visibility

## Required backend behavior

### Embodiment feedback

The backend telemetry/bridge path must support the first meaningful embodiment signals, such as:

- blocked or obstructed movement
- collision or contact event
- inability to reach the next waypoint under current local conditions
- route execution exception state if needed

These signals must be stored in Python-owned runtime state and be visible through the canonical bridge.

### Operational consequences

The backend should be able to observe that Unity route execution is no longer proceeding normally.

This task does not need to fully solve backend replanning or policy response, but it must make those conditions visible and structurally usable later.

## Unity-side expectations

If the Unity project is present in the workspace, Unity should:

- move route-following vehicles in a slightly more embodied way than pure abstract waypoint snapping
- use minimal built-in physics or collision-aware movement where appropriate
- detect when movement is blocked or colliding
- report that state back through the existing telemetry bridge
- keep placeholder visuals acceptable

This phase is about meaningful execution signals, not polished realism.

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- `autonomous_ops_sim/unity_bridge.py`
- `autonomous_ops_sim/live_app.py`
- tests covering embodiment/blockage feedback
- Unity route-following/runtime code for minimal terrain/physics embodiment
- tiny glue changes required by the canonical bridge

## Files that must not be broadly rewritten

- world-model files
- routing/dispatch architecture
- unrelated frontend/operator files
- unrelated simulation subsystems
- large Unity scene systems unrelated to route execution

## Deliverables

1. Minimal terrain/physics-aware Unity route execution
2. Canonical bridge support for blockage/exception feedback
3. Backend-visible embodiment status stored in Python-owned runtime state
4. Tests validating backend-side embodiment feedback behavior
5. Existing Python-only and Python-motion paths still working

## Acceptance criteria

This task is complete when:

- Unity execution can surface physically meaningful blockage/exception outcomes
- those outcomes are reported back to Python through the canonical bridge
- Python can observe embodiment failures without surrendering operational truth
- route execution still works in the non-blocked case
- the existing bridge remains canonical
- Python-motion mode still works unchanged

## Practical rule

Prefer:

- meaningful embodiment signals over ambitious realism
- explicit backend-visible status over local Unity-only behavior
- small, testable seams
- reversible changes

Reject:

- Unity-owned operational truth
- second reporting channels
- advanced realism before operational usefulness
- giant rewrites