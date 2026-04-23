# Autonomous Operations Sim — Architecture v2

## Purpose

This document defines ownership, truth boundaries, and runtime contracts for Autonomous Operations Sim.

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

Must not allow:

- direct client mutation of simulator internals
- hidden route/vehicle truth outside commands

## 4. Derived Surface Layer

Owns:

- replay/export surfaces
- live bundle surfaces
- inspection read models
- command-center read models
- render-ready geometry projections
- structured summaries for clients and analysis

Must not own:

- competing runtime truth
- independent route truth
- independent motion logic

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

## Motion authority model

The architecture must support two modes:

### Python motion authority
Python computes and advances motion.
Clients render the resulting state.

### Unity motion authority
Python issues route/goal intent.
Unity executes embodied motion and reports telemetry back.
Python remains authoritative for task, routing legality, command truth, and session truth.

## Python ↔ Unity contract

Python sends:

- bootstrap world/state bundles
- route or target intent
- permissions / accepted commands
- future runtime constraints

Unity sends:

- telemetry
- progress/completion events
- collision/blockage events
- future sensor summaries where needed

## Truth matrix

- Static world truth: World Model
- Runtime vehicle truth: Simulator Runtime
- Command truth: Command Layer
- Render/read models: Derived Surface Layer
- Client interaction state: Runtime Clients
- Persistent edits: Authoring Layer

## Anti-patterns

Reject changes that create:

- frontend shadow truth
- Unity-only simulation truth disconnected from Python
- environment-specific architecture forks
- visual realism that contradicts runtime truth
- speculative multi-runtime sprawl without clear ownership

## Final statement

Autonomous Operations Sim is a Python-authoritative simulation system with explicit command/session semantics, a derived-surface layer for safe consumption, and runtime clients such as Unity that embody and present truth without replacing it.