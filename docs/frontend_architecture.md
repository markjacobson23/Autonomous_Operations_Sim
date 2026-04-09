# Frontend Architecture Lock

This note records the Step 41 frontend decision and is the repo-level reference for the serious UI direction entering Phase A.

## Locked choices

- Primary stack: `React + TypeScript + Vite` in a dedicated frontend workspace.
- Primary renderer strategy: responsive `SVG` scene rendering for the serious operator shell baseline.
- Fallback stack: the existing Python-generated standalone serious viewer HTML export path.
- Simulator authority: Python remains authoritative for runtime state, commands, routing, trace, replay bundles, live-session bundles, and live-sync bundles.
- Frontend authority: the serious UI consumes derived surfaces and submits explicit typed commands through backend/session boundaries; it does not directly mutate simulator internals.

## Why this stack

The project needs a stronger UI ceiling than the standalone exported viewer while preserving the existing Simulation API contract. `React + TypeScript + Vite` gives fast iteration, a mature component model, and a clean way to build a real operator shell without moving simulator authority out of Python.

`SVG` is the initial rendering choice because it works well with the current geometry-heavy derived surfaces, supports deterministic layer ordering, stays debuggable during the early UI steps, and avoids prematurely committing to a heavier graphics stack before camera, selection, and scene-layer requirements are proven.

## Backend and frontend split

The split for the next phase is:

- Backend: Python simulator, session control, bundle generation, command validation, live-session truth, live-sync truth.
- Frontend: application shell, scene rendering, inspector panes, command-center presentation, timeline controls, transport adapters, and future operator workflows.

The frontend reads versioned Simulation API surfaces. Step 41 does not introduce a new transport runtime. The transport assumption is intentionally narrow:

- Immediate compatibility path: load replay/live/live-sync bundle JSON surfaces.
- Next live path: connect the serious frontend to backend-provided session/live-sync surfaces without changing simulator authority.

## Repo layout lock

The serious frontend workspace lives at:

- `frontend/serious_ui/`

The locked layout inside that workspace is:

- `package.json`: frontend scripts and dependency boundary
- `tsconfig.json`: TypeScript compiler settings
- `vite.config.ts`: Vite dev/build configuration
- `index.html`: app entry document
- `src/main.tsx`: React bootstrap
- `src/App.tsx`: initial application shell
- `src/app-shell.css`: shell tokens and layout styling

This keeps the serious frontend isolated from the Python package while still living in the same repository.

## Fallback path

The fallback path remains the existing standalone serious viewer:

- Python renders HTML from Simulation API bundles.
- This path stays supported for export/showcase use and for environments where the serious frontend workspace is unavailable.

That fallback is compatibility support, not the primary end-state UI.

## Non-goals for Step 41

This step does not add:

- live transport runtime implementation
- production scene interaction behavior
- map editing tools
- frontend command execution
- visual polish beyond a compileable placeholder shell

## Validation checkpoint

Step 41 is complete when:

- the primary stack and fallback stack are explicit
- Python authority versus frontend rendering responsibility is unambiguous
- `frontend/serious_ui/` exists as a dedicated app workspace
- the app shell is present and intended to compile/run cleanly once Node tooling is installed
