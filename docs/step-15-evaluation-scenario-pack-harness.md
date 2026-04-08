# Step 15 Evaluation and Scenario-Pack Harness

## Goal
Finish Step 15 cleanly by adding deterministic batch execution and evaluation over scenario packs.

## Required implementation
Add a narrow scenario-pack / benchmark harness that can execute multiple scenario files and produce stable per-scenario and aggregate outputs.

## Required design
- Add a scenario-pack runner module such as:
  - `autonomous_ops_sim/io/scenario_pack_runner.py`
  - or `autonomous_ops_sim/simulation/scenario_batch.py`
- Reuse the existing:
  - scenario loader
  - scenario executor
  - metrics/export surfaces
- Define one narrow pack input convention, such as:
  - directory-based scenario discovery
  - or a small manifest file listing scenario paths
- Produce deterministic machine-readable output for pack results

## Required behavior
- Multiple scenarios can be executed in one deterministic batch run
- Per-scenario outputs remain stable
- Aggregate pack output remains stable
- Repeated runs with the same scenario pack produce identical results

## Minimum expected scope
At minimum, Step 15 should support:
- discovering or loading multiple scenario files
- executing them in deterministic order
- collecting per-scenario summaries
- producing one stable aggregate result surface
- at least one test fixture or regression check covering batch execution

## Design constraints
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not redesign multi-vehicle coordination
- Do not build a dashboard or large reporting UI
- Do not overbuild a generic experiment framework
- Keep the implementation small and production-like

## Preferred strategy
- Reuse existing single-scenario execution paths directly
- Keep ordering rules explicit and deterministic
- Favor one narrow, fully working pack execution path over a flexible but under-specified benchmark system
- Prefer machine-readable outputs over presentation-heavy formatting
- Keep pack orchestration separate from core execution logic

## Tests to add
Add tests for:
- deterministic scenario-pack discovery/execution order
- stable per-scenario summary collection
- stable aggregate pack output
- repeated batch runs producing identical results
- at least one regression fixture or exact-output comparison for a scenario pack

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
