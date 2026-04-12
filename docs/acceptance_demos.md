
---

# `docs/acceptance_demos.md`

# Autonomous Operations Sim — Acceptance Demos

## Purpose

This document defines the concrete demo scenarios that should prove Autonomous Operations Sim is succeeding.

It is not enough for the codebase to contain good architecture, good modules, or partial realism in isolation.
The system should be able to demonstrate its value through end-to-end scenarios that are:

* visually convincing
* operationally meaningful
* inspectable
* interactive
* grounded in authoritative simulator truth

This document defines those proof scenarios.

The execution plan already locks in three major showcase directions:

* **mining** as the flagship acceptance environment
* **construction yard** as the first proof of extensibility beyond mining
* **city street** as the strongest test of lane/traffic realism 

---

## 1. Role of acceptance demos

Acceptance demos serve five purposes.

### 1.1 Prove the architecture

A demo should prove that the system architecture actually supports the intended product, not just that the code compiles.

### 1.2 Prove the product

A demo should show that the frontend, simulator, and workflows come together into something usable and coherent.

### 1.3 Prove realism

A demo should show believable:

* world behavior
* vehicle behavior
* traffic behavior
* operational behavior

### 1.4 Prove operator usefulness

A demo should show an operator can:

* inspect
* preview
* command
* mutate
* understand

### 1.5 Prove extensibility

A demo should show the system is not trapped inside one environment family.

---

## 2. Acceptance demo philosophy

Each acceptance demo should be judged as a **product/system proof**, not a feature checklist.

A good acceptance demo should feel like:

* a convincing operational scene
* with believable vehicle behavior
* inside a readable world
* with meaningful operator intervention
* and trustworthy system feedback

A bad acceptance demo is one that technically uses many subsystems but still feels:

* confusing
* flat
* fake
* debug-heavy
* non-interactive
* environment-specific in a brittle way

---

## 3. Demo tiers

The project should eventually support three tiers of demos.

## 3.1 Tier 1 — Core acceptance demo

This is the main flagship proof that the project works at a serious level.

Current target:

* **Mining Flagship Demo**

## 3.2 Tier 2 — Extensibility demos

These prove the architecture expands beyond the flagship domain.

Targets:

* **Construction Yard Demo**
* **City Street Demo**

## 3.3 Tier 3 — Stress and research demos

These prove:

* system robustness
* policy experimentation
* scaling
* anomaly/hazard/deadlock handling

These are important, but they are not the first proof that the product is good.

---

## 4. Global acceptance standards for all demos

Every acceptance demo should satisfy these baseline standards.

## 4.1 Visual standard

The demo must look intentionally designed, not prototype-grade.

That means:

* readable scene
* readable vehicles
* coherent overlays
* calm default map
* map-first presentation
* minimal debug clutter

## 4.2 Operational standard

The scene must contain real operational meaning, not just movement.

That means:

* vehicles have tasks or meaningful destinations
* infrastructure matters
* congestion or bottlenecks can occur
* commands can change outcomes

## 4.3 Interaction standard

The operator must be able to:

* inspect vehicles and infrastructure
* preview a meaningful action
* commit a command
* understand what changed

## 4.4 Truth standard

Everything shown must remain grounded in simulator truth and derived surfaces, not frontend invention.

## 4.5 Presentation standard

The demo should be strong enough to show another person and have it communicate what the product is trying to become.

---

## 5. Demo A — Mining Flagship Demo

## 5.1 Purpose

This is the primary acceptance demo for the whole project.

Mining remains the flagship environment in the execution plan, and this demo is the main proof that the simulator, frontend, realism stack, and operator workflows are all coming together 

## 5.2 What this demo must prove

The mining flagship must prove:

* the world model supports a rich operational environment
* the serious frontend can present that environment convincingly
* multiple vehicles can move believably
* queues and congestion can emerge
* hazards and bottlenecks matter
* operator commands matter
* inspection and explanation are useful
* the product is not just a route animation

## 5.3 Recommended scenario content

The mining flagship should include:

* haul roads
* loading area(s)
* unloading/crusher area(s)
* staging/holding area(s)
* at least one meaningful bottleneck
* at least one constrained corridor or merge/conflict area
* multiple active vehicles
* a non-trivial work pattern

Optional but desirable:

* weather/hazard effect
* dynamic reroute event
* resource occupancy bottleneck

## 5.4 Required behaviors

This demo should show:

* multiple vehicles moving
* spacing/following behavior
* queue buildup and release
* route assignment or rerouting
* operator inspection of a vehicle
* operator preview of a command
* operator commit of a command
* visible effect after command
* at least one explainable delay or wait reason

## 5.5 Required operator walkthrough

A convincing mining demo walkthrough should allow this sequence:

1. open live mining scenario
2. orient to the map quickly
3. click a moving haul truck
4. inspect its current state, route, and task context
5. identify a bottleneck or blocked route
6. preview a reroute or closure response
7. commit the command
8. observe changed behavior in the scene
9. inspect a waiting or delayed truck and understand why

## 5.6 Mining-specific acceptance criteria

The mining flagship passes when:

* the scene feels operationally meaningful, not just navigational
* loading/unloading/staging or bottleneck semantics matter
* multiple trucks do not visually cheat through each other
* queueing is visible and explainable
* operator intervention visibly changes the run
* the demo is strong enough to be shown externally as the flagship story

## 5.7 Mining failure modes

The mining flagship does **not** pass if:

* vehicles just drift around with little operational meaning
* the frontend still feels like a debug viewer
* bottlenecks are invisible or meaningless
* commands technically work but feel disconnected from the map
* the scene looks flat, cluttered, or confusing
* explanations are too weak to justify delays

---

## 6. Demo B — Construction Yard Demo

## 6.1 Purpose

This demo proves the architecture is not mining-only.

It should demonstrate that the same world model, frontend, and operational patterns can support a distinct environment with different spatial and task characteristics.

## 6.2 What this demo must prove

The construction-yard demo must prove:

* the shared architecture generalizes
* environment semantics are not overfit to mining
* yard operations feel distinct from haul-road operations
* the same frontend/product model still works

## 6.3 Recommended scenario content

The yard demo should include:

* tighter movement spaces than mining
* staging or work areas
* loading/unloading or drop zones
* support for smaller or different vehicle types
* visible resource contention or yard organization logic

Possible content:

* forklifts
* service trucks
* material staging zones
* dropoff/pickup zones
* tighter intersections/corridors

## 6.4 Required behaviors

The yard demo should show:

* distinct vehicle movement patterns from mining
* different spatial feel from mining
* staging/resource interactions
* operator inspection
* route preview and command interaction
* visible bottleneck or operational coordination issue

## 6.5 Yard-specific acceptance criteria

The yard demo passes when:

* it clearly feels like a different environment family
* it still fits the same frontend and world model cleanly
* the workflow remains usable without environment-specific product hacks
* smaller-scale operational coordination still feels meaningful

## 6.6 Yard failure modes

The yard demo does **not** pass if:

* it just feels like a tiny mining map
* it requires custom UI logic to work at all
* operational semantics are too weak to distinguish it
* the environment only differs cosmetically

---

## 7. Demo C — City Street Demo

## 7.1 Purpose

This demo is the strongest proof that the traffic model is general enough.

The execution plan explicitly positions city street as the strongest test of lane, queue, merge, and traffic-control realism 

## 7.2 What this demo must prove

The city demo must prove:

* the world model supports lane/control-rich traffic scenes
* the lane/connector/control stack works
* congestion is readable
* merges/queues/controls feel believable
* the system is not haul-road-only

## 7.3 Recommended scenario content

The city demo should include:

* multiple roads/intersections
* lane-level structure
* stop/yield or signal-ready control semantics
* meaningful turn paths/connectors
* visible congestion potential
* at least one merge/conflict area

## 7.4 Required behaviors

The city demo should show:

* lane-aware movement
* turning/curved motion
* queueing at controlled points
* yielding or stopping behavior
* merge or lane-choice behavior
* operator inspection of traffic state
* route preview and command interaction where appropriate

## 7.5 City-specific acceptance criteria

The city demo passes when:

* lane and control semantics are clearly visible in behavior
* congestion feels urban/traffic-centric rather than mining-like
* the city scene is readable and not overly cluttered
* the same frontend product model still works

## 7.6 City failure modes

The city demo does **not** pass if:

* the city is only a visual skin on haul-road logic
* vehicles still snap unrealistically through intersections
* lane semantics exist only visually and not behaviorally
* the traffic stack is too shallow to make the city feel distinct

---

## 8. Demo D — Live Operator Intervention Demo

## 8.1 Purpose

This is not defined by environment first. It is defined by **workflow**.

Its job is to prove that the serious UI is a real operator tool.

## 8.2 What this demo must prove

This demo must prove:

* the operator can work entirely through the serious UI
* preview-before-commit works
* command results are clear
* live control is not an afterthought

## 8.3 Required walkthrough

The operator should be able to:

1. launch live scenario from the supported live path
2. pause/play/step
3. select a vehicle
4. preview a destination/route change
5. commit it
6. block or unblock a road
7. inspect resulting traffic or vehicle consequences
8. optionally mutate the scene with a spawn/job/hazard action

## 8.4 Acceptance criteria

This demo passes when:

* no ad hoc Python-side manual intervention is required for the core operational workflow
* command results remain grounded in authoritative backend state
* operator actions visibly change the run
* the UI remains understandable during action

This directly aligns with the roadmap’s serious-UI command execution and live mutation goals 

---

## 9. Demo E — Hazard / Bottleneck Demo

## 9.1 Purpose

This demo proves the system can show meaningful operational disruption.

## 9.2 What it must prove

* hazards matter operationally
* bottlenecks are visible and inspectable
* route changes and traffic consequences are believable
* explanation surfaces are useful

## 9.3 Recommended content

* blocked road, closure, or hazard zone
* affected vehicles
* alternative routing possibilities
* queue buildup caused by disruption

## 9.4 Acceptance criteria

This demo passes when:

* disruption visibly changes behavior
* the operator can inspect why vehicles slowed/stopped/rerouted
* the operator can intervene meaningfully
* the world still feels coherent after mutation

---

## 10. Demo F — Explanation / Suggestion Demo

## 10.1 Purpose

This demo proves that AI-style explanation/suggestion surfaces are grounded and useful, not gimmicky.

## 10.2 What it must prove

* explanations are tied to real simulator state
* anomalies are meaningful
* suggestions are concrete and bounded
* the operator can connect suggestion → map → action

## 10.3 Required walkthrough

A user should be able to:

* select a waiting/delayed vehicle
* get a grounded explanation
* review an anomaly or suggestion
* jump to the relevant map context
* optionally act on the suggestion

## 10.4 Acceptance criteria

This demo passes when:

* the explanation is genuinely useful
* the rationale is grounded
* the suggestion feels actionable
* the operator still remains in control

This lines up with the roadmap’s later AI explanation and suggestion refinement goals 

---

## 11. Demo G — Authoring / Edit Loop Demo

## 11.1 Purpose

This demo proves the project can evolve beyond hand-editing scenario JSON.

## 11.2 What it must prove

* geometry edits are possible
* validation is meaningful
* save/reload works
* edited scenes still run deterministically

## 11.3 Required walkthrough

A user should be able to:

* enter editor mode
* modify a road, node, or zone
* validate changes
* save scene
* reload/rerun
* observe the change in the simulation

## 11.4 Acceptance criteria

This demo passes when:

* authoring feels real, not fake
* invalid geometry is rejected clearly
* edited content persists correctly
* editing and runtime remain connected through a clean workflow

This reflects the roadmap’s authoring backbone and live editing goals 

---

## 12. Demo H — Stress / Performance Demo

## 12.1 Purpose

This demo proves the system can hold together under load.

## 12.2 What it must prove

* dense scenes remain understandable
* runtime behavior remains coherent
* frontend remains usable
* performance work is benchmark-driven

## 12.3 Recommended content

* dense mining traffic
* dense city traffic
* multi-vehicle queue/corridor pressure
* operator inspection during load

## 12.4 Acceptance criteria

This demo passes when:

* bottlenecks are measurable
* the system stays operationally understandable
* performance issues are explicit and benchmarked rather than guessed

This aligns with the roadmap’s benchmark and scaling checkpoints 

---

## 13. Demo sequence priority

These demos should be prioritized in this order.

### Tier 1 priority

1. Mining Flagship Demo
2. Live Operator Intervention Demo
3. Hazard / Bottleneck Demo

### Tier 2 priority

4. Construction Yard Demo
5. City Street Demo

### Tier 3 priority

6. Explanation / Suggestion Demo
7. Authoring / Edit Loop Demo
8. Stress / Performance Demo

This ordering keeps the project focused on proving the core thesis before over-expanding into every secondary surface.

---

## 14. Acceptance checklist template for any demo

Use this checklist when judging a demo.

### Visual quality

* Does it look intentionally designed?
* Is the map readable?
* Are vehicles readable?
* Is clutter controlled?

### Operational meaning

* Are vehicles doing meaningful work?
* Do bottlenecks, queues, or constraints matter?
* Does the environment feel like a real operational place?

### Interaction

* Can the operator inspect what matters?
* Can the operator preview action?
* Can the operator commit action?
* Is the result visible and trustworthy?

### Realism

* Does motion feel believable?
* Do traffic behaviors feel believable?
* Are hazards/resources/controls meaningful where relevant?

### Extensibility

* Does this rely on environment-specific hacks?
* Does it fit the shared architecture?

### Presentation-worthiness

* Would this be strong enough to show externally as evidence of the project’s direction?

---

## 15. Demo anti-patterns

Reject demos that are technically dense but fail product-wise.

### 15.1 Feature pile demo

Many features exist, but the scene is unreadable and the operator cannot form a coherent mental model.

### 15.2 Pretty but fake demo

The visuals look better, but movement, traffic, or control behavior are shallow or misleading.

### 15.3 Command theater demo

The UI has buttons, but commands do not feel grounded, previewable, or operationally meaningful.

### 15.4 Environment skin demo

The scene looks like a different environment, but behavior and semantics are still effectively identical.

### 15.5 AI magic demo

Explanations/suggestions look fancy but are not grounded in real simulator state.

---

## 16. Open questions

These should be refined later as demos mature.

### 16.1 Mining flagship scope

How large and complex should the flagship mining demo be before it becomes too broad for a clean acceptance target?

### 16.2 Yard/city distinction

What specific scenario content most strongly differentiates yard and city from mining?

### 16.3 AI demo maturity

At what point is the explanation/suggestion layer good enough to be demoed without undermining trust?

### 16.4 Performance targets

What concrete FPS/update/latency thresholds should count as acceptable for dense live demos?

---

## Final statement

The project is not truly succeeding just because individual features exist.

It is succeeding when it can demonstrate, end-to-end:

* a convincing mining flagship
* clear extensibility to yard and city
* real operator workflows
* meaningful disruptions and bottlenecks
* grounded explanations
* trustworthy live control
* presentation-worthy product quality

That is what the acceptance demos are meant to prove.

---
