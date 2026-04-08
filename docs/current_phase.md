# Current Phase

## Active roadmap step
Step 6 — Single-vehicle execution and trace

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: active
- Step 7: not started

## What already exists
The repository already has:
- working package structure
- `pyproject.toml`
- CLI entry point
- pytest / Ruff / mypy baseline
- CI workflow
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing
- `Router` as the public routing surface
- `SimulationEngine` with explicit simulated time and deterministic run control

## Goal of the current phase
Add single-vehicle execution over simulated time and record a deterministic trace.

The main Step 6 objective is:
- execute one vehicle over a route
- advance simulated time correctly
- emit trace events in deterministic order
- prepare a clean foundation for later jobs/resources without implementing Step 7 yet

## In-scope work
Work that is allowed right now:
- add `simulation/trace.py`
- add a single-vehicle execution module such as `simulation/vehicle_process.py`
- integrate single-vehicle execution with `SimulationEngine`
- advance simulated time according to traversal timing
- add tests for trace monotonicity, event ordering, and arrival timing
- small additive refactors that make Step 6 cleaner without introducing Step 7 concepts

## Out-of-scope work
Do not do any of the following in the current phase:
- add jobs/tasks/resources
- add queues or service resources
- add dispatcher logic
- add multi-vehicle logic
- add behavior systems beyond what is strictly needed for one vehicle following a route
- add rich visualization systems

## Architectural guidance for this phase
- Keep the engine as the run coordinator.
- Keep vehicle execution logic separate from engine core.
- Keep trace types small and explicit.
- Prefer event records over overbuilt telemetry frameworks.
- Do not overbuild an agent architecture yet.

## Completion criteria for Step 6
Step 6 is complete when:
- one vehicle can follow a route over simulated time
- trace events are emitted in monotone time order
- arrival timing matches expected traversal timing
- tests/lint/type checks pass
