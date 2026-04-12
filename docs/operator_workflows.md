
---

# `docs/operator_workflows.md`

# Autonomous Operations Sim — Operator Workflows

## Purpose

This document defines the human workflows Frontend v2 and the broader system must support.

It answers:

* what operators actually need to do
* what information they need before acting
* what the system should show during and after action
* which workflows are primary versus secondary
* what “good” looks like at the workflow level

This is not a component spec and not a step list.
It is a product and interaction spec focused on operator behavior.

The roadmap already makes clear that live operator interaction is a major missing capability and a central target of the next major phase. 

---

## 1. Workflow philosophy

Operator workflows should follow five rules.

### 1.1 Map first

The map is the main operational surface.
The operator should not need to leave the map mentally in order to act.

### 1.2 Selection before form entry

Primary workflows should start from selecting real things in the world:

* vehicle
* road
* hazard
* destination
* route
* queue
* environment object

Raw IDs may exist for debug or advanced tools, but they should not be the default operator path.

### 1.3 Preview before commitment

Where actions may materially affect routing or flow, the operator should be able to preview consequences before committing.

### 1.4 Explanation nearby

When the system asks the operator to decide, it should show the relevant state close to the decision:

* why a vehicle is waiting
* why a route is blocked
* why a queue is building
* why a suggestion is being made

### 1.5 Frontend is not authority

The workflow may compose decisions locally, but command truth and runtime effect remain simulator-authoritative. 

---

## 2. Primary operator persona

The primary operator persona for this product is not a developer debugging internals.

The operator is someone who needs to:

* monitor a live scenario
* understand vehicles and traffic conditions quickly
* intervene when needed
* inspect problems
* reroute or reassign
* manage hazards and congestion
* trust what the UI says

This persona may be:

* a mining operations operator
* a dispatch coordinator
* a yard/fleet manager
* a scenario demonstrator
* a researcher running controlled operational tests

The product should support technical users, but should not assume developer-mode workflow by default.

---

## 3. Workflow categories

The system should support six major workflow categories.

1. **Observe**
2. **Inspect**
3. **Plan**
4. **Act**
5. **Mutate**
6. **Analyze**

These categories often overlap, but they are useful for keeping the product disciplined.

---

## 4. Observe workflows

Observe workflows are about fast situational understanding.

## 4.1 Workflow: Open and orient to a live scenario

### Goal

The operator opens a scenario and quickly understands:

* what environment this is
* where vehicles are
* what is moving
* what areas matter
* whether anything is obviously wrong

### Inputs

* live session launch or reconnect
* current bundle/snapshot

### Operator actions

* open live scenario
* pan/zoom if needed
* glance at map, minimap, and high-level status surfaces

### System should show

* environment/map clearly
* vehicles clearly
* quiet default map
* session status
* compact operational summary if useful

### Good outcome

The operator understands the scene in seconds, not minutes.

---

## 4.2 Workflow: Watch live movement

### Goal

The operator can follow vehicles and traffic behavior in real time.

### Operator actions

* watch map
* focus selected vehicle if desired
* use minimap/fit/zoom as needed

### System should show

* believable movement
* readable vehicle identity
* readable queues/congestion when present
* no overwhelming label clutter

### Good outcome

The operator can visually track important motion without constant inspection clicks.

---

## 4.3 Workflow: Monitor emerging issues

### Goal

The operator notices problems early.

### Operator actions

* observe map and alerts/anomaly surfaces
* shift to a selected road/queue/vehicle when something seems wrong

### System should show

* queue growth
* blocked roads/hazards
* stalled vehicles
* diagnostics/warnings
* anomaly callouts where appropriate

### Good outcome

The operator notices congestion, stoppage, or hazard effects before everything becomes confusing.

---

## 5. Inspect workflows

Inspect workflows answer “what is this doing and why?”

## 5.1 Workflow: Inspect a vehicle

### Goal

Learn what a vehicle is, what it is doing, and why.

### Operator actions

* click a vehicle on the map

### System should show

* highlight on map
* compact popup and/or inspector update
* vehicle identity
* state
* current route/task
* wait reason if waiting
* control detail if relevant
* ETA / heading / speed where helpful
* diagnostics/warnings where available

### Good outcome

The operator can answer:

* what is this vehicle doing?
* where is it headed?
* why is it stopped or delayed?

This is already a core roadmap milestone: moving vehicles must remain selectable and feed the inspector reliably. 

---

## 5.2 Workflow: Inspect a road, lane, or queue

### Goal

Understand a traffic problem at the infrastructure level.

### Operator actions

* click road/lane/queue overlay or congested segment

### System should show

* selected road or queue context
* queue count / congestion level
* connected control semantics where relevant
* relevant vehicle IDs/counts
* possible blockage/hazard relation

### Good outcome

The operator can understand whether the problem is:

* queue buildup
* blocked route
* merge bottleneck
* control delay
* spillback risk

---

## 5.3 Workflow: Inspect a hazard

### Goal

Understand what is blocked or hazardous and what it is affecting.

### Operator actions

* click hazard/blocked region/road

### System should show

* hazard location and scope
* affected road/edge/zone
* related vehicles or routes if available
* whether the hazard is causing slowdown, closure, or caution behavior

### Good outcome

The operator understands the operational consequence, not just the geometry.

---

## 5.4 Workflow: Inspect a selected route preview

### Goal

Understand what a planned route would do before committing.

### Operator actions

* click a plan entry or selected preview path

### System should show

* highlighted route
* destination
* distance
* actionability
* reservation/conflict context where available
* likely reason for failure if non-actionable

### Good outcome

The operator can answer:

* is this route valid?
* is it safe/actionable?
* what will it affect?

---

## 6. Plan workflows

Plan workflows are about forming an intended action before committing.

## 6.1 Workflow: Plan a vehicle destination

### Goal

Assign a vehicle to a destination through map-first interaction.

### Operator actions

* select vehicle
* select destination/place/target
* create plan entry
* inspect preview
* commit

### System should show

* selected vehicle
* selected destination
* plan entry in a compact list
* route preview on the map
* route details in popup/inspector

### Good outcome

No raw-ID-first interaction is necessary for the primary path.

---

## 6.2 Workflow: Compare route options or outcomes

### Goal

Understand whether one command choice is better than another.

### Operator actions

* generate one or more previews
* inspect each preview
* compare distance/conflicts/actionability

### System should show

* distinguishable plan entries
* selected preview emphasis
* comparison-friendly route details
* warnings/conflicts if relevant

### Good outcome

The operator can make an informed decision rather than trial-and-error command submission.

---

## 6.3 Workflow: Prepare a fleet action

### Goal

Stage a bounded multi-vehicle action.

### Operator actions

* multi-select vehicles
* choose destination/resource/action
* preview fleet-relevant effects where feasible
* commit

### System should show

* selected fleet summary
* selected fleet states
* grouped preview info if available
* clear confirmation of intended scope

### Good outcome

The operator knows exactly which vehicles are affected and what the command intends to do.

---

## 7. Act workflows

Act workflows are about issuing commands that mutate live runtime behavior.

## 7.1 Workflow: Commit destination/route assignment

### Goal

Apply a previewed route command.

### Operator actions

* commit from plan entry or command surface

### System should show

* pending/accepted/rejected command feedback
* authoritative response/result
* updated runtime state once the bundle refreshes

### Good outcome

The operator sees:

* what was submitted
* whether it succeeded
* what changed

---

## 7.2 Workflow: Reposition a vehicle

### Goal

Move a vehicle to a new node/location through an explicit control action.

### Operator actions

* select vehicle
* choose reposition target through workflow surface
* confirm reposition

### System should show

* affected vehicle
* target
* result/error
* updated vehicle location after authoritative update

### Good outcome

Repositioning is explicit, bounded, and clearly visible.

---

## 7.3 Workflow: Block or unblock a road

### Goal

Temporarily alter infrastructure availability.

### Operator actions

* select road/edge/hazard-relevant object
* choose block/unblock action
* confirm

### System should show

* what is being blocked/unblocked
* route/traffic impact if previewable
* result/error
* affected map state after update

### Good outcome

The operator can intentionally change route availability and immediately understand the new state.

---

## 7.4 Workflow: Play, pause, and step a session

### Goal

Control live simulation progression.

### Operator actions

* play
* pause
* step

### System should show

* current play state
* step interval if relevant
* visible world updates in sync with authority

### Good outcome

The operator can examine behavior carefully without leaving the product.

The roadmap explicitly includes this as a core serious-UI command capability later. 

---

## 8. Mutate workflows

Mutate workflows change the running scenario, not just immediate routing.

## 8.1 Workflow: Spawn a vehicle

### Goal

Add a vehicle during a live run.

### Operator actions

* choose spawn type
* choose spawn point or target location
* confirm spawn

### System should show

* spawn request context
* validation/result
* newly visible vehicle in scene once applied

### Good outcome

The operator can change live fleet composition in a controlled way.

---

## 8.2 Workflow: Remove a vehicle

### Goal

Remove a vehicle during a live run.

### Operator actions

* select vehicle
* choose remove action
* confirm

### System should show

* target vehicle
* confirmation
* command result
* disappearance of vehicle after authoritative update

### Good outcome

The operator can intentionally remove a vehicle with clear feedback.

---

## 8.3 Workflow: Inject a job/task

### Goal

Add meaningful new work during a scenario.

### Operator actions

* choose task/job parameters
* associate with relevant destination/resource
* submit

### System should show

* job intent
* affected vehicles/resources if relevant
* result/error
* visible operational consequences later

### Good outcome

The operator can create new work without destabilizing the session.

---

## 8.4 Workflow: Declare or clear a hazard

### Goal

Add or remove a temporary operational disruption.

### Operator actions

* choose hazard target and semantics
* submit
* optionally clear later

### System should show

* hazard identity/location
* operational effect
* result/error
* visible world/traffic consequences

### Good outcome

Hazards become a live operational tool, not just static scene decoration.

The roadmap explicitly includes this kind of live mutation as a major later milestone. 

---

## 9. Analyze workflows

Analyze workflows are about understanding causes, anomalies, and consequences.

## 9.1 Workflow: Explain why a vehicle is waiting

### Goal

Get a grounded reason for delay.

### Operator actions

* select waiting vehicle
* inspect details or explanation panel

### System should show

* wait reason
* related control/conflict/queue context
* route/context explanation
* diagnostic/warning context if relevant

### Good outcome

The operator gets a useful reason, not just “waiting.”

The roadmap explicitly calls out this explanation goal for later AI refinement. 

---

## 9.2 Workflow: Understand congestion or queue buildup

### Goal

Understand not just where congestion is, but why.

### Operator actions

* select congested road/queue area
* expand traffic/analyze details as needed

### System should show

* queue length/intensity
* nearby control or merge factors
* blockage/hazard relation
* deadlock or spillback context if relevant

### Good outcome

The operator can distinguish between:

* ordinary density
* controllable bottleneck
* hazard-induced slowdown
* structural deadlock risk

---

## 9.3 Workflow: Review anomalies or AI suggestions

### Goal

Understand suggested actions or warnings without surrendering authority.

### Operator actions

* open anomaly/suggestion
* inspect rationale
* optionally act on it

### System should show

* grounded reason
* affected vehicles/roads
* suggested next step
* link to relevant map selection or route preview

### Good outcome

Suggestions feel like operational help, not magical guesses.

---

## 10. Editor workflows

These workflows apply when the user is editing authored/imported scenes.

## 10.1 Workflow: Edit geometry

### Goal

Change a road, area, node, or zone and keep the scene valid.

### Operator actions

* enter editor mode
* select geometry
* drag/edit handles
* inspect validation
* save/reload

### System should show

* edit handles
* modified geometry
* validation messages
* draft-versus-saved state
* save result

### Good outcome

Scene editing is structured, visible, and deterministic.

---

## 10.2 Workflow: Validate and save a scene

### Goal

Persist scene changes safely.

### Operator actions

* review edit summary
* validate
* save
* reload or rerun

### System should show

* what changed
* validation warnings/errors
* successful persistence state
* updated scene on reload

### Good outcome

No mystery mutations. No silent invalid scenes.

---

## 11. Workflow success criteria by category

## 11.1 Observe

The operator can orient to a scenario quickly.

## 11.2 Inspect

The operator can explain current state without hunting through raw data.

## 11.3 Plan

The operator can preview meaningful action before committing.

## 11.4 Act

Commands can be issued confidently and results are clearly surfaced.

## 11.5 Mutate

The operator can safely alter the live scenario through bounded explicit actions.

## 11.6 Analyze

The operator can understand delays, anomalies, and suggested actions in grounded terms.

---

## 12. Primary workflow priority order

These workflows matter most and should be considered top-tier product workflows.

### Tier 1

* open and orient to live scenario
* inspect vehicle
* preview route
* commit destination command
* play/pause/step
* inspect queue/congestion

### Tier 2

* block/unblock road
* fleet selection and fleet action
* inject job/task
* spawn/remove vehicle
* inspect hazard effects

### Tier 3

* editor geometry workflow
* anomaly/suggestion review
* richer comparative route analysis
* import/edit/save convergence flow

This priority ordering keeps the product grounded in operator usefulness before expanding into every possible feature.

---

## 13. Workflow anti-patterns

Reject product changes that push workflows toward:

### 13.1 Raw-ID-first operation

The operator must translate map understanding into arbitrary IDs for common actions.

### 13.2 Inspector as a dump

Selection shows too much unstructured data instead of answering operator questions.

### 13.3 No-preview commitment

High-impact actions are committed blindly when preview is feasible.

### 13.4 Hidden command effects

The operator submits commands but cannot clearly see what changed or why a command failed.

### 13.5 Dashboard-over-map

Panels and cards dominate so much that the map stops being the primary operating surface.

### 13.6 AI without grounding

Explanations or suggestions appear without clearly relating to simulator state.

These anti-patterns are especially important because the execution plan warns against false peaks where backend/UI surfaces expand without materially improving operator workflow. 

---

## 14. Open workflow questions

These should be filled in later as the product sharpens.

### 14.1 Planning workflow

Should all route planning go through a persistent plan list, or should there also be a quick-commit path?

### 14.2 Popup versus inspector

What minimum info belongs in the map popup versus the side inspector?

### 14.3 Fleet UX

What is the minimum viable multi-select/batch workflow that is worth supporting early?

### 14.4 Hazard UX

What is the best operator model for declaring hazards: geometry-first, road-first, or zone-first?

### 14.5 Analyze/AI UX

How should explanation and anomaly surfaces integrate with the inspector without creating clutter?

---

## Final statement

The product is on the right path when an operator can:

* understand a live scene quickly
* inspect what matters
* preview meaningful changes
* commit actions confidently
* mutate the scenario when needed
* understand why the system is behaving the way it is

If those workflows feel smooth, grounded, and map-first, then the frontend and simulator are working together the way this project intends.

---
