Read `AGENTS.md`, `docs/current_phase.md`, `docs/roadmap.md`, and `docs/step-9-conflict-handling.md` first.

Start Step 9 only.

Task:
Add a deterministic multi-vehicle conflict-handling mechanism.

Requirements:
- Add a reservation/conflict structure such as `autonomous_ops_sim/simulation/reservations.py`
- Support a small deterministic multi-vehicle execution path
- Prevent conflicting occupancy in the supported cases
- Use deterministic priority ordering
- Support waiting and/or simple replanning as conflict response
- Add tests proving:
  - no double occupancy in a simple conflict case
  - deterministic priority handling
  - conflict response behavior
  - repeated deterministic outcomes

Constraints:
- Do not introduce Step 10 behavior systems
- Do not add advanced MAPF optimization frameworks
- Do not overbuild the first multi-vehicle implementation
- Keep the baseline narrow and production-like

Verification:
- python3 -m pytest
- python3 -m ruff check .
- python3 -m mypy autonomous_ops_sim tests
