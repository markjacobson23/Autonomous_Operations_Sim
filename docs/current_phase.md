# Current Phase

## Active roadmap step
Step 4 — CostModel and Router refactor

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: active
- Step 5: not started

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
- static map/topology separated from runtime blocked-edge state via `WorldState`

## Goal of the current phase
Refactor routing so shortest-path behavior depends on an injectable cost model and a stable router-facing API, while honoring runtime world state.

The main Step 4 objective is:
- introduce a `CostModel` interface/protocol
- introduce a `Router` abstraction as the public routing surface
- keep Dijkstra as the implementation underneath for now
- make routing decisions depend on injected cost logic rather than hardcoded edge distance

## In-scope work
Work that is allowed right now:
- add `routing/cost_model.py`
- add one or more initial concrete cost models
- add `routing/router.py`
- refactor pathfinding usage so public callers go through `Router`
- update Dijkstra to use injected edge costs
- make routing honor `WorldState`
- add/update tests for cost-model-swappable routing behavior
- add/update tests for non-negative cost assumptions

## Out-of-scope work
Do not do any of the following in the current phase:
- add simulation engine/run loop
- add trace/event systems
- add jobs/resources/dispatch logic
- add multi-vehicle logic
- add behavior systems
- add future optimization frameworks
- redesign scenarios beyond what Step 4 strictly needs

## Architectural guidance for this phase
- `Router` should be the stable public routing surface.
- `pathfinding.py` should remain the implementation module, not the main external interface.
- `CostModel` should be small and explicit.
- Keep Dijkstra-based assumptions clear: edge costs must be non-negative.
- Prefer additive refactoring over broad rewrites.
- Do not overbuild for future algorithms yet.

## Completion criteria for Step 4
Step 4 is complete when:
- `CostModel` exists and routing uses it
- `Router` exists and is the intended public routing entry point
- blocked edges are still honored through `WorldState`
- at least two cost models can produce different route choices on the same graph
- routing rejects or clearly guards against negative costs
- tests/lint/type checks pass
