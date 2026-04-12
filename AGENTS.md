# AGENTS.md

## Purpose

This file gives repo-wide guidance for implementation agents working in this repository.

The current active focus is:

- **Phase A only**
- **Frontend v2 product completion**
- taking the serious frontend from prototype/debug quality to a genuinely good map-first operator product

The active execution source of truth is:

- `docs/execution_plan.md`

The active product/design references are:

- `docs/frontend_v2.md`
- `docs/operator_workflows.md`
- `docs/architecture_v2.md`
- `docs/acceptance_demos.md`

If there is any conflict between this file and `docs/execution_plan.md`, follow `docs/execution_plan.md`.

---

## Current mission

Right now, the goal is **not** to broadly improve the whole simulator.

The goal is to complete **Frontend v2** as a real product foundation.

That means delivering a frontend that is:

- map-first
- calm by default
- selection-driven
- operationally useful
- previewable
- trustworthy
- presentation-worthy

Do not optimize for “less bad.”
Optimize for “good enough to be the real foundation for later phases.”

---

## Priority order

When making decisions during the current phase, optimize in this order:

1. simulator authority and truth boundaries
2. operator usefulness
3. map readability and interaction quality
4. product quality and visual coherence
5. extensibility for later phases
6. implementation neatness
7. speculative future flexibility

---

## Core architectural rules

### 1. Python simulator remains authoritative
The simulator owns:
- topology truth
- runtime vehicle truth
- routing truth
- conflict/reservation truth
- command/session truth
- deterministic progression semantics

Do not move these into the frontend.

### 2. Frontend remains a consumer
Frontend v2 may own:
- camera/viewport state
- scene mode/layer state
- selection/highlight state
- popup/inspector state
- local planning workflow state
- mode/panel state
- editor gesture state

Frontend v2 must not own:
- authoritative runtime truth
- final route truth
- conflict truth
- topology truth

### 3. No frontend shadow truth
Do not create local frontend state that quietly becomes a competing source of truth for:
- vehicle state
- route state
- traffic/conflict state
- world state

Previews and workflows may exist locally, but authoritative results must come from backend truth.

### 4. Map-first product rule
The map is the primary surface.
Panels support the map and must not dominate it.

Default UX should be:
- quiet
- readable
- selection-driven
- progressive disclosure

Not:
- debug-heavy
- form-first
- stacked-card-first
- label-spam-heavy

### 5. No environment forks
Do not build separate frontend architectures for:
- mining
- yard
- city

Frontend v2 must stay environment-agnostic at the product-architecture level.

### 6. Do not keep patching the old UI indefinitely
If the old serious UI path is blocking Frontend v2 quality, prefer bounded replacement instead of endless patching.

Do not preserve bad structure just because it already exists.

---

## Frontend v2 product rules

### 1. Quiet default map
The default map should show:
- world/environment form
- roads
- vehicles
- only essential context

The default map should not show:
- always-on node labels
- always-on place labels
- always-on vehicle labels
- always-on destination labels
- large explanatory chrome
- debug clutter

### 2. Selection-driven detail
Details should appear through:
- selection
- preview
- explicit mode/panel use
- explicit layer toggles

Not through constant always-on text.

### 3. Primary interaction model
The primary interaction model is:

- click to select
- inspect in popup + inspector
- preview on the map
- commit action from a compact workflow surface

Not:
- type raw IDs into the main workflow

### 4. Operate mode is the heart of the product
Operate mode should feel like:
- large map
- compact inspector
- compact planning/command surface
- minimal session controls

Not:
- a console with a map attached

### 5. Every mode needs a real product role
Frontend v2 must provide real homes for:
- Operate
- Traffic
- Fleet
- Editor
- Analyze

Do not create empty placeholder modes with no clear purpose.

### 6. Popup and inspector rules
Popup should be:
- compact
- map-friendly
- selection-scoped

Inspector should be:
- useful
- compact by default
- expandable when needed
- organized around operator questions, not raw dumps

### 7. Command workflows must feel grounded
Commands should be:
- typed
- explicit
- previewable when appropriate
- selection-aware
- backed by authoritative results/errors

Do not build fake or disconnected command UX.

---

## Working style for Codex

### 1. Be implementation-first
Prefer:
- making the change
- wiring the feature
- updating tests
- validating it

Avoid:
- long speculative discussion
- unnecessary exploration
- broad refactors outside the requested step

### 2. Respect exact scope
If asked for a specific step, do only that step.

Do not silently implement adjacent future work unless a tiny seam is required.

### 3. Bundle related work in one pass
When a step clearly requires:
- component changes
- state plumbing
- styles
- tests

do them together in one pass.

Do not leave obvious half-finished wiring if the step clearly requires completion.

### 4. Prefer replacement over patch-stacking when justified
If a local area is too tangled to support the requested step cleanly, do a bounded replacement.

Do not preserve bad structure out of habit.

### 5. Keep communication concise
When reporting back:
- say what changed
- say what files were touched
- say how it was validated
- say what remains

Do not write long narrative summaries unless asked.

---

## Implementation boundaries

### Acceptable during this phase
- frontend-v2 app shell work
- map shell work
- renderer work
- selection/popup/inspector work
- mode/panel work
- command/preview workflow work
- frontend-specific styling/polish
- small backend seams strictly required for Frontend v2 completion

### Not acceptable during this phase unless explicitly requested
- deep simulator realism work
- lane behavior systems
- advanced kinematics
- major hazard/weather systems
- broad schema expansion
- AI suggestion depth
- native acceleration work
- large backend read-model churn with weak frontend payoff

---

## Testing and validation

### Frontend changes
Run:
```bash
cd frontend/serious_ui && npm run build
cd frontend/serious_ui && npm test

### Backend changes
run:
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
