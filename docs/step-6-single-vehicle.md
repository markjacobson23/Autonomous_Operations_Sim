# Step 6 Single-Vehicle Execution

## Goal
Finish Step 6 cleanly without introducing Step 7 concepts.

## Required implementation
Add single-vehicle route execution over simulated time and a trace surface.

## Required design
- Add `autonomous_ops_sim/simulation/trace.py`
- Add a single-vehicle execution module such as `autonomous_ops_sim/simulation/vehicle_process.py`
- Integrate that execution path with `SimulationEngine`
- Use existing routing/world-state/engine surfaces rather than bypassing them

## Required behavior
- One vehicle can traverse a route from start to destination
- Simulated time advances consistently with traversal timing
- A deterministic trace is produced
- Trace events should be sufficient to observe route execution at the level of nodes/edges

## Minimum expected trace contents
At minimum, support trace events that can represent:
- route start / depart
- edge entry
- node arrival
- route completion

## Design constraints
- Do not add jobs/tasks/resources
- Do not add queue/resource logic
- Do not add dispatcher logic
- Do not add multi-vehicle logic
- Keep the trace model and vehicle execution surface small and production-like

## Tests to add
Add tests for:
- trace timestamps are monotone
- event ordering is correct for a simple route
- arrival time matches expected traversal timing
- repeated runs with the same seed/setup produce the same trace

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
