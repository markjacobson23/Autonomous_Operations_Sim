# Autonomous Operations Sim — Execution Plan
# Phase B Only: World Model v2 and Scene/Render Foundation

## Purpose

This plan covers **only Phase B**.

Phase B is responsible for building a **good** world-model and scene/render foundation underneath the now-usable Frontend v2 product.

At the end of this phase, the system must have:

- a clearer environment/world representation
- renderer-ready spatial semantics
- environment-aware but product-shared scene modeling
- believable world form for mine / yard / city style scenarios
- a stable bridge between simulator truth and map rendering truth

Phase B is **not** a frontend workflow redesign phase.
It exists to make the world the frontend consumes feel spatially coherent, extensible, and ready for later realism work.

This phase should improve:

- world form readability
- scene/render truth
- environment semantics
- geometry layering
- object/surface meaning
- future support for richer motion, traffic, hazards, and authoring

without violating the rule that the frontend remains a consumer of simulator-derived truth.

---

## Relationship to Phase A

Phase A established:

- Frontend v2 shell
- map shell
- selection / popup / inspector
- route preview
- command workflows
- mode structure
- visual system
- live app control path

Phase B must **build on** that work, not replace it.

Carry-over note:
- live playback during continuous play may still look visually jumpy because frontend sampling is coarser than ideal
- treat that as a **small carry-over stabilization item**, not the center of Phase B

---

## Design references

Use these docs as the design source of truth:

- `docs/frontend_v2.md`
- `docs/operator_workflows.md`
- `docs/architecture_v2.md`
- `docs/acceptance_demos.md`

---

## Locked decisions

### 1. Python simulator remains authoritative
Do not move world authority into the frontend.

Frontend must not own:
- authoritative topology truth
- runtime vehicle truth
- final route truth
- deterministic progression semantics
- conflict/reservation truth

### 2. One shared product model across environments
Phase B must improve support for:
- mining
- yard / depot
- city / road-network environments

without creating environment-specific frontend architectures or scene-render forks.

### 3. World semantics come before realism polish
This phase is about:
- what the world is
- how it is structured
- how it is exposed to rendering
- how it is surfaced to inspection and editing

It is not the phase for advanced behavior realism.

### 4. Scene/render foundation must support later phases
Phase B should create a foundation that later supports:
- richer motion
- traffic realism
- hazards
- diagnostics
- authoring
- explanation surfaces

without another world-model rewrite.

### 5. Frontend remains map-first
Phase B should improve the world **for the map**, not turn the product into a world debugger.

---

## Out of scope for this phase

Do not use Phase B for:

- deep vehicle behavior realism
- advanced lane-level traffic policy
- full hazard / weather systems
- advanced AI explanation systems
- batch fleet workflow depth
- command-center redesign
- renderer-stack replacement
- native performance optimization
- broad import pipeline work beyond small seams strictly needed for world-model structure

---

## Definition of done

Phase B is done only when all of these are true:

### World-model milestone
- world/environment semantics are clearer and more structured
- world features are represented in a way that supports mine / yard / city cases
- renderer-facing geometry truth is cleaner and less ad hoc
- scene-level semantics no longer depend on fragile one-off inference rules

### Scene foundation milestone
- roads, areas, intersections, surfaces, and world-form features have a coherent render contract
- world form reads spatially better in the map
- scene bounds / framing reflect real environment geometry, not just a subset of operational geometry
- geometry layering is stable enough for later realism work

### Frontend contract milestone
- Frontend v2 consumes the new world-model/render surfaces without gaining shadow truth
- selection, inspection, and scene highlighting remain grounded in authoritative surfaces
- Phase A flows still work after the new world/render foundation lands

### Extensibility milestone
- later motion / traffic / hazard / authoring work now has a clean world-model base
- adding new environment archetypes no longer implies product-level hacks

If any of those are false, Phase B is not done.

---

## Execution rules

### Rule 1
If prompted with `step-x`, do only that step.

### Rule 2
Do not redesign frontend workflows unless a small compatible seam is strictly required by the new world-model contract.

### Rule 3
Each step must produce:
- code
- tests where applicable
- visible structural gain
- a clear validation path

### Rule 4
Do not accept “slightly richer geometry” as success.
Accept only “cleaner world-model and scene/render foundation.”

### Rule 5
Do not introduce frontend shadow truth to compensate for backend/world-model gaps.

### Rule 6
Prefer general world semantics over environment-specific hacks.

---

# Step plan

## Step 56 — Phase B architecture note and boundary lock
**Goal:** lock what belongs to world model, render geometry, runtime state, and frontend consumption.

### Scope
- define world-model-v2 boundaries
- define simulator-owned world semantics vs render-ready geometry vs frontend adapters
- define how mine / yard / city fit one shared model
- define allowed compatibility seams with existing Frontend v2

### Deliverables
- Phase B architecture note
- ownership / boundary notes
- explicit world-model-v2 terminology

### Must not do
- no feature building disguised as architecture
- no environment-specific renderer branch
- no frontend-only geometry truth

### Done when
- there is one clear source of truth for world semantics
- there is one clear render-facing surface contract
- there is no ambiguity about what later phases should build on

---

## Step 57 — Environment archetypes and world-form taxonomy
**Goal:** define a stable world-form vocabulary that works across environments.

### Scope
- environment family / archetype structure
- world-form feature categories such as:
  - roads
  - lanes
  - intersections / control nodes
  - buildings / structures
  - yards / work areas
  - loading / unloading surfaces
  - no-go / hazard-prone surfaces
  - terrain / pit / embankment / boundary surfaces
- semantic grouping rules shared across environments

### Deliverables
- world-form taxonomy
- typed environment / archetype model
- tests around taxonomy / serialization where applicable

### Must not do
- no hardcoding to mining-only semantics
- no purely visual categories without operational meaning

### Done when
- mine / yard / city cases can all be described through one structured taxonomy
- world features have clearer meaning than “misc area polygon”

---

## Step 58 — World model surface v2
**Goal:** build the authoritative world-model surface that later rendering and inspection consume.

### Scope
- world feature inventory
- stable identifiers and feature categories
- grouping / layering metadata
- feature relationships where needed
- environment metadata richer than the current thin display-name layer

### Deliverables
- world model v2 surface
- serialization / export path
- tests for shape and compatibility

### Must not do
- no frontend-owned reinterpretation of the world
- no duplicate truth between map surface and world model without explicit relationship

### Done when
- the world has a coherent machine-readable structure
- render and inspection layers can consume it predictably

---

## Step 59 — Render geometry contract cleanup
**Goal:** make render geometry a cleaner projection of world truth rather than a loose mixed bag.

### Scope
- clarify which surfaces are authoritative semantics vs render projections
- improve geometry layering
- improve feature-specific render geometry organization
- remove or reduce fragile inference patterns where possible
- ensure render geometry is renderer-ready but still derived

### Deliverables
- cleaned render geometry contract
- compatibility mapping for Frontend v2
- tests for render geometry construction

### Must not do
- no renderer-stack replacement
- no geometry duplication without a reason
- no hidden coupling between rendering and command semantics

### Done when
- render geometry is easier to consume, reason about, and extend
- scene rendering no longer depends on unclear mixed-purpose geometry blobs

---

## Step 60 — Scene bounds, framing, and spatial extents foundation
**Goal:** make scene framing and overview reflect the real environment.

### Scope
- better scene bounds from meaningful world geometry
- environment-aware framing inputs
- spatial extents that include real world-form context
- clean support for minimap and fit/focus using better scene truth

### Deliverables
- improved scene bounds logic
- tests around bounds / framing inputs
- compatibility with current frontend camera usage

### Must not do
- no camera UX redesign here
- no frontend hacks to guess missing environment extents

### Done when
- fit / overview can rely on better environment geometry
- world form is less likely to clip or disappear from framing decisions

---

## Step 61 — World-aware scene rendering baseline
**Goal:** make the scene renderer consume the better world/render foundation in a shared way.

### Scope
- render consumption of new world-form / render layers
- cleaner treatment of:
  - structural massing
  - terrain-like surfaces
  - yards / zones
  - roads / intersections
- preserve quiet-default map rules while improving world readability

### Deliverables
- renderer integration with Phase B surfaces
- tests where practical
- before / after validation on at least the mining scenario

### Must not do
- no mode redesign
- no label clutter regression
- no environment-specific component forks unless strictly necessary

### Done when
- the map reads more like a real environment
- world-form improvements are visible without breaking Phase A workflows

---

## Step 62 — Inspection and selection alignment with world model
**Goal:** ensure the richer world model improves selection and inspection instead of just rendering.

### Scope
- world feature selection compatibility
- clearer inspection summaries for environment features
- more coherent relationship between selected scene objects and their semantic role
- support for future editor / analyze work through cleaner feature identity

### Deliverables
- aligned selection / inspection adapters
- tests for feature identity / selection presentation where useful

### Must not do
- no inspector bloat
- no debug-dump surfaces as a substitute for semantic clarity

### Done when
- selecting world objects reveals cleaner semantic meaning
- the richer scene foundation improves usability, not just visuals

---

## Step 63 — Phase B acceptance walkthroughs
**Goal:** prove the new world/render foundation is real and safe to build on.

### Required walkthroughs

#### A. World-form walkthrough
1. launch mining scenario
2. fit scene
3. inspect world-form readability
4. verify roads / structures / areas / terrain-like context are clearer
5. verify quiet-default map still holds

#### B. Selection walkthrough
1. select vehicle
2. select road
3. select area / structure / world feature
4. verify inspection reflects clearer semantic identity

#### C. Renderer stability walkthrough
1. switch view modes
2. pan / zoom / focus / minimap
3. verify framing is stable and world-aware
4. verify no regression in preview / selection / commands

#### D. Foundation walkthrough
1. verify Phase A operator loop still works
2. verify world / render contracts are cleaner
3. verify later motion / traffic / hazard work now has a stronger base

### Deliverables
- working walkthroughs
- validation notes
- any final small fixes required to make the phase credible

### Must not do
- no moving on because “the docs are cleaner”
- no shipping a prettier but still ad hoc world-model layer

### Done when
- the world/render foundation is visibly stronger
- Phase A functionality still works
- the project is ready for richer realism work without another scene-model rewrite

---

# Validation checklist

## World model
- Is the environment/world taxonomy clearer?
- Is world truth structured enough to support multiple environment families?
- Are stable identifiers and feature categories present where needed?

## Render geometry
- Is render geometry clearly derived from world semantics?
- Are geometry layers easier to consume and reason about?
- Has fragile inference been reduced?

## Scene framing
- Do scene bounds reflect real environment geometry?
- Do fit/focus/minimap have better world-aware inputs?

## Scene readability
- Does the map read more like a world and less like a thin overlay?
- Are roads, structures, areas, and surfaces more coherent together?
- Is the quiet-default rule preserved?

## Selection and inspection
- Do selected world features have clearer meaning?
- Does inspection benefit from the richer model without becoming bloated?

## Compatibility
- Do Phase A workflows still work?
- Has Frontend v2 remained a consumer instead of becoming a competing authority?

## Product readiness
- Does the project now have a world/render foundation strong enough for later realism work?
- Would later phases be building on a clean base instead of another patch layer?

If any answer is “no,” Phase B is not done.

---

## What comes after Phase B

Only after Phase B is complete should the project move on to:
- deeper vehicle motion realism
- richer traffic realism
- hazard systems
- operational diagnostics / explanation depth
- stronger authoring flows
- benchmark-guided polish

Later phases should improve a **good world/render foundation**, not rescue a weak one.
