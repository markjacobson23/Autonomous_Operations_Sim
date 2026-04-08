# Current Phase

## Active roadmap step
Step 13 — Scenario schema for operations

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
- Step 13: active
- Step 14: not started

## What already exists
The repository already has:
- scenario parsing and deterministic summaries
- executable scenario-driven runs for a narrow single-vehicle job path
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, baseline dispatch, and multi-vehicle conflict handling
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Expand the scenario schema so scenario files can describe more of the operational world and runtime setup.

The main Step 13 objective is:
- move more execution configuration into scenario files
- support scenario-defined resources
- support scenario-defined runtime world-state setup
- support scenario-defined dispatcher selection/config in a narrow form
- keep scenario-driven execution deterministic and regression-friendly

## In-scope work
Work that is allowed right now:
- add resource specs to the scenario schema
- add runtime blocked-edge/world-state initialization to the scenario schema
- add dispatcher selection/config to the scenario schema in a narrow form
- extend scenario loading and validation
- extend scenario execution/orchestration to instantiate these runtime objects
- add richer executable scenario fixtures and golden regression coverage
- make small additive refactors that keep scenario execution clean

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the persistent vehicle/entity model
- add visualization
- add interactive control/command surfaces
- redesign multi-vehicle coordination
- add richer map import formats
- over-generalize the scenario schema
- build a broad scenario DSL

## Architectural guidance for this phase
- Keep schema growth minimal and tied to real execution needs.
- Keep parsing separate from runtime instantiation.
- Reuse existing operations/runtime surfaces rather than creating parallel structures.
- Prefer one narrow fully working scenario-driven configuration path over a flexible but half-finished schema.
- Preserve deterministic trace/export behavior.

## Completion criteria for Step 13
Step 13 is complete when:
- scenarios can define resources used by execution
- scenarios can define initial runtime blocked-edge/world-state conditions
- scenarios can define dispatcher selection in a narrow supported form
- scenario-driven execution remains deterministic
- at least one richer scenario-run golden regression fixture exists
- tests/lint/type checks pass
