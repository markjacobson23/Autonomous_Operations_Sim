# Current Phase

## Active roadmap step
Step 29 — Profiling and benchmark harness

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
- Step 23: complete
- Step 24: complete
- Step 25: complete
- Step 26: complete
- Step 27: complete
- Step 28: complete
- Step 29: active
- Step 30: not started

## What already exists
The repository already has:
- deterministic scenario parsing and execution
- operational jobs/resources/dispatch/workloads
- typed command/control surfaces with deterministic history
- visualization replay state
- text and graphical replay viewers
- improved playback and live interaction UX
- graph-map realism
- optional research comparison tooling
- a live simulation session bridge
- a live sync surface between runtime and viewer layers

## Goal of the current phase
Add a disciplined profiling and benchmark harness so performance/scaling work is driven by measurements rather than guesses.

The main Step 29 objective is:
- make performance visible
- benchmark the main likely hotspots
- establish stable measurement surfaces for later optimization work
- preserve the simulator’s deterministic architecture while evaluating its scaling behavior

## In-scope work
Work that is allowed right now:
- add benchmark/profiling modules or scripts
- benchmark routing behavior
- benchmark reservation/conflict handling where practical
- benchmark scenario-pack execution throughput
- benchmark replay/export/sync generation costs where practical
- define stable benchmark result formats or summaries
- add deterministic tests for benchmark harness behavior where appropriate
- perform additive refactors and targeted normal refactors needed to keep performance instrumentation clean

## Out-of-scope work
Do not do any of the following in the current phase:
- prematurely optimize algorithms without measurement
- split components into other languages yet
- redesign the simulator around benchmarking concerns
- weaken determinism or trace/export stability for speed
- build a large performance dashboard/platform

## Architectural guidance for this phase
- Measure first, optimize later.
- Keep benchmark code separate from core simulator logic where possible.
- Favor stable, scriptable benchmark surfaces over ad hoc timing snippets.
- Benchmark the current architecture honestly, including replay/viewer-facing surfaces where relevant.
- Preserve clean boundaries and avoid dangerous rewrites.

## Completion criteria for Step 29
Step 29 is complete when:
- a repeatable benchmark/profiling harness exists
- major likely hotspots have baseline measurements
- benchmark outputs are stable and useful enough to guide optimization work
- tests/lint/type checks pass
