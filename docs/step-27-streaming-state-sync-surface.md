# Step 27 Streaming / State Sync Surface

## Goal
Finish Step 27 cleanly by introducing a stable live state/command sync surface between simulator runtime and viewer layers.

## Required implementation
Add a transport-agnostic live sync surface that represents runtime state, viewer-relevant updates, and command effects without binding the simulator to a specific UI stack or network transport.

## Required design
- Reuse the existing:
  - `LiveSimulationSession`
  - typed command/control surfaces
  - visualization state builders
  - live viewer controller concepts where helpful
- Add a module such as:
  - `autonomous_ops_sim/visualization/live_sync.py`
  - or `autonomous_ops_sim/simulation/state_sync.py`

## Required behavior
- Live runtime state can be surfaced in a stable viewer-facing form
- Command effects can be surfaced coherently alongside state
- The sync surface remains deterministic for the same session and command sequence
- Replay/export compatibility is preserved

## Minimum expected scope
At minimum, Step 27 should support:
- stable runtime snapshot representation
- stable ordered update representation
- deterministic repeated update generation
- integration with existing live-session and viewer flows

## Design constraints
- Do not redesign the simulator around async/networking
- Do not build a full remote streaming protocol
- Do not bypass live-session and command surfaces
- Do not overbuild a frontend framework boundary
- Keep the implementation small and production-like

## Preferred strategy
- Keep the sync surface transport-agnostic
- Build a narrow snapshot/update model and implement it well
- Reuse existing trace, command, and visualization semantics where they already fit
- Prepare for future frontend separation without prematurely committing to it

## Tests to add
Add tests for:
- deterministic runtime snapshot generation
- deterministic ordered update generation
- repeated session/action sequences producing identical sync output
- compatibility with existing replay/viewer state derivation where applicable

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
