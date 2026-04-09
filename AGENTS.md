# AGENTS.md

## Purpose

This repository is a deterministic autonomous operations simulator focused on scenario-driven execution, operational tasks, coordination, replay, and controlled experimentation.

Work in this repo should preserve:

- determinism
- explicit state ownership
- trace-centered observability
- additive, disciplined evolution
- small, testable public interfaces
- clean boundaries between core simulation, control, visualization, and optional research tooling

This file is intentionally phase-independent. Step-specific scope belongs in:
- `docs/current_phase.md`
- `docs/step-*.md`

---

## Core architectural principles

### 1. Determinism is first-class
The simulator should produce stable results for the same inputs and seed.

Preserve:
- explicit seeds
- stable event ordering
- deterministic tie-breaking
- stable JSON exports
- replayable command and visualization behavior where applicable

Do not introduce hidden nondeterminism through:
- unordered iteration where order matters
- uncontrolled randomness
- wall-clock-driven simulation semantics
- ad hoc background behavior that changes execution order

### 2. Static topology is separate from runtime state
Static world structure and mutable run state must remain distinct.

Examples:
- `Graph` / `Map` are reusable topology assets
- `WorldState` owns runtime blocked-edge conditions
- reservations belong to coordination/runtime structures, not topology assets
- visualization state is derived output, not authoritative runtime state

Do not mutate static topology objects to represent per-run conditions.

### 3. Trace is the core observability surface
Trace events are the main stable outward-facing execution record.

Metrics, exports, replay state, and regression fixtures should derive from trace and explicit runtime state rather than ad hoc internal peeking.

When adding behavior:
- prefer explicit trace events
- keep trace semantics stable and understandable
- avoid shadow truth when trace already captures the event

### 4. Commands and interactions must remain explicit
Viewer-facing interactions should translate into typed commands rather than bypassing runtime ownership.

Preserve:
- typed command surfaces
- validated application
- deterministic command ordering
- replayable command history

Avoid:
- direct viewer mutation of engine internals
- hidden control paths outside the command surface

### 5. Visualization is a consumer, not an owner
Viewers, replay tools, and future graphical frontends must consume stable visualization/control surfaces.

They should not become the source of truth for:
- vehicle state
- routing state
- world-state mutation
- coordination logic

### 6. Prefer additive refactoring over rewrites
Evolve the simulator through small, explicit layers.

Prefer:
- adding a focused module
- extending a narrow interface
- extracting orchestration from overloaded modules
- promoting stable concepts into explicit types

Avoid:
- speculative frameworks
- giant rewrites
- premature infrastructure for hypothetical future needs

### 7. Keep responsibilities explicit
Maintain clean boundaries across:
- parsing / validation
- runtime instantiation
- simulation execution
- control / command application
- visualization / replay generation
- optional research wrappers

### 8. Keep the architecture language-flexible
The repository is currently Python-first, but future components do not need to stay all-Python.

Healthy future splits may include:
- graphical frontend in a different UI stack
- performance-critical planners/kernels in Rust or C++
- Python retained for orchestration, scenarios, experiments, and exports

Do not split by language prematurely. Only do so when there is a clear payoff in:
- capability
- performance
- development efficiency
- maintainability

---

## Development rules

### 1. Respect current phase boundaries
Before making changes, read:
- `docs/current_phase.md`
- the active `docs/step-*.md`

Do not pull later-phase architecture into the current step.

### 2. Reuse existing execution paths
Prefer wiring new features into the existing engine / trace / metrics / export / control / visualization surfaces instead of building parallel systems.

### 3. Keep parsing and execution separate
Scenario/config parsing should remain distinct from:
- runtime object construction
- execution orchestration
- export/replay generation

### 4. Protect regression surfaces
Changes that alter:
- trace ordering
- metrics summaries
- command history
- visualization state
- exports / golden fixtures

must be intentional and covered by tests.

### 5. Keep schema growth controlled
When extending scenarios or visualization/control formats:
- add only fields needed for the active step
- keep compatibility where reasonable
- avoid turning formats into catch-all bags of future concepts

### 6. Profile before optimizing or splitting
When performance/scaling becomes a focus:
- measure bottlenecks first
- add benchmark/profiling surfaces
- prefer data-informed optimization over intuition
- consider mixed-language separation only after profiling

---

## Testing expectations

All substantive changes should preserve or extend deterministic coverage.

Run:
```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
