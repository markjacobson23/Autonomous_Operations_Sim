# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 4 — Route execution in Unity

## Objective

Implement the first end-to-end route execution slice where Unity can follow backend-issued route intent instead of only consuming a bootstrap snapshot.

This task is about route-following over backend truth, not about advanced physics, terrain realism, collision handling, or ML/AI behavior.

## Why this task exists

Phases 1–3 established:

- a canonical Python ↔ Unity bridge
- a real-simulator Unity bootstrap
- explicit motion authority
- a dedicated Unity bridge module

The next required step is to make Unity execute backend-issued route intent in a minimal but real way.

The system must now support:

- Python computing and owning route intent
- Unity consuming that route intent as waypoints or ordered route nodes
- Unity reporting route progress back through the canonical bridge
- Python tracking progress without surrendering operational truth

## In scope

- expose backend-issued route-following data in the canonical Unity bridge
- provide enough ordered route/waypoint information for Unity to follow a route
- implement minimal Unity-side route following for placeholder vehicles
- report route progress and arrival/completion back to Python through the canonical bridge
- keep progress and completion semantics explicit and backend-visible
- preserve stable vehicle identity mapping
- preserve Python-motion mode unchanged
- make Unity-route execution apply only where motion authority and current bridge semantics allow it

## Out of scope

- do not remove or break Python motion
- do not redesign routing or dispatch logic
- do not move route legality into Unity
- do not redesign the world model
- do not add terrain-aware driving yet
- do not add collision/blockage physics yet unless a tiny placeholder status is strictly needed
- do not add WebSockets or gRPC yet
- do not add ML-Agents, sensors, or advanced vehicle controllers yet
- do not implement per-vehicle authority switching unless a tiny seam is required for future support

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - route legality
  - task identity
  - command truth
  - session truth

- Unity may execute route motion only as an embodied client/runtime layer

- Unity route-following data must be derived from backend route truth, not invented locally

- The canonical bridge must remain the only Python ↔ Unity bridge path

## Required backend behavior

### Route intent for Unity

The canonical Unity bootstrap or related canonical bridge payload should expose enough backend-derived route information for Unity to follow a route for a vehicle under Unity motion authority.

At minimum, Unity should be able to determine:

- which vehicle has an active backend-issued route
- the ordered route nodes and/or waypoint positions
- the current destination / target node
- when the backend considers the route pending vs active vs complete if such state is already available

### Progress feedback

Unity must report route-following progress back to Python through the canonical telemetry/bridge path.

At minimum, the bridge should support reporting:

- vehicle id
- current position/speed/timestamp
- current route progress signal
- current target waypoint/node if known
- arrival/completion signal when the route is finished

This task may extend the telemetry contract if needed, but must do so through the existing canonical bridge path rather than inventing a second reporting channel.

### Python-motion mode

In Python-motion mode:

- existing behavior must remain unchanged
- Unity route-following logic must not become authoritative

### Unity-motion mode

In Unity-motion mode:

- Unity may follow backend-issued route data
- Python still owns operational/task/command truth
- progress and completion must remain backend-visible and must not bypass Python session truth

## Unity-side expectations

If the Unity project is present in the workspace, Unity should:

- consume the route-following data from the canonical bootstrap/bridge payload
- move placeholder vehicles along the ordered route in a minimal, deterministic way
- preserve stable `vehicle_id` identity
- avoid taking over backend concepts like command legality or task truth
- report progress back to Python through the existing bridge

Minimal placeholder movement is acceptable.
This phase is about route execution semantics, not realism.

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- `autonomous_ops_sim/unity_bridge.py`
- `autonomous_ops_sim/live_app.py`
- tests covering route-following bridge behavior
- Unity bootstrap/runtime consumer code for minimal route execution
- tiny glue changes required by the canonical bridge

## Files that must not be broadly rewritten

- world-model files
- routing/dispatch architecture
- unrelated frontend/operator files
- unrelated simulation subsystems
- full terrain/physics systems
- unrelated Unity scene systems

## Deliverables

1. Backend-derived route-following data exposed through the canonical bridge
2. Minimal Unity-side route execution over backend-issued route intent
3. Progress/completion reporting back to Python through the canonical bridge
4. Tests validating backend-side route/progress contract behavior
5. Existing Python-only and Python-motion paths still working

## Acceptance criteria

This task is complete when:

- Unity can follow backend-issued routes in a minimal way
- route data is clearly derived from backend truth
- route progress and arrival/completion are reported back to Python
- Python can track route progress without surrendering operational truth
- the existing bridge remains canonical
- Python-motion mode still works unchanged

## Practical rule

Prefer:

- explicit route/progress contracts
- additive seams over redesign
- minimal placeholder movement over ambitious realism
- behavioral clarity over visual polish

Reject:

- Unity-owned route legality
- local route invention in Unity
- second bridge/reporting channels
- premature terrain/physics complexity
- giant rewrites