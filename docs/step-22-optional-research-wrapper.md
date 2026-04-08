# Step 22 Optional Research Wrapper

## Goal
Finish Step 22 cleanly by adding one thin optional experimentation wrapper on top of the existing simulator surfaces.

## Required implementation
Add a narrow optional wrapper or adapter that makes controlled experimentation easier without changing the simulator’s core ownership model.

## Required design
- Add a research/experimentation module such as:
  - `autonomous_ops_sim/research/wrapper.py`
  - `autonomous_ops_sim/research/comparison.py`
- Reuse the existing:
  - scenario execution
  - scenario-pack evaluation
  - command/control surfaces
  - visualization/export surfaces
- Support one narrow research workflow such as:
  - comparing multiple command policies on the same scenario
  - comparing multiple interaction sequences
  - exposing a minimal reset/step wrapper over a controlled engine run

## Required behavior
- The wrapper is optional and additive
- It does not replace the main simulator interfaces
- It remains deterministic
- Repeated runs with the same inputs produce identical outputs

## Minimum expected scope
At minimum, Step 22 should support:
- one clear optional experimentation interface
- one deterministic comparison/demo case
- stable output or export for the experimental path
- tests proving repeatability and non-intrusive integration

## Design constraints
- Do not redesign the simulator around Gym/RL APIs
- Do not make research abstractions the main architecture
- Do not add a training framework
- Do not overbuild benchmarking or optimization infrastructure
- Keep the implementation small and production-like

## Preferred strategy
- Pick one narrow optional workflow and implement it well
- Prefer adapters over abstractions that leak into the rest of the codebase
- Reuse existing scenario/command/visualization/export surfaces directly
- Keep the wrapper obviously optional in package structure and public surfaces
- Preserve deterministic behavior and stable exports

## Tests to add
Add tests for:
- deterministic wrapper/comparison behavior
- repeated experimental runs producing identical results
- stable output/export for the experimental path
- at least one regression fixture or exact-output comparison for the wrapper path

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
