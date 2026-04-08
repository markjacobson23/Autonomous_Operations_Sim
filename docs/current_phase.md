# Current Phase

## Active roadmap step
Step 17 — Coordination upgrade

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
- Step 17: active
- Step 18: not started

## What already exists
The repository already has:
- deterministic scenario parsing and summaries
- executable scenario-driven runs
- scenario-defined resources, blocked-edge runtime setup, and dispatcher config
- a persistent runtime-facing `Vehicle` entity integrated into execution
- deterministic scenario-pack / batch execution with stable aggregate outputs
- a narrow richer-operations workload path for repeated dispatch over time
- static topology separated from runtime blocked-edge state via `WorldState`
- graph-based routing with injectable cost models
- deterministic simulated-time execution through `SimulationEngine`
- jobs, tasks, shared resources, baseline dispatch, and narrow multi-vehicle conflict handling
- vehicle behavior FSM with explicit transitions
- trace-centered metrics, exports, and golden regression coverage

## Goal of the current phase
Upgrade multi-vehicle coordination beyond the current narrow reservation baseline while preserving determinism and clear runtime boundaries.

The main Step 17 objective is:
- strengthen coordination logic for multi-vehicle movement
- improve conflict handling realism and observability
- add bounded coordination upgrades without destabilizing the simulator
- preserve deterministic trace/export behavior

## In-scope work
Work that is allowed right now:
- strengthen reservation/conflict handling in a narrow, explicit way
- improve multi-vehicle coordination semantics such as:
  - clearer wait behavior
  - better reservation conflict reasoning
  - bounded deadlock prevention or observability
  - narrow corridor/intersection-style handling if it stays small
- add deterministic multi-vehicle regression scenarios and fixtures
- extend metrics/trace only where needed to support the coordination upgrade
- perform additive refactors and targeted normal refactors needed to keep coordination logic clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add visualization
- add interactive control/command surfaces
- build a full MAPF or optimal planner framework
- redesign the simulator into an event-scheduling platform
- add broad map realism/import work
- overbuild coordination abstractions beyond the narrow upgrade needed now

## Architectural guidance for this phase
- Keep coordination logic deterministic and explicit.
- Prefer bounded upgrades to the existing reservation model over wholesale replacement.
- Preserve trace-centered observability; coordination changes should remain inspectable in trace/metrics.
- Reuse the current engine/runtime surfaces rather than creating a separate multi-agent subsystem.
- Add only the minimum new semantics needed to improve realism and safety.
- Avoid dangerous rewrites.

## Completion criteria for Step 17
Step 17 is complete when:
- multi-vehicle coordination is meaningfully stronger than the Step 9 baseline
- the upgraded coordination behavior is deterministic
- at least one stronger multi-vehicle regression scenario/fixture exists
- trace/metrics remain stable or are intentionally updated with coverage
- tests/lint/type checks pass
