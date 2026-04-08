# Step 17 Coordination Upgrade

## Goal
Finish Step 17 cleanly by improving multi-vehicle coordination beyond the current narrow reservation baseline.

## Required implementation
Add a bounded deterministic coordination upgrade that improves conflict handling realism and safety without replacing the simulator’s core architecture.

## Required design
- Reuse the existing:
  - `SimulationEngine`
  - reservation/conflict structures
  - routing surfaces
  - trace/metrics/export surfaces
- Upgrade the current coordination logic in a narrow way, such as:
  - stronger reservation reasoning
  - improved wait behavior
  - bounded deadlock prevention or detection
  - narrow corridor/intersection semantics
- Keep the implementation inspectable through trace and regression fixtures

## Required behavior
- Multi-vehicle movement coordination is stronger than the current baseline
- The upgraded coordination remains deterministic
- Waiting/conflict behavior is traceable and regression-testable
- Repeated runs with the same setup produce identical results

## Minimum expected scope
At minimum, Step 17 should support:
- one clearly improved coordination behavior beyond the Step 9 baseline
- deterministic multi-vehicle execution covering that behavior
- at least one scenario or fixture demonstrating the stronger coordination path
- stable summary/export behavior for the upgraded case

## Design constraints
- Do not add visualization
- Do not add interactive control/command surfaces
- Do not build a full optimal MAPF framework
- Do not redesign the simulator around a new runtime architecture
- Do not overbuild coordination abstractions
- Keep the implementation small and production-like

## Preferred strategy
- Pick one narrow coordination upgrade and implement it well
- Prefer a bounded, testable enhancement over broad algorithmic ambition
- Reuse the existing reservation-based foundation where possible
- Extend metrics/trace only where they improve observability of the coordination change
- Preserve deterministic ordering and tie-breaking

## Tests to add
Add tests for:
- deterministic upgraded multi-vehicle coordination behavior
- traceable wait/conflict behavior for the stronger coordination case
- repeated runs producing identical results
- at least one regression fixture or exact-output comparison for the upgraded coordination path

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
