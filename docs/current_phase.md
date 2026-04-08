# Current Phase

## Active roadmap step
Step 11 — Scenario packs, metrics, visualization hooks, and optional external wrapper

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
- Step 11: active

## What already exists
The repository already has:
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing and `Router`
- `SimulationEngine` with explicit simulated time
- single-vehicle route execution and deterministic trace output
- jobs, tasks, and shared resources
- a baseline dispatcher
- deterministic multi-vehicle conflict handling
- a vehicle-centric behavior layer

## Goal of the current phase
Add stable outward-facing analysis surfaces so simulator runs can be measured, exported, and regression-tested.

The main Step 11 objective is:
- add metrics summaries
- add stable export formats
- add a golden-scenario regression surface
- optionally add minimal visualization hooks without overbuilding

## In-scope work
Work that is allowed right now:
- add metrics/summary modules
- add export support such as JSON and/or CSV
- add a stable golden-scenario regression test
- add minimal visualization hooks if they stay small
- small additive refactors that improve external usability without changing simulator scope

## Out-of-scope work
Do not do any of the following in the current phase:
- build a large dashboard or UI
- build a broad RL framework unless it stays clearly optional and minimal
- overbuild rendering/animation systems
- turn this step into general cleanup without a clear metrics/export/regression goal

## Architectural guidance for this phase
- Prefer derived metrics as the main stable outward-facing surface.
- Keep export formats simple and stable.
- Favor regression-friendly outputs over flashy presentation.
- Keep visualization hooks minimal and decoupled.

## Completion criteria for Step 11
Step 11 is complete when:
- stable metrics summaries exist
- at least one structured export format exists
- at least one golden-scenario regression test exists
- tests/lint/type checks pass
