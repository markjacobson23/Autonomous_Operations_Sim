# Unity Hybrid Simulation — Design / Spec

## Purpose

This document defines the target design for a **hybrid simulation architecture** where:

- **Python remains the authoritative simulator and operations backend**
- **Unity becomes the 3D runtime client for world rendering, physics, and eventually sensor/AI work**

The goal is not to replace the current Python simulator.
The goal is to extend it with a Unity-based execution layer that can support:

- believable 3D vehicle motion
- terrain-aware movement
- collision/physics interactions
- richer scene presence
- future sensor simulation
- future ML/AI control experiments

while preserving the existing strengths of the Python codebase:

- deterministic command/control
- routing
- job/dispatch logic
- reservation/conflict logic
- structured runtime/export surfaces
- stable scenario-driven workflows

---

## Relationship to the current project plan

This spec is a **future-facing architecture note** that must stay compatible with the current project direction.

The current execution plan states that:

- Python remains authoritative
- the frontend remains a consumer of simulator-derived truth
- Phase B focuses on world model / render foundation, not deep motion realism

This Unity work must therefore be treated as:

- an extension of simulator authority, not a transfer of authority away from Python
- a consumer/executor of simulator-issued intent
- a realism/3D runtime layer that depends on a stronger world/render foundation

This spec should guide future Unity integration work without violating the existing simulator ownership boundaries.

---

## Design goals

### Primary goals

1. Preserve **Python authority** for operations and simulator truth.
2. Use Unity as a **3D execution/runtime client** rather than a second simulator brain.
3. Support a gradual migration from Python-only motion to Unity-executed motion.
4. Keep the system usable before full realism lands.
5. Build toward eventual sensor simulation and ML experimentation.

### Secondary goals

- better visual and spatial intuition during simulation
- believable vehicle motion over 3D terrain
- reusable architecture for mine / yard / city style environments
- future support for multiple vehicle embodiments and controllers

---

## Non-goals

This phase/spec does **not** require:

- replacing routing with Unity navigation
- moving dispatch logic into Unity
- moving job logic into Unity
- moving reservation/conflict logic into Unity
- making Unity the source of topology truth
- immediately implementing full wheel/terrain realism
- immediately implementing ML-Agents or autonomous control models

---

## Existing Python capabilities to preserve

The current Python codebase already provides a strong simulator/control foundation.
Unity integration should be built around these existing capabilities, not around a fresh rewrite.

### 1. Live runtime / session control
The Python app already has a local HTTP-driven live runtime model with:

- scenario bootstrapping
- session progression
- play/pause/step controls
- command application
- route preview support

This currently lives in the live app/server path.

### 2. Stable structured export surfaces
The backend already builds structured JSON surfaces such as:

- replay bundle
- live session bundle
- live sync bundle

These already separate concepts like:

- metadata
- map/topology surface
- render geometry
- runtime snapshot
- command results
- motion segments
- traffic surfaces
- command center surfaces

This is the natural starting point for a Unity-facing bridge.

### 3. Deterministic routing and command logic
The Python code already supports:

- route computation
- destination assignment
- vehicle spawn/reposition/remove
- job injection
- blocked edges / hazards
- deterministic control application

### 4. Runtime vehicle model
The runtime vehicle model already tracks:

- vehicle id
- current node id
- position
- velocity
- payload/max payload
- max speed
- behavior / operational state
- vehicle type

This is enough to support a Unity-controlled embodiment while keeping Python-side identity and task state.

### 5. World/render foundation work
The project is already moving toward a cleaner world model and render geometry contract.
That work is directly useful for Unity because Unity will need:

- topology truth
- world feature truth
- render-facing geometry truth
- stable ids
- environment semantics

---

## Current limitations in Python-only motion

The current simulator still performs runtime motion itself.
In the current design, Python can:

- arm routes
- advance active routes over simulated time
- interpolate along edges
- update vehicle positions directly
- complete route segments/nodes internally

This is useful and should remain available as a fallback mode.
However, it means Unity cannot yet be the motion authority for a vehicle without an explicit architecture seam.

---

## Target hybrid architecture

## Core rule

**Python remains authoritative for operational intent and simulator truth.**

**Unity becomes authoritative only for physical execution details of selected runtime entities.**

### Python owns

- topology truth
- world/model truth
- route computation
- dispatch/job logic
- reservation/conflict truth
- scenario loading
- simulator command semantics
- stable ids and object identity
- session/playback state
- final operational acceptance/rejection of commands

### Unity owns

- 3D scene rendering
- transforms/orientation
- rigidbody/physics motion
- collision interaction
- terrain interaction
- future sensor simulation
- future embodied control loops
- future ML/AI environment execution

### Shared contract

Python sends:

- world bootstrap data
- route/target intent
- allowed movement permissions / command acknowledgements
- future state constraints

Unity sends:

- vehicle telemetry (position/orientation/speed)
- completion/progress signals
- collision/exception events
- future sensor summaries if needed

---

## Motion authority model

The system should explicitly support at least two motion modes:

### Mode A — Python motion authority
Current/default mode.

Python:

- computes routes
- advances vehicles along routes
- updates positions directly

Unity:

- renders received positions only

Use this mode for:

- current product stability
- deterministic fallback
- debugging
- scenarios where full physics is unnecessary

### Mode B — Unity motion authority
Target hybrid mode.

Python:

- computes route/goal intent
- validates command legality
- maintains operational/task truth
- consumes telemetry updates

Unity:

- physically moves the vehicle
- updates real pose/orientation
- reports progress and telemetry back to Python

Use this mode for:

- 3D embodied motion
- terrain interaction
- collision handling
- future autonomy experiments

### Requirement

The architecture must support per-session and eventually per-vehicle motion authority selection.

---

## Minimum viable Unity runtime responsibilities

The first Unity runtime must be intentionally small.
It does not need to be a full game/simulator immediately.

### Phase 1 responsibilities

Unity should be able to:

1. load a bootstrap payload from Python
2. instantiate one or more runtime vehicle representations
3. move a vehicle toward a Python-provided target/route point
4. post telemetry back to Python
5. show the world in 3D with basic camera control

### Phase 2 responsibilities

Unity should additionally be able to:

- instantiate route waypoint objects from backend topology
- follow multi-point routes
- keep vehicle-to-vehicle identity stable
- report route progress
- report completion/failure conditions

### Phase 3 responsibilities

Unity should additionally be able to:

- operate over terrain/mesh-based world form
- use Rigidbody-based motion where desired
- support collisions and obstacle interaction
- emit richer telemetry and events

### Phase 4 responsibilities

Unity should additionally be able to:

- host virtual sensors
- serve as an embodied runtime for learned/AI controllers
- support multiple vehicle embodiments
- support replay/live mixed inspection workflows

---

## Unity-side object model

The initial Unity scene should be organized around a few clear concepts.

### SimulationManager
Owns:

- Python connection/bootstrap
- runtime entity registry
- telemetry scheduling
- command polling/refresh
- scene-level coordination

### VehicleController
Owns per-vehicle:

- target/route following
- local movement logic
- transform updates
- future rigidbody interaction
- telemetry extraction

### WorldBootstrapLoader
Owns:

- parsing topology/world/bootstrap payloads
- instantiating waypoint or feature markers
- future environment geometry instantiation

### CameraController
Owns:

- operator/developer camera movement
- follow/focus convenience

The first implementation can combine some of these, but this is the intended separation.

---

## Python ↔ Unity transport design

### Transport principles

1. Start simple.
2. Reuse existing HTTP/JSON patterns first.
3. Keep payloads versioned and explicit.
4. Avoid inventing a completely separate truth model just for Unity.

### Phase 1 transport

Use HTTP/JSON.

#### Python → Unity

- `GET /bundle` or equivalent bootstrap endpoint
- returns a structured bundle-like payload

#### Unity → Python

- `POST /telemetry`
- sends current vehicle telemetry

This is sufficient for the first round-trip prototype.

### Later transport options

Once the contract is stable, the system may move selected flows to:

- polling + incremental updates
- server-sent updates
- WebSockets
- gRPC or other lower-latency transport

But transport sophistication should come **after** schema and ownership are proven.

---

## Unity-facing payload design

Unity should eventually consume a backend payload derived from the same simulator surfaces already exposed by Python.

### Bootstrap payload should include

- metadata/schema version
- map/world/model identity
- render geometry / world geometry reference data
- runtime vehicle snapshot
- pending route/target intent
- optionally scene framing hints

### Minimal example shape

```json
{
  "metadata": {
    "surface_name": "unity_bootstrap",
    "surface_schema_version": 1
  },
  "snapshot": {
    "vehicles": [
      {
        "vehicle_id": 1,
        "position": [0.0, 0.5, 0.0],
        "operational_state": "MOVING"
      }
    ]
  },
  "command_center": {
    "targets": [
      {
        "vehicle_id": 1,
        "target_position": [8.0, 0.5, -3.0],
        "speed": 2.5
      }
    ]
  }
}
```

### Preferred long-term direction

Do not maintain a separate ad hoc Unity payload forever.
Unity should consume a projection derived from existing backend bundle concepts.

---

## Telemetry contract

Unity must report telemetry back to Python in a stable format.

### Minimum telemetry fields

- vehicle id
- x/y/z position
- speed
- timestamp

### Soon after

Add:

- heading/rotation
- current edge id or nearest node id if known
- route progress / active target id
- collision flag / blocked flag

### Example telemetry shape

```json
{
  "vehicle_id": 1,
  "x": 3.2,
  "y": 0.5,
  "z": -1.4,
  "speed": 2.5,
  "time_s": 14.7
}
```

### Python-side handling

Python should ingest Unity telemetry into a dedicated bridge/update path rather than directly scattering it through unrelated UI-facing code.

---

## Route / command execution contract

Unity must not invent its own independent tasks.
Python remains the source of task/route intent.

### Python issues

- destination assignment
- route node sequence
- future route segment permissions
- pause/stop/reposition commands

### Unity executes

- movement toward current target point / waypoint
- local path embodiment over terrain/scene
- physical stopping/arrival detection

### Unity reports back

- current telemetry
- target reached
- route segment entered/completed
- blocked/collision/failure events

---

## Environment/world requirements for Unity

The Unity sim must be compatible with the project’s world-model direction.
It should not hardcode a mine-only world.

### Required support

- mine-like environments
- yard/depot environments
- city/road-network environments

### Therefore Unity runtime assumptions must be

- topology-driven, not environment-hardcoded
- world-form aware, not only waypoint-only
- capable of consuming scene/render/world surfaces from Python

### First implementation can be visually simple

The first Unity runtime can represent:

- roads as simple segments
- areas as flat surfaces
- vehicles as cubes/placeholders
- waypoints as invisible transforms

But the contract must allow later richer geometry.

---

## Phased implementation plan

## Phase 0 — Learning / spike
Already effectively underway.

Deliverables:

- one Unity scene
- one movable object
- JSON file loading
- HTTP target loading
- telemetry POST back to Python

Success criteria:

- Unity can consume backend state and send state back

## Phase 1 — Toy bridge with simulator-shaped payloads

Deliverables:

- mini bundle bootstrap endpoint
- Unity bundle parser
- stable vehicle id mapping
- telemetry loop

Success criteria:

- Unity no longer depends on ad hoc one-field target payloads

## Phase 2 — Real Python live-session bootstrap

Deliverables:

- derive Unity bootstrap from real simulator session/bundle surfaces
- spawn runtime vehicles from actual simulator data
- ingest simulator-issued route/destination intent

Success criteria:

- Unity can represent a real scenario loaded by Python

## Phase 3 — Motion authority seam

Deliverables:

- explicit motion authority mode
- Python-authoritative mode still works
- Unity-authoritative mode available for selected vehicles/sessions
- telemetry ingestion path updates runtime vehicle state safely

Success criteria:

- the same scenario can run in either Python-motion or Unity-motion mode

## Phase 4 — Route following and terrain embodiment

Deliverables:

- waypoint/route following in Unity
- route progress events
- terrain-aware movement
- richer vehicle representation

Success criteria:

- Unity-controlled vehicles can complete backend-issued routes while Python retains operational control

## Phase 5 — Physics and collision semantics

Deliverables:

- Rigidbody or equivalent motion where appropriate
- collision event reporting
- blocked/failure feedback into Python

Success criteria:

- Unity can surface physically meaningful execution outcomes to Python

## Phase 6 — Sensor / AI extension

Deliverables:

- optional sensor simulation
- optional ML runtime hooks
- future autonomy experimentation support

Success criteria:

- Unity can act as an embodied experimental environment without replacing simulator authority

---

## Risks and architectural traps

### 1. Splitting truth between Python and Unity
This is the main risk.

Avoid by keeping Python authoritative for:

- ids
- task state
- command legality
- route intent
- scenario truth

### 2. Replacing working Python motion too early
Do not delete or break current Python motion before Unity motion mode is stable.
Python motion should remain the fallback path.

### 3. Building a Unity-only data model
Unity should consume a backend projection, not define a second incompatible simulation contract.

### 4. Overbuilding transport too early
Do not jump to complex transport before payload shape and ownership are proven.

### 5. Hardcoding mine-specific semantics
The Unity runtime must remain environment-agnostic at the architecture level.

---

## Acceptance criteria for the hybrid architecture

The hybrid architecture is viable when all of the following are true:

### Round-trip viability
- Python can issue target/route intent
- Unity can execute it visually/physically
- Unity can report telemetry back to Python

### Authority clarity
- Python remains authoritative for operational truth
- Unity owns only embodied execution details
- no competing truth emerges for route/task identity

### Compatibility
- existing Python-only simulation path still works
- current live/session workflows are not broken
- the world/render foundation remains reusable across environments

### Extensibility
- the design can later support terrain, collisions, sensors, and AI
- the architecture does not require a rewrite to scale from cube demo to real vehicle runtime

---

## Immediate next implementation target

The next meaningful implementation target should be:

1. replace the toy target payload with a simulator-shaped bootstrap payload
2. parse that payload in Unity
3. preserve stable vehicle ids
4. continue posting telemetry back to Python
5. begin designing the explicit motion authority seam in Python

That sequence preserves project momentum while minimizing architectural risk.

---

## Summary

The desired Unity simulation is **not** a replacement simulator.
It is a **3D embodied execution layer** for the existing Python simulator.

The intended long-term split is:

- **Python**: operations brain, authoritative truth, routing, dispatch, commands, world truth
- **Unity**: physical body, 3D scene, motion embodiment, collisions, terrain, sensors, future AI runtime

The system should evolve incrementally from:

- Python-only motion
- to Python-issued targets with Unity rendering
- to Unity-executed motion with Python operational authority
- to richer embodied environments suitable for realistic and experimental autonomy work

without ever losing clarity about where truth lives.
