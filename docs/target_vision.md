# `docs/target_vision.md`

# Autonomous Operations Sim — Target Vision

## Purpose

Autonomous Operations Sim is meant to become a deterministic simulation platform for operational environments where vehicles, tasks, traffic, hazards, and operator decisions all interact inside a believable, inspectable world.

It is not just a routing demo, not just a viewer, and not just a research sandbox.

The target is a system where:

* a Python simulator owns the authoritative world and runtime truth
* a serious frontend presents that truth through a strong map-first operator experience
* the world feels spatial and operationally meaningful
* vehicle motion and traffic behavior feel believable
* live operator commands can change the course of a run
* replay/export/live surfaces remain grounded in the same deterministic simulator state
* AI assistance explains and suggests against real simulator truth rather than inventing shadow state 

## North star

The end-state experience should feel like this:

A user launches a live scenario in a serious UI, sees a readable and spatially convincing world, watches vehicles move through it with believable behavior, clicks on anything important to inspect why it is doing what it is doing, previews operator actions before committing them, mutates the live scenario when needed, and can trust that everything visible in the frontend comes from the same authoritative simulator state that also powers trace, replay, export, and diagnostics.

## What this project should be

This codebase should become a platform for:

### Deterministic operational simulation

The simulator should produce stable results for the same scenario, seed, command sequence, and live-session progression. Determinism is not a side benefit. It is part of the product. The system should remain replayable, inspectable, and trustworthy under repeated runs. 

### Rich world and environment modeling

The system should support multiple environment families under one internal model:

* mine depot and haul-road operations
* construction yard operations
* city street operations

Mining remains the flagship acceptance environment, but the architecture must not be mine-only. Yard and city support should be natural extensions, not bolt-ons. 

### Believable motion and traffic behavior

Vehicles should not merely teleport between nodes or glide along viewer-only interpolations. The project should support a progression toward:

* heading-aware motion
* acceleration/deceleration-aware traversal
* curve-following
* following distance and spacing envelopes
* queues and congestion
* stop, yield, and control logic
* merging, lane choice, and bounded overtaking
* deadlock and gridlock detection/mitigation

These behaviors should be simulator-side truths, not frontend illusions. 

### Real operator workflows

The serious frontend should become a real operator surface, not a read-only demo. Operators should be able to:

* inspect vehicles, roads, queues, hazards, and routes
* issue commands from the UI
* preview consequences before committing actions
* control live session playback
* mutate live scenarios in bounded ways
* work with fleets, not only single vehicles

The user experience should be map-first and product-quality, not raw-ID-first or debug-first. This aligns directly with the repo’s stated focus on frontend and experience quality as the biggest remaining gap. 

### Grounded AI/operator assistance

AI features should come later and stay grounded. They should explain:

* why a vehicle is waiting
* why a route was selected
* where congestion is building
* what anomaly or risk is present

They should suggest bounded actions:

* reroute here
* reopen this road
* redirect this vehicle
* watch this deadlock risk

They should not become a competing source of truth. They should derive from deterministic simulator state and structured read models.  

## What this project should not be

This codebase should not become:

A frontend-owned fake simulator where the UI silently owns route, vehicle, or conflict truth.

A collection of loosely related demos where mining, yard, and city each require their own special-case architecture.

A research playground detached from operator usefulness.

A polished shell hiding shallow world behavior.

A large pile of backend read models that do not materially improve realism, visual quality, operator workflow, or extensibility. The execution plan explicitly warns against over-investing in these false peaks. 

## Core product identity

The identity of the project should rest on five traits.

### 1. Simulator authority

The Python simulator remains authoritative for topology, runtime state, routing, coordination, reservations, metrics, commands, trace, and live progression. Frontend and exported surfaces consume that truth.  

### 2. Strong map-first UX

The serious UI should feel like a real operational map product. It should be calm by default, progressively detailed on selection, and capable of supporting live decision-making.

### 3. Operational realism

The project should model not just motion through space, but work through space:

* loading
* unloading
* staging
* resource contention
* bottlenecks
* hazards
* fleet coordination

### 4. Extensible environment model

The internal world model should handle multiple environments under one conceptual system. Roads, areas, lanes, zones, buildings, hazards, and terrain forms should all fit without environment-specific hacks.

### 5. Explainable, replayable truth

Everything important should be explainable after the fact and inspectable during the run through stable trace, metrics, and derived structured surfaces. 

## Target user experiences

The codebase should eventually support at least these five concrete experiences.

### Experience 1: Live operator control

A user launches a scenario, sees vehicles moving through a believable world, clicks on a vehicle, inspects its current task and wait reason, previews a reroute, commits it, and watches the result unfold.

### Experience 2: Traffic and bottleneck understanding

A user can quickly see where congestion is forming, why it is forming, which roads or intersections are causing delay, and what control/hazard/resource condition is contributing.

### Experience 3: Scenario mutation

A user can inject new work, spawn or remove vehicles, declare a temporary hazard, or block a road during a run and still trust that the session remains stable and deterministic.

### Experience 4: Authoring iteration

A user can edit geometry or scene semantics, save the scenario, rerun it, and preserve valid structure without hand-editing JSON for every change.

### Experience 5: Explanation and suggestion

A user can ask, explicitly or implicitly through the UI, what is happening and what might help, and receive explanations/suggestions grounded in actual simulator truth.

## Environment vision

The platform should support three environment families clearly.

### Mining

Mining remains the flagship and the strongest demonstration of the platform’s value. It should showcase:

* haul roads
* depots
* loading and unloading sites
* crushers or bottlenecks
* narrow corridors
* queue buildup
* hazards/weather effects
* operator rerouting and dispatch
* AI-assisted explanation/suggestion

This is the primary acceptance environment. 

### Construction yard

Construction yard scenes should prove the system is not overfit to mining. They should emphasize:

* tighter vehicle movements
* staging areas
* material/resource contention
* yard-specific geometry and operational flow

### City street

City scenes should prove the traffic stack is generalizable. They should emphasize:

* lane semantics
* intersections
* stop/yield/control behavior
* merge behavior
* queue and congestion
* route preview and traffic-aware control

## World realism vision

The world should eventually be represented not just as edges and nodes, but as a layered operational space.

That means the codebase should be able to represent:

* roads and lanes
* intersections and control points
* depots, yards, pads, and staging zones
* buildings and structures
* pits, berms, stockpiles, and terrain forms
* hazard zones and no-go areas
* resource sites and bottlenecks

The rendering and modeling approach should prefer geometry and semantics over hardcoded environment-specific logic. A pit should read like a recessed form because it is a pit, not because “mine mode” is active. A building should read like a raised mass because it is a structure, not because “city mode” is active.

## Vehicle realism vision

Vehicles should become readable both operationally and visually.

Operationally, each vehicle should support:

* position
* heading
* speed
* class/role
* task/job affiliation
* route state
* wait reason
* diagnostics/warnings
* resource interactions

Visually, the system should support:

* class-distinct glyphs or silhouettes
* heading-aware rendering
* curve-following motion
* spacing and queue readability
* selected vehicle clarity
* compact inspection surfaces rather than always-on labels

## Traffic realism vision

Traffic realism should be layered, not solved in one abstraction leap.

The intended ladder is:

* lane geometry and connectors
* kinematics-backed motion
* following distance and envelopes
* queue formation and discharge
* stop/yield/control logic
* merge and lane-choice baseline
* deadlock/gridlock mitigation

This matches the roadmap structure and is the right progression for keeping realism grounded and testable. 

## Frontend vision

The serious frontend should become a separate, high-quality application path optimized for product feel rather than constrained by the current standalone viewer assumptions. The repo already locks in that the stronger frontend path should win when there is tension between UI quality and legacy assumptions. 

The frontend should have:

### A map-first operate experience

The map is the primary surface. It should show:

* world form
* roads and lanes where needed
* vehicles
* hazards/queues/routes when relevant
* compact selection-based detail

### A real operator shell

The operator should have access to:

* command center
* inspector
* traffic/queue/conflict surfaces
* fleet workflows
* editor workflows
* analysis and explanation surfaces

### Progressive detail

The UI should avoid constant clutter. Details should appear through:

* selection
* preview
* explicit layer toggles
* focused workflows

## Live operations vision

The project should support a full live session workflow:

* launch a scenario into a live session
* connect a serious frontend without custom glue
* play, pause, and step
* issue commands
* preview effects before committing
* mutate the session
* preserve deterministic command history and replayability

That live path is central to the roadmap, not a side feature. 

## Authoring vision

The project should outgrow JSON-only manual authoring.

It should support:

* an authoring model
* edit transactions
* deterministic validation
* live save/reload
* geometry edits
* import-to-edit convergence

Imported scenes and hand-authored scenes should land in one internal representation rather than split the project into incompatible content paths. 

## AI and research vision

The project should eventually support a research layer, but only after the operational and realism layers are strong enough to justify it.

That means:

* explanations before aggressive suggestions
* suggestions before autonomous action
* a pluggable policy sandbox
* generated stress scenarios
* multi-agent experimentation
* benchmarked comparison

The research layer should sit on top of a strong product and simulation foundation, not compensate for a weak one. The execution plan is explicit about avoiding premature AI overreach. 

## Performance vision

The project should scale in a measured way.

Performance work should:

* follow benchmarks
* identify hotspots before rewriting
* keep Python as the broad authority path
* use narrow native acceleration only where clearly justified and parity-tested

This keeps the project from turning into a speculative mixed-runtime rewrite.  

## Acceptance standard

The project is on the right path when it can convincingly demonstrate:

### Mining flagship demo

A polished live or replayable mining scenario where:

* vehicles move believably
* queues and bottlenecks emerge
* hazards affect operations
* operator commands matter
* explanations and suggestions are grounded
* the UI feels presentation-worthy

### Construction-yard demo

A smaller but distinct environment proving the architecture generalizes.

### City-street demo

A traffic-centric environment proving lane/control/congestion logic is not mining-only.

These three demos together should prove the thesis of the platform. The roadmap already places them as explicit later-phase showpieces. 

## Final statement

Autonomous Operations Sim should become a deterministic autonomous-operations platform where a Python-authoritative simulator, a serious map-first frontend, believable world and traffic behavior, live operator workflows, and grounded AI assistance all reinforce each other instead of competing with each other.

The point is not to build a pretty viewer, and not to build a simulator no one wants to use.

The point is to build a system that is:

* operationally useful
* visually convincing
* architecturally clean
* extensible across environments
* grounded in authoritative truth
* strong enough to support both product use and research use

---