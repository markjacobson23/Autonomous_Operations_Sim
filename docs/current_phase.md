# Current Phase

## Active roadmap step
Step 2 — Scenario/config spine with determinism plumbing

## Step status summary
- Step 1: complete
- Step 2: nearly complete
- Step 3: not started

## What already exists
The repository already has:
- working package structure
- `pyproject.toml`
- CLI entry point
- pytest / Ruff / mypy baseline
- CI workflow
- scenario dataclasses:
  - `Scenario`
  - `MapSpec`
  - `VehicleSpec`
- JSON-first scenario loading
- scenario validation tests
- example scenario file
- core graph/map/routing foundation needed so far

## What is still missing for Step 2 closure
Step 2 is not complete until the CLI exposes the scenario-loading path.

The key missing deliverables are:
1. a real CLI command that accepts a scenario JSON path
2. validated loading through the existing scenario loader
3. deterministic, stable scenario summary output
4. CLI tests for successful and failing scenario loads

## In-scope work
Work that is allowed right now:
- update CLI argument structure
- add a `run` subcommand
- load scenario files through the existing loader
- print a stable validated scenario summary
- add or update tests for the Step 2 CLI path
- small additive refactors that make Step 2 cleaner without introducing later-step architecture

## Out-of-scope work
Do not do any of the following in the current phase:
- introduce `WorldState`
- move dynamic map state out of `Map`
- add `Router`
- introduce cost model protocols
- refactor routing to use world-state-aware cost evaluation
- add simulation engine/run loop
- add agent processes
- add trace/event systems
- add jobs/resources/dispatch logic
- add multi-vehicle logic

## Architectural guidance for this phase
- Keep `cli.py` thin.
- Keep scenario loading separate from scenario formatting/reporting.
- Preserve the current scenario schema unless a very small change is clearly necessary.
- Treat `seed` as part of the validated scenario surface.
- Keep output deterministic and stable.
- Prefer straightforward code over “framework” code.

## Completion criteria for Step 2
Step 2 is complete when:
- `autonomous-ops-sim run <scenario_path>` works
- the scenario is validated through the existing loader
- a stable scenario summary is produced
- invalid inputs fail cleanly
- tests/lint/type checks pass