# Step 14 Persistent Vehicle Entity Model

## Goal
Finish Step 14 cleanly by promoting a real persistent vehicle/entity model into the execution path.

## Required implementation
Refactor the simulator so vehicle runtime execution uses a meaningful `Vehicle` entity instead of relying primarily on threaded scalar fields.

## Required design
- Expand `autonomous_ops_sim/vehicles/vehicle.py` into a real execution-facing entity
- Refactor the relevant execution paths so `VehicleProcess` and/or `SimulationEngine` operate on a `Vehicle` object where appropriate
- Ensure the vehicle model relates cleanly to:
  - position / current node
  - payload / max payload
  - max speed
  - behavior state integration
  - scenario-instantiated runtime state
- Update scenario execution so parsed `VehicleSpec` objects are turned into runtime `Vehicle` entities

## Required behavior
- Runtime execution can use a persistent `Vehicle` object
- The vehicle’s core runtime state is represented explicitly and consistently
- Existing job execution, dispatch execution, and trace behavior continue to work deterministically
- Repeated runs with the same scenario still produce identical output

## Minimum expected scope
At minimum, Step 14 should support:
- scenario-instantiated runtime vehicles
- execution paths that rely on vehicle objects rather than passing speed/payload/start state as scattered scalars everywhere
- tests covering vehicle-backed single-vehicle execution and scenario execution

## Design constraints
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not redesign multi-vehicle coordination
- Do not overbuild a giant vehicle lifecycle/domain framework
- Do not introduce ECS/actor-system rewrites
- Keep the implementation small and production-like

## Preferred strategy
- Keep `Vehicle` narrow and execution-oriented
- Migrate the most important runtime vehicle state first
- Reduce duplication between `Vehicle`, `VehicleProcess`, and behavior controller
- Preserve backward-compatible outward behavior where reasonable
- Prefer clear ownership over convenience mirroring

## Tests to add
Add tests for:
- scenario execution instantiates and uses runtime vehicles
- vehicle-backed job execution remains deterministic
- vehicle-backed dispatch execution remains deterministic
- repeated runs produce identical summary/export output
- any intentional trace/export changes are covered and golden fixtures updated if needed

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
