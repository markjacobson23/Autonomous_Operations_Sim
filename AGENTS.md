# AGENTS.md

## Purpose

This repository is a deterministic autonomous operations simulator focused on:
- scenario-driven execution
- operational tasks and dispatch
- coordination and control
- replay/export/live-sync surfaces
- viewer/frontend consumption of authoritative simulator state

This file is intentionally **repo-wide and step-independent**.

The single operational source of truth for roadmap status, active work, and step-by-step execution rules is:

- `docs/execution_plan.md`

If there is any conflict between broad guidance in this file and step-specific guidance in `docs/execution_plan.md`, follow `docs/execution_plan.md`.

---

## Core architectural principles

### 1. Determinism is first-class
The simulator should produce stable results for the same:
- scenario
- seed
- command sequence
- live-session progression
- replay/export/live-sync inputs

Preserve:
- explicit seeds
- stable ordering
- deterministic tie-breaking
- stable JSON and structured exports
- replayable command/session/viewer behavior where applicable

Do not introduce hidden nondeterminism through:
- unordered iteration where order matters
- uncontrolled randomness
- wall-clock-driven simulation semantics
- UI-driven direct mutation of runtime truth

### 2. Static topology is separate from runtime state
Static world structure and mutable per-run state must remain distinct.

Examples:
- `Graph` / `Map` are reusable topology assets
- `WorldState` owns runtime blocked-edge conditions
- reservations and live coordination state belong to runtime/session layers
- visualization state, replay bundles, and live sync are derived surfaces, not authoritative truth

Do not mutate static topology objects to represent per-run conditions.

### 3. The simulator core is authoritative
The core simulator owns:
- execution semantics
- vehicle/runtime truth
- routing and coordination truth
- typed commands and live sessions
- replay/export/live-sync truth

Viewers and frontends must consume stable simulator surfaces.
They must not become the source of truth.

### 4. Commands and interactions must remain explicit
Viewer-facing and operator-facing actions should translate into typed commands rather than bypassing runtime ownership.

Preserve:
- typed command surfaces
- validated application
- deterministic command ordering
- replayable command/session history

Avoid:
- direct viewer mutation of engine internals
- hidden control paths outside the command/session surfaces

### 5. Trace and structured surfaces are the main observability contract
Trace events and explicit runtime state are the outward-facing execution record.

Metrics, exports, replay bundles, visualization state, and live sync should derive from:
- trace
- explicit runtime/session state
- stable structured contracts

Avoid shadow truth when existing trace or structured surfaces already capture the behavior.

### 6. Visualization is a consumer, not an owner
Replay viewers, live viewers, and future higher-fidelity frontends must consume:
- replay/export surfaces
- live-sync surfaces
- command/result surfaces

They should not own:
- vehicle state
- routing state
- world-state mutation
- coordination logic

### 7. Keep responsibilities explicit
Maintain clean boundaries across:
- parsing / validation
- runtime instantiation
- simulation execution
- control / command application
- live-session progression
- replay / export / sync generation
- viewer/frontend consumption
- optional research/benchmark tooling

### 8. Keep the architecture language-flexible
The repository is currently Python-first, but future components do not need to stay all-Python.

Healthy future splits may include:
- a higher-quality graphical frontend in another UI/rendering stack
- performance-critical planners/kernels in Rust or C++
- Python retained for orchestration, scenarios, experiments, exports, and authoritative runtime behavior

Do not split by language prematurely.
Only do so when there is a clear payoff in:
- capability
- UI/UX quality
- performance
- development efficiency
- maintainability

### 9. Prefer additive refactoring over rewrites
Prefer:
- adding a focused module
- extending a narrow interface
- formalizing an existing stable concept
- creating transport-agnostic boundaries
- bounded subsystem replacement when justified

Avoid:
- speculative frameworks
- giant rewrites without interface continuity
- simulator-core changes made only for frontend convenience

---

## Development rules

### 1. Read the master plan first
Before making changes, read:
- `docs/execution_plan.md`

Do not rely on old step docs or outdated roadmap/current-phase files.

### 2. Respect the single-step workflow
Execution is step-driven through `docs/execution_plan.md`.

If the user prompts with:
- `step-x`

then only that step should be worked on, subject to the rules in `docs/execution_plan.md`.

Do not silently work on adjacent or future steps.

### 3. Reuse existing execution paths
Prefer wiring new work into the existing:
- engine
- trace
- metrics
- command/control
- live session
- replay/export
- live sync
- viewer-facing surfaces

Do not build parallel systems unless a step explicitly justifies it.

### 4. Keep schema and surface growth controlled
When extending:
- scenario formats
- replay/export formats
- live-sync contracts
- viewer-facing state

add only what is needed for the active step.
Do not turn structured formats into catch-all containers.

### 5. Protect regression surfaces
Changes that alter:
- trace ordering
- metrics summaries
- command/session history
- visualization state
- replay/export/live-sync contracts
- golden fixtures

must be intentional and covered by tests.

### 6. Measure before optimizing or splitting
When performance/scaling becomes relevant:
- benchmark first
- profile bottlenecks first
- prefer data-informed optimization
- consider mixed-language separation only after measurement justifies it

---

## Testing expectations

All substantive changes should preserve or extend deterministic coverage.

Run:
```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
```

If a step adds or changes a CLI/tool entrypoint, verify that entrypoint explicitly.

When changing:
- replay/export surfaces
- visualization state
- live sync
- benchmarks
- protocol-like data contracts

add or update deterministic tests and regression fixtures where appropriate.

---

## Long-term direction

This repository is evolving toward a broader autonomous operations platform with:
- richer visualization
- stronger live interactivity
- smoother and more realistic motion
- richer road/map/traffic realism
- AI-assisted operator features later
- performance/scaling work driven by benchmarks
- possible mixed-stack viewer or runtime components where justified

That expansion should preserve the core strengths of the project:
- determinism
- explicit state ownership
- stable trace/export/replay/live-sync surfaces
- modular layering
- clean separation between simulator authority and frontend presentation
