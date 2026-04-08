# Step 4 Routing Refactor

## Goal
Finish Step 4 cleanly without introducing Step 5 concepts.

## Required implementation
Introduce a `CostModel` abstraction and a `Router` public routing surface.

## Required design
- Add `autonomous_ops_sim/routing/cost_model.py`
- Add `autonomous_ops_sim/routing/router.py`
- Keep `autonomous_ops_sim/routing/pathfinding.py` as the Dijkstra implementation module
- Make routing depend on injected edge costs rather than hardcoded `edge.distance`
- Keep blocked-edge behavior dependent on `WorldState`

## Minimum expected cost models
At minimum, support:
- distance-based routing
- time-based routing using edge distance and speed limit

## Required behavior
- Callers should be able to choose a cost model without changing pathfinding call sites
- Same graph may produce different routes under different cost models
- Routing must continue to respect blocked edges through `WorldState`
- Negative edge costs must be rejected clearly because Dijkstra requires non-negative weights

## Design constraints
- Do not add simulation engine logic
- Do not add tasks/jobs/resources
- Do not introduce future-step abstractions unless strictly necessary
- Keep `Router` small and production-like
- Prefer additive refactoring over broad rewrites

## Tests to add
Add tests for:
- distance model chooses expected route
- time model chooses expected route when it differs from distance model
- blocked-edge routing still works through `WorldState`
- negative-cost model is rejected clearly
- public routing goes through `Router`

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
