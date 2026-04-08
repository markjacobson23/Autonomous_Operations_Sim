# Step 8 Simple Dispatcher

## Goal
Finish Step 8 cleanly without introducing Step 9 concepts.

## Required implementation
Add a small dispatcher interface and one baseline deterministic dispatch policy.

## Required design
- Add `autonomous_ops_sim/operations/dispatcher.py`
- Add a dispatcher interface/protocol
- Add one concrete baseline dispatcher
- Reuse the existing engine/job execution surfaces

## Required behavior
- Dispatcher can choose one job from a set of pending jobs
- Selection is deterministic for the same setup
- Selected job can then be executed correctly
- Job completion under simple load is testable

## Design constraints
- Do not add multi-vehicle road conflict handling
- Do not add advanced optimization
- Do not add behavior frameworks
- Keep the dispatcher small and production-like

## Tests to add
Add tests for:
- deterministic job selection
- assignment correctness
- selected job completion through the existing engine
- repeated runs with same setup produce same choices and outcomes

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
