# Step 9 Multi-Vehicle Conflict Handling

## Goal
Finish Step 9 cleanly without introducing Step 10 concepts.

## Required implementation
Add a deterministic multi-vehicle conflict-handling mechanism.

## Required design
- Add a reservation/conflict structure such as `autonomous_ops_sim/simulation/reservations.py`
- Support a small deterministic multi-vehicle planning/execution path
- Use a reservation model consistent with the graph abstraction
- Use deterministic priority ordering

## Required behavior
- At least two vehicles can be coordinated safely
- Conflicting occupancy is prevented in the supported cases
- Later-priority vehicles respond deterministically to conflicts
- Waiting and/or simple replanning is supported

## Design constraints
- Do not add Step 10 behavior systems
- Do not add advanced MAPF optimization frameworks
- Keep the baseline narrow and production-like
- Prefer a clear supported subset over a sprawling partial solution

## Tests to add
Add tests for:
- no double occupancy in a simple conflict case
- deterministic priority handling
- conflict response behavior (wait and/or reroute)
- repeated runs with the same setup produce the same outcome

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
