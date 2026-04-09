# Step 25 Live Control Loop Bridge

## Goal
Finish Step 25 cleanly by adding a narrow live runtime session/control bridge on top of the existing deterministic command surface.

## Required implementation
Add a bounded session-oriented control layer that supports progression of a live run and command application during that run.

## Required design
- Reuse the existing:
  - `SimulationEngine`
  - `SimulationController`
  - typed commands
  - trace / command history
  - visualization state / replay surfaces
- Add a small session/runtime bridge module such as:
  - `autonomous_ops_sim/simulation/live_session.py`
  - or `autonomous_ops_sim/simulation/runtime_session.py`

## Required behavior
- A run can exist as an active controlled session
- Session progression is explicit and deterministic
- Commands can be applied during the active session
- Replay/export surfaces remain coherent after session progression and command application

## Minimum expected scope
At minimum, Step 25 should support:
- creating a live/active session from an existing scenario or engine setup
- bounded progression of that session
- typed command application during the session
- deterministic trace/command ordering for repeated runs with the same inputs

## Design constraints
- Do not add full viewer click interaction yet
- Do not bypass the typed command surface
- Do not redesign the simulator around async/event-loop frameworks
- Do not introduce networking/streaming yet
- Keep the implementation small and production-like

## Preferred strategy
- Start with a narrow session abstraction and implement it well
- Keep session progression explicit rather than magical
- Reuse existing control and replay/export surfaces directly
- Preserve deterministic ownership and event ordering

## Tests to add
Add tests for:
- deterministic session progression
- deterministic command application during a session
- stable trace/command ordering after session control
- repeated session runs producing identical results

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
