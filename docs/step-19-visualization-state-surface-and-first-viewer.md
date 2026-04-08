# Step 19 Visualization State Surface and First Viewer

## Goal
Finish Step 19 cleanly by adding a stable visualization-oriented state surface and a minimal first viewer.

## Required implementation
Add a visualization state/export layer and one narrow viewer that consumes it.

## Required design
- Add a visualization module such as:
  - `autonomous_ops_sim/visualization/state.py`
  - `autonomous_ops_sim/visualization/replay.py`
  - optionally a very small viewer entrypoint such as `autonomous_ops_sim/visualization/viewer.py`
- Reuse the existing:
  - `SimulationEngine`
  - `Map`
  - `Vehicle`
  - `WorldState`
  - trace
  - command history / controlled exports where helpful
- Keep visualization state separate from engine internals and from presentation code

## Required behavior
- Simulator runs can be converted into stable visualization-oriented state
- The same run produces the same visualization playback/snapshots
- A first narrow viewer can display map and vehicle progression from that state
- The viewer is a consumer, not an owner, of simulator truth

## Minimum expected scope
At minimum, Step 19 should support:
- map/node/edge geometry in visualization-ready form
- vehicle position/state snapshots or replay frames
- deterministic playback over a completed run
- one narrow viewer surface, likely:
  - text/CLI playback, or
  - a very lightweight local viewer if it stays small

## Design constraints
- Do not add full live interactivity yet
- Do not build a heavy web app/dashboard
- Do not redesign the simulator around a rendering framework
- Do not make visualization code reach deep into runtime ownership
- Keep the implementation small and production-like

## Preferred strategy
- Start with replay of completed runs rather than live streaming
- Prefer a stable frame/snapshot surface over ad hoc viewer queries
- Keep the first viewer simple and demonstrative
- Reuse existing trace/command/export surfaces where that reduces duplication
- Add only the minimum viewer features needed to prove the architecture

## Tests to add
Add tests for:
- deterministic visualization-state generation
- deterministic replay/frame ordering
- stable vehicle/map state projection for at least one run
- at least one regression fixture or exact-output comparison for visualization-state output

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
