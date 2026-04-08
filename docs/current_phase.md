# Current Phase

## Active roadmap step
Step 20 — Interactive manipulation layer

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
- Step 18: complete
- Step 19: complete
- Step 20: active
- Step 21: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- a persistent runtime-facing `Vehicle` entity integrated into execution
- deterministic scenario-pack / batch execution with stable aggregate outputs
- a narrow richer-operations workload path for repeated dispatch over time
- upgraded corridor-aware deterministic coordination
- a typed control-command surface with deterministic command history
- a visualization state surface with replay frames
- a first text-based viewer consuming visualization state
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, dispatch, and multi-vehicle coordination
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Add a narrow interactive manipulation layer so the simulator can accept viewer-facing runtime actions through the existing command/control architecture.

The main Step 20 objective is:
- connect interaction intent to the command surface
- support a small set of meaningful interactive actions
- preserve deterministic command ordering and replayability
- make the simulator feel manipulable without introducing a heavy UI framework

## In-scope work
Work that is allowed right now:
- add an interaction layer or viewer-facing control adapter
- support a narrow initial interactive action set such as:
  - assign destination
  - reposition vehicle
  - inject blocked edge
- connect those actions to the existing typed command/controller surface
- extend the viewer in a narrow way if needed to accept user-directed actions
- add deterministic tests for interaction-to-command behavior
- add at least one regression fixture or exact-output comparison for an interaction-driven run
- perform additive refactors and targeted normal refactors needed to keep the interaction layer clean

## Out-of-scope work
Do not do any of the following in the current phase:
- build a heavy graphical UI framework
- redesign the simulator around an event loop or async runtime
- add free-form direct engine mutation from the viewer
- overbuild a full product UI or dashboard
- redesign scenario execution, coordination, or visualization foundations
- add broad environment/map realism work

## Architectural guidance for this phase
- Interactions should translate into explicit commands, not bypass them.
- Preserve deterministic ordering and replayability.
- Keep viewer concerns separate from runtime ownership logic.
- Start with a small set of interactions that map directly to existing command types.
- Prefer a thin adapter layer over a large UI-control framework.
- Avoid dangerous rewrites.

## Completion criteria for Step 20
Step 20 is complete when:
- a narrow set of viewer-facing interactions can drive the simulator through the command surface
- interaction-driven runs remain deterministic and replayable
- at least one interaction-driven regression/demo surface exists
- tests/lint/type checks pass
