
---

# `docs/world_model_v2.md`

# Autonomous Operations Sim — World Model v2

## Purpose

This document is the Phase B architecture note for the world-model boundary lock.

World Model v2 defines the unified internal representation for the environments Autonomous Operations Sim must support.

Its job is to make sure that:

* mining, construction yard, and city street scenes all fit one coherent model
* environment semantics are explicit instead of hacked into rendering or frontend logic
* the simulator can reason over topology, zones, tasks, traffic, hazards, and resources consistently
* authoring and import can converge into one internal scene representation later

This is the scene/world model the rest of the system should build on:

* simulator runtime
* render geometry generation
* frontend consumption
* editor/authoring
* import adapters
* hazards/weather/resource systems

The execution plan explicitly calls this out as a major foundational step: the project needs a stronger world/scene model before richer realism and editing can land cleanly, and that model must represent mining, yard, and city without hacks. 

## 0. Phase B boundary lock

World Model v2 is the simulator-owned source of truth for static world semantics.

It owns:

* scene identity and metadata
* environment family and archetype
* topology and spatial world structure
* zones, surfaces, structures, terrain-like forms, and operational anchors
* imported/authored static scene representation

It must not own:

* runtime vehicle truth
* live queue or congestion truth
* reservations or per-run closures
* frontend selection, viewport, or panel state
* render-only presentation state

The render-facing contract is separate:

* world model v2 describes what the world is
* render-ready geometry describes how the world is presented
* world-form rendering hints such as `form_type`, `height_hint`, and `depth_hint` remain simulator-derived and shared across environment families
* scene framing and spatial extents are derived from the shared world/render surfaces, not guessed locally by frontend consumers
* frontend adapters translate derived bundle surfaces into UI state

The frontend may consume the derived surfaces, but it must not become a competing authority for topology, route truth, or world truth.

## 0.1 Explicit terminology

Use these terms consistently:

* `world-model-v2`: the unified simulator-owned world semantics and static scene model
* `render-ready geometry`: derived geometry surfaces prepared for visualization and selection
* `frontend adapters`: consumer-side translators from derived bundles into presentable UI state
* `derived bundle surfaces`: backend-emitted read models for frontend, replay, analysis, and authoring consumers

Mine, yard, and city are all environment families inside the same world-model-v2 architecture.

---

## 1. Design goals

World Model v2 must satisfy five goals.

### 1.1 One model, multiple environment families

The same internal model must support:

* mine depot / haul-road environments
* construction yard environments
* city street environments

### 1.2 Explicit semantics

Important world concepts should be first-class and typed, not hidden in ad hoc names or frontend assumptions.

### 1.3 Separation of static and runtime truth

World Model v2 describes static scene structure and static environment semantics.
Per-run closures, queue states, reservations, active tasks, and transient congestion remain runtime state, not world-asset mutation. This matches the repo-wide architectural rule. 

### 1.4 Geometry and semantics together

The model must support both:

* geometric representation
* operational meaning

A polygon is not enough. A polygon should be able to mean:

* pit
* yard
* building footprint
* stockpile
* loading zone
* no-go zone
* hazard zone
  depending on semantics.

### 1.5 Extensible without environment forks

The model must not become:

* “mine world model”
* plus special-case yard add-ons
* plus special-case city logic

Environment differences should mostly be expressed through typed semantics, archetypes, and capabilities.

---

## 2. Core worldview

World Model v2 treats a scene as layered structure:

1. **Environment identity**
2. **Static topology**
3. **Spatial surfaces and zones**
4. **Structures and terrain forms**
5. **Operational semantics**
6. **Spawn/resource/task anchors**
7. **Presentation archetype metadata**

That means a scene is more than a graph and more than a rendered picture.

It is:

* a navigable structure
* an operational environment
* a renderable world
* a reusable authored/imported asset

---

## 3. Top-level scene structure

A scene should conceptually contain:

### 3.1 Scene metadata

* scene id
* name
* version/schema version
* description
* author/source metadata
* seed defaults
* tags

### 3.2 Environment identity

* environment family: `mine | construction_yard | city_street | other`
* environment archetype id
* optional scenario style/theme metadata
* optional presentation hints

### 3.3 Static world layers

* topology layer
* zone/surface layer
* structure/terrain layer
* operational anchor layer

### 3.4 Runtime bootstrap content

* initial vehicles
* initial jobs/tasks
* initial resource states
* initial closures/hazards if they are part of scenario initialization

---

## 4. Environment family model

World Model v2 should separate **environment family** from **scene content**.

### 4.1 Environment family

This identifies broad scene type:

* mine
* construction yard
* city street

It is useful for:

* validation expectations
* archetype defaults
* demo grouping
* import/export presets

It is **not** enough to drive simulation or rendering on its own.

### 4.2 Environment archetype

An archetype provides reusable semantics and defaults, such as:

* mine depot with haul roads, pits, crusher, stockpile areas
* yard with staging pads, unloading bays, forklift corridors
* city street with blocks, intersections, lanes, sidewalks, buildings

Known Phase B archetypes are expected to remain family-scoped and reusable:

* `mine` family: `mine_depot`, `legacy_mine_depot`
* `construction_yard` family: `construction_staging_yard`, `legacy_construction_yard`
* `city_street` family: `urban_delivery_corridor`, `legacy_city_street`

An archetype can influence:

* default zone meanings
* common structure types
* common vehicle classes
* default task/resource patterns
* render/presentation hints
* allowed world-form combinations

### 4.3 Shared taxonomy rule

Environment family and archetype do not replace the shared world-form taxonomy.
They only scope defaults and capability emphasis.

The same category names should mean the same things across mine, yard, and city, even when the underlying geometry differs.

### 4.4 Why this distinction matters

Environment family tells us what broad world we are in.
Archetype tells us what specific style/operational pattern that world uses.

This gives extensibility without hardcoding behavior to “mine mode” or “city mode.”

---

## 5. Static topology model

The topology layer remains the navigable structural backbone.

### 5.1 Nodes

Nodes should represent significant graph anchors such as:

* intersections
* endpoints
* depot anchors
* loading/unloading anchors
* staging anchors
* lane-connector anchors
* control points

Node data should support:

* id
* position
* type
* tags
* optional semantics references

### 5.2 Edges

Edges represent traversable graph connections.

Edge data should support:

* id
* start node
* end node
* distance
* nominal speed limit
* tags
* optional road/lane references

### 5.3 Roads

Roads are larger navigable units that may contain one or more lanes.

Road data should support:

* id
* edge membership
* centerline geometry
* class/type
* width
* directionality
* lane count if applicable
* road-role semantics

Examples:

* haul road
* service road
* city connector
* access road
* lane group host

### 5.4 Intersections / junctions

Intersections should be first-class topology features, not just node labels.

They should support:

* id
* node anchor(s)
* polygon/footprint
* intersection/junction type
* connected roads
* optional control semantics

### 5.5 Why topology still matters

Even as the world becomes more spatial and semantic, the graph/topology layer still underpins:

* routing
* conflict reasoning
* lane transitions
* stop/yield logic
* queue/corridor logic
* command targets

---

## 6. Lane and connector layer

The execution plan makes lane geometry a major later step, so World Model v2 must reserve clean space for it now. 

### 6.1 Lanes

A lane should be a first-class path-like object with:

* id
* parent road
* centerline
* width
* directionality
* role

Examples of lane roles:

* travel
* passing
* staging
* loading access
* unloading access
* turn-only
* merge-only

### 6.2 Turn connectors

A turn connector links lane-to-lane movement through intersections or complex transitions.

### 6.3 Stop lines

A stop line is a control-relevant geometric object linked to lanes/control points.

### 6.4 Merge zones

A merge zone is a structured region where multi-lane or converging behavior has semantic meaning.

### 6.5 Why these are separate

Lanes, connectors, stop lines, and merge zones should not be treated as frontend-only decorations. They should become part of the internal scene model because they feed:

* traffic realism
* queue behavior
* control logic
* merge/overtake semantics
* rendering

---

## 7. Surface and zone model

This is where the world stops being “just roads” and becomes an operational place.

### 7.1 Surface concept

A surface is a spatial region with geometric form and semantics.

Surfaces can represent:

* yard
* pad
* plaza
* loading zone
* unloading zone
* pit floor
* staging area
* no-go area
* hazard area
* sidewalk
* parking/service area
* stockpile region

### 7.2 Zone concept

A zone is a semantic/operational classification layered onto geometry.

A surface may be a zone. A structure may host a zone. A polygon may carry multiple semantic aspects.

### 7.3 Required surface/zone properties

A surface/zone should be able to express:

* id
* polygon/shape
* semantic type
* tags
* operational flags
* render-form hint
* occupancy/resource behavior hooks

### 7.4 Surface/zone examples

Mining:

* loading zone
* unloading zone
* pit floor
* stockpile
* haul staging area
* crusher zone

Construction yard:

* staging area
* material drop zone
* forklift corridor
* unloading bay
* work zone

City:

* building lot
* sidewalk
* parking/service area
* curbside load zone
* plaza/service surface

---

## 8. Structure and terrain-form model

World Model v2 must be able to describe things that are not just flat zones.

### 8.1 Structure concept

A structure is a spatial object with physical/world presence.

Examples:

* building
* shed
* warehouse
* crusher structure
* office
* yard facility
* city block massing

### 8.2 Terrain form concept

A terrain form is a spatial world feature whose shape matters.

Examples:

* pit
* berm
* stockpile
* hill
* embankment
* trench/cut
* mound
* wall/barrier

### 8.3 Form categories

At the world-model level, each structure/terrain feature should be expressible as one of:

* flat
* raised
* recessed

This does **not** mean the model should be limited to those three forever. It means those are the minimal reusable categories that let the renderer and simulator agree on broad world form.

### 8.4 Why this matters

The renderer needs a geometry-first way to understand:

* what reads as ground
* what reads as a raised mass
* what reads as a depression/pit
  without baking in environment-family-specific rendering logic.

---

## 9. Operational semantics layer

The same geometry can mean very different things operationally.
World Model v2 needs explicit semantic hooks for operations.

### 9.1 Traversability semantics

A feature may be:

* traversable
* conditionally traversable
* non-traversable
* traversable only by certain vehicle classes

### 9.2 Activity semantics

A feature may support:

* loading
* unloading
* staging
* queuing
* service access
* waiting
* parking/idling
* protected or restricted occupancy

### 9.3 Control semantics

A feature may participate in:

* stop control
* yield control
* signal/control logic
* protected conflict logic
* merge priority logic

### 9.4 Resource semantics

A feature may model:

* limited occupancy
* service capacity
* throughput bottlenecks
* contention rules

### 9.5 Hazard semantics

A feature may represent or host:

* hazard region
* caution region
* closure-capable region
* weather-affected region

---

## 10. Spawn, anchor, and task-point model

The world model must support operational anchors that connect geometry to runtime activity.

### 10.1 Vehicle spawn anchors

Used for:

* initial vehicles
* live vehicle spawning

### 10.2 Task anchors

Used for:

* job destinations
* pickup/dropoff points
* loading/unloading points
* staging anchors

### 10.3 Resource anchors

Used for:

* bays
* crusher feeds
* depots
* service points
* bottleneck resources

### 10.4 Why anchors matter

They let tasks and operations bind to stable world semantics instead of brittle raw-node-only assumptions.

---

## 11. Environment-semantic taxonomy

The world model should define a taxonomy broad enough to cover all three flagship families.

Below is a starting skeleton.

### 11.1 Road / mobility types

These are mobility-bearing world forms, not just drawable road shapes.

* haul_road
* service_road
* arterial_street
* local_street
* yard_path
* connector
* ramp
* access_lane
* lane
* turn_connector
* stop_line
* merge_zone

### 11.2 Intersection / junction types

These are control-relevant junction forms, including places where right-of-way or merge behavior matters.

* uncontrolled
* stop_controlled
* yield_controlled
* signal_ready
* merge_junction
* depot_gate
* yard_crossing
* control_point
* crossing
* junction

### 11.3 Zone / surface types

These are semantic operational surfaces. They may be flat, sloped, bounded, or partially enclosed.

* loading_zone
* unloading_zone
* staging_zone
* work_zone
* depot_zone
* parking_zone
* sidewalk_zone
* service_zone
* hazard_zone
* no_go_zone
* stockpile_zone
* pit_floor_zone
* pad_zone
* service_surface
* boundary_surface
* access_surface

### 11.4 Structure types

These are physical world objects with meaningful presence beyond a polygonal surface.

* building
* warehouse
* office
* crusher
* gatehouse
* wall
* barrier

### 11.5 Terrain form types

These are earth/grade forms whose shape matters to navigation, visibility, or operational behavior.

* berm
* stockpile
* hill
* mountain
* pit
* trench
* embankment
* cut
* basin
* retaining_wall

### 11.6 Anchor / operational point types

These are stable points or regions that connect world form to runtime activity.

* spawn_point
* task_point
* loading_point
* unloading_point
* service_point
* staging_point
* resource_point
* control_point

This taxonomy can evolve, but v2 should make these concepts natural rather than awkward.

---

## 12. Presentation hooks in the world model

The world model should support presentation without becoming renderer-owned.

### 12.1 Allowed presentation metadata

The world model may include:

* display labels
* presentation keys
* category tags
* optional palette/archetype hints
* render-form hints

### 12.2 Must not become

The world model should not be overloaded with:

* frontend-specific layout hacks
* direct UI panel instructions
* brittle theme-specific styling data
* fake labels that substitute for semantics

### 12.3 Rule

Presentation metadata may assist rendering.
It must not replace geometry or operational semantics.

---

## 13. Static vs runtime separation

This needs to be explicit.

## 13.1 Static world owns

* topology
* road/lane/intersection geometry
* zones/surfaces/structures/terrain
* archetype/environment semantics
* spawn/task/resource anchors
* persistent authored/imported scene content

## 13.2 Runtime owns

* closures
* hazards as transient live events unless encoded as scenario defaults
* active reservations
* queues
* congestion
* current task assignments
* current vehicle positions
* current resource occupancy
* live session state

This is non-negotiable and consistent with repo-wide architecture. 

---

## 14. World Model v2 and rendering

World Model v2 is not the renderer, but it must support rendering well.

### 14.1 Render geometry derivation

The world model should be able to derive or serialize:

* roads
* lanes
* intersections
* surfaces
* structures
* terrain forms
* anchor markers
* control features

### 14.2 Renderer expectations

The renderer should be able to consume world-derived geometry and know:

* what is ground
* what is road
* what is a raised form
* what is a recessed form
* what is selectable
* what is operationally important

### 14.3 Important rule

The renderer should not be forced to guess all environment semantics from labels.
World Model v2 should expose enough meaning that rendering and simulation stay aligned.

---

## 15. World Model v2 and simulation

The simulator should be able to use World Model v2 for:

* route graph construction
* lane graph construction
* control-point semantics
* hazard/weather modifiers
* resource/task anchoring
* occupancy rules
* vehicle-class restrictions
* bottleneck reasoning

World Model v2 should therefore not be “just for rendering.”

---

## 16. World Model v2 and authoring/import

This model must also serve as the convergence target for:

* hand-authored scenarios
* editor-generated scenes
* imported prototype scenes

That means the internal representation should be:

* editable
* serializable
* semantically stable
* not dependent on one ingestion path

This aligns directly with later execution-plan steps for authoring backbone, live editing, import groundwork, and convergence. 

---

## 17. Proposed conceptual schema skeleton

This is not final code schema, but the conceptual object layout should look something like:

### Scene

* metadata
* environment
* topology
* roads
* lanes
* intersections
* surfaces
* structures
* terrain_forms
* anchors
* resources
* initial_actors
* initial_tasks
* scenario_defaults

The implemented world-model surface v2 should expose a stable `feature_inventory` plus categorized `feature_groups` and layered feature views for roads, intersections, zones, structures, terrain forms, anchors, sidewalks, boundaries, and no-go areas.

### Environment

* family
* archetype_id
* tags
* presentation_hints

### Topology objects

* nodes
* edges

### Mobility objects

* roads
* lanes
* turn_connectors
* stop_lines
* merge_zones
* control_points

### Spatial objects

* surfaces
* structures
* terrain_forms
* no_go_areas
* hazard_regions

### Operational anchors

* spawn_points
* task_points
* loading_points
* unloading_points
* service_points
* staging_points

This is the right level of structure to guide schema design later.

---

## 18. Validation expectations

World Model v2 should support deterministic validation rules such as:

### Topology validation

* no invalid node/edge references
* no broken lane/road relationships
* no impossible connector references

### Geometry validation

* valid polygons
* non-empty centerlines where required
* reasonable structural consistency

### Semantic validation

* allowed zone/structure/terrain types
* valid environment-family usage
* anchor references resolve
* resource/task anchors attach to meaningful world features

### Cross-layer validation

* loading/unloading anchors belong to valid zones
* road/lane/intersection/control relationships are coherent
* non-traversable areas are not mistakenly encoded as route graph edges

---

## 19. Acceptance criteria for World Model v2

World Model v2 is good enough when:

1. one mining scene can be represented cleanly
2. one yard scene can be represented cleanly
3. one city street scene can be represented cleanly
4. these scenes all fit the same internal structure
5. lanes/connectors/control features have obvious places to live
6. surfaces/structures/terrain have explicit semantics
7. authored and future imported scenes can plausibly converge into this model
8. runtime state is still clearly separate from static world data

This matches the execution plan’s explicit acceptance direction for the unified world/scene model step. 

---

## 20. Open questions to fill in

These are the most important remaining design questions for this doc.

### 20.1 Semantic taxonomy

Which zone, structure, and terrain types must be first-class in v2 versus left extensible?

### 20.2 Terrain depth

How much actual elevation/height semantics need to exist in the internal model versus render-time approximation?

### 20.3 Lane granularity

What lane detail is required for mining first, before city-street requirements expand the model?

### 20.4 Resource model linkage

How tightly should resources/bottlenecks attach to surfaces versus anchors versus tasks?

### 20.5 Import convergence

What minimum normalized representation must all imported scenes map into?

---

## Final statement

World Model v2 should make the scene a real operational world rather than a graph plus some decorative polygons.

It should provide:

* one unified internal scene language
* explicit semantics for topology, zones, structures, terrain, and anchors
* a clean bridge to simulation, rendering, editing, and import
* enough flexibility to support mining first without trapping the project inside mining-only assumptions

---
