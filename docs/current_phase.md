# Current Phase

## Active roadmap step
Step 21 — Environment/map realism expansion

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
- Step 20: complete
- Step 21: active
- Step 22: not started

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
- a thin interaction layer translating viewer-facing actions into commands
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, dispatch, and multi-vehicle coordination
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Expand environment and map realism beyond the current narrow grid-first assumptions while preserving deterministic runtime behavior and clean topology/runtime boundaries.

The main Step 21 objective is:
- add richer map/environment semantics
- support a more realistic topology representation than the current grid-only focus
- preserve compatibility with the existing routing, execution, visualization, and command surfaces
- avoid destabilizing the simulator with a giant map/import rewrite

## In-scope work
Work that is allowed right now:
- add a narrow richer map/environment model or map kind
- add explicit environment/site semantics where they map cleanly to existing runtime concepts
- extend scenario schema and map construction as needed for the chosen realism improvement
- adapt routing/execution surfaces only where necessary to support the richer topology
- add deterministic tests and at least one richer environment scenario fixture/regression surface
- perform additive refactors and targeted normal refactors needed to keep map/environment ownership clean

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the simulator around GIS or a heavy map framework
- add a giant import pipeline for many map formats
- build a full world editor
- redesign command/control, visualization, or workload foundations
- overbuild zone/site semantics beyond the narrow realism gain chosen for this step

## Architectural guidance for this phase
- Keep static topology and runtime state separate.
- Prefer one narrow environment/map realism improvement and implement it well.
- Reuse existing `Map`, routing, scenario, visualization, and execution surfaces where possible.
- Avoid turning this into a broad asset/import framework prematurely.
- Preserve deterministic behavior and stable regression surfaces.
- Avoid dangerous rewrites.

## Completion criteria for Step 21
Step 21 is complete when:
- the simulator supports one meaningful map/environment realism improvement beyond the current baseline
- the improvement is scenario-driven or otherwise cleanly integrated
- routing/execution/visualization still work over the richer map model
- tests/lint/type checks pass
