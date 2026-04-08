# Current Phase

## Active roadmap step
Step 12 — Executable scenario harness

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
- Step 12: active
- Step 13: not started

## What already exists
The repository already has:
- scenario/config parsing and deterministic scenario summaries
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models through `Router`
- `SimulationEngine` with explicit simulated time and deterministic RNG
- single-vehicle route execution with deterministic trace output
- jobs, tasks, shared resources, and baseline dispatching
- deterministic multi-vehicle reservation-based conflict handling
- a vehicle behavior FSM with explicit transitions
- stable metrics summaries, deterministic exports, and golden regression coverage

## Goal of the current phase
Turn scenario files into real executable simulator runs rather than validation-only inputs.

The main Step 12 objective is:
- wire scenario input into end-to-end simulator execution
- keep the execution path deterministic
- produce stable export output directly from scenario-driven runs
- establish the scenario-run harness that later steps can build on

## In-scope work
Work that is allowed right now:
- add a scenario execution/orchestration path
- extend the CLI so a scenario can drive a real simulation run
- convert parsed scenario data into instantiated map/world-state/engine/runtime setup
- add deterministic export output for scenario-driven runs
- add at least one golden regression fixture for a scenario-driven run
- perform small additive refactors that make scenario execution cleaner without changing simulator scope

## Out-of-scope work
Do not do any of the following in the current phase:
- add real-time visualization
- add interactive live control surfaces
- promote a full persistent `Vehicle` entity model yet
- redesign the reservation/conflict algorithm
- add richer map import formats beyond what Step 12 strictly needs
- build a dashboard, viewer, or UI
- add broad command/replay infrastructure

## Architectural guidance for this phase
- Keep the current deterministic trace/export surface as the source of truth.
- Prefer orchestration code that reuses existing engine/job/dispatch APIs over new parallel execution paths.
- Keep schema expansion minimal and only introduce fields needed to support real scenario execution.
- Separate parsing from runtime instantiation cleanly.
- Do not smuggle in later-step visualization or interaction architecture.
- Avoid large rewrites.

## Completion criteria for Step 12
Step 12 is complete when:
- a scenario file can drive a real simulator run, not just validation/summary
- the CLI can produce deterministic export output from a scenario-driven run
- repeated runs with the same scenario produce identical output
- at least one scenario-run golden regression fixture exists
- tests/lint/type checks pass
