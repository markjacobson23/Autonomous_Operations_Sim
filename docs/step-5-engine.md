# Step 5 Engine

## Goal
Finish Step 5 cleanly without introducing Step 6 concepts.

## Required implementation
Introduce a simulation engine with explicit simulated time and deterministic run control.

## Required design
- Add `autonomous_ops_sim/simulation/engine.py`
- Add a `SimulationEngine` public class
- Engine should own or be initialized with the core runtime objects needed for a run:
  - map
  - world state
  - router
  - seed
- Engine should expose simulated time clearly
- Engine should support `run(until_s: float)`

## Required behavior
- Engine starts at simulated time 0
- Running to a target time advances simulated time to that target
- Engine behavior is deterministic for the same seed and same initial setup
- This step is about time/run control, not yet about vehicle execution

## Design constraints
- Do not add Step 6 vehicle processes
- Do not add trace/event systems beyond minimal engine necessities
- Do not add jobs/resources/dispatch logic
- Keep the engine API small and production-like
- Prefer additive refactoring over broad rewrites

## Tests to add
Add tests for:
- engine initializes at time 0
- `run(until_s)` advances simulated time correctly
- repeated engine setup with same seed behaves deterministically
- invalid run targets are handled clearly if applicable

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
