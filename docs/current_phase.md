# Current Phase

## Active roadmap step
Step 19 — Visualization state surface and first viewer

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
- Step 19: active
- Step 20: not started

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
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, dispatch, and multi-vehicle coordination
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Add a visualization state surface and a first narrow viewer so simulator runs can be watched without making the UI the source of simulator truth.

The main Step 19 objective is:
- expose stable visualization-oriented state derived from the simulator
- support replay/viewing of runs in a deterministic way
- add a minimal first viewer that consumes the visualization state surface
- preserve clean separation between simulator logic and presentation

## In-scope work
Work that is allowed right now:
- add a visualization-state module or export surface
- derive stable frame/snapshot data from map + vehicles + world state + trace and/or command history
- add a minimal first viewer, likely text/CLI or very lightweight local viewer, that consumes the visualization state surface
- support deterministic playback of completed runs
- add tests for visualization-state generation and stable replay order
- add at least one regression fixture or exact-output comparison for visualization state output
- perform additive refactors and targeted normal refactors needed to keep the visualization surface clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add full live interactive manipulation
- add a heavy web app or dashboard
- redesign the simulator around a render loop
- make the viewer own runtime truth
- overbuild animation/rendering infrastructure
- redesign the command/control layer beyond what a viewer minimally needs

## Architectural guidance for this phase
- The viewer must consume simulator state; it must not become the source of truth.
- Prefer a stable visualization-state surface over direct engine introspection inside UI code.
- Start with deterministic replay of completed runs, not a full live interactive UI.
- Keep the first viewer narrow and lightweight.
- Reuse existing map, vehicle, trace, export, and command-history surfaces where possible.
- Avoid dangerous rewrites.

## Completion criteria for Step 19
Step 19 is complete when:
- a stable visualization-oriented state surface exists
- at least one narrow viewer can consume that surface to show vehicle/map/run state
- playback/viewing is deterministic for the same run
- tests/lint/type checks pass
