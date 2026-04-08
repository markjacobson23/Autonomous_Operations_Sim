# Step 7 Jobs, Tasks, and Resources

## Goal
Finish Step 7 cleanly without introducing Step 8 concepts.

## Required implementation
Add minimal operational primitives for tasks, jobs, and shared resources.

## Required design
- Add `autonomous_ops_sim/operations/tasks.py`
- Add `autonomous_ops_sim/operations/jobs.py`
- Add `autonomous_ops_sim/operations/resources.py`
- Reuse the existing engine, routing, and trace surfaces
- Support at least:
  - move task
  - load task
  - unload task

## Required behavior
- Tasks execute in simulated time
- Jobs execute ordered task sequences
- Shared resources can be busy and force waiting
- Trace/output should make waiting and service timing observable

## Design constraints
- Do not add dispatcher logic
- Do not add multi-vehicle road conflict handling
- Do not add behavior frameworks
- Keep the primitives small and production-like

## Tests to add
Add tests for:
- ordered task execution
- load/unload service timing
- resource waiting behavior
- deterministic repeated execution for the same setup

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
