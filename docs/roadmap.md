# Roadmap

This document is a condensed text version of the project roadmap. Development should proceed in order. Later steps may influence earlier design, but later-step architecture should not be implemented prematurely unless there is a clear additive refactor that supports the current step cleanly.

---

## Step 1 — Production foundation
Goal:
- Make the project installable, runnable, testable, and CI-checked.

Key deliverables:
- `pyproject.toml`
- installable package
- CLI entry point
- pytest baseline
- Ruff baseline
- mypy baseline
- CI workflow

Acceptance criteria:
- editable install works
- package imports work
- CLI help/version works
- tests run cleanly
- lint/type checks run cleanly in CI

Notes:
- This step is about stable execution surface and engineering baseline, not simulation behavior.

---

## Step 2 — Scenario/config spine with determinism plumbing
Goal:
- Create the stable input/configuration layer for future simulation runs.

Key deliverables:
- typed scenario dataclasses
- JSON-first scenario schema
- scenario loader/validator
- deterministic seed captured in the scenario/config surface
- CLI path that loads a scenario and reports validated scenario information

Acceptance criteria:
- scenario files are parsed and validated cleanly
- raw JSON is converted into typed dataclasses before broader use
- scenario loading is accessible through the CLI
- repeated loads of the same scenario produce stable validated summary output
- schema is minimal now but future-ready

Notes:
- This is still pre-simulation.
- Do not introduce world-state/runtime mutation architecture here.
- Do not introduce simulation engine or event processing here.

---

## Step 3 — Static Map vs dynamic WorldState split
Goal:
- Separate immutable map/topology from runtime-changing simulation state.

Key deliverables:
- `WorldState`
- blocked edges / dynamic conditions moved out of static map ownership
- clean resettable runtime state

Acceptance criteria:
- the same map can be reused across runs without contamination
- runtime changes do not mutate the static map asset
- reset behavior is explicit and deterministic

Notes:
- This is the step where dynamic closures, runtime restrictions, and similar state should be refactored out of `Map`.

---

## Step 4 — CostModel and Router refactor
Goal:
- Make routing depend on injectable cost logic and dynamic world state.

Key deliverables:
- cost model interface/protocol
- `Router` abstraction
- shortest path API routed through stable surface
- cost-model-based routing rather than hardcoded distance-only assumptions

Acceptance criteria:
- different cost models can choose different routes
- routing honors dynamic world state
- non-negative cost assumptions are enforced for Dijkstra-based routing

---

## Step 5 — Simulation engine and clock
Goal:
- Introduce the simulation execution model and explicit simulated time.

Key deliverables:
- simulation engine
- time/run controls
- deterministic seed-aware initialization surface for execution

Acceptance criteria:
- run-to-time behavior works
- repeated runs with same inputs are reproducible

---

## Step 6 — Single-vehicle execution and trace
Goal:
- Make one vehicle move through the system under simulated time and produce trace output.

Key deliverables:
- single-vehicle process/agent
- trace events
- deterministic route-following behavior

Acceptance criteria:
- timestamps are monotone
- arrival timing matches configured routing/cost behavior

---

## Step 7 — Jobs, tasks, and resources
Goal:
- Add operational primitives like move/load/unload and shared resources.

Key deliverables:
- task/job primitives
- queue/resource behavior
- haul-cycle-style execution

Acceptance criteria:
- queue discipline and service behavior are testable and deterministic

---

## Step 8 — Dispatcher
Goal:
- Add baseline assignment logic for jobs/tasks.

Key deliverables:
- dispatcher interface
- baseline heuristic policy

Acceptance criteria:
- assignments are correct
- job completion works under load

---

## Step 9 — Multi-vehicle conflict handling
Goal:
- Prevent invalid shared-space occupancy and handle replanning/conflict logic.

Key deliverables:
- conflict handling / reservation logic
- replan triggers
- no-double-occupancy behavior

Acceptance criteria:
- conflicts are prevented or detected
- deadlock-related behavior is test-covered

---

## Step 10 — Behavior layer
Goal:
- Add operational behavior/state logic for agents.

Key deliverables:
- FSM-style state layer first
- future-friendly path toward richer behavior systems later

Acceptance criteria:
- state transitions and recovery logic are testable

---

## Step 11 — Scenario packs, metrics, visualization, optional RL wrapper
Goal:
- Add analysis/export/visualization surfaces and optional external environment wrapping.

Key deliverables:
- metrics export
- visualization hooks
- docs
- optional RL wrapper

Acceptance criteria:
- golden-scenario regression support
- export formats are stable and tested

---

## Planning rule
When working on any task:
1. identify the active step
2. implement only what is required to close that step
3. avoid pulling later-step abstractions earlier unless absolutely necessary
4. prefer small, production-looking additive changes