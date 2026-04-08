# Current Phase

## Active roadmap step
Step 15 — Evaluation and scenario-pack harness

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
- Step 15: active
- Step 16: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- a persistent runtime-facing `Vehicle` entity integrated into execution
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, baseline dispatch, and multi-vehicle conflict handling
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Add an evaluation and scenario-pack harness so the simulator can run multiple canonical scenarios deterministically and compare their results in a stable batch-oriented way.

The main Step 15 objective is:
- support scenario packs / batch execution
- generate stable per-scenario summary outputs
- create deterministic aggregate reporting across a pack
- strengthen the simulator as a benchmark and regression platform

## In-scope work
Work that is allowed right now:
- add a scenario-pack runner / benchmark harness
- define a narrow scenario-pack manifest or discovery convention
- batch-execute multiple scenario files deterministically
- collect stable per-scenario summaries and aggregate results
- add deterministic output conventions for pack-level results
- add tests for repeated deterministic batch execution
- add at least one scenario-pack regression fixture or equivalent stable comparison surface
- make small additive refactors that keep evaluation logic clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add visualization
- add interactive control/command surfaces
- redesign multi-vehicle coordination
- add richer map import formats
- build a dashboard or large reporting UI
- add optimization frameworks
- overbuild a full experiment platform beyond the narrow benchmark harness needed now

## Architectural guidance for this phase
- Keep the trace/export surface as the source of truth.
- Reuse existing scenario execution, metrics, and export paths.
- Prefer simple deterministic filesystem/ordering rules.
- Keep pack execution/reporting separate from simulator runtime logic.
- Favor stable machine-readable outputs over presentation-heavy reporting.
- Avoid dangerous rewrites.

## Completion criteria for Step 15
Step 15 is complete when:
- multiple scenarios can be executed deterministically through a batch/pack harness
- stable per-scenario summaries are produced
- deterministic aggregate pack output is produced
- repeated runs of the same scenario pack produce identical output
- tests/lint/type checks pass
