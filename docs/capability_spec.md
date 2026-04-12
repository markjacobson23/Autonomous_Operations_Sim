
# `docs/capability_spec.md`

# Autonomous Operations Sim — Capability Specification

## Purpose

This document translates the target vision into concrete capabilities the codebase must support.

It is not an implementation plan and not a step list.
It defines what the system must eventually be able to do, what must remain true while doing it, and what acceptance looks like at a capability level.

This spec assumes the repo-wide architectural rules remain locked:

* deterministic simulator authority in Python
* frontend as a consumer of derived simulator truth
* explicit command and session semantics
* replay/export/live surfaces derived from authoritative runtime state
* mining as the flagship acceptance environment with clean extension to construction yard and city street scenes  

## 1. Global capability requirements

The codebase must eventually be able to:

1. simulate operational environments deterministically
2. represent multiple environment families under one internal world model
3. show believable vehicle and traffic behavior
4. support real operator workflows through a serious frontend
5. expose stable replay/export/live surfaces from the same runtime truth
6. support scenario editing and live mutation safely
7. provide grounded explanations and suggestions on top of simulator truth
8. scale through measurement-driven optimization rather than speculative rewrites

## 2. Determinism and authority capabilities

### 2.1 Deterministic execution

The system must produce stable outputs for the same:

* scenario
* seed
* command sequence
* live-session progression

### 2.2 Stable observability

The following must remain derivable from authoritative simulator truth:

* trace
* metrics
* replay bundles
* live bundles
* inspection surfaces
* command/session history

### 2.3 No shadow ownership

The following must not become frontend-owned truth:

* vehicle runtime state
* route truth
* conflict/reservation truth
* topology mutation semantics outside validated edit/command paths

### Acceptance

A scenario rerun with the same inputs yields materially identical:

* command results
* trace ordering
* visible vehicle behavior
* replay/live state
* operator inspection surfaces

## 3. World and environment capabilities

## 3.1 Unified world model

The codebase must support one internal world model that can represent:

* mine depot / haul-road scenes
* construction yard scenes
* city street scenes

### 3.2 Static world primitives

The world model must be able to encode:

* nodes and edges
* roads
* intersections/junctions
* depots/yards/pads
* loading/unloading zones
* buildings/structures
* hazard/no-go zones
* terrain-like forms
* lane-level geometry where needed
* stop lines / connectors / merge zones

### 3.3 Environment semantics

The model must allow distinct semantics for:

* mining
* construction yard
* city street

without splitting the codebase into separate world architectures.

### 3.4 Geometry-first rendering support

The world model and rendering pipeline together must support a geometry-first interpretation of the environment, including:

* flat surfaces
* raised forms
* recessed forms
* road ribbons
* structure silhouettes

### Acceptance

At least one mining, one yard, and one city scene can be represented without hacks or environment-specific renderer forks.

## 4. Vehicle capabilities

## 4.1 Vehicle classes

The codebase must support multiple vehicle families, including:

* haul trucks
* forklifts
* cars
* utility/support vehicles
* future extensible classes

## 4.2 Vehicle runtime state

Each vehicle must be representable with:

* identity
* class/type
* position
* heading
* speed
* operational state
* current route
* current task/job
* wait reason
* diagnostics/warnings
* spacing/collision envelope

## 4.3 Vehicle motion realism

The motion system must eventually support:

* kinematics-aware movement
* acceleration/deceleration-aware traversal
* heading updates
* curve-following
* turn arcs
* ETA tied to runtime motion assumptions

## 4.4 Vehicle presentation

The frontend must be able to present vehicles with:

* class-distinct glyphs or silhouettes
* readable heading
* motion clarity
* selection clarity
* compact inspection detail

### Acceptance

Mixed vehicle scenes are readable at a glance, and selected vehicles expose believable motion and inspection context.

## 5. Traffic and coordination capabilities

## 5.1 Conflict and reservation baseline

The simulator must support coordination semantics for:

* route conflict handling
* reservation-aware movement
* conflict inspection

## 5.2 Spacing and following behavior

The simulator must support:

* spacing envelopes
* following distance
* non-overlapping multi-vehicle movement
* visible waiting/slowdown when space is constrained

## 5.3 Queue and congestion behavior

The simulator must support:

* queue formation
* queue discharge
* congestion buildup
* congestion inspection/visualization

## 5.4 Control behavior

The simulator must support:

* stop lines
* yielding
* right-of-way / protected conflict behavior
* controlled vs uncontrolled junction differences

## 5.5 Lane behavior

Where scenes require it, the system must support:

* explicit lanes
* turn connectors
* merge zones
* lane choice
* bounded overtaking baseline

## 5.6 Deadlock handling

The simulator must support:

* deadlock/gridlock detection
* mitigation or operator-visible risk surfacing
* deterministic behavior under dense traffic stress

### Acceptance

A dense multi-vehicle scenario produces:

* no visual overlap cheating
* clear queueing behavior
* inspectable wait reasons
* explainable congestion
* no silent deadlock failure

## 6. Operational and dispatch capabilities

## 6.1 Route and destination control

The codebase must support:

* assign destination
* preview route before commit
* inspect route consequences
* commit and observe runtime effects

## 6.2 Live session control

The codebase must support:

* launch live scenario
* reconnect bundle/session
* play
* pause
* single-step

## 6.3 World/traffic mutation

The codebase must support:

* block/unblock road
* declare/clear hazard
* other bounded runtime operational mutations

## 6.4 Vehicle/task mutation

The codebase must support:

* spawn vehicle
* remove vehicle
* inject job/task
* reassign vehicle work as command surfaces allow

## 6.5 Fleet operations

The operator surface must support:

* multi-select
* bounded batch actions
* fleet-scoped command workflows

### Acceptance

An operator can run a live session entirely through the serious UI without relying on ad hoc Python-side manual intervention for core operational actions.

## 7. Frontend and operator UX capabilities

## 7.1 Serious frontend path

The project must support a dedicated serious frontend path optimized for UI quality rather than being constrained by legacy standalone viewer assumptions. 

## 7.2 Map-first operate experience

The primary operator UX must support:

* pan/zoom/fit/focus
* Iso/Birdseye or equivalent major scene modes
* minimap
* selection highlighting
* compact popup/inspector detail
* progressive disclosure rather than constant clutter

## 7.3 Object interaction

The frontend must support selecting:

* moving vehicles
* roads
* queues
* conflict areas
* hazards
* relevant environment objects/surfaces

## 7.4 Route and command UX

The frontend must support:

* route preview
* consequence inspection
* command submission
* result/error feedback
* map-first planning workflow rather than raw-ID-only control

## 7.5 Product-quality presentation

The frontend must become presentation-worthy, not prototype-grade, with:

* coherent visual language
* readable overlays
* usable layout on laptop-scale screens
* strong scene readability

### Acceptance

A live scenario can be launched and operated through a frontend experience that feels like a real product and not a debugging shell.

## 8. Inspection, observability, and explanation capabilities

## 8.1 Vehicle inspection

The system must provide inspection access to:

* current node/position
* route ahead
* current task/job
* wait reason
* traffic control detail
* diagnostics/warnings

## 8.2 Road/traffic inspection

The system must provide inspection access to:

* queue states
* congestion intensity
* active/queued vehicles
* control state where relevant

## 8.3 Route/conflict inspection

The system must provide:

* reservation/conflict overlays
* selected-route preview
* conflict explanation before commit where possible

## 8.4 Explanation surfaces

The system must be able to explain, in grounded terms:

* why a vehicle is waiting
* why a reroute happened
* why a queue formed
* why ETA changed
* why a hazard is affecting traffic

### Acceptance

A user can click a waiting or delayed entity and get a grounded explanation from simulator-derived truth.

## 9. Task, resource, and operational realism capabilities

## 9.1 Task model

The system must support tasks/jobs involving:

* movement
* loading
* unloading
* staging
* depot/bay occupancy
* resource bottlenecks

## 9.2 Resource contention

The system must support resource constraints that influence operations, including:

* loading bay occupancy
* unloading/crusher bottlenecks
* staging congestion
* yard/depot throughput limitations

## 9.3 Environment-specific operational meaning

Mining, yard, and city scenes must feel different not only visually but operationally.

### Acceptance

A mining scenario can demonstrate meaningful loading/unloading/resource bottlenecks instead of only navigation.

## 10. Hazards and weather capabilities

## 10.1 Hazard model

The system must support hazards that can affect:

* routing
* closures
* slowdown/caution behavior
* operator decisions

## 10.2 Weather model

The system must support weather-like operational conditions that can affect:

* speed
* route availability
* caution behavior
* inspection/explanation surfaces

### Acceptance

At least one scenario demonstrates a hazard or weather condition that materially changes behavior and is visible/explainable in the UI.

## 11. Authoring and editing capabilities

## 11.1 Authoring model

The codebase must support:

* edit transaction model
* deterministic validation
* save/reload workflow
* clear invalid-edit rejection

## 11.2 Geometry editing

The editor path must support:

* move nodes
* edit roads
* edit areas/zones
* save and rerun modified scenes

## 11.3 Unified content representation

Imported scenes and hand-authored scenes must converge into one editable internal representation.

### Acceptance

A scene can be edited, validated, saved, and rerun without losing semantics or requiring manual schema patching.

## 12. Import and extensibility capabilities

## 12.1 Import seam

The codebase must provide a clear adapter boundary for imported maps/standards.

## 12.2 Internal-model convergence

Imported data must normalize into the same internal world model used by authored scenarios.

## 12.3 Extensibility rule

The project must remain open to future:

* stronger frontend stack choices
* narrow native accelerators
* external map adapters

without breaking simulator authority boundaries.  

## 13. AI and research capabilities

## 13.1 Grounded AI explanation

The codebase must support AI explanation layers that derive from simulator truth and structured read models.

## 13.2 Grounded AI suggestion

The codebase must support bounded suggestion surfaces for:

* reroutes
* reopen/closure actions
* dispatch adjustments
* anomaly response

## 13.3 Policy experimentation

The codebase must support a pluggable policy/dispatch sandbox for deterministic comparison.

## 13.4 Stress-case generation

The codebase must support reproducible structured stress-scenario generation or assisted generation.

## 13.5 Multi-agent experimentation

The codebase must support comparative multi-policy or multi-agent experiments without corrupting the main simulator authority model.

### Acceptance

The system can compare policies and explain outcomes while preserving deterministic, inspectable truth surfaces.

## 14. Performance and scaling capabilities

## 14.1 Benchmark-first optimization

Performance work must be guided by measurement and benchmark evidence, not speculation.  

## 14.2 Narrow acceleration

Native acceleration, if introduced, must be:

* hotspot-justified
* parity-tested
* bounded
* optional/fallback-safe

## 14.3 Large-scene usability

The combined simulator + frontend stack must remain usable for dense scenarios with:

* many vehicles
* meaningful traffic interactions
* live session updates
* operator inspection workflows

### Acceptance

Performance bottlenecks are measurable, named, and targeted rather than guessed at.

## 15. Flagship acceptance demos

The codebase should eventually satisfy these showcase-level capability tests.

## 15.1 Mining flagship

Must demonstrate:

* believable world
* believable motion
* congestion/queues
* live operator control
* hazards/weather effects
* inspection and AI assistance

## 15.2 Construction-yard showcase

Must demonstrate:

* distinct environment semantics
* resource/staging realism
* extension beyond mining

## 15.3 City-street showcase

Must demonstrate:

* lane/control behavior
* merge/queue/congestion behavior
* extension beyond mining

## 16. Explicit non-capabilities for now

The codebase does **not** currently need to fully support as hard requirements:

* full physics-engine integration
* sensor simulation
* broad external-standard interoperability breadth
* full maintenance/repair ecosystem
* fully autonomous learned control as default authority
* high-end audio/day-night/weather presentation as structural blockers

Those are intentionally deferred in the master plan. 

## 17. Capability review checklist

Use this when evaluating whether the codebase is moving in the right direction.

### Simulator truth

* Does this preserve Python authority?
* Does this preserve determinism?
* Does this create any shadow truth?

### Product quality

* Does this improve operator usefulness?
* Does this improve visual or map quality?
* Does this reduce prototype feel?

### Realism

* Does this improve world, vehicle, or traffic realism?
* Is the realism grounded in simulator-side truth?

### Extensibility

* Does this work for mining, yard, and city?
* Does this strengthen the shared world model instead of creating special cases?

### Performance

* Is this change benchmark-driven if it affects scaling?
* Does it preserve a correct fallback path?

---
