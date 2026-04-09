# Autonomous Operations Sim — Master Execution Plan

This document is the single source of truth for:
- project direction
- architectural rules
- roadmap status
- per-step scope
- Codex execution behavior

It replaces the old multi-doc workflow:
- `docs/roadmap.md`
- `docs/current_phase.md`
- `docs/step-*.md`

---

# 1. Purpose

This repository is evolving into a deterministic autonomous operations simulation platform with:

- authoritative simulation/runtime logic
- stable control, replay, export, and live-sync surfaces
- a serious visual frontend
- richer motion, map, and traffic realism
- richer vehicle/entity realism
- later AI-assisted operations features
- later performance/scaling work driven by measurement

This is **not** primarily a game project.

It should be visually compelling, operationally impressive, and realism-oriented, but the simulator core remains the authoritative system of record.

The long-horizon objective is a simulator that can grow into a convincing autonomous operations environment across:
- construction yards
- mine depots / mining operations
- city-street-style operational networks

with a UI and visualization layer that feels significantly beyond a debug tool.

---

# 2. Core principles

## 2.1 Determinism is first-class
The simulator must remain deterministic for the same:
- scenario
- seed
- command sequence
- session progression
- replay/export input

Preserve:
- stable ordering
- explicit seeds
- canonical exports where practical
- replay compatibility
- command/session/sync consistency

Do not introduce hidden nondeterminism through:
- uncontrolled randomness
- unordered state transitions where order matters
- UI-driven direct mutation of runtime truth
- time-of-day / wall-clock semantics leaking into simulation authority

## 2.2 The simulator core is authoritative
The core simulator owns:
- execution semantics
- vehicle/runtime truth
- routing/coordination truth
- commands and live sessions
- replay/export/live-sync truth

Frontends and viewers must consume stable simulator surfaces.
They must not become the source of truth.

## 2.3 Frontend stack is allowed to differ from simulator stack
The simulator core is currently Python and may remain Python.

The viewer/frontend does **not** need to stay Python.
Best UI/UX quality wins.

Healthy split:
- Python core for deterministic simulation, commands, sessions, replay/export, sync, and experimentation
- external frontend/rendering stack for high-quality visualization and interaction

Do not split languages prematurely for no gain.
Do split when quality, development speed, or architecture cleanliness clearly improve.

## 2.4 Simulation realism matters, not just visual polish
The target system should eventually improve both:
- **presentation realism**
- **simulation realism**

That includes future work around:
- continuous movement
- curved/lane-aware road geometry
- spacing and collision envelopes
- traffic queues and congestion
- right-of-way behavior
- vehicle realism
- richer operational environments like mine depots, construction yards, and city-like networks

## 2.5 Additive refactoring over reckless rewrites
Prefer:
- clean new modules
- stable interfaces
- transport-agnostic boundaries
- bounded subsystem replacement when justified

Avoid:
- giant rewrites without interface continuity
- simulator-core changes for frontend convenience
- speculative abstractions with no concrete milestone behind them

## 2.6 UI quality matters more than stack loyalty
The project should not remain in a weaker frontend stack just because it is already in use.

If a bounded frontend/viewer stack change materially improves:
- visual quality
- interaction quality
- iteration speed
- maintainability
- deployability

then that change is acceptable as long as simulator authority boundaries remain clean.

---

# 3. Target product direction

## 3.1 Target environments
The simulator should feel expandable, centered initially on:
- construction yard
- mine depot / mining operation
- city street environment

These are not isolated demos; the architecture should remain expandable beyond them.

## 3.2 Target vehicle classes
Near- and medium-term vehicle focus:
- transport trucks
- cars
- forklifts
- mixed fleets later

Longer-term fleet diversity can expand, but the initial realism work should be grounded in believable ground-vehicle operations.

## 3.3 Target realism direction
Long-term realism direction includes:
- continuous movement along edges
- heading/orientation while moving
- acceleration/deceleration
- turning arcs through curves/intersections
- lane-based movement
- collision envelopes / spacing
- stop lines / yielding / traffic lights
- queues and traffic buildup
- richer road geometry and environment context
- believable operator-facing visualization
- AI-assisted operational understanding later

## 3.4 Dream showpiece direction
The long-horizon showpiece is a mining/construction/city-style autonomous operations environment where:
- vehicles move continuously
- routes interact visibly
- congestion and hazards matter
- operators can inspect and redirect vehicles live
- the system looks polished and feels operationally credible

## 3.5 Detailed environment and map wishlist
The target map/road/network environment should eventually support:
- curved roads
- lanes
- intersections with shapes
- one-way and two-way road semantics
- road classes
- parking areas
- depots
- loading bays
- sidewalks
- no-go zones
- zones/areas/buildings/background art
- richer site context for mine-depot / yard / city-like operations
- imported maps from external formats later, when the data model is mature enough

The visual target is somewhere between:
- clean operational clarity
- semi-realistic spatial context
- almost game-like polish eventually

without turning the project into a game-first product.

## 3.6 Detailed vehicle capability wishlist
Vehicle realism should eventually be able to grow toward:
- max speed constraints
- acceleration and braking
- turning behavior
- lane following
- reversing
- trailers / articulation later
- payload and cargo type
- battery / fuel / charging later
- vehicle-class permissions and restrictions
- diagnostic and warning telemetry later, such as low tire pressure or vehicle-health issues

The short-term viewer can still use simplified moving entities, but the long-term goal is believable operational vehicles.
It is acceptable for early vehicle visuals to stay abstract as long as:
- motion is understandable
- orientation is visible
- clicking a vehicle can reveal richer context or even a richer vehicle diagram later

## 3.7 Detailed live interaction wishlist
The target live environment should eventually support as many of these as practical:
- click a moving vehicle to inspect it
- reassign destination mid-route
- pause / play / single-step
- drag vehicles
- close/open roads
- inject jobs/tasks
- spawn/remove vehicles
- inspect reservations/conflicts
- inspect route/path overlays
- inspect traffic queues
- edit map geometry live
- select multiple vehicles
- issue fleet-wide commands

Not all of these must be mouse-driven.
Typed commands, assisted control, or automatic allocation are also acceptable where better.
Examples of acceptable operator workflows:
- command a nearest suitable truck to pick up more rock
- redirect an already-related truck to satisfy a new operational need
- ask for a fleet-level response rather than micromanaging every vehicle manually

## 3.8 Detailed inspection and operator context wishlist
When clicking a vehicle, the long-term goal is to expose as much of the following as practical:
- current node
- exact position
- current task/job
- route ahead
- speed
- payload
- operational state
- blocked/waiting reason
- command history
- trace/events
- assigned destination
- ETA
- resource assignment
- future diagnostic information
- AI-generated explanation of what it is doing

This level of context should extend to nodes/roads/areas later where useful.

## 3.9 Detailed visual and "cool factor" wishlist
The visualization/frontend should eventually support as many of these as practical:
- smooth motion
- strong visual design
- cinematic map look
- glowing path overlays
- traffic density / liveliness
- nice icons / sprites
- vehicle orientation arrows
- animated queues / congestion
- layered minimap / overview
- hover effects
- slick inspector panels
- route previews before commit
- heatmaps for traffic / congestion
- replay scrubber / timeline
- good sounds eventually
- day/night or weather eventually

These are not all near-term requirements, but they are real long-term aspirations and should influence architecture choices.

## 3.10 Detailed traffic realism wishlist
Traffic realism should eventually be able to grow toward:
- multiple vehicles moving visibly
- actual congestion and waiting
- lane-based following
- signals / right-of-way
- merging behavior
- overtaking later if justified
- deadlock / gridlock avoidance
- operationally meaningful queueing
- visually understandable traffic density and bottlenecks

## 3.11 Detailed AI inclusion wishlist
AI-related features that are acceptable or desirable later include:
- AI as route/dispatch policy
- AI as higher-level planner
- AI assistant inside the UI explaining what is happening
- AI-generated job/task suggestions
- AI scenario generation
- AI anomaly detection
- AI operator copiloting
- learned vehicle behavior later
- multi-agent AI experimentation later

Early AI work should focus on low-risk, high-value operator assistance rather than replacing deterministic simulator truth.

---

# 4. Current architectural truth

At this point, the repository already has a substantial deterministic foundation:
- deterministic scenario parsing/execution
- routing
- jobs/resources/dispatch/workloads
- command/control surfaces
- replay/export surfaces
- graphical replay viewer
- live session bridge
- live viewer actions
- live state/command sync surface
- benchmark harness
- graph-map realism

The existing Python/Tk viewer should now be treated as:
- a valid engineering tool
- a useful prototype/debug surface
- not necessarily the final frontend stack

The strongest current architectural asset is:
- stable simulator surfaces that can support a better frontend without rewriting core runtime logic

The biggest current gap relative to the long-horizon vision is not core determinism.
It is the combination of:
- serious viewer/frontend quality
- continuous motion
- richer map geometry
- traffic realism
- richer operational inspection and control surfaces

---

# 5. Codex operating rules

These rules are part of the execution contract for this repository.

## 5.1 Prompting convention
The user may prompt Codex with only:

- `step-29`
- `step-30`
- `step-31`
- etc.

When prompted that way, Codex must:
1. read this document
2. locate the matching step section
3. execute **only that step**
4. avoid working on any other step unless explicitly instructed

## 5.2 Single-step rule
When prompted with `step-x`, Codex must:
- work only on Step X
- not implement Step X+1 or later
- not backfill unrelated earlier steps unless Step X explicitly requires a bounded refactor
- not silently “help out” by doing adjacent roadmap work

## 5.3 Respect prerequisites
If the prompted step depends on earlier steps that are not complete, Codex must:
- say so clearly
- explain the missing prerequisite
- stop rather than improvising a cross-step rewrite

## 5.4 No speculative roadmap jumping
Codex must not:
- work on future steps because they seem related
- redesign the architecture around later goals before the current step asks for it
- treat future ambitions as permission to overbuild now

## 5.5 Preserve authority boundaries
Codex must preserve:
- simulator core authority
- typed command/control semantics
- live session authority
- replay/export/live-sync stability

Frontend/viewer work must consume those surfaces rather than redefining them.

## 5.6 Tests and checks
For any substantive implementation step, Codex should verify:

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
```

If a step adds a CLI/tool entrypoint, verify it explicitly.

## 5.7 Documentation changes
Codex should not rewrite this master plan unless the user explicitly asks for a plan update.
Normal implementation work should follow the plan, not edit it.

## 5.8 Step prompt examples
If the user says:
- `step-30`

Codex must work only on Step 30 from this document.

If the user says:
- `step-35`

Codex must:
- verify prerequisite completion
- work only on Step 35 if prerequisites are satisfied
- otherwise explain the prerequisite problem and stop

This shorthand is intentional and should be treated as the normal workflow.

---

# 6. Roadmap status

## Completed
- Step 1 through Step 29: complete

## Active
- Step 30: active until explicitly marked complete

## Future
- Step 31 onward: planned below

---

# 7. Priority order for the next major program

This roadmap is intentionally adapted to the project’s stated priorities.

Priority ranking:
1. better graphics / visual polish
2. richer map realism
3. traffic realism
4. smooth continuous motion
5. vehicle realism
6. live interactivity
7. AI-assisted features
8. frontend quality / maybe non-Python UI
9. performance/scaling
10. benchmark/research capability

That means after the benchmark step, the roadmap shifts toward:
- Simulation API boundary
- serious frontend/viewer direction
- continuous motion
- road geometry realism
- traffic realism
- richer vehicle and operations UX
before deeper scaling/native-split work

---

# 8. Recommended architectural direction

## Strong recommendation
Keep the simulator core authoritative in Python, but introduce a versioned simulation I/O boundary and be willing to move the serious viewer to a better frontend/rendering stack if that clearly improves UI/UX.

## Practical interpretation
Near term:
- Python core remains authoritative
- existing viewer remains useful
- define a cleaner frontend-facing boundary

Medium term:
- decide whether the serious viewer should remain Python-based or become an external client
- likely candidates later:
  - Unity
  - Godot
  - a high-quality web frontend
  - another frontend stack if justified

The important architectural decision is the boundary, not blind loyalty to a specific stack.

## What should remain authoritative no matter what
Regardless of frontend stack, the authoritative simulator-side responsibilities should remain:
- scenario parsing and validation
- simulation execution semantics
- commands and command history
- live session progression
- replay/export semantics
- live-sync semantics
- benchmark/profiling truth
- operational state ownership

The frontend should be a consumer of those surfaces, not a replacement for them.

---

# 9. Roadmap

---

## Step 29 — Profiling and benchmark harness
**Status:** complete

### Goal
Add a repeatable profiling and benchmark harness so later performance/scaling work is driven by measurement instead of guesswork.

### Why this step exists
Even though performance is lower priority than realism/UI right now, baseline measurement is still important before later optimization work.

### In scope
- repeatable benchmark/profiling surfaces
- routing benchmark(s)
- scenario/scenario-pack benchmark(s)
- at least one coordination/reservation benchmark or proxy
- at least one replay/export/live-sync generation benchmark
- stable result formatting
- benchmark harness tests where practical

### Out of scope
- major optimization work
- mixed-language performance split
- redesigning the simulator around benchmark convenience

### Architecture guidance
- benchmark honestly
- keep the benchmark harness separate from runtime semantics
- measure current architecture rather than idealized future architecture

### Done when
- repeatable benchmark suite exists
- results are stable and structured
- baseline hotspot measurements exist
- tests/lint/type checks pass

---

## Step 30 — Simulation API boundary
**Status:** active

### Goal
Define a versioned, stable simulator-facing API boundary for both replay and live operation.

### Why now
Before investing heavily in a serious viewer/frontend, the simulator needs a cleaner formal interface.
This is the step that prevents the current viewer stack from becoming a trap.

### In scope
- define a versioned Simulation API boundary
- formalize stable replay-bundle structure
- formalize stable live session/sync structure
- define viewer-facing command/result semantics
- make the boundary transport-agnostic
- create stable serialization/export contracts
- add compatibility tests where practical

### Out of scope
- major frontend rewrite
- deep visual polish
- heavy networking architecture
- native/runtime split

### Architecture guidance
- the boundary must expose:
  - map/geometry state
  - entity/vehicle state
  - events/triggers
  - commands/results
  - replay timeline
  - live sync snapshots and updates
- keep simulator core authoritative
- optimize for future frontend flexibility
- think explicitly about:
  - replay bundles
  - live session streaming
  - viewer command acknowledgements
  - compatibility/versioning policy

### Done when
- the authoritative simulator I/O boundary is explicit and versioned
- replay/live surfaces are coherent under one API philosophy
- frontend work can proceed without depending on internal engine structure

---

## Step 31 — Serious viewer foundation
**Status:** planned

### Goal
Establish the real long-term viewer foundation on top of the Simulation API boundary.

### Why now
Once the interface is formalized, the project can stop treating the current GUI as the likely final viewer.

### In scope
- evaluate serious viewer direction
- choose the best medium-term viewer approach for UI/UX quality
- build the first serious viewer foundation against the Simulation API
- support:
  - map rendering
  - vehicle rendering
  - replay mode
  - live session consumption
  - selection and inspection hooks
  - timeline and operational overlays
- preserve simulator authority boundaries

### Out of scope
- final traffic realism
- deep AI/operator features
- performance tuning as the main goal

### Architecture guidance
- best UI/UX wins
- staying in Python is allowed if it truly delivers enough quality
- switching to a better frontend stack is allowed if justified
- do not rewrite simulator core into the viewer stack
- design for:
  - higher rendering ceiling
  - higher interaction ceiling
  - future extensibility
  - possible scene-asset use later

### Done when
- a serious viewer path exists
- it consumes the Simulation API cleanly
- it has a clearly higher quality ceiling than the current Tk viewer

---

## Step 32 — Continuous motion and temporal interpolation
**Status:** planned

### Goal
Move from state-jump visualization toward smooth continuous movement.

### Why now
Smooth motion is one of the highest-value improvements for realism and cool factor.

### In scope
- continuous movement along edges
- temporal interpolation between authoritative state changes
- heading/orientation while moving
- first motion profiles for acceleration/deceleration
- replay and live-view motion coherence
- motion data contracts needed by the viewer

### Out of scope
- full physics simulation
- lane-level traffic realism
- advanced collision handling
- final road-geometry realism

### Architecture guidance
- begin with motion interpolation and simple kinematic profiles
- do not prematurely build a full physics engine
- keep authoritative runtime semantics separate from viewer smoothing where appropriate
- ensure moving vehicles remain inspectable and selectable while in motion

### Done when
- vehicles move continuously rather than only snapping between nodes
- heading and speed changes are visually understandable
- replay/live movement feels substantially more believable

---

## Step 33 — Road geometry and map realism upgrade
**Status:** planned

### Goal
Evolve from graph-only road topology toward richer visible road/network geometry.

### Why now
Visual realism and traffic realism both depend on better geometry.

### In scope
- curved roads
- lane-aware road representations
- shaped intersections
- one-way vs two-way visual semantics
- road classes
- depots / loading bays / parking semantics
- no-go zones / sidewalks / environment areas
- zones / buildings / background context
- scene layout/background context
- map data-model upgrades needed to support this

### Out of scope
- full external map import pipeline
- full GIS stack
- complete city-scale world authoring tools

### Architecture guidance
- distinguish:
  - operational graph semantics
  - rendered geometry semantics
- do not lose the simplicity of authoritative routing graphs
- allow richer visual geometry to be derived or layered
- leave room for imported maps later without overcommitting now

### Done when
- road/network visuals are materially richer
- maps feel more like places and less like abstract node-edge diagrams
- the architecture supports future lane/traffic realism cleanly

---

## Step 34 — Traffic baseline and operational movement realism
**Status:** planned

### Goal
Introduce credible traffic behavior and vehicle-to-vehicle interaction.

### Why now
After motion and map geometry improve, traffic becomes the next biggest realism multiplier.

### In scope
- spacing envelopes
- simple following behavior
- queue formation
- congestion visibility
- right-of-way baseline
- stop/yield behavior
- signals where needed
- first merging/flow rules
- deadlock/gridlock prevention heuristics where practical

### Out of scope
- fully general traffic microsimulation
- extremely detailed overtaking logic unless justified
- external traffic simulator co-sim unless explicitly chosen later

### Architecture guidance
- start with deterministic traffic baseline
- build the simplest believable traffic layer first
- avoid exploding complexity too early
- ensure the model remains visually explainable to operators

### Done when
- vehicles visibly interact in traffic-like ways
- queues/congestion become real phenomena
- the environment starts to feel alive rather than merely animated

---

## Step 35 — Live command-center interaction
**Status:** planned

### Goal
Make the simulator feel like a real operations command center.

### Why now
Once vehicles move believably in richer environments, live operations become much more meaningful.

### In scope
- click moving vehicles to inspect them
- route/path overlays
- retasking mid-route
- closures/openings
- inject jobs/tasks
- spawn/remove vehicles
- inspect reservations/conflicts
- inspect queues
- selection of multiple vehicles
- fleet-level commands where practical
- route preview before commit
- mix of GUI actions, typed commands, and assisted control where appropriate

### Out of scope
- full map editing platform
- multiplayer
- remote/cloud operations productization

### Architecture guidance
- explicit actions remain routed through authoritative command/session surfaces
- optimize for operator usability
- support both GUI actions and typed/assisted commands
- avoid binding every useful action to mouse-only workflows

### Done when
- the system feels operationally manipulable
- live command workflows feel coherent
- viewer interaction and simulator authority remain cleanly separated

---

## Step 36 — Vehicle inspection, diagnostics, and operator UX
**Status:** planned

### Goal
Deepen vehicle/entity inspection and make the system easier to understand during live operation.

### Why now
Once there is continuous motion, traffic, and live control, operators need richer contextual understanding.

### In scope
- richer clickable vehicle inspector
- current task/job
- route ahead
- exact position
- speed
- payload
- state
- wait/block reason
- command history
- trace/event slices
- ETA
- resource assignment
- future-facing diagnostics hooks
- richer selection panels and overlays
- support for richer vehicle diagrams/panels later if practical

### Out of scope
- full maintenance simulation
- full sensor/telemetry realism
- AI-heavy explanation features as the main focus

### Architecture guidance
- inspection surfaces should compose from existing authoritative data
- avoid creating a second truth layer in the frontend
- make inspection useful for moving vehicles, not just paused vehicles

### Done when
- clicking a vehicle gives genuinely useful operational context
- inspection feels like a serious tool, not just debug text

---

## Step 37 — AI-assisted operations baseline
**Status:** planned

### Goal
Add the first low-risk, high-value AI-assisted operational features.

### Why now
AI should come after the environment, interaction model, and operator UX are strong enough to support it.

### In scope
- AI explanation of what a vehicle is doing
- AI operator-copilot assistance
- AI-generated job/task suggestions
- assisted retasking suggestions
- anomaly explanation over authoritative state
- optional scenario-generation assistance hooks

### Out of scope
- learned driving behavior as a required baseline
- replacing deterministic simulator control with black-box AI
- broad multi-agent training platform

### Architecture guidance
- AI should initially sit above the simulator, not inside core truth
- use AI for explanation, suggestion, and operator support first
- preserve deterministic simulator authority

### Done when
- at least one useful AI-assisted operator workflow exists
- AI adds value without destabilizing the simulator core

---

## Step 38 — Mining operations showpiece demo
**Status:** planned

### Goal
Pull the previous realism/UI steps into a serious showcase scenario.

### Why now
A strong vertical slice validates the roadmap better than isolated features.

### In scope
- mine/construction-style scenario pack
- ore pickups / loading flows
- congestion and tight routes
- hazards and operational constraints
- high-quality live viewer presentation
- command-center interaction
- inspector-rich vehicle monitoring
- replay and export support
- a demonstration that the simulator is visually impressive without becoming a game

### Out of scope
- every possible environment type
- broad productization beyond the showpiece scope

### Architecture guidance
- this step is an integration milestone
- prioritize coherence and wow factor without violating simulator truth

### Done when
- the repo has a credible serious demo that looks and feels substantially beyond the current state

---

## Step 39 — Python-side scaling improvements
**Status:** planned

### Goal
Use benchmark data to improve performance within the Python architecture first.

### Why now
Only after the realism/UI direction is concrete should optimization target the right hotspots.

### In scope
- routing optimizations
- reservation/conflict structure improvements
- replay/export/live-sync efficiency
- benchmark-backed performance changes

### Out of scope
- native/kernel split
- speculative performance rewrites without evidence

### Architecture guidance
- benchmark first
- optimize measured hotspots only
- preserve correctness and determinism

### Done when
- the benchmark suite shows meaningful Python-side gains
- architecture remains stable

---

## Step 40 — Optional native or mixed-runtime acceleration
**Status:** planned

### Goal
If benchmark evidence justifies it, isolate one bounded hotspot for non-Python acceleration.

### Why now
Language/runtime separation should be earned, not assumed.

### In scope
- select one bounded hotspot
- define a clean interface
- prove measurable benefit
- preserve authoritative Python orchestration where appropriate

### Out of scope
- rewriting the whole simulator
- arbitrary language migration for prestige

### Architecture guidance
- isolate only what needs acceleration
- keep authority boundaries explicit
- benchmark before and after

### Done when
- one native/mixed-runtime boundary exists with clear benefit and low semantic disruption

---

# 10. Step ordering rule

The intended sequence is:
- Step 30
- Step 31
- Step 32
- Step 33
- Step 34
- Step 35
- Step 36
- Step 37
- Step 38
- Step 39
- Step 40

No future step should begin before its prerequisites are complete unless the user explicitly overrides the plan.

---

# 11. What not to do

Do not let the project get trapped by:
- polishing the wrong viewer stack forever
- overbuilding traffic realism before motion/geometry foundations exist
- adding AI before the operator/system surfaces are informative enough
- optimizing performance before benchmarks and target workloads are clear
- rewriting the simulator core into a frontend or game-engine architecture
- confusing visually impressive with must become a game

Also avoid prematurely getting lost in:
- full physics
- full sensor simulation
- heavy RL/training-platform work
- giant external map/import pipelines
- productizing multiplayer or cloud deployment before the simulator is ready

These may become relevant later, but they are not the near-term focus.

---

# 12. Current completion estimate

Relative to the current expanded vision:

## Operations simulator core
Approximate completion: 65–75%

Reason:
- deterministic execution, control, replay, live session, sync, and benchmark foundations are already real

## Viewer/live interaction foundation
Approximate completion: 45–55%

Reason:
- real viewers, live actions, and live sync exist, but the serious frontend direction is not finalized

## High-realism motion / map / traffic environment
Approximate completion: 20–30%

Reason:
- the foundations are there, but continuous motion, richer road geometry, traffic realism, and richer operational scene context are still largely ahead

## AI-assisted operations layer
Approximate completion: 5–15%

Reason:
- the architecture can support it later, but the actual AI-assisted workflows are mostly still ahead

## Full target system
Approximate completion: 25–35%

Reason:
- the foundation is substantial
- the dream version is much larger than the original scope

---

# 13. Execution shorthand

If the user prompts:
- `step-30`

Codex must execute only Step 30 from this document.

If the user prompts:
- `step-34`

Codex must:
- verify that Steps 30–33 are complete
- if they are complete, work only on Step 34
- if they are not complete, explain the prerequisite issue and stop

If the user prompts:
- `step-37`

Codex must:
- verify that Steps 30–36 are complete
- if they are complete, work only on Step 37
- if they are not complete, explain the prerequisite issue and stop

This shorthand is intentional and should be treated as the normal workflow.
