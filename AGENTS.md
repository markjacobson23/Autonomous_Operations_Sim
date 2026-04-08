# AGENTS.md

## Project
This repository is `autonomous_ops_sim`, a Python project intended to grow into a production-quality autonomous operations / vehicle simulator.

## Development priority
Follow the roadmap in `docs/roadmap.md`.

Current active phase:
- See `docs/current_phase.md`

Current concrete task:
- See `docs/step-2-closure.md`

## Core rules
- Stay aligned to the roadmap.
- Do not casually jump ahead to later steps.
- Prefer additive refactoring over broad rewrites.
- Keep responsibility boundaries clean and production-like.
- Avoid premature abstraction.
- Do not introduce bandaid structure that creates future patchwork.
- Grid maps are an early/testing map source, not the long-term identity of the simulator.
- Do not lock the project into only Dijkstra or only current map types.
- Do not use external graph libraries for the project’s core graph logic.

## Code generation rules
- Keep `cli.py` thin.
- Keep parsing/loading separate from formatting/reporting.
- Preserve existing package structure unless the current roadmap step clearly requires a change.
- Do not introduce new packages or modules unless they are justified by the active roadmap step.
- Do not perform speculative refactors for future steps.

## Roadmap boundary rules
- If the active task is Step 2, do not introduce Step 3 concepts such as `WorldState`.
- Do not refactor routing/map dynamic state until Step 3.
- Do not introduce simulation engine/event loop concepts until the roadmap reaches that step.
- Do not introduce multi-vehicle coordination, behavior systems, or resource scheduling unless the active roadmap step requires them.

## Testing and quality bar
Before considering a task complete, run:

- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`

If the task changes CLI behavior, also verify:

- `python3 -m autonomous_ops_sim.cli --help`
- `python3 -m pip install -e .`
- `autonomous-ops-sim --help`

## Definition of success
A change is successful only if:
- it satisfies the active roadmap step
- it does not smuggle in later-step architecture
- tests/lint/type checks pass
- the resulting code looks like production-quality Python, not tutorial/demo code

## Source of truth
Read these before making changes:
1. `docs/current_phase.md`
2. `docs/step-2-closure.md`
3. `docs/roadmap.md`