# Autonomous Operations Sim — Architecture v2

## Purpose

This document defines ownership, truth boundaries, runtime contracts, and canonical derived surfaces for Autonomous Operations Sim.

It exists to keep the codebase centered on one rule:

**The Python simulator owns truth. Other layers consume, embody, present, or edit that truth through explicit contracts.**

## Core architecture

The system is organized as:

**world/scenario model → simulator runtime → command/session layer → derived surfaces → runtime clients / operator surfaces**

## Primary subsystems

1. World and Scenario Model
2. Simulator Runtime Core
3. Command and Live Session Layer
4. Derived Surface Layer
5. Runtime Clients and Operator Surfaces
6. Authoring / Research / Benchmark Extensions

## 1. World and Scenario Model

Owns:

- static world semantics
- scenario schema
- topology
- roads, lanes, zones, structures, terrain-like forms
- environment family and archetype
- authored/imported static scene representation

Must not own:

- live vehicle truth
- queue state
- reservations
- transient hazards/closures
- client selection state

## 2. Simulator Runtime Core

Owns:

- runtime vehicle truth
- routing truth
- traffic/conflict/reservation truth
- task/job execution
- deterministic progression
- metrics and trace inputs
- backend-owned Unity-ingested telemetry, progress, and embodiment history after ingestion

Must not own:

- client UI state
- local selection/highlight state
- speculative explanation state not grounded in runtime truth

## 3. Command and Live Session Layer

Owns:

- typed commands
- validation
- deterministic ordering
- play/pause/step semantics
- replayable command history
- runtime mutation path
- session-level motion authority selection

Must not allow:

- direct client mutation of simulator internals
- hidden route/vehicle truth outside commands

## 4. Derived Surface Layer

Owns:

- live bundle surfaces
- Unity bootstrap projection
- operator-facing read models
- replay/analysis read models
- command-center read models
- render-ready geometry projections
- structured summaries for clients and analysis

Must not own:

- competing runtime truth
- independent route truth
- independent motion logic

## Canonical derived surfaces

The intended long-lived derived surfaces are:

### Live session bundle core
Canonical for simulator/live state shared across operator-facing consumers.

### Unity bootstrap
Canonical for Unity runtime consumption.

This surface should expose nested canonical sections, not flat compatibility mirrors.

### `operator_state`
Canonical for operator-facing live inspection.

This is the operator-facing projection of Unity-influenced route progress, embodiment state, blockage state, and motion authority, as owned by Python.

### `replay_analysis`
Canonical for backend-owned replay and analysis.

This is derived from Python-owned history after Unity-originated signals have been ingested into backend runtime state.

## 5. Runtime Clients and Operator Surfaces

These are consumers and executors, not authorities.

### 5.1 Unity Runtime

Unity owns:

- 3D rendering
- transforms/orientation
- physics embodiment
- collision interaction
- terrain interaction
- future sensors and embodied AI runtime

Unity may be motion-authoritative for selected vehicles, but only inside a contract where Python still owns operational truth.

Unity must not own:

- topology truth
- dispatch/job logic
- reservation/conflict truth
- final command legality
- stable scenario truth
- task identity
- replay truth
- operator truth

### 5.2 Browser / Operator Surfaces

Operator-facing clients own:

- camera/viewport
- selection/highlight state
- local workflow state
- inspector/panel state
- command composition
- replay/analysis presentation

They must not own:

- runtime vehicle truth
- final route truth
- conflict truth
- topology truth
- Unity-only truth outside backend projections

## Motion authority model

The architecture supports two modes:

### Python motion authority

Python computes and advances motion.
Clients render the resulting state.

Use this mode for:

- deterministic fallback
- debugging
- sessions where full physics is unnecessary
- compatibility while Unity motion matures

### Unity motion authority

Python issues route/goal intent.
Unity executes embodied motion and reports telemetry back.
Python remains authoritative for task, routing legality, command truth, session truth, and replay truth.

Use this mode for:

- embodied vehicle motion
- terrain interaction
- collision-aware execution
- future autonomy/runtime experiments

### Requirement

Motion authority must be explicit.

The architecture should support:

- per-session authority selection first
- per-vehicle authority selection later

Telemetry must not silently become authoritative motion truth merely because it exists.

## Python ↔ Unity contract

Python sends:

- bootstrap world/state bundles
- route or target intent
- accepted commands
- future runtime constraints

Unity sends:

- telemetry
- route progress/completion events
- collision/blockage/exception events
- future sensor summaries where needed

All Unity-originated signals become meaningful only after ingestion into Python-owned runtime state.

## Transport principles

The bridge follows these rules:

1. Start simple.
2. Reuse existing HTTP/JSON patterns first.
3. Keep payloads versioned and explicit.
4. Avoid inventing a separate truth model just for Unity.

More complex transports are possible later, but must not change authority boundaries.

## Telemetry contract

Minimum telemetry includes:

- vehicle id
- x/y/z position
- speed
- timestamp

The bridge may also include:

- heading/rotation
- nearest node id or current edge id when known
- active target or route-progress state
- embodiment/blockage/exception state

Python must ingest Unity telemetry through one dedicated bridge/update path rather than scattering it into unrelated UI code.

## Route and command execution contract

Python remains the source of route and task intent.

Python issues:

- destination assignments
- route node sequences
- future route-segment permissions
- pause/stop/reposition commands

Unity executes:

- movement toward the current target point or waypoint
- local path embodiment over terrain/scene
- physical stopping and arrival detection

Unity reports:

- current telemetry
- route progress
- completion
- blocked/collision/failure events

## Environment/runtime assumptions

Unity must remain compatible with the shared world-model direction.
It must not hardcode a mine-only world.

Unity runtime assumptions should be:

- topology-driven, not environment-hardcoded
- world-form aware, not only waypoint-only
- capable of consuming scene/render/world surfaces derived from Python

## Truth matrix

- Static world truth: World Model
- Runtime vehicle truth: Simulator Runtime
- Command truth: Command Layer
- Live/read/replay projections: Derived Surface Layer
- Client interaction state: Runtime Clients
- Persistent edits: Authoring Layer

## Anti-patterns

Reject changes that create:

- frontend shadow truth
- Unity-only simulation truth disconnected from Python
- Unity-owned operator truth
- Unity-owned replay truth
- environment-specific architecture forks
- visual realism that contradicts runtime truth
- speculative multi-runtime sprawl without clear ownership
- reintroduced flat compatibility mirrors without a real consumer
- a separate long-lived Unity-only data model

## Final statement

Autonomous Operations Sim is a Python-authoritative simulation system with explicit command/session semantics, explicit motion authority, a canonical Unity bridge, backend-owned operator and replay surfaces, and runtime clients such as Unity that embody and present truth without replacing it.