# Autonomous Operations Sim — World Model v2

## Purpose

World Model v2 defines the simulator-owned static world representation for Autonomous Operations Sim.

It exists to ensure that mining, construction yard, and city street scenes fit one coherent model and that static world semantics remain separate from runtime truth.

## Core rule

World Model v2 owns **static world semantics**.

It owns:

- scene identity and metadata
- environment family and archetype
- topology
- roads, lanes, connectors, intersections
- surfaces, zones, structures, terrain-like forms
- operational anchors
- authored/imported static scene representation

It must not own:

- runtime vehicle truth
- live queue/congestion state
- reservations
- transient closures/hazards
- client selection or viewport state
- render-only presentation state

## Design goals

1. One model for multiple environment families  
2. Explicit semantics rather than hacks  
3. Clear separation between static and runtime truth  
4. Support for both geometry and operational meaning  
5. Extensibility without environment-specific architecture forks  

## Top-level scene structure

A scene contains:

- scene metadata
- environment identity
- static topology
- surfaces and zones
- structures and terrain forms
- operational anchors
- runtime bootstrap content where needed

## Environment families

World Model v2 must support:

- mining
- construction yard
- city street

Environment family does not change the architecture.
It only scopes defaults, archetypes, and common semantics.

## Static topology

The topology layer includes:

- nodes
- edges
- roads
- intersections/junctions
- future lane/connector structures where relevant

Topology remains the structural backbone for routing and command targets.

## Surfaces and zones

The model must support semantic surfaces such as:

- loading zones
- unloading zones
- staging areas
- pit floors
- no-go zones
- hazard-prone surfaces
- sidewalks
- parking/service areas
- work zones

A surface is not just geometry.
It must be able to carry operational meaning.

## Structures and terrain forms

The model must support:

- buildings
- yards
- crushers
- depots
- pits
- berms
- stockpiles
- other structure-like or terrain-like forms

These are simulator-owned semantic world features, not purely client-side rendering tricks.

## Operational anchors

The model must support anchors for:

- vehicle spawn
- job/task association
- loading/unloading interaction
- resource interaction
- staging/depot semantics

## Derived geometry relationship

World Model v2 does not directly define client rendering.

Instead:

- world model defines what the world is
- derived geometry defines how the world is presented
- clients consume that derived geometry without inventing competing world truth

## Success standard

World Model v2 is good when:

- mine, yard, and city scenes fit one structure
- static world semantics are explicit
- render and runtime layers can consume the model predictably
- later realism work does not require another world-model rewrite