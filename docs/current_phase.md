# Current Phase

## Active roadmap step
Step 22 — Optional research wrapper

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
- Step 22: active

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- richer scenario-driven operational setup
- a persistent runtime-facing `Vehicle` entity
- scenario-pack / batch execution
- repeated-work workload execution
- upgraded corridor-aware coordination
- typed command/control surfaces with deterministic history
- visualization replay state and a first viewer
- a thin interaction layer translating viewer intent into commands
- support for richer non-grid graph map scenarios with environment semantics
- deterministic routing, execution, metrics, exports, and golden regression coverage

## Goal of the current phase
Add a thin optional research/experimentation wrapper that makes the simulator easier to use for comparative experiments without turning the simulator into a research-framework-first codebase.

The main Step 22 objective is:
- expose a narrow experimentation wrapper on top of stable simulator surfaces
- support controlled comparison workflows
- preserve determinism and keep the wrapper clearly optional
- avoid redesigning the simulator around RL or benchmark framework assumptions

## In-scope work
Work that is allowed right now:
- add a thin optional experimentation wrapper or adapter
- support a narrow workflow such as:
  - policy comparison over existing scenario packs
  - command/interaction sequence comparison
  - wrapper-style step/reset interface for controlled experiments
- reuse existing scenario execution, command, visualization, and export surfaces
- add deterministic tests and at least one comparison/demo fixture
- perform additive refactors and targeted normal refactors needed to keep the wrapper clearly optional

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the simulator around Gym/RL APIs
- make research abstractions the new core architecture
- add a broad training framework
- add stochastic learning loops or optimization systems
- overbuild a benchmark platform beyond the narrow optional wrapper goal

## Architectural guidance for this phase
- The wrapper must sit on top of existing simulator surfaces.
- Keep it clearly optional and adapter-like.
- Preserve deterministic behavior and replayability.
- Prefer one narrow experimental workflow over a broad framework abstraction.
- Avoid changing core runtime ownership just to satisfy wrapper ergonomics.
- Avoid dangerous rewrites.

## Completion criteria for Step 22
Step 22 is complete when:
- one thin optional experimentation/research wrapper exists
- it reuses existing simulator surfaces cleanly
- deterministic comparison or wrapper-style execution is covered by tests
- tests/lint/type checks pass
