# Step 11 Metrics and Exports

## Goal
Finish Step 11 cleanly as the outward-facing analysis layer.

## Required implementation
Add stable metrics summaries, structured exports, and a golden regression surface.

## Required design
- Add a metrics/summary module such as `autonomous_ops_sim/simulation/metrics.py`
- Add an export module such as `autonomous_ops_sim/io/exports.py` or equivalent
- Reuse the existing trace and execution surfaces rather than duplicating simulator logic
- Add at least one golden-scenario regression test

## Required behavior
- Simulator runs can produce stable derived metrics
- Metrics and/or trace can be exported in at least one structured format
- A known scenario/run can be checked against a stable expected result

## Design constraints
- Do not build a large dashboard/UI
- Do not overbuild visualization systems
- Keep optional external wrappers clearly optional
- Keep the outward-facing surface small and production-like

## Tests to add
Add tests for:
- metrics summary correctness
- export format stability
- golden-scenario regression correctness
- repeated deterministic runs produce identical summary/export output

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
