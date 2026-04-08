# Current Phase

## Active roadmap step
Step 3 — Static Map vs dynamic WorldState split

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: active
- Step 4: not started

## What already exists
The repository already has:
- working package structure
- `pyproject.toml`
- CLI entry point
- pytest / Ruff / mypy baseline
- CI workflow
- scenario/config spine
- JSON-first scenario loading
- CLI scenario-loading path
- deterministic scenario summary output
- core graph/map/routing foundation

## Goal of the current phase
Separate static topology/geometry from runtime-changing simulation state.

The main Step 3 objective is:
- `Map` remains static
- runtime blocked-edge state moves out of `Edge` / `Map`
- `WorldState` becomes the owner of blocked-edge runtime state

## In-scope work
Work that is allowed right now:
- add `simulation/world_state.py`
- move blocked-edge ownership to `WorldState`
- update pathfinding to query `WorldState`
- remove or update any map-owned blocking helpers so `Map` remains static
- add/update tests proving static map vs dynamic world-state separation
- small additive refactors that make Step 3 cleaner without introducing Step 4 architecture

## Out-of-scope work
Do not do any of the following in the current phase:
- introduce `Router`
- introduce `CostModel`
- refactor routing beyond what is needed to honor `WorldState`
- add simulation engine/run loop
- add trace/event systems
- add jobs/resources/dispatch logic
- add multi-vehicle logic
- add behavior systems

## Architectural guidance for this phase
- `Map` is static.
- `WorldState` is runtime state for a run.
- blocked-edge state should not live on `Edge`.
- prefer one clear source of truth for runtime conditions.
- keep the change focused on the state split, not future routing architecture.

## Completion criteria for Step 3
Step 3 is complete when:
- `WorldState` exists and owns blocked-edge runtime state
- `Edge` no longer owns blocked-edge runtime state
- pathfinding honors blocked edges through `WorldState`
- the same `Map` can be reused with different `WorldState` instances independently
- fresh/default `WorldState` restores baseline behavior
- tests/lint/type checks pass
