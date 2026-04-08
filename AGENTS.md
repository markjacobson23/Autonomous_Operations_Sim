# AGENTS.md

## Purpose

This repository is built as a deterministic, production-style autonomous operations simulator.

Work in this repo should preserve:
- deterministic behavior
- explicit state boundaries
- trace-centered observability
- additive, scoped evolution
- small, testable public interfaces

This file is intentionally step-independent. It describes enduring repo rules and development philosophy. Step-specific scope belongs in:
- `docs/current_phase.md`
- `docs/step-*.md`

---

## Core architectural principles

### 1. Determinism is first-class
The simulator is expected to produce stable results for the same inputs and seed.

Preserve:
- explicit seeds
- stable trace ordering
- deterministic export output
- deterministic tie-breaking
- replayable behavior where possible

Do not introduce hidden nondeterminism through:
- unordered iteration over sets/dicts when order matters
- implicit wall-clock behavior
- uncontrolled random sources
- ad hoc async/background behavior that changes run order

### 2. Static topology is separate from runtime state
Static world structure and mutable run state must remain distinct.

Examples:
- `Graph` / `Map` are reusable topology assets
- `WorldState` owns runtime blocked-edge conditions
- reservation/conflict state belongs to runtime coordination structures, not static topology

Do not mutate static topology objects to represent per-run conditions.

### 3. Trace is the primary truth surface
The simulator’s most stable outward-facing surface is the trace.

Metrics, exports, and regression fixtures should derive from trace data rather than from ad hoc internal state peeking.

When adding new runtime behavior:
- prefer emitting explicit trace events
- keep trace semantics clear and stable
- avoid adding duplicate shadow state when trace already captures the truth

### 4. Prefer additive refactoring over rewrites
The repo should evolve through small, explicit layers.

Prefer:
- introducing a new focused module
- extending an existing small interface
- adding a narrow orchestration layer
- making local refactors that reduce duplication

Avoid:
- broad rewrites without necessity
- “framework first” abstractions
- speculative architecture for future hypothetical needs

### 5. Keep responsibilities explicit
The repo should preserve clean module boundaries.

Examples:
- parsing/validation is separate from runtime instantiation
- runtime execution is separate from visualization
- routing is separate from dispatch
- behavior state is separate from trace summarization
- metrics/export are derived surfaces, not execution drivers

### 6. Public surfaces should stay small
When adding APIs, prefer narrow production-like interfaces over sprawling convenience layers.

Examples of good public surfaces:
- `Router.route(...)`
- `SimulationEngine.run(...)`
- `SimulationEngine.execute_job(...)`
- `summarize_engine_execution(...)`
- `export_engine_json(...)`

Be cautious about expanding `__init__.py` exports if that risks circular imports or unclear boundaries.

---

## Development rules

### 1. Respect current phase boundaries
Before making changes, read:
- `docs/current_phase.md`
- the active `docs/step-*.md`

Do not pull later-phase architecture into the current step.

### 2. Reuse existing execution paths
When adding a new feature, prefer wiring into existing engine / trace / metrics / export flows rather than creating parallel code paths.

### 3. Keep parsing and execution separate
Scenario/config parsing should remain distinct from:
- runtime object construction
- simulation execution
- metrics/export generation

### 4. Protect regression surfaces
Changes that alter:
- trace ordering
- metrics summaries
- export format
- golden fixtures

must be intentional, explained, and covered by updated tests.

### 5. Keep schema growth controlled
When expanding scenario/config schema:
- add only fields needed for the active step
- keep backward compatibility where reasonable
- avoid turning the schema into a grab-bag of future concepts

### 6. Treat visualization and interactivity as consumers, not owners
Future viewers, control surfaces, or interactive tools should consume simulator state through explicit interfaces.

They should not become the place where simulator truth lives.

---

## Testing expectations

All substantive changes should preserve or extend deterministic coverage.

Run:
```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
