# AGENTS.md

## Purpose

This file gives repo-wide guidance for implementation agents working in this repository.

The active execution/design sources of truth are:

- `docs/architecture_v2.md`
- `docs/execution_plan.md`
- `docs/current_task.md`
- `docs/world_model_v2.md`
- `docs/operator_workflows.md`

If there is any conflict between this file and the docs above, follow the docs above.

---

## Current repo reality

This repository is no longer in a narrow “Frontend v2 only” phase.

The implemented hybrid stack now includes:

- a canonical Python ↔ Unity HTTP/JSON bridge
- a real simulator-derived Unity bootstrap
- explicit Python-motion and Unity-motion authority modes
- Unity route execution over backend-issued route intent
- backend-owned embodiment and blockage feedback
- an operator-facing `operator_state` read model
- a backend-owned `replay_analysis` read model
- a cleanup pass that removed redundant bootstrap compatibility mirrors

Implementation work must respect that architecture rather than drifting back to older frontend-only assumptions.

---

## Current mission

Follow `docs/current_task.md`.

If `docs/current_task.md` says there is no active implementation slice, do not invent one.
Wait for a deliberate new task brief.

---

## Priority order

When making decisions, optimize in this order:

1. simulator authority and truth boundaries
2. canonical surface clarity
3. operator usefulness
4. maintainability of the hybrid stack
5. extensibility for later tracks
6. implementation neatness
7. speculative future flexibility

---

## Core architectural rules

### 1. Python remains authoritative
Python owns:

- topology truth
- runtime vehicle truth
- routing truth
- conflict/reservation truth
- command/session truth
- deterministic progression semantics
- replay/analysis truth after Unity signals are ingested

Do not move these into Unity or frontend/operator surfaces.

### 2. Unity is an execution client, not a truth owner
Unity may own:

- rendering
- transforms/orientation
- embodied motion execution
- terrain interaction
- collision/blockage sensing
- future sensor simulation

Unity must not own:

- topology truth
- authoritative runtime truth
- routing legality
- command truth
- task identity
- operator truth
- replay truth

### 3. Operator/frontend surfaces remain consumers
Operator-facing clients may own:

- camera/viewport state
- scene mode/layer state
- selection/highlight state
- popup/inspector state
- local workflow composition state
- replay/analysis presentation state

They must not own:

- authoritative runtime truth
- final route truth
- topology truth
- Unity-only truth outside backend projections

### 4. No shadow truth
Do not create local state that quietly becomes a competing source of truth for:

- vehicle state
- route state
- traffic/conflict state
- embodiment state
- replay state
- world state

### 5. Preserve canonical surfaces
Prefer the canonical surfaces that now exist:

- Unity bootstrap for Unity runtime consumption
- `operator_state` for operator-facing live inspection
- `replay_analysis` for backend-owned replay and analysis

Do not reintroduce removed compatibility mirrors unless there is a documented consumer and reason.

### 6. No environment forks
Do not build separate architecture tracks for:

- mining
- yard
- city

The world model and hybrid runtime must remain environment-agnostic at the architecture level.

---

## Working style for implementation agents

### 1. Be implementation-first
Prefer:

- making the change
- wiring the feature
- updating tests
- validating it

Avoid:

- long speculative discussion
- unnecessary exploration
- broad refactors outside the requested slice

### 2. Respect exact scope
If asked for a specific slice, do only that slice.

Do not silently implement adjacent future work unless a tiny seam is required.

### 3. Bundle related work in one pass
When a step clearly requires:

- code changes
- state plumbing
- tests
- small doc updates

do them together in one pass.

### 4. Prefer bounded cleanup over patch-stacking
If a local area is too tangled to support the requested slice cleanly, do a bounded extraction or cleanup.

Do not preserve bad structure out of habit.
Do not let cleanup become a rewrite.

### 5. Keep communication concise
When reporting back:

- say what changed
- say what files were touched
- say how it was validated
- say what remains

---

## Implementation boundaries

### Acceptable when requested
- Unity bridge work
- live bundle/read-model work
- operator-facing projection work
- replay/analysis projection work
- narrow frontend/operator integration work
- narrow backend seams required by the current task
- cleanup that clarifies canonical surfaces

### Not acceptable unless explicitly requested
- broad simulator redesign
- authority-boundary changes
- major transport rewrites
- speculative sensor/AI systems
- environment-specific architecture forks
- broad UI rewrites unrelated to the current task

---

## Validation

### Backend changes
Run the smallest relevant validation set first, then expand if needed:

```bash
python3 -m pytest tests/test_live_app.py -q
