
---

# `docs/frontend_v2.md`

# Autonomous Operations Sim — Frontend v2

## Purpose

Frontend v2 defines the target serious UI for Autonomous Operations Sim.

Its job is to describe:

* what the frontend is for
* what it owns
* what it must never own
* what the operator experience should feel like
* what the major UI surfaces are
* how map, inspection, planning, commands, editing, and analysis should fit together

This document is not a step plan and not a component inventory for one sprint.
It is the intended product and interaction architecture the frontend should grow toward.

The execution plan already locks in that a stronger separate frontend path is expected and preferred when it materially improves UI quality. Frontend v2 assumes that direction. 

---

## 1. Frontend v2 thesis

Frontend v2 should be a **map-first operator product**, not a debug viewer.

A user should be able to:

* open a live scenario
* understand the world visually
* inspect moving vehicles and traffic conditions
* preview and commit commands
* mutate the live scenario in bounded ways
* edit geometry when in authoring mode
* understand why things are happening
* trust that everything visible is derived from simulator truth

The frontend should feel closer to:

* a polished operational map product
  than to:
* a graph debugger
* a command console with a map attached
* a dashboard pasted on top of an SVG

---

## 2. Core frontend principles

## 2.1 Map first

The map is the primary surface.
Everything else exists to support map-based understanding and action.

## 2.2 Progressive disclosure

The UI should stay quiet by default.
Details should appear when:

* something is selected
* a route is previewed
* a layer is explicitly enabled
* the operator enters a specific workflow

No constant label spam.
No always-on debug clutter.

## 2.3 Frontend as consumer

Frontend v2 owns interaction and presentation, but it must not own:

* runtime vehicle truth
* authoritative route truth
* conflict/reservation truth
* hidden topology mutation semantics

This is already a locked architectural rule. 

## 2.4 Product feel matters

The frontend should be presentation-worthy.
The execution plan explicitly identifies frontend/product quality as one of the biggest remaining gaps. 

## 2.5 One frontend architecture for multiple environments

Frontend v2 must work for:

* mining
* construction yard
* city street

without environment-specific forks in the product model.

---

## 3. Frontend v2 product goals

Frontend v2 should eventually satisfy five product goals.

### 3.1 Readability

A user can quickly answer:

* what world am I looking at?
* where are the vehicles?
* what is moving?
* what is blocked?
* where is congestion building?

### 3.2 Inspectability

A user can click a thing and learn:

* what it is
* what it is doing
* why it is doing it
* what matters about it right now

### 3.3 Commandability

A user can issue meaningful commands through the frontend, not only observe.

### 3.4 Mutability

A user can perform bounded live changes and later editing tasks through explicit validated flows.

### 3.5 Trustworthiness

The frontend never feels like it is inventing reality.
It presents simulator-derived truth cleanly and consistently.

---

## 4. Primary user modes

Frontend v2 should support several major modes, even if they are phased in over time.

## 4.1 Operate mode

Primary live operational mode.

Main activities:

* watch the live system
* inspect vehicles/roads/queues/hazards
* preview and commit commands
* manage fleet activity
* respond to emerging issues

## 4.2 Traffic mode

Focused traffic and congestion understanding.

Main activities:

* inspect queues
* inspect congestion
* inspect control points
* inspect deadlock risk/conflict areas
* understand traffic bottlenecks

## 4.3 Fleet mode

Focused vehicle/fleet management.

Main activities:

* multi-select vehicles
* inspect roles/status
* issue batch actions
* inspect diagnostics and warnings
* compare current assignments

## 4.4 Editor mode

Authoring and scenario geometry editing mode.

Main activities:

* move/edit geometry
* validate scene changes
* save/reload
* inspect authoring errors
* work with imported/authored scenes through one interface

## 4.5 Analyze mode

Diagnostics and explanation mode.

Main activities:

* inspect why something happened
* inspect anomalies
* inspect AI explanation/suggestion surfaces
* compare routes, bottlenecks, or warning signals

These align with the broader direction of the current serious shell and roadmap, but Frontend v2 should reorganize them around a cleaner product model. 

---

## 5. Top-level frontend layout

Frontend v2 should be organized as a serious application shell, but the layout should always remain subordinate to the map.

The intended layout should conceptually be:

### 5.1 App shell

Contains:

* app header
* environment/session identity
* connection state
* top-level mode switching
* global alerts/status

### 5.2 Main map region

The primary visual and interaction surface.

### 5.3 Secondary panels

Contextual, not dominant:

* inspector
* plan/command panel
* traffic details
* fleet details
* editor details
* analysis/AI details

### 5.4 Utility surfaces

* minimap
* layer controls
* session controls
* notification/alert toasts
* validation surfaces when editing

### Layout rule

The map should always remain visually primary in Operate mode.

---

## 6. Core map contract

Frontend v2’s map should have a very explicit default contract.

## 6.1 Quiet default

Default map should show:

* world/environment form
* roads and lanes where appropriate
* vehicles
* only essential context

Default map should not show:

* always-on place labels
* always-on node IDs
* always-on vehicle labels
* always-on destination labels
* oversized explanatory chrome

## 6.2 Map camera

Frontend v2 should support:

* pan
* zoom
* fit scene
* focus selected
* minimap navigation
* at least two major camera modes, such as Iso and Birdseye

## 6.3 Selection

Clicking something should:

* highlight it
* open a compact popup and/or inspector update
* keep the map readable

## 6.4 Layer system

The frontend should support explicit layer toggles, but they should be secondary tools, not the main reading path.

Potential layers:

* roads
* lanes
* vehicles
* routes
* traffic
* hazards
* reservations/conflicts
* editing overlays
* debug layers

## 6.5 Minimap

The minimap should live inside the map region and feel like part of the product, not a separate analytics card.

---

## 7. Map interaction model

The map interaction model should be simple and predictable.

## 7.1 Primary gestures

* click to select
* pan
* zoom
* minimap recenter
* hover only where useful

## 7.2 Selection targets

At minimum, the frontend should support selecting:

* vehicles
* roads
* lanes where relevant
* intersections/control points
* queues/conflict areas
* hazards
* environment surfaces/areas
* route previews

## 7.3 Selection result

Selection should update:

* map highlight
* compact popup
* inspector panel
* context-sensitive command or planning affordances

## 7.4 Debug separation

Debug detail should exist, but it should live behind:

* debug mode
* explicit toggle
* editor mode
* inspector detail expansion

It should not be the default operator experience.

---

## 8. Operate mode design

Operate mode is the heart of the product.

## 8.1 Primary goal

Let an operator understand and influence a live scenario through the map.

## 8.2 Operate mode must support

* live scene watching
* selected-object inspection
* route preview
* command execution
* compact live session control
* queue/hazard awareness
* multi-vehicle awareness

## 8.3 Planning workflow target

The preferred planning model should be map-first:

* select vehicle
* select destination / target
* create plan entry
* preview route/consequence
* commit command

Not:

* type raw IDs into the main workflow

## 8.4 Operate mode visual rule

The page should feel like:

* large map
* compact inspector
* compact planning/command surface
* minimal session controls

Not:

* stacked cards dominating the map

---

## 9. Inspector design

The inspector is the main “what is this and what is happening” surface.

## 9.1 Inspector should support

* vehicle inspection
* road/lane inspection
* queue/congestion inspection
* hazard inspection
* route preview inspection
* environment object/surface inspection

## 9.2 Vehicle inspection fields

Eventually:

* id / display name
* class/type
* operational state
* position/context
* route ahead
* current task/job
* wait reason
* control detail
* diagnostics/warnings
* ETA / speed / heading where relevant

## 9.3 Road/traffic inspection fields

Eventually:

* road/lane identity
* road class/type
* queue count
* congestion level
* active vehicles
* control state
* conflict/reservation context

## 9.4 Inspector behavior

The inspector should be:

* compact by default
* expandable for deeper detail
* selection-driven
* capable of linking to related actions

---

## 10. Command center design

The command center should become a real operator surface, not a loose set of form inputs.

The execution plan explicitly calls for promotion of command execution into the serious UI later in the roadmap. 

## 10.1 Command center should support

* destination assignment
* route preview
* reposition
* block/unblock road
* pause/play/step
* hazard declaration/clearing
* spawn/remove vehicle
* job/task injection
* fleet/batch actions later

## 10.2 Command design rules

Commands should be:

* typed
* explicit
* previewable where appropriate
* validated through backend surfaces
* accompanied by result/error feedback

## 10.3 UX rule

The command center should compose naturally with the map and selection state.

It should not feel like a separate console requiring the operator to translate the map back into raw IDs for basic use.

---

## 11. Route preview and plan workflow

This is important enough to define explicitly.

## 11.1 Route preview goals

Before committing a route-related command, the frontend should be able to show:

* path
* destination
* distance
* actionability
* conflicts/reservations where available
* likely wait/congestion context where available

## 11.2 Planning surface

The frontend should eventually have a compact plan list/stack that can show:

* pending plan
* active preview
* committed plan state
* relevant route details

## 11.3 Preview interaction

Selecting a plan entry should highlight the relevant path on the map and update the inspector.

---

## 12. Fleet UX

The roadmap explicitly calls for multi-select and fleet workflows later. Frontend v2 should reserve clean product space for that now. 

## 12.1 Fleet selection

Must support:

* single-select
* multi-select
* visible selection state
* clear selection management

## 12.2 Fleet actions

Eventually:

* bounded batch routing/assignment
* batch hazard response
* batch operational control where sensible

## 12.3 Fleet surfaces

The frontend should be able to show:

* fleet roster
* selected fleet state summary
* grouped diagnostics
* grouped route/context summary

---

## 13. Traffic UX

Traffic UX should help an operator understand flow, not just decorate roads.

## 13.1 Traffic surfaces should support

* queue visibility
* congestion heat or state visibility
* selected queue inspection
* stop/yield/control visibility
* deadlock/conflict surfacing later

## 13.2 Traffic UX rule

Traffic should be inspectable and explorable without overwhelming the default map.

It should appear:

* through selection
* through explicit traffic mode
* through relevant route preview context
* through anomalies/alerts

---

## 14. Editor UX

Frontend v2 must also leave room for authoring.

The roadmap explicitly calls for authoring backbone and live editing later, so the product model should anticipate it. 

## 14.1 Editor mode should support

* geometry handle editing
* validation messages
* save/reload flow
* edit transaction visibility
* imported/authored scene convergence

## 14.2 Editor rule

Editor mode should feel intentionally different from Operate mode.
It can surface more handles and semantic detail because it is not the primary operator view.

---

## 15. Analyze / AI UX

This should sit on top of strong simulator truth, not compensate for weak base workflows.

## 15.1 Analyze surfaces should support

* why-is-it-waiting explanations
* anomaly surfacing
* route comparison context
* diagnostics aggregation
* later suggestion panels

## 15.2 AI rule

AI explanations and suggestions must always feel grounded in simulator truth, not speculative UI invention. This is already a locked repo rule.  

---

## 16. Visual language

Frontend v2 should establish one cohesive visual language.

## 16.1 Visual goals

* calm by default
* spatially clear
* operationally readable
* modern/product-quality
* consistent across mining, yard, and city

## 16.2 Map style goals

* world feels spatial
* roads are readable
* vehicles are readable
* overlays are restrained
* labels appear intentionally, not constantly

## 16.3 Panel style goals

* compact
* legible
* non-dominant versus map
* expandable for deeper info
* consistent information hierarchy

## 16.4 Product bar

The frontend should become “presentation-worthy,” which the execution plan explicitly names as an important milestone. 

---

## 17. Frontend ownership model

Frontend v2 should clearly own:

* camera/viewport
* map mode/layer state
* selection/highlight state
* popup state
* inspector panel state
* local planning workflow state
* local draft form state
* top-level layout and navigation
* editor gesture state

Frontend v2 should not own:

* authoritative runtime vehicle state
* final route truth
* conflict truth
* topology truth
* deterministic progression semantics

---

## 18. Frontend architectural layers

Conceptually, the frontend should be split into layers such as:

### 18.1 App shell layer

Owns:

* navigation
* top-level layout
* global status/alerts
* mode switching

### 18.2 Map shell layer

Owns:

* map region orchestration
* minimap
* layer controls
* map controls
* popup placement
* map-specific local state

### 18.3 Scene renderer layer

Owns:

* visual rendering of world-derived geometry
* vehicles
* routes
* hazards
* overlays
* selection highlights

### 18.4 Interaction/controller layer

Owns:

* hit testing
* selection plumbing
* map gestures
* preview interactions
* editor gesture routing

### 18.5 Workflow panels

Owns:

* inspector
* command center
* plan list
* traffic panel
* fleet panel
* editor panel
* analyze/AI panel

### 18.6 Frontend view-model adapters

Owns:

* translating bundle surfaces into renderable/presentable UI data
* no shadow runtime truth

This layered split should keep the frontend from turning into one giant component pile.

---

## 19. Frontend data contract

Frontend v2 should consume:

* live simulation bundle
* replay/export bundle
* command/session endpoints
* route-preview endpoint
* authoring validation/save/reload endpoints when in editor mode

Frontend v2 should send:

* typed commands
* route preview requests
* validated editing actions or transactions

Frontend v2 should not send:

* direct runtime mutations
* direct world-state patching outside validated paths

---

## 20. Frontend acceptance milestones

Frontend v2 should eventually satisfy these milestones.

## 20.1 Baseline map milestone

* live bundle renders
* map supports pan/zoom
* roads and vehicles visible
* selection works
* compact popup works
* minimap works
* map is quiet by default

## 20.2 Operational milestone

* inspector is useful
* route preview works
* commands can be sent
* session controls work
* operator can use UI without raw-ID-first flow

## 20.3 Realism milestone

* world form is readable
* vehicle motion is believable
* queues/congestion are readable
* hazards/control logic are visually understandable

## 20.4 Product milestone

* layout feels intentional
* panels do not fight the map
* UI is screenshot-worthy
* mining live demo feels externally presentable

---

## 21. Anti-patterns for Frontend v2

Reject frontend changes that move toward:

### 21.1 Debug-first map

Always-on labels, always-on node IDs, and giant overlay clutter as the primary experience.

### 21.2 Form-first command UX

Primary workflows that require typing raw IDs when map selection should suffice.

### 21.3 Frontend shadow truth

Local route/vehicle/conflict state that diverges from authoritative backend truth.

### 21.4 Panel bloat

The map becomes secondary to stacked cards, summaries, and placeholder content.

### 21.5 Environment forks

Separate frontend architectures for mining, yard, and city rather than one shared map/product model.

---

## 22. Open questions to fill in

These are the main unresolved frontend-v2 design questions.

### 22.1 Operate workflow

What exact command/planning flow should be primary in V2?

### 22.2 Selection model

What belongs in popup versus inspector versus panel tabs?

### 22.3 Traffic mode

How much traffic information should be available in the default Operate view versus dedicated Traffic mode?

### 22.4 Fleet UX

What is the minimum viable batch/fleet workflow before it becomes overbuilt?

### 22.5 Editor separation

How distinct should editing feel from operating, visually and interaction-wise?

---

## Final statement

Frontend v2 should be a serious, map-first operator application that:

* renders simulator truth clearly
* supports live inspection and command workflows
* stays quiet by default and detailed on demand
* scales across mining, yard, and city scenes
* never becomes a competing authority layer

It should be the product surface that makes the simulator feel usable, convincing, and real.

---
