# Current Phase

## Active roadmap step
Step 16 — Richer operations realism

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
- Step 16: active
- Step 17: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- a persistent runtime-facing `Vehicle` entity integrated into execution
- deterministic scenario-pack / batch execution with stable aggregate outputs
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, baseline dispatch, and multi-vehicle conflict handling
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Move from isolated one-job execution toward richer operations realism with multiple jobs over time and more meaningful fleet-style workload studies.

The main Step 16 objective is:
- support repeated or sequential operational work in one run
- make longer-lived workload execution possible without hand-stitching isolated single-job runs
- improve realism around ongoing work assignment and utilization-oriented studies
- preserve determinism and the existing trace/export surfaces

## In-scope work
Work that is allowed right now:
- add a narrow repeated-work / multi-job-over-time execution path
- support sequential job execution for a persistent vehicle within one scenario/run
- add scenario support for richer ongoing workload definitions only if needed for the chosen execution path
- extend metrics in narrow ways needed to summarize longer-lived operational runs
- add deterministic tests and at least one richer long-running scenario fixture/golden regression surface
- perform additive refactors and targeted normal refactors needed to keep workload execution clean

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign multi-vehicle coordination
- add visualization
- add interactive control/command surfaces
- add richer map import formats
- build a fleet optimization framework
- add stochastic demand generation unless it is tightly controlled and deterministic
- overbuild a scheduling/planning platform beyond the narrow richer-operations goal

## Architectural guidance for this phase
- Reuse the persistent vehicle model and existing engine/job/dispatch paths.
- Prefer a narrow, clearly deterministic longer-run execution path over broad operational ambition.
- Keep workload orchestration separate from low-level task execution.
- Preserve trace-centered observability and stable exports.
- Extend metrics only where they help characterize richer operations runs.
- Avoid dangerous rewrites.

## Completion criteria for Step 16
Step 16 is complete when:
- a persistent vehicle can execute multiple jobs over time within one coherent run
- richer operational workload behavior is scenario-driven or otherwise cleanly orchestrated
- deterministic summaries/exports remain stable for repeated runs
- at least one richer long-run regression fixture exists
- tests/lint/type checks pass
