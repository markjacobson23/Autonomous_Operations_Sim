# Current Phase

## Active roadmap step
Step 23 — Graphical replay viewer foundation

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
- Step 21: complete
- Step 22: complete
- Step 23: active
- Step 24: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- richer operational scenario support
- a persistent runtime-facing vehicle model
- scenario-pack / batch execution
- repeated-work workload execution
- corridor-aware coordination
- typed command/control surfaces
- visualization replay state and a text viewer
- viewer-facing interactions translated into commands
- graph-map realism
- optional research comparison tooling

## Goal of the current phase
Build the first real graphical viewer on top of the existing visualization replay surface.

The main Step 23 objective is:
- render map and vehicle replay state graphically
- consume the existing visualization state rather than bypassing it
- preserve deterministic playback over completed runs
- establish the first true graphical visualization milestone without overcommitting to a heavy UI architecture

## In-scope work
Work that is allowed right now:
- add a graphical replay viewer on top of `VisualizationState`
- render nodes, edges, vehicles, and frame progression
- support narrow replay controls over completed runs, such as:
  - frame stepping
  - play / pause
  - reset to start
- reuse existing visualization export/load/replay surfaces
- add deterministic tests for visualization state consumption where feasible
- add at least one regression or demonstrative fixture for graphical replay input/output behavior
- perform additive refactors and targeted normal refactors needed to keep viewer boundaries clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add live runtime manipulation yet
- redesign the simulator around a render loop
- bypass visualization state and read deep engine internals directly from the viewer
- build a heavy product-style dashboard
- add streaming/network architecture yet
- start performance or language separation work prematurely

## Architectural guidance for this phase
- The graphical viewer must consume visualization state as a client surface.
- Start with replay of completed runs, not live simulation control.
- Keep the viewer small and demonstrative.
- Keep the simulator core authoritative.
- Stay open to future mixed-stack separation, but do not force it yet.
- Avoid dangerous rewrites.

## Completion criteria for Step 23
Step 23 is complete when:
- a real graphical replay viewer exists
- it renders map and vehicle progression from `VisualizationState`
- replay remains deterministic for the same run
- tests/lint/type checks pass
