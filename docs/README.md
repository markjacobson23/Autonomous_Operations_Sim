# Autonomous Operations Sim — Design Docs

This folder contains the active design docs for Autonomous Operations Sim.

The project direction is:

- Python remains the authoritative simulator and source of truth
- Unity is the embodied 3D runtime for motion, physics, rendering, and future sensors/AI
- operator-facing clients remain consumers of simulator truth, not competing authorities
- mining remains the flagship environment, with yard and city as required extensions

## Current code reality

The implemented hybrid stack now includes:

- a canonical Python ↔ Unity HTTP/JSON bridge
- a real simulator-derived Unity bootstrap
- explicit Python-motion and Unity-motion authority modes
- Unity route execution over backend-issued route intent
- backend-owned embodiment and blockage feedback
- an operator-facing `operator_state` read model
- a backend-owned `replay_analysis` read model
- a cleanup pass that removed redundant bootstrap compatibility mirrors

## Canonical docs

### `architecture_v2.md`
Start here.
Defines ownership, truth boundaries, canonical derived surfaces, Python/Unity responsibilities, and anti-patterns.

### `execution_plan.md`
The durable roadmap and status document.
Defines what has been completed, what remains stable, and what future tracks are available.

### `current_task.md`
Defines the exact slice that should be worked on right now.
This is the active implementation brief for Codex and should stay short and disposable.

### `world_model_v2.md`
Defines the simulator-owned static world model.

### `operator_workflows.md`
Defines the workflows the system must support for operators and technical users.

### `target_vision.md`
Defines the north star and project identity.

## Reading order for implementation agents

1. `architecture_v2.md`
2. `execution_plan.md`
3. `current_task.md`
4. `world_model_v2.md`
5. `operator_workflows.md`
6. `target_vision.md`

## Canonicality rule

If two docs seem to overlap:

- `architecture_v2.md` wins on ownership, truth boundaries, and canonical surface definitions
- `execution_plan.md` wins on roadmap status and next-track choices
- `current_task.md` wins only on the exact current implementation slice
- `world_model_v2.md` wins on static-world semantics
- `operator_workflows.md` wins on user-facing behavior
- `target_vision.md` wins on long-term intent

No other doc should compete with these for authority.

## Notes for implementation agents

- Treat `AGENTS.md` as repo-wide working guidance, but not as a competing design authority.
- Prefer the canonical derived surfaces that now exist in code:
  - Unity bootstrap for Unity runtime consumption
  - `operator_state` for operator-facing live inspection
  - `replay_analysis` for backend-owned replay and analysis
- Do not reintroduce removed compatibility mirrors unless there is a concrete consumer and a documented reason.

## How to use `current_task.md`

`current_task.md` should:

- name the active roadmap item or stabilization pass
- state the exact objective right now
- list the minimum files allowed to change
- list the files that must not be broadly rewritten
- define acceptance criteria for the current slice

It should not restate the whole architecture or roadmap.
It should point back to the canonical docs above.