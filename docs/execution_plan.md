# Autonomous Operations Sim — Master Execution Plan (Post-Step-40)

## Purpose

This is the single master execution plan for the next major phase after Step 40.
It is optimized for the real target vision:
- visually impressive simulator UI
- richer map/world realism
- believable traffic and vehicle motion
- live operator interaction
- expandable environments centered on **mine depot**, with clean extension to **construction yard** and **city street**
- grounded AI-assisted operator features
- preserved deterministic simulator authority

## Current baseline entering this plan

By the end of Step 40, the project already has:
- deterministic Python simulator authority
- versioned replay / live-session / live-sync Simulation API bundles
- serious viewer and showcase export flow
- command-center, vehicle inspection, traffic, and AI-assist read models
- mining showpiece scenarios
- benchmark harness
- optional native reservation acceleration

The biggest remaining gap is now **experience quality**:
- frontend/product quality
- map realism
- traffic realism
- vehicle realism
- live operator interaction

---

## Locked decisions

### 1. Simulator authority stays in Python
The Python simulator remains the source of truth for topology, runtime state, routing, jobs/tasks, reservations, metrics, and trace.

### 2. View state remains derived from simulator truth
Frontend state, AI-assist state, traffic overlays, and inspection surfaces remain **derived** from simulator truth rather than becoming competing authority layers.

### 3. Split architecture is allowed and preferred for UI quality
The long-term serious UI should not be constrained by the current Python/standalone-HTML path.
A separate serious frontend is expected.

### 4. Best-looking UI wins
When there is tension between “keep everything in Python UI” and “get a substantially better cross-platform frontend,” prefer the stronger frontend path.

### 5. Mining remains the flagship environment
Construction-yard and city-street support must be designed in, but the mining operation remains the flagship demo and acceptance target.

### 6. Native acceleration remains narrow and benchmark-justified
Do not move logic into native code unless:
- a benchmark shows a real hotspot
- parity is testable
- the fallback path remains correct

---

## What to preserve vs. what to supersede

### Preserve
- Simulation API bundle architecture
- deterministic trace and metrics model
- reservation-based conflict-handling baseline
- command-center / inspection / AI-assist read-model concept
- showcase/export flow
- benchmark harness
- mining scenarios as seed assets

### Supersede or evolve
- standalone serious-viewer-as-end-state assumption
- simplistic post-hoc-only motion rendering
- road-level-only realism where lane-level semantics are needed
- early UI layout and visual language once a real frontend app exists

---

## Execution rules for implementation

### Step triggering rule
If prompted with `step-41`, `step-52`, or `step-73`, do **only that step**.

### Scope rule
Do not pre-implement future steps unless the current step explicitly requires a small forward-compatible seam.

### Refactoring rule
Refactoring is allowed when necessary for the current step, but must stay tightly bounded and justified.
Do not perform speculative architecture cleanup that is not required for the step.

### Output rule for implementation work
Each step implementation should leave behind:
- code
- tests
- any required docs or scenario/demo assets
- a clear way to validate that the step is complete

### Anti-false-peak rule
Do not over-invest in backend/API surfaces that do not directly improve one of these:
- visual quality
- realism
- operator workflow
- extensibility for the targeted environments
- performance for proven hotspots

---

## Phase overview

- **Phase A (Steps 41–46):** serious frontend foundation and operator shell
- **Phase B (Steps 47–54):** world/map realism and authoring backbone
- **Phase C (Steps 55–62):** vehicle motion and traffic realism
- **Phase D (Steps 63–68):** live operations UX and scenario mutation
- **Phase E (Steps 69–76):** resource realism, diagnostics, hazards, imports
- **Phase F (Steps 77–82):** AI/operator/research layers on top of richer truth
- **Phase G (Steps 83–88):** performance, showpieces, and final polish checkpoints

---

# Detailed roadmap

## Step 41 — Frontend architecture lock
**Type:** foundation
**Goal:** Lock the serious UI direction, app boundaries, transport assumptions, and repo layout for the next phase.
**Why now:** The project needs a stable frontend direction stronger than standalone exported HTML.
**Dependencies:** Step 40 complete.
**Likely touches:** docs, frontend app scaffold, repo tooling docs.
**Must not change yet:** simulator authority logic, Simulation API semantics, existing serious-viewer exporter behavior.
**Do not pre-implement:** full frontend features, transport runtime, UI polish.
**Deliverables:** locked frontend technology choice, locked backend/frontend split, locked directory structure, architecture note.
**Acceptance criteria:** one primary stack, one fallback stack, no ambiguity about Python authority vs. frontend rendering.
**Demo/checkpoint:** architecture note and empty app shell compile/run cleanly.

## Step 42 — Live app launch path
**Type:** foundation / UI-product
**Goal:** Provide a built-in command that launches a live simulator session and opens the serious frontend without custom scripts.
**Why now:** The project already has showcase export; the next usability milestone is a real live-run path.
**Dependencies:** Step 41.
**Likely touches:** CLI entrypoints, backend live-session startup path, frontend launch integration, docs/README.
**Must not change yet:** command semantics, core engine behavior.
**Do not pre-implement:** advanced scene interactions, editor features.
**Deliverables:** `autonomous-ops-sim live --scenario ...`, backend session bootstrap, frontend connection bootstrap.
**Acceptance criteria:** one command starts a live scenario and opens the serious UI; no handwritten glue script is needed.
**Demo/checkpoint:** live mining scenario opens in the serious frontend from repo root.

## Step 43 — Serious frontend app shell
**Type:** UI-product
**Goal:** Build the actual serious UI shell: app frame, toolbars, panes, timeline region, command-center region, inspector region, alerts region.
**Why now:** A real operator shell is required before deeper interaction and realism work can land cleanly.
**Dependencies:** Step 42.
**Likely touches:** frontend app shell files, theme/tokens/layout components.
**Must not change yet:** live command behavior, rendering engine choice.
**Do not pre-implement:** map editing, advanced AI panels.
**Deliverables:** responsive shell, persistent dock/panel layout, timeline placeholder, minimap/overview placeholder.
**Acceptance criteria:** layout remains usable on typical laptop screens; live session metadata and bundle status are visible.
**Demo/checkpoint:** screenshot-worthy shell with live bundle data populating core panes.

## Step 44 — Camera, scene graph, and layer controls
**Type:** foundation / UI-product
**Goal:** Add pan/zoom, fit-to-scene, selection focus, scene layers, and minimap navigation.
**Why now:** Users must be able to navigate larger mining and future city scenes before richer map and traffic visuals matter.
**Dependencies:** Step 43.
**Likely touches:** frontend scene renderer, viewport controller, minimap and layer-toggle components.
**Must not change yet:** lane model, traffic logic.
**Do not pre-implement:** route-editing tools, fleet workflows.
**Deliverables:** scene camera controls, layer toggles for geometry/routes/traffic/reservations/hazards, minimap panel.
**Acceptance criteria:** large scenes are comfortably navigable; layer toggles do not break rendering correctness.
**Demo/checkpoint:** mining map can be panned, zoomed, fit, and viewed via minimap.

## Step 45 — Direct selection and hover interaction baseline
**Type:** UI-product
**Goal:** Support clicking moving vehicles, roads, queues, and conflict areas; add hover states and selected-object highlighting.
**Why now:** This is the first step where the UI becomes operationally useful instead of merely viewable.
**Dependencies:** Step 44.
**Likely touches:** frontend scene hit-testing, selection store, inspector state plumbing.
**Must not change yet:** command semantics, map editing behavior.
**Do not pre-implement:** batch commands, drag-to-edit map geometry.
**Deliverables:** click-to-select vehicle, click-to-select road/edge, hover states/tooltips, route/reservation emphasis.
**Acceptance criteria:** moving vehicles remain selectable while animating; selected-object state feeds the inspector reliably.
**Demo/checkpoint:** operator clicks a moving vehicle and sees consistent highlight + inspector update.

## Step 46 — Visual polish pass 1
**Type:** UI-product / realism
**Goal:** Do the first major visual pass so the simulator stops looking prototype-grade.
**Why now:** Visual quality is one of the highest project priorities.
**Dependencies:** Steps 43–45.
**Likely touches:** frontend theming, typography, iconography, color system, panel styling, path/overlay effects.
**Must not change yet:** traffic algorithms, lane semantics.
**Do not pre-implement:** day/night system, audio system.
**Deliverables:** better styling tokens, more cinematic scene treatment, improved overlay palette, cleaner inspector presentation.
**Acceptance criteria:** the serious frontend is presentation-worthy; overlays are easier to parse.
**Demo/checkpoint:** before/after visual comparison on the mining showcase.

## Step 47 — World model v2 for expandable environments
**Type:** foundation / realism
**Goal:** Define the next world/scene model so mining, construction yard, and city street all fit cleanly.
**Why now:** The project needs a stronger scene abstraction before richer map realism and editing are added.
**Dependencies:** Step 41.
**Likely touches:** map/geometry modules, scenario schema/models, render-geometry serialization.
**Must not change yet:** lane traffic algorithms, imported map adapters.
**Do not pre-implement:** full editor UX, weather systems.
**Deliverables:** world layer taxonomy for roads/intersections/depots/sidewalks/zones/buildings/no-go areas; environment archetype model for mine/construction/city.
**Acceptance criteria:** the model can represent all three target environment families without hacks; existing mining scenarios map cleanly.
**Demo/checkpoint:** architecture sample showing one mining, one yard, and one street scene in the unified model.

## Step 48 — Environment archetypes and world asset layers
**Type:** realism
**Goal:** Add explicit support for reusable environment archetypes and layered visual/background assets.
**Why now:** Once the world model exists, it should immediately gain visible benefit through richer environment semantics.
**Dependencies:** Step 47.
**Likely touches:** scenario/world schema, render geometry/building/background layers, showcase scenarios.
**Must not change yet:** lane behavior logic, map import pipeline.
**Do not pre-implement:** editor-driven asset placement tools beyond what the step requires.
**Deliverables:** mine depot archetype assets and semantics, construction yard scaffolding, city street scaffolding.
**Acceptance criteria:** each environment family has distinct zone/area/building semantics; mining remains the richest path.
**Demo/checkpoint:** one scene from each environment family rendered with visibly different environmental character.

## Step 49 — Authoring model and editor backbone
**Type:** foundation / UI-product
**Goal:** Create the backend and frontend structure needed for live geometry editing and future scenario authoring.
**Why now:** Map realism will stall if every improvement still requires hand-editing scenario JSON.
**Dependencies:** Steps 47–48.
**Likely touches:** scenario/editor modules, frontend editing state, serialization/update path.
**Must not change yet:** imported external map standards, full multi-user editing ideas.
**Do not pre-implement:** advanced editor polish, full undo/redo beyond minimal support.
**Deliverables:** authoring data model, edit transaction format, live validation rules for geometry mutations.
**Acceptance criteria:** geometry edits can be represented and saved cleanly; invalid topology edits are rejected deterministically.
**Demo/checkpoint:** authoring model round-trips a modified scene without losing semantics.

## Step 50 — Live map editing baseline
**Type:** UI-product / realism
**Goal:** Support operator/editor actions to move nodes, edit roads, change zones, and save scene changes.
**Why now:** This is the first true map-editing milestone and unlocks much faster scenario iteration.
**Dependencies:** Step 49.
**Likely touches:** frontend editing tools, backend validation/update path, scenario save/load code.
**Must not change yet:** lane traffic engine internals, import adapters.
**Do not pre-implement:** fully polished content pipeline.
**Deliverables:** edit handles for geometry, live save/reload workflow, validation messages in UI.
**Acceptance criteria:** operator can edit map geometry live and persist changes; edited scenario still loads and runs deterministically.
**Demo/checkpoint:** modify a road or area in the mining scene and rerun immediately.

## Step 51 — Lane geometry model
**Type:** realism / foundation
**Goal:** Introduce explicit lane-level geometry and semantics.
**Why now:** Lane-based traffic, stop lines, merges, and overtaking should become natural extensions rather than viewer-only artifacts.
**Dependencies:** Steps 47–50.
**Likely touches:** geometry model, scenario schema, API bundle world surfaces, frontend lane rendering.
**Must not change yet:** car-following and merging algorithms.
**Do not pre-implement:** full lane-changing behavior logic.
**Deliverables:** lane centerlines, lane directionality, turn connectors, stop lines, merge zones.
**Acceptance criteria:** scenes can encode one-way/two-way roads with lane-level detail; mining/loading-bay lane semantics are representable.
**Demo/checkpoint:** mining scene displays explicit lanes and stop-line/connector geometry.

## Step 52 — Kinematics model introduction
**Type:** realism / foundation
**Goal:** Create a simulation-side kinematics model that can drive motion, headings, acceleration bounds, and ETA more truthfully than pure interpolation.
**Why now:** Viewer-only smoothstep motion is a fidelity gap.
**Dependencies:** Step 51.
**Likely touches:** engine/motion modules, trace or derived motion generation, ETA calculations.
**Must not change yet:** detailed lane-change logic, external physics integration.
**Do not pre-implement:** sensor simulation, full rigid-body dynamics.
**Deliverables:** kinematics model interface, acceleration/deceleration-aware traversal model, heading/orientation model.
**Acceptance criteria:** motion surface and ETA derive from shared kinematic assumptions; viewer playback matches simulation-side outputs.
**Demo/checkpoint:** side-by-side comparison of old interpolation vs. kinematics-backed motion.

## Step 53 — Curve-following and turn arcs
**Type:** realism
**Goal:** Make vehicles visibly follow curves and turn arcs through intersections and connectors.
**Why now:** Once kinematics exist, the next realism win is actual path-following over curves and junctions.
**Dependencies:** Step 52.
**Likely touches:** motion/path-following modules, geometry/lane connector surfaces, frontend renderer.
**Must not change yet:** queue algorithms, signals.
**Do not pre-implement:** full merge/overtake logic.
**Deliverables:** curved path traversal support, turn-arc rendering and playback, heading arrows that follow motion naturally.
**Acceptance criteria:** vehicles no longer appear to snap direction at intersections; curve-following works for mining and at least one non-mining scene.
**Demo/checkpoint:** replay of turning vehicles through curved roads and shaped intersections.

## Step 54 — Vehicle presentation upgrade
**Type:** UI-product / realism
**Goal:** Introduce distinct visual/inspection identities for haul trucks, forklifts, cars, and future vehicle families.
**Why now:** Vehicle realism is not only motion; users need to recognize vehicle types and roles quickly.
**Dependencies:** Steps 45, 52, 53.
**Likely touches:** vehicle model/presentation metadata, frontend icon/glyph rendering, inspector / optional vehicle diagram panels.
**Must not change yet:** diagnostics/warnings logic, advanced fleet ops.
**Do not pre-implement:** photoreal asset pipeline.
**Deliverables:** distinct vehicle class renderers, optional clicked vehicle info/diagram presentation, role-aware inspector labels.
**Acceptance criteria:** haul trucks, forklifts, and cars are distinguishable in motion and in inspection.
**Demo/checkpoint:** multi-vehicle scene with mixed classes that are readable at a glance.

## Step 55 — Collision envelopes and following distance
**Type:** realism
**Goal:** Add vehicle footprints, spacing envelopes, and safe following behavior.
**Why now:** Multiple moving vehicles do not feel believable until spacing constraints are visible and enforced.
**Dependencies:** Steps 51–54.
**Likely touches:** vehicle motion/spacing logic, traffic state derivations, visualization overlays.
**Must not change yet:** full lane-change / overtaking policies.
**Do not pre-implement:** all intersection logic in the same step.
**Deliverables:** collision/spacing envelope model, following-distance logic, spacing/conflict overlays.
**Acceptance criteria:** trailing vehicles slow or wait instead of visually overlapping leaders; spacing metrics are inspectable.
**Demo/checkpoint:** visible stop-and-follow behavior in a shared corridor.

## Step 56 — Queue formation and congestion baseline
**Type:** realism
**Goal:** Make queue growth, queue discharge, and congestion buildup operationally and visually explicit.
**Why now:** This is the first step where “traffic density / liveliness” becomes clearly visible.
**Dependencies:** Step 55.
**Likely touches:** traffic logic, command-center queue surfaces, frontend overlays/heatmaps.
**Must not change yet:** signals and right-of-way complexity.
**Do not pre-implement:** full gridlock avoidance system.
**Deliverables:** queue state model, animated queue overlays, congestion intensity/heatmap surfaces.
**Acceptance criteria:** the UI shows visible queue buildup and release; queue states can be inspected per road/intersection.
**Demo/checkpoint:** multi-vehicle mining route with clear queue and congestion visualization.

## Step 57 — Stop lines, yielding, and traffic-control logic
**Type:** realism
**Goal:** Add stop lines, yielding, protected conflict areas, and traffic-control semantics.
**Why now:** Queue realism without credible control behavior still feels incomplete.
**Dependencies:** Steps 51, 55, 56.
**Likely touches:** lane/intersection semantics, traffic-control state, behavior/wait-reason derivations, UI overlays.
**Must not change yet:** lane-change / overtaking / merge intelligence.
**Do not pre-implement:** city-wide advanced signal optimization.
**Deliverables:** stop-line semantics, yield logic, signal-ready control point model, control state visualization.
**Acceptance criteria:** vehicles stop/yield for appropriate reasons and surface those reasons in inspection; controlled intersections behave differently from free-flow junctions.
**Demo/checkpoint:** visible stop/yield behavior with wait-reason inspection.

## Step 58 — Lane choice, merging, and overtaking baseline
**Type:** realism
**Goal:** Add route-aware lane choice, merge behavior, and limited overtaking where appropriate.
**Why now:** This is the next step from lane geometry to lane behavior.
**Dependencies:** Steps 51, 55–57.
**Likely touches:** lane behavior logic, route planning extensions, UI lane/trajectory overlays.
**Must not change yet:** full learned driver behavior.
**Do not pre-implement:** full autonomous policy experimentation.
**Deliverables:** basic lane selection rules, merge behavior, constrained overtaking baseline.
**Acceptance criteria:** multilane roads produce visibly different movement choices; merge and overtaking behavior are bounded and deterministic.
**Demo/checkpoint:** city-street or yard scenario showing merge and overtaking baseline.

## Step 59 — Deadlock and gridlock avoidance
**Type:** realism / operations
**Goal:** Add explicit anti-deadlock logic for intersections, depots, narrow corridors, and queue spillback.
**Why now:** As traffic density increases, deadlock handling becomes mandatory for believable operations.
**Dependencies:** Steps 55–58.
**Likely touches:** reservation/conflict logic, traffic state derivations, command-center diagnostics/anomalies.
**Must not change yet:** AI dispatch policy layer.
**Do not pre-implement:** generic multi-agent research framework.
**Deliverables:** deadlock detection rules, mitigation strategies, operator-visible deadlock risk surfaces.
**Acceptance criteria:** dense demo scenarios no longer silently jam without explanation; mitigations and remaining risk are inspectable.
**Demo/checkpoint:** corridor/intersection stress test showing deadlock avoidance or detection.

## Step 60 — Command execution from the serious UI
**Type:** UI-product / operations
**Goal:** Promote the command-center from read model to real operator tool within the frontend.
**Why now:** The UI should now be ready to do real command work on a richer, more believable world.
**Dependencies:** Steps 42–45 and 55–59.
**Likely touches:** frontend command center, backend command transport, live session update loop.
**Must not change yet:** job injection semantics beyond current command set unless required.
**Do not pre-implement:** batch fleet workflows beyond small baseline support.
**Deliverables:** assign destination, block/unblock road, reposition vehicle, pause/play/single-step live session from UI.
**Acceptance criteria:** core operator commands work entirely through the serious UI; command results and errors remain grounded in authoritative backend state.
**Demo/checkpoint:** live operator walkthrough from frontend only, no Python script needed.

## Step 61 — Route previews, reservation inspection, and conflict overlays
**Type:** UI-product / operations
**Goal:** Deepen pre-commit previews and conflict inspection so the operator can understand consequences before acting.
**Why now:** Once commands can be sent from the UI, the next UX priority is confidence and explainability.
**Dependencies:** Step 60.
**Likely touches:** command center surfaces, route preview model, reservation/conflict overlays, inspector panels.
**Must not change yet:** AI copilot decision-making depth.
**Do not pre-implement:** full route editor.
**Deliverables:** route preview before commit, reservation/conflict inspection panels, selected path overlays, queue overlays bound to selected commands/vehicles.
**Acceptance criteria:** operator can inspect likely effects before applying a destination or closure command.
**Demo/checkpoint:** preview a reroute, inspect conflicts, then commit it.

## Step 62 — Fleet operations UX baseline
**Type:** UI-product / operations
**Goal:** Add multi-select, batch actions, and fleet-scoped workflows.
**Why now:** Single-vehicle control is not enough for mining and yard operations.
**Dependencies:** Steps 60–61.
**Likely touches:** selection state, command center UI, live session command batching.
**Must not change yet:** learned policy/AI fleet control.
**Do not pre-implement:** fully autonomous fleet manager.
**Deliverables:** multi-select, fleet-wide destination/resource actions where sensible, bulk road operation workflows.
**Acceptance criteria:** operator can issue bounded batch actions without inconsistent state.
**Demo/checkpoint:** select multiple vehicles and perform a fleet action in a live scenario.

## Step 63 — Live scenario mutation: spawn/remove/inject jobs
**Type:** operations / UI-product
**Goal:** Allow the operator to mutate the running scenario in more meaningful ways.
**Why now:** Real operations require adding work, vehicles, and constraints mid-run.
**Dependencies:** Steps 60–62.
**Likely touches:** live session and command transport, scenario mutation surfaces, frontend command center UI.
**Must not change yet:** free-form geometry mutation beyond validated scope.
**Do not pre-implement:** full scenario editor inside the same workflow unless needed.
**Deliverables:** spawn vehicle, remove vehicle, inject job/task, temporary hazard/closure mutation.
**Acceptance criteria:** live session remains stable after scenario mutations; mutations appear in trace/inspection surfaces clearly.
**Demo/checkpoint:** add extra rock-haul work mid-run and redirect the nearest truck.

## Step 64 — Task/resource realism expansion
**Type:** realism / operations
**Goal:** Deepen operational semantics for loading, unloading, depots, bays, staging areas, and resource bottlenecks.
**Why now:** Movement realism is stronger now; operational realism should catch up.
**Dependencies:** Steps 47–63.
**Likely touches:** tasks/jobs/resources models, scenario schema, inspection and command-center summaries.
**Must not change yet:** vehicle health warnings, weather systems.
**Do not pre-implement:** every industry-specific task family.
**Deliverables:** richer load/unload/staging semantics, yard/depot/loading-bay occupancy rules, stronger resource contention visualization.
**Acceptance criteria:** mining and construction workflows feel operationally meaningful, not just navigational.
**Demo/checkpoint:** mining scenario with visible loading bay and crusher bottlenecks.

## Step 65 — Vehicle diagnostics and warning surfaces
**Type:** realism / operations / AI-supporting
**Goal:** Add believable non-failure diagnostics and operator-visible warnings.
**Why now:** Warnings enrich inspection and AI explanation without requiring full breakdown simulation yet.
**Dependencies:** Step 64.
**Likely touches:** vehicle inspection surfaces, command center surfaces, AI-assist inputs, frontend inspector UI.
**Must not change yet:** full maintenance subsystem, stochastic breakdown engine.
**Do not pre-implement:** full repair workflows.
**Deliverables:** warning codes/severity model, example warnings like low tire pressure and overheating, diagnostic surfacing in UI.
**Acceptance criteria:** warnings are deterministic, grounded, and visible in inspection/alerts.
**Demo/checkpoint:** selected vehicle displays realistic warnings in the inspector.

## Step 66 — Weather and hazard baseline
**Type:** realism
**Goal:** Introduce weather/hazard layers that materially affect routing, traffic, and operations.
**Why now:** The flagship vision explicitly includes hazards and weather challenges.
**Dependencies:** Steps 47–65.
**Likely touches:** world model, routing modifiers, traffic and command-center surfaces, frontend overlays.
**Must not change yet:** full atmospheric/sensor simulation.
**Do not pre-implement:** full day/night rendering system beyond hooks if not required.
**Deliverables:** hazard zone model, weather state model, slowdown / closure / caution behaviors tied to these layers.
**Acceptance criteria:** hazards and weather change vehicle behavior and operator decisions; the UI surfaces why vehicles are slowing or rerouting.
**Demo/checkpoint:** mining hazard scenario with visible detour and slower travel behavior.

## Step 67 — Imported-map adapter groundwork
**Type:** foundation / extensibility
**Goal:** Prepare the project for future imported maps/external formats without derailing current authoring flow.
**Why now:** World, lane, and traffic models are now mature enough to define adapter boundaries.
**Dependencies:** Steps 47–66.
**Likely touches:** import adapter interfaces, world/lane schema mapping docs, scenario tooling.
**Must not change yet:** core internal world model.
**Do not pre-implement:** full OpenDRIVE/OpenSCENARIO coverage in one step.
**Deliverables:** importer adapter interface, one constrained prototype importer path, schema-mapping documentation.
**Acceptance criteria:** imported map support has a clear seam and one proof-of-concept path.
**Demo/checkpoint:** prototype imported geometry appears correctly inside the internal scene model.

## Step 68 — Editor and import convergence pass
**Type:** foundation / UI-product
**Goal:** Make sure authored scenes and imported scenes converge into the same editable internal representation.
**Why now:** Future content growth depends on not splitting the world into incompatible authoring paths.
**Dependencies:** Steps 49–50, 67.
**Likely touches:** editor model, import pipeline, save/export pipeline.
**Must not change yet:** external standard coverage breadth.
**Do not pre-implement:** full marketplace/content library concepts.
**Deliverables:** unified editable internal scene representation, import → edit → save loop.
**Acceptance criteria:** imported scenes can be edited with the same tooling as hand-authored scenes.
**Demo/checkpoint:** import a prototype scene, edit it live, save it, rerun it.

## Step 69 — AI explanation refinement
**Type:** AI/research / UI-product
**Goal:** Upgrade AI-style explanations so they clearly explain current motion, waiting, rerouting, and congestion in grounded terms.
**Why now:** AI is worth deepening only after motion, traffic, inspection, and hazards are rich enough to explain.
**Dependencies:** Steps 52–66.
**Likely touches:** command_center AI-assist surfaces, explanation generation logic, frontend assistant UI.
**Must not change yet:** autonomous high-level planner control loop.
**Do not pre-implement:** unconstrained LLM-generated simulator state.
**Deliverables:** richer explanation surfaces, rationale-code taxonomy, UI assistant panel improvements.
**Acceptance criteria:** AI explanations reference real simulator state and are inspectably grounded.
**Demo/checkpoint:** click a waiting vehicle and get a useful, grounded explanation of why it is waiting.

## Step 70 — AI suggestions and anomaly detection refinement
**Type:** AI/research / operations
**Goal:** Make AI suggestions materially useful for operations.
**Why now:** Explanations should mature before suggestions become more aggressive.
**Dependencies:** Step 69.
**Likely touches:** AI-assist surfaces, anomaly rules, command-center recommendation UI.
**Must not change yet:** learned dispatch policy as default authority.
**Do not pre-implement:** autonomous command execution without operator approval.
**Deliverables:** reroute/reopen/dispatch suggestions, anomaly types for congestion, underutilization, deadlock risk, warnings.
**Acceptance criteria:** suggestions are concrete, bounded, and tied to proposed operator actions.
**Demo/checkpoint:** AI panel surfaces a useful reroute or reopen recommendation during a live run.

## Step 71 — AI route/dispatch policy sandbox
**Type:** AI/research
**Goal:** Create a controlled sandbox for pluggable routing/dispatch policies.
**Why now:** The sim now has enough operational richness for policy experiments to be meaningful.
**Dependencies:** Steps 62–70.
**Likely touches:** dispatcher/policy interfaces, evaluation harness, scenario execution plumbing.
**Must not change yet:** simulator authority model, deterministic baseline policies.
**Do not pre-implement:** full learned fleet control as production default.
**Deliverables:** pluggable policy interface, baseline heuristic vs. experimental policy comparison support.
**Acceptance criteria:** policies can be swapped without breaking simulator truth surfaces.
**Demo/checkpoint:** compare baseline policy vs. one experimental policy on a mining scenario.

## Step 72 — Scenario generation and stress-case tooling
**Type:** AI/research / extensibility
**Goal:** Support AI-assisted or procedural generation of structured stress scenarios.
**Why now:** Policy and realism work need better scenario coverage than hand-authored cases alone.
**Dependencies:** Steps 47–71.
**Likely touches:** scenario tooling, research harness, generation/evaluation pipeline.
**Must not change yet:** main showcase scenarios as stable regression assets.
**Do not pre-implement:** open-ended content generation without validation constraints.
**Deliverables:** stress-case generation hooks, generator constraints for mining/yard/street, reproducible generated scenario IDs/seeds.
**Acceptance criteria:** generated scenarios are valid, reproducible, and evaluable.
**Demo/checkpoint:** generate a congestion-heavy mining stress scenario and run it through the benchmark/eval loop.

## Step 73 — Multi-agent experimentation layer
**Type:** AI/research
**Goal:** Add structured support for multi-agent experimentation over dispatch, coordination, or route behaviors.
**Why now:** This is the natural extension of policy sandboxing once stress-case generation exists.
**Dependencies:** Steps 71–72.
**Likely touches:** experiment orchestration, evaluation surfaces, scenario/policy harnesses.
**Must not change yet:** default operational simulator behavior for showcase paths.
**Do not pre-implement:** giant generic research platform abstractions.
**Deliverables:** experiment definition surface, comparison tooling for multiple agent/policy variants.
**Acceptance criteria:** experiment runs are comparable and repeatable.
**Demo/checkpoint:** run multiple policy variants on one fixed scenario pack and compare outcomes.

## Step 74 — Performance and scaling checkpoint 1
**Type:** performance/scaling
**Goal:** Profile the richer frontend + traffic + motion stack and identify the next true bottlenecks.
**Why now:** More realism and interactivity will likely shift hotspot locations.
**Dependencies:** Steps 41–73.
**Likely touches:** perf harness, frontend perf instrumentation, benchmark scenarios.
**Must not change yet:** architecture split.
**Do not pre-implement:** speculative native rewrites without data.
**Deliverables:** updated benchmark cases, frontend performance metrics, hotspot report.
**Acceptance criteria:** top 3–5 bottlenecks are identified with measurement, not guesswork.
**Demo/checkpoint:** performance report on dense mining and city scenes.

## Step 75 — Native acceleration phase 2 only where justified
**Type:** performance/scaling
**Goal:** Add narrow native acceleration only for newly proven hotspots.
**Why now:** This follows the benchmark-justified pattern already established by Step 40.
**Dependencies:** Step 74.
**Likely touches:** hotspot modules only, perf harness, parity tests.
**Must not change yet:** broad Python-first architecture.
**Do not pre-implement:** sweeping mixed-runtime rewrite.
**Deliverables:** one or more narrow accelerated paths with parity coverage.
**Acceptance criteria:** measurable speedup on targeted cases; deterministic parity with fallback implementation.
**Demo/checkpoint:** benchmark comparison before and after new acceleration path.

## Step 76 — Mining flagship showpiece v2
**Type:** realism / UI-product / showcase
**Goal:** Rebuild the mining flagship demo using the richer world, motion, traffic, operations, and AI surfaces.
**Why now:** The mining environment should now prove the full thesis of the simulator.
**Dependencies:** Steps 41–75.
**Likely touches:** mining scenarios, showcase flow, frontend presets, asset/layout tuning.
**Must not change yet:** construction and city showpieces beyond what is needed to keep extensibility.
**Do not pre-implement:** broad content explosion across many environments.
**Deliverables:** upgraded mining scenario pack, upgraded replay/live/live-sync showcase artifacts, stronger route/queue/hazard/operator flows.
**Acceptance criteria:** mining demo visibly shows congestion, hazards, live control, inspection, and AI assist.
**Demo/checkpoint:** flagship mining demo suitable for external demonstration.

## Step 77 — Construction-yard showpiece
**Type:** realism / showcase
**Goal:** Prove the architecture expands beyond mining with a believable construction-yard demo.
**Why now:** The project must not become overfit to one environment.
**Dependencies:** Steps 47–76.
**Likely touches:** environment assets, scenarios, resource/task semantics.
**Must not change yet:** city-specific traffic complexity if not required.
**Do not pre-implement:** all niche yard equipment families.
**Deliverables:** construction-yard environment, jobs, and showcase scenario(s).
**Acceptance criteria:** construction-yard flow feels distinct from mining while using the same core architecture.
**Demo/checkpoint:** construction-yard live or replay showpiece.

## Step 78 — City-street showpiece
**Type:** realism / showcase
**Goal:** Prove that the same system can support a more traffic-centric city environment.
**Why now:** This is the strongest test of the lane/traffic/queue/merge stack.
**Dependencies:** Steps 47–77.
**Likely touches:** city scenes, lane/traffic tuning, signal/control presets.
**Must not change yet:** physics/sensor simulator ambitions.
**Do not pre-implement:** full urban-driving autonomy stack.
**Deliverables:** city-street environment and showcase scenario(s).
**Acceptance criteria:** city scene demonstrates lane behavior, control logic, and urban-style congestion clearly.
**Demo/checkpoint:** city-street replay/live showcase with readable traffic behavior.

## Step 79 — Visual polish pass 2
**Type:** UI-product / realism
**Goal:** Do a second major art/UX pass once the core simulation behaviors are richer.
**Why now:** Late polish is now worth it because the simulator content is strong enough to justify a more refined presentation.
**Dependencies:** Steps 76–78.
**Likely touches:** frontend design system, scene styling, animation details, inspector/command-center polish.
**Must not change yet:** core traffic semantics.
**Do not pre-implement:** audio and day/night as required features unless ready.
**Deliverables:** improved overlays, iconography, transitions, minimap polish, inspector polish.
**Acceptance criteria:** UI feels cohesive and intentionally designed across all flagship scenes.
**Demo/checkpoint:** before/after polished walkthrough across mining, yard, and city scenes.

## Step 80 — Day/night, weather visual, and audio hooks
**Type:** realism / UI-product
**Goal:** Add optional hooks for day/night presentation, weather visuals, and sound integration without making them structural blockers.
**Why now:** These features matter for atmosphere, but they are lower priority than core realism and operations.
**Dependencies:** Steps 66, 79.
**Likely touches:** frontend rendering and theme systems, optional environment presentation hooks.
**Must not change yet:** simulator authority boundaries.
**Do not pre-implement:** full game-like audio stack.
**Deliverables:** day/night hooks, weather presentation hooks, audio event hook points.
**Acceptance criteria:** optional presentation layers can be added without corrupting simulator truth or UX clarity.
**Demo/checkpoint:** one showcase scene rendered in alternate presentation modes.

## Step 81 — Performance and scaling checkpoint 2
**Type:** performance/scaling
**Goal:** Re-evaluate large-scene and multi-fleet performance after the showpieces and extra polish features.
**Why now:** The final major complexity increase has landed; this is the right time to measure whole-system behavior.
**Dependencies:** Steps 76–80.
**Likely touches:** benchmark suite, showcase scenarios, frontend perf instrumentation.
**Must not change yet:** feature scope.
**Do not pre-implement:** arbitrary micro-optimizations without evidence.
**Deliverables:** updated scaling benchmarks, frame/render/update metrics, large-scene operational guidance.
**Acceptance criteria:** performance targets and remaining bottlenecks are clearly documented.
**Demo/checkpoint:** performance report comparing dense mining/yard/city scenarios.

## Step 82 — Post-Step-82 planning checkpoint
**Type:** planning / consolidation
**Goal:** Consolidate lessons from the full realism/front-end phase and prepare the next execution-plan tranche.
**Why now:** The project should not drift into unchecked complexity after this major build-out.
**Dependencies:** Steps 41–81.
**Likely touches:** planning docs, README/docs updates, acceptance/review notes.
**Must not change yet:** stable showcase assets except for final documentation updates.
**Do not pre-implement:** new major feature families without a new plan.
**Deliverables:** updated project status summary, new gap analysis, next-phase recommendations.
**Acceptance criteria:** remaining gaps are explicit; priorities are re-ranked based on the now-built system.
**Demo/checkpoint:** project review document and updated roadmap proposal.

---

# Capability coverage check

## Environments
**Covered by:** Steps 47, 48, 76, 77, 78  
**Status:** fully covered in this phase

## Vehicle realism
**Covered by:** Steps 52, 53, 54, 55, 65  
**Status:** fully covered at baseline-to-strong level

## Traffic realism
**Covered by:** Steps 51, 55, 56, 57, 58, 59, 78  
**Status:** fully covered at baseline-to-strong level

## Map/world realism
**Covered by:** Steps 47, 48, 49, 50, 51, 66, 67, 68  
**Status:** fully covered with future import extensibility

## Live interactivity
**Covered by:** Steps 42, 43, 44, 45, 60, 61, 62, 63  
**Status:** fully covered

## Inspection / command center
**Covered by:** Steps 43, 45, 60, 61, 62, 65, 69, 70  
**Status:** fully covered

## AI features
**Covered by:** Steps 69, 70, 71, 72, 73  
**Status:** fully covered at the requested near/mid-term level

## Performance/scaling
**Covered by:** Steps 74, 75, 81  
**Status:** fully covered with benchmark-gated native work

## Research/experimentation
**Covered by:** Steps 71, 72, 73, 82  
**Status:** fully covered

---

# Top 5 false peaks to avoid

1. Over-investing in new backend/API read models before the frontend and realism materially improve.
2. Trying to solve all traffic realism in one huge abstract step instead of layering lanes, spacing, queues, controls, merges, and deadlock handling separately.
3. Letting the current serious viewer HTML path silently become the permanent frontend architecture.
4. Adding AI features before there is enough simulator truth for them to explain or act on meaningfully.
5. Jumping into broad native/C rewrites without benchmark evidence and parity guarantees.

---

# What to lock now

- Python simulator remains authoritative.
- Frontend can become a separate app and should optimize for UI quality.
- Simulation API remains the cross-boundary contract.
- Mining remains the flagship acceptance environment.
- Lane/world data models should be designed for mining + construction yard + city street together.
- AI stays grounded in deterministic simulator truth.
- Native acceleration stays narrow and benchmark-gated.

---

# What to defer until later

- full physics-engine integration
- sensor simulation
- OpenSCENARIO/OpenDRIVE-grade interoperability breadth
- full maintenance/repair ecosystem
- broad learned behavior as default operational authority
- full soundscape and high-end environmental presentation as hard requirements
