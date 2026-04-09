# Step 24 Playback Control Maturity

## Goal
Finish Step 24 cleanly by improving playback navigation and control for the graphical replay viewer.

## Required implementation
Extend the graphical replay viewer and replay controller with stronger deterministic playback/navigation behavior.

## Required design
- Reuse the existing:
  - `VisualizationState`
  - replay helpers
  - `ReplayController`
  - graphical viewer
- Improve playback controls in a bounded way, such as:
  - previous frame
  - first / last frame
  - jump to frame index
  - playback speed adjustment
  - richer frame metadata/status display

## Required behavior
- Playback navigation is stronger than the Step 23 baseline
- The same replay input still produces the same frame progression
- The viewer remains a consumer of completed replay state
- Navigation and frame selection remain deterministic

## Minimum expected scope
At minimum, Step 24 should support:
- at least two meaningful new replay controls beyond play/pause/next/reset
- deterministic navigation over completed frames
- stable metadata/status updates tied to the selected frame
- tests covering navigation behavior and frame selection

## Design constraints
- Do not add live runtime control yet
- Do not inject commands from the viewer yet
- Do not redesign the simulator around a live loop
- Do not overbuild UI features beyond replay maturity
- Keep the implementation small and production-like

## Preferred strategy
- Extend the current replay controller rather than replacing it
- Keep the control surface explicit and frame-oriented
- Improve inspectability first, live control later
- Preserve compatibility with existing visualization state

## Tests to add
Add tests for:
- previous/first/last/jump navigation behavior
- deterministic playback speed or timing behavior if added
- stable status/frame metadata updates
- repeated navigation sequences producing identical results

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
