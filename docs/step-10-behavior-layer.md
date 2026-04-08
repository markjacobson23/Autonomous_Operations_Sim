# Step 10 Behavior Layer

## Goal
Finish Step 10 cleanly without introducing Step 11 concepts.

## Required implementation
Add a small FSM-style behavior layer for vehicle operational state.

## Required design
- Add a behavior/state module such as `autonomous_ops_sim/simulation/behavior.py`
- Add a vehicle operational state enum
- Add explicit transition logic
- Integrate the behavior layer with existing movement/task/conflict/resource/job execution flows

## Required behavior
- Vehicles have explicit operational states
- Valid transitions are allowed and testable
- Invalid transitions fail clearly
- Basic failure/recovery behavior is represented

## Design constraints
- Do not add a full behavior tree framework
- Do not add large AI planning systems
- Keep the baseline small and production-like
- Prefer a clear FSM over a sprawling abstraction

## Tests to add
Add tests for:
- valid state transitions
- invalid transitions
- basic recovery/failure behavior
- repeated deterministic behavior for the same setup

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
