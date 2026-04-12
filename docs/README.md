# Autonomous Operations Sim — Design Docs

This folder contains the high-level design set for the next major phase of Autonomous Operations Sim.

These docs exist to answer a simple question:

**What is this codebase supposed to become, and how do we keep implementation aligned with that target?**

They are meant to complement, not replace, the step-by-step execution plan.

## How these docs fit with the repo plan

The authoritative implementation roadmap remains:

- `docs/execution_plan.md`

That file defines:
- execution order
- step boundaries
- what is locked now
- what should and should not be implemented at each stage

This design set exists to support that plan by making the intended end-state clearer.

The repo’s locked direction is:

- Python simulator remains authoritative
- frontend and AI surfaces remain derived from simulator truth
- a stronger serious frontend is expected and preferred for UI quality
- mining remains the flagship acceptance environment
- construction yard and city street must fit the same architecture
- native acceleration remains narrow and benchmark-justified :contentReference[oaicite:1]{index=1}

## Recommended reading order

If you want the big picture first:

1. `target_vision.md`  
   What the project is trying to become.

2. `capability_spec.md`  
   What the codebase must eventually be able to do.

3. `architecture_v2.md`  
   Which subsystem owns what, and how truth flows through the system.

4. `world_model_v2.md`  
   The unified internal world model for mining, yard, and city scenes.

5. `frontend_v2.md`  
   What the serious frontend should be, own, and feel like.

6. `operator_workflows.md`  
   The human workflows the product must support well.

7. `acceptance_demos.md`  
   The concrete demo scenarios that should prove the system is actually good.

If you are doing implementation work, also keep `execution_plan.md` open.

## Document guide

### `target_vision.md`
Defines the project’s intended identity and north star.

Use this when asking:
- What is the point of this project?
- What kind of product/system are we building?
- What should it feel like when it is good?

### `capability_spec.md`
Defines the capability-level requirements.

Use this when asking:
- What must the codebase eventually support?
- What areas are in scope?
- What counts as a real capability versus a partial prototype?

### `architecture_v2.md`
Defines subsystem ownership and truth boundaries.

Use this when asking:
- Should this live in the simulator, frontend, derived surfaces, or authoring layer?
- Who owns runtime truth?
- Is this creating shadow truth or crossing a boundary incorrectly?

### `world_model_v2.md`
Defines the unified scene/world model.

Use this when asking:
- How should mining, yard, and city fit one internal model?
- Where do roads, lanes, zones, structures, terrain, and anchors belong?
- What is static world structure versus runtime state?

### `frontend_v2.md`
Defines the target serious frontend.

Use this when asking:
- What should the frontend actually be?
- What does the map-first product model look like?
- What should the operator experience feel like?

### `operator_workflows.md`
Defines the workflows the product must support.

Use this when asking:
- What should an operator be able to do smoothly?
- What should happen before, during, and after commands?
- What information should appear for inspection, planning, and analysis?

### `acceptance_demos.md`
Defines the concrete proof scenarios.

Use this when asking:
- How will we know the system is actually good?
- What does the flagship mining demo need to show?
- What proves the architecture extends beyond mining?

## How to use this folder during implementation

### If you are planning work
Start with:
- `target_vision.md`
- `capability_spec.md`
- `architecture_v2.md`

Then read:
- `execution_plan.md`

### If you are working on world/model/schema changes
Start with:
- `world_model_v2.md`
- `architecture_v2.md`
- `capability_spec.md`

Then map your work back to:
- `execution_plan.md`

### If you are working on frontend/product changes
Start with:
- `frontend_v2.md`
- `operator_workflows.md`
- `acceptance_demos.md`

Then verify your step boundaries in:
- `execution_plan.md`

### If you are evaluating whether something is worth building
Check:
- does it improve visual quality?
- does it improve realism?
- does it improve operator workflow?
- does it improve extensibility for mining + yard + city?
- does it solve a benchmark-proven performance problem?

If not, it may be a false peak. The execution plan explicitly warns against backend/read-model churn that does not materially improve those areas :contentReference[oaicite:2]{index=2}

## What these docs are not

These docs are not:
- a replacement for `execution_plan.md`
- a license to pre-implement future steps
- a permission slip for giant speculative rewrites
- frontend authority over simulator truth
- a new roadmap separate from the repo plan

They are design anchors.

## Current intended arc

At a high level, the codebase is moving toward:

- a deterministic Python-authoritative simulator
- a serious map-first frontend
- believable world, vehicle, and traffic behavior
- live operator control and scenario mutation
- mining as the flagship demo
- clean extension to construction yard and city street
- grounded AI assistance layered on top of richer simulator truth :contentReference[oaicite:3]{index=3}

## Practical rule

When there is tension between:
- implementation convenience
- and the intended product/system direction

use this folder to re-anchor the decision.

When there is tension between:
- broad design intent in this folder
- and a specific step in `execution_plan.md`

follow `execution_plan.md`.

## Next likely additions

Possible future docs that may belong here later:

- `resource_model.md`
- `traffic_model.md`
- `command_surfaces.md`
- `authoring_model.md`
- `ai_assist_model.md`
- `performance_strategy.md`

Only add them when they solve a real design ambiguity.

## Final note

This folder should help keep the project coherent while it grows.

The goal is not just to accumulate features.

The goal is to build a system that is:
- operationally useful
- visually convincing
- architecturally clean
- extensible across environments
- grounded in authoritative truth