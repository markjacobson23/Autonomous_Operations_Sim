# Step 18 Control-Command Surface

## Goal
Finish Step 18 cleanly by adding a narrow explicit command surface for controlling simulation behavior.

## Required implementation
Add a deterministic control-command layer that applies explicit runtime actions through validated commands.

## Required design
- Add a command/control module such as:
  - `autonomous_ops_sim/simulation/commands.py`
  - `autonomous_ops_sim/simulation/control.py`
- Reuse the existing:
  - `SimulationEngine`
  - `WorldState`
  - `Vehicle`
  - routing / execution surfaces
  - trace / metrics / export surfaces
- Support one narrow, clearly defined initial command set

## Required behavior
- Commands can be represented as explicit typed inputs
- Commands are validated before application
- Command application is deterministic
- Repeated runs with the same initial state and command sequence produce identical results

## Minimum expected scope
At minimum, Step 18 should support:
- one or more useful runtime commands such as:
  - inject blocked edge
  - reposition vehicle
  - assign destination
- deterministic application order
- traceable or exportable command-driven execution behavior
- at least one regression fixture or exact-output comparison covering command-driven control

## Design constraints
- Do not add visualization
- Do not add a full interactive UI
- Do not redesign the simulator around async/event-loop frameworks
- Do not overbuild a generic command bus or event-sourcing framework
- Keep the implementation small and production-like

## Preferred strategy
- Pick a small initial command set and implement it well
- Prefer commands that map directly to existing runtime concepts
- Preserve backward-compatible scenario and execution behavior where reasonable
- Keep command application explicit, deterministic, and testable
- Add only the minimum new surfaces needed for future interactive growth

## Tests to add
Add tests for:
- deterministic command application
- validation/rejection of invalid commands
- stable replay of the same command sequence
- at least one regression fixture or exact-output comparison for command-driven execution

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
