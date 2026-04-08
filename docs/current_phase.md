# Current Phase

## Active roadmap step
Step 18 — Control-command surface

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
- Step 14: complete
- Step 15: complete
- Step 16: complete
- Step 17: complete
- Step 18: active
- Step 19: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- a persistent runtime-facing `Vehicle` entity integrated into execution
- deterministic scenario-pack / batch execution with stable aggregate outputs
- a narrow richer-operations workload path for repeated dispatch over time
- upgraded corridor-aware deterministic coordination
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, dispatch, and multi-vehicle coordination
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Add a replayable control-command surface that can drive simulation changes through explicit commands rather than ad hoc direct mutation.

The main Step 18 objective is:
- introduce explicit simulation commands
- support deterministic command application and replayability
- create a clean bridge between the deterministic simulator core and future interactive tooling
- preserve trace/export stability and small public interfaces

## In-scope work
Work that is allowed right now:
- add a command/control module for simulation actions
- support a narrow initial command set, such as:
  - pause/resume/step-oriented control state
  - assign destination
  - inject blocked edge / closure
  - reposition vehicle
- define how commands are validated and applied to runtime state
- add deterministic command application tests
- add at least one regression fixture or exact-output comparison for command-driven execution
- perform additive refactors and targeted normal refactors needed to keep the command surface clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add visualization
- add a full interactive UI
- redesign the simulator around async or a new runtime framework
- overbuild a generic command bus/event-sourcing platform
- add broad environment/map realism work
- redesign the entire engine lifecycle beyond what is needed for a narrow command surface

## Architectural guidance for this phase
- Commands should be explicit inputs to the simulator, not arbitrary direct state mutation.
- Keep the initial command set small and useful.
- Preserve deterministic ordering and replayability.
- Reuse existing engine/runtime/vehicle/world-state surfaces where possible.
- Keep command handling separate from visualization concerns.
- Avoid dangerous rewrites.

## Completion criteria for Step 18
Step 18 is complete when:
- the simulator has a narrow explicit control-command surface
- command application is deterministic and replayable
- at least one meaningful runtime change can be driven through commands
- tests/lint/type checks pass
