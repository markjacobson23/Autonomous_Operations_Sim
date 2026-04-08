# Current Phase

## Active roadmap step
Step 8 — Simple dispatcher

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: complete
- Step 7: complete
- Step 8: active
- Step 9: not started

## What already exists
The repository already has:
- working package structure
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing and `Router`
- `SimulationEngine` with explicit simulated time
- single-vehicle route execution
- deterministic trace output
- jobs, tasks, and shared resources

## Goal of the current phase
Add a baseline dispatcher that chooses which job a vehicle should execute next.

The main Step 8 objective is:
- introduce a dispatcher interface
- add one deterministic baseline dispatch policy
- connect dispatch selection to existing job execution
- support job completion under simple load

## In-scope work
Work that is allowed right now:
- add `operations/dispatcher.py`
- add a dispatcher interface/protocol
- add one concrete baseline dispatcher
- integrate dispatch choice with existing engine/job execution
- add tests for assignment correctness and repeated deterministic execution
- small additive refactors that make Step 8 cleaner without introducing Step 9 concepts

## Out-of-scope work
Do not do any of the following in the current phase:
- add multi-vehicle road conflict handling
- add advanced optimization or search
- add behavior systems
- add learning-based dispatch
- add broad planning frameworks

## Architectural guidance for this phase
- Keep the dispatcher interface small.
- Keep the baseline policy simple and deterministic.
- Reuse existing jobs/tasks/resources execution instead of duplicating it.
- Do not overbuild dispatch abstractions yet.

## Completion criteria for Step 8
Step 8 is complete when:
- a dispatcher interface exists
- a baseline dispatcher can select a job deterministically
- selected jobs execute correctly through the existing engine/job path
- tests/lint/type checks pass
