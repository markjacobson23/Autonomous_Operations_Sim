# Current Phase

## Active roadmap step
Step 5 — Simulation engine and clock

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: active
- Step 6: not started

## What already exists
The repository already has:
- working package structure
- `pyproject.toml`
- CLI entry point
- pytest / Ruff / mypy baseline
- CI workflow
- scenario/config spine
- static map/topology separated from runtime blocked-edge state via `WorldState`
- `CostModel` routing
- `Router` as the public routing surface

## Goal of the current phase
Introduce a first-class simulation engine with explicit simulated time and deterministic run control.

The main Step 5 objective is:
- add `SimulationEngine`
- define engine run control around simulated time
- make seed ownership explicit at the engine level
- prepare a clean foundation for later vehicle/process execution without implementing Step 6 yet

## In-scope work
Work that is allowed right now:
- add `simulation/engine.py`
- introduce explicit simulated time
- implement `run(until_s)`
- use SimPy internally if helpful
- add tests for engine initialization, run control, and determinism
- small additive refactors that make Step 5 cleaner without introducing Step 6 behavior

## Out-of-scope work
Do not do any of the following in the current phase:
- add single-vehicle route-following processes
- add trace/event systems beyond minimal engine necessities
- add jobs/resources/dispatch logic
- add multi-vehicle logic
- add behavior systems

## Architectural guidance for this phase
- Keep the public engine API small.
- Simulated time is the focus, not rich agent behavior yet.
- Do not overbuild abstractions around the clock.
- Prefer a production-looking engine surface over a toy script-driven loop.

## Completion criteria for Step 5
Step 5 is complete when:
- `SimulationEngine` exists
- engine tracks simulated time explicitly
- `run(until_s)` works
- same seed and same initial setup produce deterministic engine-level behavior
- tests/lint/type checks pass
