# Autonomous Operations Sim — Design Docs

This folder contains the active design docs for Autonomous Operations Sim.

The project direction is:

- Python remains the authoritative simulator and source of truth
- Unity becomes the embodied 3D runtime for motion, physics, rendering, and future sensors/AI
- browser/operator surfaces remain consumers of simulator truth, not competing authorities
- mining remains the flagship environment, with yard and city as required extensions

## Active docs

### `target_vision.md`
What the project is trying to become.

### `architecture_v2.md`
System ownership, truth boundaries, Python/Unity split, and runtime contracts.

### `world_model_v2.md`
The simulator-owned static world model.

### `operator_workflows.md`
What operators need to do and how the system should support them.

### `execution_plan.md`
The current implementation roadmap.

## Reading order

1. `target_vision.md`
2. `architecture_v2.md`
3. `world_model_v2.md`
4. `operator_workflows.md`
5. `execution_plan.md`