# Step 12 Executable Scenario Harness

## Goal
Finish Step 12 cleanly by making scenario files executable end-to-end simulator inputs.

## Required implementation
Add a scenario execution harness that converts parsed scenario/config input into a real deterministic simulator run.

## Required design
- Add a scenario execution/orchestration module such as:
  - `autonomous_ops_sim/simulation/scenario_executor.py`
  - or `autonomous_ops_sim/io/scenario_runner.py`
- Reuse the existing:
  - scenario loader
  - map construction
  - `WorldState`
  - `SimulationEngine`
  - operations layer
  - metrics/export surfaces
- Extend the CLI so scenario execution is a first-class supported path
- Keep parsing/validation separate from runtime instantiation and execution

## Required behavior
- A scenario file can be loaded and turned into a real simulator run
- The run produces deterministic output
- The run can emit stable export JSON
- The same scenario run repeated multiple times produces identical results

## Minimum expected scope
At minimum, Step 12 should support:
- building the map from the scenario
- instantiating vehicle runtime setup from the scenario
- creating the engine from scenario-driven inputs
- executing one deterministic scenario-run path
- exporting the run result through existing export infrastructure

## Design constraints
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not over-expand the scenario schema
- Do not redesign the vehicle/entity model yet
- Do not add richer map import formats unless strictly necessary
- Keep the implementation small and production-like

## Preferred strategy
- Keep existing scenario schema support working
- Extend the schema only where necessary to support execution
- Reuse existing deterministic demos/tests as the basis for the first executable scenario-run fixture
- Prefer one narrow, fully working scenario-run path over broad half-finished flexibility

## Tests to add
Add tests for:
- scenario-driven execution succeeds end-to-end
- repeated runs with the same scenario produce identical output
- scenario-run export output is stable
- at least one scenario-run golden fixture matches exactly

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
