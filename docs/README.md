# Autonomous Operations Sim — Design Docs

This folder contains the active design docs for Autonomous Operations Sim.

The project direction is:

- Python remains the authoritative simulator and source of truth
- Unity becomes the embodied 3D runtime for motion, physics, rendering, and future sensors/AI
- operator-facing clients remain consumers of simulator truth, not competing authorities
- mining remains the flagship environment, with yard and city as required extensions

## Canonical docs

### `architecture_v2.md`
Start here.
Defines ownership, truth boundaries, Python/Unity split, runtime contracts, and anti-patterns.

### `execution_plan.md`
The active implementation roadmap.
Defines what to build next and in what order.

### `world_model_v2.md`
Defines the simulator-owned static world model.

### `operator_workflows.md`
Defines the workflows the system must support for operators and technical users.

### `target_vision.md`
Defines the north star and project identity.

### `current_task.md`
Defines the exact slice that should be worked on right now.
This is the active implementation brief for Codex.

## Reading order for implementation agents

1. `architecture_v2.md`
2. `execution_plan.md`
3. `world_model_v2.md`
4. `operator_workflows.md`
5. `target_vision.md`
6. `current_task.md`

## Canonicality rule

If two docs seem to overlap:

- `architecture_v2.md` wins on ownership and truth boundaries
- `execution_plan.md` wins on sequencing and current priorities
- `world_model_v2.md` wins on static-world semantics
- `operator_workflows.md` wins on user-facing behavior
- `target_vision.md` wins on long-term intent
- `current_task.md` wins only on the exact current implementation slice

No other doc should compete with these for authority.

## How to use `current_task.md`

`current_task.md` should be short and disposable.

It should contain:
- the active phase or step from `execution_plan.md`
- the exact objective right now
- the files allowed to change
- the files that must not change
- the acceptance criteria for this slice

It should not restate the whole architecture or roadmap.
It should point back to the canonical docs above.