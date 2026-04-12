
# `docs/architecture_v2.md`

# Autonomous Operations Sim — Architecture v2

## Purpose

This document defines the target architecture for the next major phase of Autonomous Operations Sim.

It exists to make subsystem ownership explicit, preserve deterministic simulator authority, and prevent the codebase from drifting into shadow-truth frontend logic, backend sprawl, or environment-specific hacks.

This is not a step plan.
It is the intended steady-state architecture the step plan should move toward.

## Core architectural thesis

The system should be organized around one authoritative execution core and several derived consumer layers.

The authoritative path is:

**scenario / world model → simulator runtime → commands / session progression → runtime state / trace / metrics → derived bundle surfaces → frontend / replay / AI / analysis consumers**

The core rule is simple:

**The simulator owns truth. Everything else consumes, explains, edits through explicit contracts, or presents that truth.**

That rule is already locked at the repo level and must remain intact.  

---

## 1. Top-level subsystem model

Architecture v2 has six primary subsystems:

1. **World and Scenario Model**
2. **Simulator Runtime Core**
3. **Command and Live Session Layer**
4. **Derived Surface Layer**
5. **Serious Frontend**
6. **Authoring / Research / Benchmark Extensions**

These are described below.

---

## 2. World and Scenario Model

## 2.1 Purpose

This subsystem defines the static world.

It should represent:

* environment family and archetype
* topology
* roads/intersections/lanes/connectors
* areas, zones, structures, terrain-like forms
* scenario configuration
* initial actors/resources/tasks
* environment semantics for mining, yard, and city scenes

It should also define one shared world-form taxonomy so roads, lanes, intersections, zones, structures, terrain forms, and anchors mean the same thing across mine, yard, and city.

## 2.2 Owns

* scenario schema
* static map/world schema
* reusable world assets/archetypes
* import-normalized internal world representation

## 2.3 Must not own

* per-run closures
* reservations
* live queue state
* transient runtime conflict state
* live vehicle progress
* frontend selection/view state

That separation is already a core repo rule: static topology must remain separate from runtime state. 

## 2.4 Key design requirement

The world model must be unified across:

* mine depot
* construction yard
* city street

It must not fork into separate environment-specific architectures. The execution plan explicitly requires one expandable model that fits all three families cleanly. 

---

## 3. Simulator Runtime Core

## 3.1 Purpose

This is the authoritative engine.

It executes the world over time and owns the actual operational truth.

## 3.2 Owns

* runtime world state
* vehicle state
* job/task execution
* routing truth
* motion truth
* traffic/conflict/reservation truth
* queue/congestion state
* hazard/weather effects on behavior
* deterministic progression
* runtime metrics and trace inputs

## 3.3 Must not own

* frontend-only presentation state
* panel/UI workflow state
* local client interaction state
* speculative AI conclusions not grounded in runtime truth

## 3.4 Key design requirement

The runtime must remain deterministic for:

* scenario
* seed
* command sequence
* live session progression 

## 3.5 Internal conceptual modules

Architecture v2 should expect the runtime to have conceptually distinct modules for:

* world instantiation
* vehicle state progression
* motion / kinematics
* routing / dispatch baseline
* traffic / coordination / reservation handling
* tasks / jobs / resources
* hazards / weather effects
* metrics / trace generation

These modules do not need to live in separate packages immediately, but the responsibilities should stay explicit.

---

## 4. Command and Live Session Layer

## 4.1 Purpose

This layer is the only valid mutation path from operator-facing systems into runtime behavior.

It translates explicit actions into validated, deterministic simulator changes.

## 4.2 Owns

* typed command definitions
* command validation
* deterministic command ordering
* live session progression controls
* command application results
* session state
* replayable command history

## 4.3 Must not own

* direct frontend mutation of runtime internals
* hidden mutation paths bypassing command semantics
* UI-owned route or vehicle truth

This matches the repo-wide rule that commands and interactions must remain explicit. 

## 4.4 Required command families

Architecture v2 should accommodate at least:

* assign destination
* route preview request
* reposition vehicle
* block/unblock road
* declare/clear hazard
* pause/play/step session
* spawn/remove vehicle
* inject job/task
* editor mutation commands or validated edit transactions

## 4.5 Live session contract

A live session should be able to:

* launch
* connect/reconnect
* play
* pause
* step
* publish stable derived bundle updates
* remain replayable and inspectable

---

## 5. Derived Surface Layer

## 5.1 Purpose

This layer converts authoritative runtime state into stable consumer-facing surfaces.

It exists so consumers do not need to know internal engine details.

This is also the boundary where render-ready geometry is derived from world-model-v2 semantics. The world model owns the static meaning of the scene; derived surfaces own the presentation-ready shape of that scene; frontend adapters only translate those derived surfaces into UI state.

The derived surface contract should preserve the shared taxonomy, not collapse it into generic miscellaneous geometry.

The static world surface should expose a stable feature inventory and semantic feature groups so later rendering and inspection can consume the same world truth without reinterpretation.

The render geometry contract should also expose a layer manifest that names the semantic and projection layers explicitly, so map consumers can reason about organization without re-inferring meaning from raw polygons.

Scene bounds and framing inputs should likewise be derived from the shared world/render surfaces, including world-form context such as boundaries, terrain, structures, and asset coverage when those exist. Frontend consumers may fit or focus using those derived bounds, but they should not invent their own extents from a thin subset of geometry.

## 5.2 Owns

* replay/export surfaces
* live bundle surfaces
* inspection read models
* command-center read models
* traffic overlays/read models
* AI-assist input surfaces
* structured derived summaries for frontend/replay/analysis

## 5.3 Must not own

* competing runtime truth
* independent routing truth
* independent vehicle progression logic
* UI-originated state masquerading as runtime fact

The execution plan explicitly locks derived frontend and AI surfaces to simulator truth rather than allowing them to become competing authority layers. 

## 5.4 Design requirement

Surface growth must stay controlled.
The repo-wide guidance already warns against catch-all data containers and backend/read-model expansion that does not materially improve visual quality, realism, operator workflow, extensibility, or measured performance.  

---

## 6. Serious Frontend

## 6.1 Purpose

The frontend is the primary operator-facing product surface.

Its job is to:

* render the world clearly
* support live operator workflows
* expose selection/inspection/preview/command UX
* present derived truth beautifully and usefully

## 6.2 Owns

* rendering
* camera/viewport
* scene mode
* selection/highlight state
* popup/inspector state
* route-planning workflow state
* panel/tab layout
* local form/draft workflow state
* minimap and visual layer controls
* product-level interaction design

## 6.3 Must not own

* runtime vehicle truth
* command truth after submission
* authoritative route truth
* conflict/reservation truth
* topology mutation semantics outside validated authoring flow

## 6.4 Architectural implication

The frontend may and likely should be a separate serious app path.
That is already an explicit locked decision: a stronger separate frontend is allowed and preferred when it materially improves UI quality. 

## 6.5 Frontend boundary contract

The frontend should consume:

* live bundle surfaces
* replay/export surfaces
* command/session endpoints
* authoring/edit validation endpoints when editing is enabled

The frontend should emit:

* typed command requests
* edit transactions / editor actions through validated backend surfaces
* no direct runtime mutation

---

## 7. Authoring Layer

## 7.1 Purpose

This layer supports scenario and geometry editing without collapsing the separation between static world assets and runtime truth.

## 7.2 Owns

* edit transaction model
* deterministic validation rules
* save/reload workflow
* import-to-edit convergence
* persistent scenario mutation logic

## 7.3 Must not own

* direct bypasses into runtime state
* unvalidated geometry mutation
* inconsistent authored/imported scene representations

## 7.4 Design requirement

Imported scenes and hand-authored scenes must converge into one editable internal representation.
The execution plan explicitly calls this out as a needed later convergence point. 

---

## 8. Research and Benchmark Layer

## 8.1 Purpose

This layer enables policy experiments, generated stress cases, evaluation, and measured optimization without destabilizing the main product architecture.

## 8.2 Owns

* policy sandbox interfaces
* experiment definitions
* reproducible scenario generation hooks
* benchmark suites
* performance instrumentation
* comparative evaluation workflows

## 8.3 Must not own

* production operational authority
* hidden simulator mutations
* frontend-owned or AI-owned runtime truth

## 8.4 Design requirement

Native or mixed-language acceleration belongs here only when benchmark evidence proves a real hotspot and parity is preserved. That is already explicitly locked.  

---

## 9. Cross-subsystem data flow

## 9.1 Static flow

Scenario / imported world
→ normalized internal world model
→ simulator instantiation

## 9.2 Runtime flow

Simulator runtime
→ runtime state updates
→ trace / metrics / inspection state
→ derived bundles

## 9.3 Operator flow

Frontend selection / preview / form state
→ typed command request
→ command validation/application
→ updated runtime truth
→ updated derived bundles
→ frontend refresh

## 9.4 Authoring flow

Frontend editor gesture
→ edit transaction
→ deterministic validation
→ updated persistent scene
→ rerun / reload
→ new runtime instantiation

## 9.5 Research flow

Scenario + seed + policy configuration
→ simulator execution
→ metrics / trace / comparison output

---

## 10. Source of truth matrix

### Static world truth

Owner: **World and Scenario Model**

### Runtime vehicle truth

Owner: **Simulator Runtime Core**

### Route truth

Owner: **Simulator Runtime Core**
Preview request/visualization may be frontend-driven, but route truth after validation remains simulator-owned.

### Command truth

Owner: **Command and Live Session Layer**

### Inspection truth

Owner: **Derived Surface Layer**, derived from simulator/runtime truth

### Frontend interaction state

Owner: **Serious Frontend**

### Editor transaction state

Owner: **Authoring Layer** until validated/applied

### Experiment/policy comparison state

Owner: **Research and Benchmark Layer**

This matrix should be used whenever there is ambiguity.

---

## 11. Environment architecture rule

Architecture v2 must not use:

* separate mine renderer
* separate city renderer
* separate yard renderer
  as primary truth-bearing architectures.

Instead, it should use:

* one internal world model
* one runtime engine family
* one frontend rendering architecture
* environment-specific semantics and archetypes layered through data, not forks

Mining remains the flagship demo and richest acceptance path, but the architecture must not become mining-only. 

---

## 12. Frontend architecture rule

The serious frontend should be structured as a consumer app, not a mega-component pile that mixes:

* runtime truth
* rendering
* editor semantics
* command semantics
* map logic
* planning logic
* panel orchestration

Architecture v2 should aim for a frontend with distinct layers such as:

* app shell
* map shell
* map canvas/renderer
* popup/inspector
* planning/command center
* editor surfaces
* traffic/fleet/analysis panels
* frontend view-model adapters

Exact file layout can evolve, but the ownership split should stay explicit.

---

## 13. Contract boundaries that must remain sharp

## 13.1 Simulator ↔ frontend

Crossing is via:

* derived bundles
* typed commands
* validated editor surfaces

Not via:

* direct UI mutation of runtime objects

## 13.2 Static world ↔ runtime world

Crossing is via:

* world instantiation
* validated persistent edits

Not via:

* mutating static topology to represent temporary runtime conditions

## 13.3 AI ↔ runtime truth

Crossing is via:

* derived read models
* trace
* structured runtime summaries

Not via:

* unconstrained invented state

## 13.4 Native acceleration ↔ Python authority

Crossing is via:

* bounded, parity-tested hotspots

Not via:

* broad speculative subsystem migration

---

## 14. Preferred implementation style

Architecture v2 should grow through:

* additive refactoring
* narrow subsystem seams
* stable interface boundaries
* bounded replacement when justified

Not through:

* giant speculative rewrites
* frontend-convenience mutations to simulator authority
* broad native or mixed-language splits without measurement

This is directly aligned with the repo-wide preference for additive refactoring over rewrites. 

---

## 15. Architectural anti-patterns to reject

Reject changes that move toward any of these:

### 15.1 Frontend shadow truth

The UI invents route state, vehicle state, or traffic truth that diverges from simulator truth.

### 15.2 Read-model sprawl

New derived surfaces are added because they are convenient, not because they materially improve product quality, realism, or operator usefulness.

### 15.3 Environment forks

Mine, yard, and city each begin to accumulate their own architecture instead of sharing one world/runtime/rendering foundation.

### 15.4 Presentation-first fake realism

The frontend adds purely visual realism that contradicts or obscures simulator truth.

### 15.5 Premature performance bifurcation

The codebase splits into broad multi-language complexity before real benchmark evidence demands it.

The master plan explicitly warns against these false peaks. 

---

## 16. What architecture v2 should make easier

If this architecture is working, it should become easier to add:

* stronger frontend product quality
* better map/world realism
* lane-level traffic logic
* richer motion realism
* operator commands from the serious UI
* live scenario mutation
* resource realism
* hazard/weather effects
* grounded AI explanations and suggestions
* policy experiments
* imported map adapters
* benchmark-driven optimization

Those are the capability families the roadmap is explicitly trying to unlock. 

---

## 17. Architecture review checklist

When evaluating a proposed change, ask:

### Truth ownership

* Does this preserve Python simulator authority?
* Does this create any shadow truth?

### Boundary clarity

* Is ownership obvious?
* Is a subsystem doing someone else’s job?

### Determinism

* Does this preserve replayable, stable behavior?

### Environment extensibility

* Does this work for mining, yard, and city?
* Or is it secretly environment-specific?

### Product quality

* Does this improve operator usefulness or realism?
* Or is it backend churn with little visible payoff?

### Performance discipline

* Is this optimization benchmark-justified?
* Is parity preserved?

---

## Final statement

Architecture v2 is a layered system with:

* **one authoritative Python simulator**
* **one explicit command/session mutation path**
* **one derived surface layer for replay/live/inspection/UI consumption**
* **one serious frontend optimized for operator experience**
* **one converged authoring path**
* **one research/performance extension layer that does not compromise core truth ownership**

If that ownership model stays clear, the project can grow in realism, UX quality, and scope without collapsing into ambiguity.

---
