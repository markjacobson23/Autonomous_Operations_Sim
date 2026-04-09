# Step 26 Live Interactive Viewer Actions

## Goal
Finish Step 26 cleanly by enabling the first real live interactive viewer actions on top of the existing live-session and command architecture.

## Required implementation
Extend the graphical viewer so it can issue bounded live actions through the interaction and command surfaces.

## Required design
- Reuse the existing:
  - graphical viewer
  - interaction types / translation
  - typed commands
  - `SimulationController`
  - `LiveSimulationSession`
  - visualization state builders
- Support a small initial live action set such as:
  - select vehicle
  - assign destination
  - block edge
  - optional bounded reposition action

## Required behavior
- Viewer actions become explicit interaction inputs
- Interactions translate into typed commands
- Commands apply through the live session/controller path
- Visualization refresh remains coherent and deterministic
- Repeated runs with the same starting state and action sequence remain identical

## Minimum expected scope
At minimum, Step 26 should support:
- one selected vehicle
- one meaningful destination-assignment flow from the viewer
- one bounded edge-blocking or reposition flow
- coherent viewer refresh after live actions
- deterministic replay/export after the same action sequence

## Design constraints
- Do not bypass the interaction/command layer
- Do not redesign the simulator around networking or async frameworks
- Do not build a heavy polished product UI
- Do not overbuild generic GUI abstractions
- Keep the implementation small and production-like

## Preferred strategy
- Start with the smallest live action set that clearly proves the architecture
- Favor explicit buttons/modes over ambiguous gesture-heavy UI
- Rebuild or refresh visualization state from the live session after actions
- Preserve deterministic ordering and existing replay/export semantics

## Tests to add
Add tests for:
- deterministic live action handling
- correct interaction-to-command translation from viewer actions
- coherent session/visualization refresh after actions
- repeated action sequences producing identical session/replay/export outputs

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
