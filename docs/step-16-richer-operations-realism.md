# Step 16 Richer Operations Realism

## Goal
Finish Step 16 cleanly by moving from isolated single-job execution toward richer longer-lived operational runs.

## Required implementation
Add a narrow deterministic execution path for repeated or sequential operational work within one run.

## Required design
- Reuse the existing:
  - persistent `Vehicle` model
  - `SimulationEngine`
  - job/task/resource execution
  - dispatcher surface
  - metrics/export surfaces
- Add a small workload orchestration layer such as:
  - `autonomous_ops_sim/operations/workload.py`
  - or `autonomous_ops_sim/simulation/workload_runner.py`
- Support one narrow longer-lived execution mode, such as:
  - sequential execution of multiple jobs for one vehicle
  - or dispatcher-driven repeated job consumption from a pending queue until completion

## Required behavior
- A persistent vehicle can execute multiple jobs over time in one run
- The execution remains deterministic
- Existing task/resource/behavior/trace semantics continue to work coherently
- Repeated runs with the same setup produce identical summary/export output

## Minimum expected scope
At minimum, Step 16 should support:
- one persistent vehicle
- multiple jobs in one run
- stable final-time / workload summary behavior
- at least one deterministic scenario or fixture covering longer-lived operations execution

## Design constraints
- Do not redesign multi-vehicle coordination
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not build a large optimization/scheduling framework
- Do not overbuild demand generation or stochastic systems
- Keep the implementation small and production-like

## Preferred strategy
- Start with one narrow longer-lived workload model and implement it well
- Prefer sequential or dispatcher-driven repeated execution over broad fleet orchestration
- Reuse existing job execution and dispatch behavior rather than inventing new execution semantics
- Extend scenario schema only if it clearly supports the chosen workload path
- Add only the minimum metrics needed to characterize richer operations runs

## Tests to add
Add tests for:
- deterministic multi-job or repeated-work execution in one run
- stable final vehicle state after a longer-lived run
- stable metrics/export output for the richer operations case
- repeated runs producing identical results
- at least one regression fixture or exact-output comparison for a richer long-run scenario

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
