# Current Phase

## Active roadmap step
Step 7 — Jobs, tasks, and resources

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: complete
- Step 7: active
- Step 8: not started

## What already exists
The repository already has:
- working package structure
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing and `Router`
- `SimulationEngine` with explicit simulated time
- single-vehicle route execution
- deterministic trace output

## Goal of the current phase
Add task/job primitives and shared resources so the simulator can model operational work rather than only route traversal.

The main Step 7 objective is:
- introduce tasks such as move/load/unload
- introduce jobs as ordered sequences of tasks
- introduce shared resources with limited capacity
- support waiting/service timing in simulated time

## In-scope work
Work that is allowed right now:
- add `operations/tasks.py`
- add `operations/jobs.py`
- add `operations/resources.py`
- integrate tasks/jobs/resources with the existing engine and trace
- add tests for queueing/service timing and ordered task execution
- small additive refactors that make Step 7 cleaner without introducing Step 8 concepts

## Out-of-scope work
Do not do any of the following in the current phase:
- add dispatcher logic
- add multi-vehicle road-network conflict handling
- add behavior systems
- add optimization frameworks
- add rich scheduling policies

## Architectural guidance for this phase
- Keep tasks small and explicit.
- Keep jobs as ordered collections of tasks.
- Keep resources limited and concrete.
- Do not overbuild workflow abstractions.
- Keep engine as the coordinator, not the home of every operation concept.

## Completion criteria for Step 7
Step 7 is complete when:
- move/load/unload task primitives exist
- jobs can execute ordered task sequences
- shared resources can cause waiting
- service timing is represented in simulated time
- tests/lint/type checks pass
