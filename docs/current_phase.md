# Current Phase

## Active roadmap step
Step 9 — Multi-vehicle conflict handling

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: complete
- Step 7: complete
- Step 8: complete
- Step 9: active
- Step 10: not started

## What already exists
The repository already has:
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing and `Router`
- `SimulationEngine` with explicit simulated time
- single-vehicle route execution and deterministic trace output
- jobs, tasks, and shared resources
- a baseline dispatcher

## Goal of the current phase
Add safe multi-vehicle movement coordination so conflicting occupancy is prevented deterministically.

The main Step 9 objective is:
- introduce a reservation/conflict mechanism
- support deterministic multi-vehicle planning/execution
- prevent double occupancy under the supported reservation model
- support simple waiting or replanning behavior when conflicts occur

## In-scope work
Work that is allowed right now:
- add a reservation table such as `simulation/reservations.py`
- add deterministic multi-vehicle coordination for a small supported case
- use priority order for initial conflict resolution
- support waiting and/or simple replanning as conflict response
- add tests for no double occupancy and deterministic conflict handling
- small additive refactors that make Step 9 cleaner without introducing Step 10 concepts

## Out-of-scope work
Do not do any of the following in the current phase:
- add behavior systems / FSM / BT layers
- add advanced MAPF optimization frameworks
- add broad planning frameworks
- add Step 10 behavior logic
- add Step 11 visualization/metrics expansion

## Architectural guidance for this phase
- Keep the reservation model explicit and testable.
- Prefer a narrow deterministic baseline over a clever but sprawling conflict system.
- Use graph-level reservation concepts that match the current abstraction level.
- Do not overbuild the first multi-vehicle implementation.

## Completion criteria for Step 9
Step 9 is complete when:
- multiple vehicles can be coordinated safely under the supported conflict model
- no double occupancy occurs under the tested cases
- deterministic priority handling works
- tests/lint/type checks pass
