# Step 13 Scenario Schema for Operations

## Goal
Finish Step 13 cleanly by expanding scenario/config support for operational execution.

## Required implementation
Extend the scenario schema and execution harness so scenario files can describe more of the runtime operational setup.

## Required design
- Extend `autonomous_ops_sim/simulation/scenario.py` with new typed scenario specs for:
  - resources
  - runtime world-state initialization
  - dispatcher selection/config
- Extend `autonomous_ops_sim/io/scenario_loader.py` to parse and validate the new fields
- Extend `autonomous_ops_sim/simulation/scenario_executor.py` to instantiate:
  - `SharedResource` objects from scenario config
  - `WorldState` blocked-edge initialization from scenario config
  - a narrow dispatcher selection path from scenario config
- Reuse existing runtime execution paths rather than adding parallel execution logic

## Required behavior
- A scenario can define resources and execution can use them
- A scenario can define initial blocked edges and execution honors them
- A scenario can define dispatcher selection in a narrow supported form
- Scenario-driven execution remains deterministic across repeated runs

## Minimum expected scope
At minimum, Step 13 should support:
- scenario-defined shared resources
- scenario-defined initial blocked edges
- scenario-defined dispatcher selection with a baseline option such as `first_feasible`
- at least one richer executable scenario that uses one or more of the above

## Design constraints
- Do not redesign the vehicle/entity model yet
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not redesign multi-vehicle coordination
- Do not over-expand the schema into a broad DSL
- Keep the implementation small and production-like

## Preferred strategy
- Extend the schema only where it maps directly to existing runtime objects
- Keep resource and dispatcher config narrow
- Preserve backward compatibility for existing scenario files where reasonable
- Add one fully working richer scenario fixture rather than many partially supported schema branches

## Tests to add
Add tests for:
- parsing and validating scenario-defined resources
- parsing and validating scenario-defined blocked-edge runtime setup
- parsing and validating narrow dispatcher config
- deterministic repeated scenario execution with the richer schema
- at least one updated or new golden scenario-run export fixture

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
