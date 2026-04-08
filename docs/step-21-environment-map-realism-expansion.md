# Step 21 Environment/Map Realism Expansion

## Goal
Finish Step 21 cleanly by adding one meaningful environment/map realism improvement beyond the current grid-first baseline.

## Required implementation
Add a narrow richer map/environment capability that improves realism while preserving the simulator’s existing runtime architecture.

## Required design
- Reuse the existing:
  - `Map`
  - scenario loader / scenario schema
  - routing surfaces
  - execution surfaces
  - visualization surfaces
- Add one narrow realism improvement such as:
  - an explicit non-grid graph/network scenario map kind
  - site/zone metadata attached to nodes
  - environment semantics for work locations / depots / corridors
- Keep the implementation bounded and production-like

## Required behavior
- The simulator can load and use a richer environment/map configuration than the current grid-only focus
- Routing and execution work correctly over the richer topology
- Visualization state can still project the richer environment/map data in a stable way
- Repeated runs with the same setup remain deterministic

## Minimum expected scope
At minimum, Step 21 should support:
- one richer map/environment feature beyond the current baseline
- one scenario or fixture demonstrating the richer environment/map
- deterministic execution and replay over that richer environment
- at least one regression fixture or exact-output comparison for the richer environment/map path

## Design constraints
- Do not redesign the simulator around a heavy map/GIS framework
- Do not add a broad import pipeline for many file formats
- Do not build a world editor
- Do not overbuild environment semantics beyond the narrow realism improvement chosen
- Keep the implementation small and production-like

## Preferred strategy
- Pick one narrow realism gain and implement it well
- Prefer compatibility with existing `Map` and routing/execution paths over introducing parallel map abstractions
- Extend scenario schema only where it directly supports the chosen improvement
- Keep visualization support minimal but correct for the richer environment/map data
- Preserve deterministic ordering and stable exports

## Tests to add
Add tests for:
- parsing/loading the richer environment/map configuration
- deterministic routing/execution over the richer environment/map
- stable visualization or export projection for the richer environment/map path
- repeated runs producing identical results
- at least one regression fixture or exact-output comparison for the richer environment/map case

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
