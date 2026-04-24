# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap/status: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Demo Track — Phase A: Hero environment blockout

## Objective

Build the first presentation-worthy Unity demo environment for the hybrid sim:

- a medium construction yard
- a small surrounding city/perimeter context
- a clean grayscale/minimal realistic look
- a stationary loader/chute landmark
- clear load, unload, and staging zones

This phase is about scene composition, readability, and demo readiness.
It is not about adding major new simulator behavior.

## Why this task exists

The hybrid stack is now real:

- canonical Python ↔ Unity bridge
- real Unity bootstrap
- explicit motion authority
- Unity route execution
- backend-owned operator and replay surfaces

The highest-leverage next step is to make Unity look intentional and presentation-ready.

Before adding more demo behavior, the world itself needs to look like a real operational site rather than a prototype scene.

## In scope

- create or refine one Unity demo scene for a medium construction yard
- add a small city/perimeter street context around the yard
- establish a clean grayscale / off-white visual style
- build readable road, pad, curb, and site massing
- create clearly readable:
  - load zone
  - unload zone
  - staging area
- add a stationary loader/chute/load-point landmark
- set up camera-ready composition for later hybrid demo use
- use free assets if helpful, but keep the scene visually consistent
- preserve compatibility with the existing backend-derived topology/runtime flow

## Out of scope

- do not add major new backend behavior
- do not redesign routing or dispatch
- do not implement true loading animation
- do not implement advanced physics or vehicle dynamics
- do not add a full traffic AI pass
- do not build a full replay UI
- do not turn this into a broad asset-integration spree
- do not add behavior that the current backend/runtime cannot honestly support

## Visual target

The visual target is:

- minimal realistic
- clean roads
- readable industrial/city massing
- mostly grayscale / concrete / off-white palette
- close in spirit to an architectural blockout / site massing reference
- visually calm rather than noisy

The yard should feel intentional and medium-scale, not tiny or empty.

## Scene requirements

The scene should include:

### Core yard
- one clear internal yard road network
- one clear load zone
- one clear unload zone
- one clear staging area
- one stationary loader/chute/load-point landmark

### Surrounding context
- one small city/perimeter road context
- enough surrounding building massing to make the yard feel embedded in a larger environment
- surrounding context must remain secondary to the yard

### Readability
- roads should be easy to read from wide and oblique views
- zones should be visually understandable from layout/material/form, not text labels
- the scene should already look good in still screenshots

## Architectural constraints

- Python remains authoritative for world truth, runtime truth, route legality, command truth, and session truth
- Unity remains an embodied runtime/client layer
- this phase must not create Unity-only operational truth
- this phase should prepare the world for later multi-vehicle demo phases, not bypass backend truth

## Allowed files to change

Only the minimum files needed for this phase.

Expected categories:
- Unity scene files
- Unity prefabs/materials
- Unity environment/blockout scripts if needed
- tiny bridge/bootstrap consumption adjustments only if strictly required for scene compatibility
- narrow docs/comments if useful

## Files that must not be broadly rewritten

- backend routing/dispatch architecture
- world model architecture
- operator read-model architecture
- replay/analysis architecture
- transport/bridge architecture
- unrelated frontend systems

## Deliverables

1. One medium construction-yard Unity scene
2. Small surrounding city/perimeter context
3. Clear load/unload/staging zone composition
4. Stationary loader/chute landmark
5. Camera-ready environment that already looks presentation-worthy without requiring rich vehicle behavior

## Acceptance criteria

This task is complete when:

- the scene no longer feels tiny or empty
- a still image already reads as a construction/industrial operations site
- the yard clearly supports later 3–5 vehicle demo phases
- the surrounding city context improves scale and realism without stealing focus
- the visual style is clean and consistent
- no authority boundaries were changed

## Practical rule

Prefer:

- strong scene composition
- readable massing
- clean roads and zones
- visual consistency
- future demo fit over unnecessary detail

Reject:

- clutter
- noisy asset mashups
- fake behaviors not supported by the backend
- broad backend changes for an environment-art task