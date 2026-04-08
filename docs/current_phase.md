# Current Phase

## Active roadmap step
Step 14 — Persistent vehicle entity model

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: complete
- Step 7: complete
- Step 8: complete
- Step 9: complete
- Step 10: complete
- Step 11: complete
- Step 12: complete
- Step 13: complete
- Step 14: active
- Step 15: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, baseline dispatch, and multi-vehicle conflict handling
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Promote a real persistent vehicle/entity model so execution flows stop relying primarily on threaded scalar vehicle parameters.

The main Step 14 objective is:
- make `Vehicle` a meaningful execution-facing runtime entity
- connect vehicle state cleanly to `VehicleProcess`, behavior, trace, and scenario execution
- reduce scalar threading for things like speed, payload, and location
- preserve determinism and existing trace/export surfaces

## In-scope work
Work that is allowed right now:
- expand `autonomous_ops_sim/vehicles/vehicle.py` into a real runtime-facing entity
- refactor execution paths to accept/use a `Vehicle` object where appropriate
- define clear ownership between vehicle state, behavior state, and process execution
- update scenario execution to instantiate runtime vehicles from `VehicleSpec`
- add tests proving the vehicle entity is integrated into execution without changing behavior semantics
- perform additive refactors and targeted normal refactors needed to reduce scalar parameter threading

## Out-of-scope work
Do not do any of the following in the current phase:
- add visualization
- add interactive control/command surfaces
- redesign multi-vehicle coordination
- add richer map import formats
- build a fleet-management optimization framework
- overbuild a large domain model around vehicles
- rewrite the simulator around ECS/actor frameworks

## Architectural guidance for this phase
- Keep the vehicle model small, explicit, and execution-facing.
- Avoid duplicating the same runtime truth across `Vehicle`, `VehicleProcess`, and behavior state.
- Preserve trace-centered observability and deterministic behavior.
- Reuse existing engine/job/dispatch paths instead of creating parallel vehicle execution flows.
- Prefer one clear runtime ownership model over convenience duplication.
- Avoid dangerous rewrites.

## Completion criteria for Step 14
Step 14 is complete when:
- a persistent `Vehicle` entity is meaningfully used in runtime execution
- key scalar vehicle parameters are no longer threaded everywhere they do not need to be
- scenario execution instantiates runtime vehicles cleanly
- existing behavior/trace/export semantics remain stable or are intentionally updated with test coverage
- tests/lint/type checks pass
