# Step 20 Interactive Manipulation Layer

## Goal
Finish Step 20 cleanly by adding a narrow interaction layer that turns viewer-facing actions into deterministic simulation commands.

## Required implementation
Add a small interaction/manipulation layer on top of the existing control-command surface.

## Required design
- Add an interaction module such as:
  - `autonomous_ops_sim/visualization/interactions.py`
  - or `autonomous_ops_sim/simulation/interaction_adapter.py`
- Reuse the existing:
  - typed simulation commands
  - `SimulationController`
  - visualization state / replay surfaces
  - viewer entrypoints where helpful
- Support a small initial interaction set that maps directly to existing commands

## Required behavior
- Viewer-facing actions can be represented as explicit interaction inputs
- Interactions are validated and translated into typed simulation commands
- Interaction-driven runs remain deterministic
- Repeated runs with the same interaction sequence produce identical results

## Minimum expected scope
At minimum, Step 20 should support:
- one or more interaction types such as:
  - assign destination
  - reposition vehicle
  - block edge
- deterministic translation from interactions to commands
- one narrow interaction-driven replay/demo path
- stable export/replay behavior after interactions are applied

## Design constraints
- Do not build a heavy graphical UI framework
- Do not redesign the simulator around async/live-loop infrastructure
- Do not bypass the command surface
- Do not overbuild a large interaction abstraction hierarchy
- Keep the implementation small and production-like

## Preferred strategy
- Start with a thin adapter from interaction intent to command objects
- Reuse the existing controller and visualization surfaces directly
- Keep the initial interaction vocabulary small and explicit
- Prefer deterministic scripted interaction sequences over ambitious live tooling
- Add only the minimum viewer changes needed to prove the architecture

## Tests to add
Add tests for:
- deterministic interaction-to-command translation
- invalid interaction rejection
- repeated interaction sequences producing identical results
- at least one regression fixture or exact-output comparison for an interaction-driven run

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
