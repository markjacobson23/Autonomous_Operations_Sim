# Step 2 Closure

## Goal
Finish Step 2 cleanly without introducing Step 3 concepts.

## Required implementation
Add a CLI scenario-loading path with deterministic validated summary output.

## Required user-facing command
Support:

- `autonomous-ops-sim run scenarios/example.json`

Equivalent module invocation may also work:

- `python3 -m autonomous_ops_sim.cli run scenarios/example.json`

## Required behavior
On success:
- load the scenario using the existing scenario loader
- validate it through the existing parsing/validation path
- print a deterministic summary of the loaded scenario

On failure:
- report a clear error
- exit nonzero

## Recommended summary contents
Keep the summary compact and stable. Include:
- scenario name
- source path
- seed
- duration
- map kind
- map params
- vehicle count
- concise vehicle summaries

## Design constraints
- keep `cli.py` thin
- separate argument parsing from scenario summary formatting
- do not redesign the scenario schema
- do not add simulation behavior
- do not introduce `WorldState`
- do not refactor routing

## Tests to add
Add tests for:
- valid `run` command against example scenario
- invalid scenario path
- invalid scenario file content
- stable repeated summary output for the same scenario

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
- `python3 -m autonomous_ops_sim.cli run scenarios/example.json`
- `autonomous-ops-sim run scenarios/example.json`