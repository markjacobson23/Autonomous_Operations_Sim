# Autonomous Operations Sim — Execution Plan
# Phase A Only: Frontend v2 Product Completion

## Purpose

This plan covers **only Phase A**.

Phase A is responsible for delivering a **good** Frontend v2 product foundation, not a partial cleanup of the old UI.

At the end of this phase, the serious frontend must be:

- map-first
- calm by default
- operationally useful
- selection-driven
- previewable
- trustworthy
- presentation-worthy

This phase must cover the full Frontend v2 scope:
- app shell
- map shell
- scene renderer
- camera/minimap/layers
- selection/popup/inspector
- Operate mode
- Traffic mode
- Fleet mode
- Editor mode baseline
- Analyze mode baseline
- command center
- plan/preview workflow
- visual system and polish
- frontend ownership and data-contract discipline

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
Frontend must not own:
- runtime vehicle truth
- final route truth
- conflict/reservation truth
- topology truth
- deterministic progression semantics

### 2. Frontend remains derived
Frontend state, panels, overlays, and workflows must remain derived from simulator truth and explicit preview/command surfaces.

### 3. Frontend v2 is map-first
The map is the primary product surface.
Panels support the map and must not dominate it.

### 4. Mining is the primary acceptance environment
Validate this phase against a live mining scenario.
Keep the frontend architecture environment-agnostic.

### 5. This phase is product-first
Do not spend this phase on deep simulator realism work unless a small backend seam is strictly required to complete Frontend v2 well.

---

## Out of scope for this phase

Do not use this phase for:
- deep lane behavior realism
- advanced kinematics
- deep hazard/weather simulation
- advanced AI suggestions
- native performance work
- broad import support
- backend/read-model expansion that does not directly improve Frontend v2

---

## Definition of done

Phase A is done only when all of these are true:

### Baseline map milestone
- live bundle renders
- map supports pan/zoom/fit/focus
- minimap works
- quiet-default contract is real
- roads, vehicles, and environment form are readable
- selection works reliably

### Operational milestone
- inspector is useful
- route preview works
- commands can be sent
- session controls work
- operator can use the UI without raw-ID-first flow

### Frontend-v2 coverage milestone
- Operate mode is real
- Traffic mode is real
- Fleet mode is real
- Editor mode baseline is real
- Analyze mode baseline is real

### Product milestone
- layout feels intentional
- map remains primary
- panels do not fight the map
- UI is screenshot-worthy
- mining live walkthrough is externally presentable

If any of those are false, the phase is not done.

---

## Execution rules

### Rule 1
If prompted with `step-x`, do only that step.

### Rule 2
Do not prebuild later simulator realism systems unless the current step needs a small compatible seam.

### Rule 3
Each step must produce:
- code
- tests where applicable
- visible product gain
- a clear validation path

### Rule 4
Do not accept “better than before” as success.
Accept only “good enough to be the real frontend foundation.”

### Rule 5
Do not create frontend shadow truth for convenience.

---

# Step plan

## Step 41 — Frontend v2 architecture and repo layout
**Goal:** Lock the frontend-v2 path, boundaries, and structure.

### Scope
- define where Frontend v2 lives
- define app-shell / map-shell / renderer / interaction / panels / adapters boundaries
- define frontend-owned state vs simulator-owned truth
- define replacement strategy for the old serious UI path

### Deliverables
- frontend-v2 architecture note
- repo layout decision
- frontend-v2 scaffold
- boundary notes

### Must not do
- no speculative feature-building
- no heavy polish work
- no half-old / half-new ambiguous structure

### Done when
- there is one clear frontend-v2 home
- there is one clear ownership model
- there is no ambiguity about shadow truth

---

## Step 42 — Live launch path and app shell
**Goal:** Make Frontend v2 launchable and give it a real shell.

### Scope
- built-in live launch path
- frontend bootstrap against a live session
- app shell with:
  - header
  - environment/session identity
  - connection state
  - global alerts/status
  - mode switching
  - map-dominant layout

### Deliverables
- live launch command/path
- app shell
- connection/session status surfaces

### Must not do
- no stacked-card shell
- no map-secondary layout
- no throwaway placeholder look

### Done when
- one command opens a live mining scenario in Frontend v2
- shell feels intentional
- map is visually primary

---

## Step 43 — Frontend data adapters and local state model
**Goal:** Build the adapter layer and local state ownership model.

### Scope
- bundle-to-UI adapters
- local state for:
  - camera/viewport
  - scene mode/layers
  - selection/highlight
  - popup state
  - inspector state
  - planning workflow state
  - mode/panel state
  - editor gesture state

### Deliverables
- adapter layer
- typed local state model
- tests around ownership boundaries where useful

### Must not do
- no frontend-owned runtime truth
- no local route/conflict truth masquerading as authority

### Done when
- frontend state ownership is clean
- data flow is predictable
- no accidental shadow truth patterns remain

---

## Step 44 — Map shell, camera, minimap, and layer controls
**Goal:** Build the reusable map shell.

### Scope
- pan
- zoom
- fit scene
- focus selected
- minimap
- scene modes (Iso/Birdseye)
- map controls
- layer controls

### Deliverables
- map shell
- camera/navigation controls
- minimap
- layer control surface

### Must not do
- no fragile camera behavior
- no minimap as separate analytics card
- no layer system that is required just to make the map readable

### Done when
- large scenes are navigable comfortably
- minimap is integrated and useful
- controls feel stable and product-like

---

## Step 45 — Scene renderer and quiet-default map
**Goal:** Build the default visual contract of Frontend v2.

### Scope
- quiet-default map
- roads readable
- vehicles readable
- environment/world form readable
- restrained overlays
- debug layers separated from the default experience

### Deliverables
- renderer baseline
- default visibility contract
- tests for quiet-default behavior

### Must not do
- no always-on node labels
- no always-on place labels
- no always-on vehicle labels
- no clutter that requires turning things off to understand the scene

### Done when
- the map is calm by default
- the map is readable at a glance
- the default view feels product-grade, not debug-grade

---

## Step 46 — Selection, popup, and inspector
**Goal:** Make direct inspection reliable and useful.

### Scope
- click-to-select:
  - vehicles
  - roads
  - lanes where applicable
  - queues/conflict areas where applicable
  - hazards where applicable
  - environment surfaces/areas where applicable
  - route previews
- compact popup
- inspector updates
- selection highlighting

### Deliverables
- hit testing
- popup
- inspector baseline
- tests for moving-object selection and inspector updates

### Must not do
- no giant popup covering the map
- no inspector data dump
- no fragile selection that breaks on motion

### Done when
- moving vehicles remain selectable
- selected state is obvious
- popup stays compact
- inspector answers operator questions quickly

---

## Step 47 — Operate mode completion
**Goal:** Complete Operate mode as the heart of the product.

### Scope
- live scene watching
- selected-object inspection
- route preview
- command execution entry point
- compact live session controls
- queue/hazard awareness
- multi-vehicle awareness

### Deliverables
- real Operate mode
- operate-specific layout and panel behavior

### Must not do
- no form-first console UX
- no stacked panels dominating the map
- no raw-ID-first main workflow

### Done when
- Operate mode is coherent and map-first
- the map remains primary
- panels support rather than compete with the map

---

## Step 48 — Command center and typed command workflows
**Goal:** Build the command center as a real operator surface.

### Scope
- typed command entry
- destination assignment
- reposition
- block/unblock road
- pause/play/step
- clear result/error feedback

### Deliverables
- command center surface
- typed command plumbing
- feedback surfaces

### Must not do
- no separate-console feel
- no command workflow detached from selection/map context
- no fake success state before authoritative confirmation

### Done when
- commands can be issued cleanly through Frontend v2
- results are understandable
- the command center composes naturally with the map and selection state

---

## Step 49 — Plan list and route preview workflow
**Goal:** Complete the map-first planning model.

### Scope
- select vehicle
- select destination/target
- create plan entry
- preview route/consequence
- select a plan entry to highlight route
- commit command

### Deliverables
- compact plan list/stack
- route preview visualization
- preview details:
  - destination
  - path
  - distance
  - actionability
  - conflicts/reservations where available
  - likely wait/congestion context where available

### Must not do
- no raw-ID-first primary planning flow
- no frontend-owned fake route truth
- no preview flow that is harder to understand than the old form

### Done when
- the golden operator loop works end-to-end
- preview is understandable
- commit is understandable
- result is visible in the scene

---

## Step 50 — Traffic mode baseline
**Goal:** Build the dedicated Traffic mode surface.

### Scope
- inspect queues
- inspect congestion
- inspect control points where available
- inspect selected traffic context
- surface traffic without polluting Operate default view

### Deliverables
- Traffic mode
- traffic panel/surfaces
- traffic-specific selection/inspection behavior

### Must not do
- no traffic clutter baked into default Operate view
- no cosmetic heatmap with weak operational meaning

### Done when
- operators can understand flow issues without cluttering the default map
- Traffic mode adds real value

---

## Step 51 — Fleet mode baseline
**Goal:** Build the dedicated Fleet mode surface.

### Scope
- single-select and multi-select support
- visible fleet selection state
- fleet roster/summary
- grouped vehicle context
- early bounded batch-action affordance hooks

### Deliverables
- Fleet mode
- fleet panel
- selection management UI

### Must not do
- no fake fleet mode that is just another inspector
- no invisible or confusing multi-select state

### Done when
- fleet state is understandable
- multi-select is real and visible
- Fleet mode is useful before later deeper fleet operations work

---

## Step 52 — Editor mode baseline
**Goal:** Build the Frontend v2 editor mode surface.

### Scope
- dedicated Editor mode
- geometry edit affordance placeholders or baseline hooks
- validation message surface
- save/reload flow surface
- clear visual distinction from Operate mode

### Deliverables
- Editor mode shell
- validation UI
- save/reload UI hooks

### Must not do
- no Operate-mode pollution
- no fake edit mode with nowhere for authoring to live later

### Done when
- editor mode feels intentionally different
- authoring has a real UI home
- the frontend is ready for later authoring work

---

## Step 53 — Analyze mode baseline
**Goal:** Build the Analyze mode surface.

### Scope
- explanation-oriented panel
- anomaly surfacing baseline
- route comparison context where available
- diagnostics aggregation baseline

### Deliverables
- Analyze mode
- analysis panel
- explanation/anomaly UI baseline

### Must not do
- no speculative AI magic
- no Analyze mode that compensates for weak Operate/Inspector design

### Done when
- Analyze mode has a real role
- it feels grounded in simulator truth
- it gives later explanation/anomaly work a real product home

---

## Step 54 — Visual system and product polish
**Goal:** Make Frontend v2 presentation-worthy.

### Scope
- cohesive visual language
- calm default palette
- spatial clarity
- compact readable panels
- consistent hierarchy
- reduced prototype feel
- consistent interaction states and transitions

### Deliverables
- tokens/styles/polish pass
- panel hierarchy cleanup
- overlay cleanup
- popup/minimap/control polish

### Must not do
- no “we’ll polish later”
- no incoherent mix of old and new visual systems

### Done when
- UI is screenshot-worthy
- layout feels intentional
- visual language is cohesive

---

## Step 55 — Phase A acceptance walkthroughs
**Goal:** Prove Phase A is actually complete.

### Required walkthroughs

#### A. Baseline map walkthrough
1. launch live mining scenario
2. orient quickly
3. pan/zoom/fit/focus
4. use minimap
5. confirm quiet default map

#### B. Inspection walkthrough
1. select moving vehicle
2. inspect it
3. select road/queue/hazard context
4. inspect it
5. keep map readable throughout

#### C. Golden operator workflow
1. select vehicle
2. select destination
3. create preview
4. inspect preview
5. commit command
6. observe result

#### D. Mode walkthrough
1. Operate mode
2. Traffic mode
3. Fleet mode
4. Editor mode
5. Analyze mode

### Deliverables
- working walkthroughs
- validation notes
- any final polish fixes required to make the walkthroughs credible

### Must not do
- no “technically passes but embarrassing to show”
- no moving on because later phases sound more fun

### Done when
- all walkthroughs feel coherent, grounded, readable, and product-grade

---

# Validation checklist

## Architecture
- Is frontend ownership clear?
- Is there any shadow truth?

## Shell
- Is the shell intentional and map-first?
- Are session/status/mode surfaces coherent?

## Map
- Is the default map quiet?
- Are roads, vehicles, and environment form readable?
- Do minimap and controls feel integrated?

## Selection and inspection
- Can moving vehicles be selected reliably?
- Does popup stay compact?
- Does inspector answer useful questions?

## Operate workflow
- Does the golden operator loop work?
- Is preview map-first?
- Is command feedback understandable?

## Mode coverage
- Does each Frontend v2 mode have a real UI home?
- Are Traffic/Fleet/Editor/Analyze credible baselines rather than empty placeholders?

## Product quality
- Does the UI still feel prototype-grade anywhere in the main workflow?
- Would you be comfortable showing the mining Phase A walkthrough externally?

If any answer is “no,” Phase A is not done.

---

## What comes after Phase A

Only after Phase A is complete should the project move on to:
- deeper world model work
- richer environment-form semantics
- lane geometry
- motion realism
- traffic realism
- hazard and diagnostic depth
- later AI/operator assistance depth

Later phases should improve a good frontend, not rescue a bad one.
