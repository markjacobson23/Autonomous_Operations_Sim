# Step 23 Graphical Replay Viewer Foundation

## Goal
Finish Step 23 cleanly by building the first real graphical viewer on top of the existing visualization replay surface.

## Required implementation
Add a graphical replay viewer that consumes `VisualizationState` and renders completed runs.

## Required design
- Add a visualization viewer module or package such as:
  - `autonomous_ops_sim/visualization/gui_viewer.py`
  - `autonomous_ops_sim/visualization/graphical_viewer.py`
- Reuse the existing:
  - `VisualizationState`
  - replay helpers
  - visualization export/load surfaces
- Keep the viewer separate from runtime ownership logic
- Keep the viewer bounded to replay of completed runs

## Required behavior
- The viewer can load or accept visualization state
- The viewer renders:
  - map nodes
  - map edges
  - vehicle positions/states
- The viewer supports narrow replay controls such as:
  - play
  - pause
  - next frame
  - reset
- The same visualization input produces the same replay order and rendered progression

## Minimum expected scope
At minimum, Step 23 should support:
- graphical rendering of a completed replay
- rendering of at least one vehicle over at least one non-trivial map
- bounded playback controls over deterministic frames
- one demonstration path from existing visualization JSON into the viewer

## Design constraints
- Do not add live interactivity yet
- Do not bypass visualization state and read engine internals directly
- Do not redesign the simulator around a new render architecture
- Do not build a large product dashboard
- Keep the implementation small and production-like

## Preferred strategy
- Start with the smallest graphical viewer that is clearly better than the text viewer
- Prefer consuming exported or in-memory visualization state directly
- Keep UI toolkit commitment minimal and pragmatic
- Preserve deterministic replay semantics
- Add only the minimum viewer controls needed to prove the architecture

## Tests to add
Add tests for:
- deterministic frame consumption/order
- stable loading of visualization state into the graphical viewer path where practical
- at least one end-to-end demonstration path from visualization state to viewer
- regression coverage for any new visualization-state assumptions

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
