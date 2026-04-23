# Current Task

## Source of authority

Use these docs as constraints:

- Architecture: `docs/architecture_v2.md`
- Roadmap: `docs/execution_plan.md`
- World model: `docs/world_model_v2.md`
- Workflows: `docs/operator_workflows.md`

If this file conflicts with those docs, the canonical docs win.

## Active roadmap item

Phase 3 — Motion authority seam

## Objective

Introduce an explicit motion-authority seam so the system can distinguish between:

- Python motion authority
- Unity motion authority

This task is about making motion ownership explicit in backend/runtime contracts and state handling.
It is not yet about full Unity route execution, full physics authority, or removing Python motion.

## Why this task exists

Phase 1 established the HTTP/JSON bridge.
Phase 2 established a clearer real-simulator bootstrap and a minimal Unity bootstrap consumer.

The next required step is to stop treating motion authority as implicit.

The system must be able to represent, explicitly and safely:

- sessions where Python computes and advances motion
- sessions where Unity is allowed to embody motion while Python remains authoritative for operational truth

Without this seam, later Unity execution work will remain brittle or ambiguous.

## In scope

- introduce explicit motion authority state in the backend/session layer
- make motion authority visible in the Unity bootstrap from real runtime/session state instead of hardcoded values
- support per-session motion authority selection now
- leave room for per-vehicle motion authority later without implementing it yet
- add safe backend handling for Unity telemetry under the future Unity-motion path
- define the backend-side guardrails for what Unity telemetry may update and what it may not update
- keep the existing Phase 1/2 bridge path as the single canonical bridge

## Out of scope

- do not remove or break Python motion
- do not make Unity the source of task, route, or command truth
- do not implement full route execution in Unity yet
- do not redesign routing, dispatch, or command legality
- do not redesign the world model
- do not add WebSockets or gRPC yet
- do not add ML-Agents, sensors, or advanced physics behavior yet
- do not implement per-vehicle motion authority yet unless a tiny seam is needed to support it later

## Architectural constraints

- Python remains authoritative for:
  - world truth
  - runtime truth
  - task identity
  - routing legality
  - command truth
  - session truth

- Unity may embody motion only under an explicit contract

- Motion authority must be represented explicitly, not inferred from whether telemetry exists

- The Unity bridge must remain one canonical path
  - do not introduce a second competing bootstrap/telemetry mechanism

- Python motion must remain available as the fallback path during transition

## Required backend behavior

### Session-level motion authority

The backend should support an explicit session-level motion authority field with values equivalent to:

- `python`
- `unity`

This field should be readable from the runtime/session layer and exposed through the Unity bootstrap.

### Python-motion mode

In Python-motion mode:

- Python remains responsible for advancing vehicle motion
- Unity telemetry may be recorded, but must not become authoritative motion truth

### Unity-motion mode

In Unity-motion mode:

- Python still owns operational/task/command truth
- Unity telemetry is expected as the embodied motion signal
- backend handling should be structured so later phases can safely reconcile telemetry into runtime state

This task does not need to fully solve that reconciliation yet, but it must establish the seam cleanly.

## Telemetry guardrails

Under the new seam, the backend should make clear:

- what telemetry fields are accepted
- what backend state may be updated from telemetry
- what backend state must never be overwritten by telemetry alone

At minimum, telemetry must not directly replace:

- task identity
- route legality
- command truth
- scenario/world truth

## Allowed files to change

Only the minimum files needed for this slice.

Expected categories:
- backend live/session runtime state
- bootstrap serialization
- telemetry ingestion path
- tests validating motion authority behavior
- Unity bootstrap consumer only if a tiny adjustment is needed to reflect the new explicit authority field

## Files that must not be broadly rewritten

- static world model files
- routing/dispatch architecture
- unrelated frontend/operator workflow files
- unrelated simulation subsystems
- full Unity movement/controller systems

## Deliverables

1. Explicit session-level motion authority state
2. Bootstrap derived from real runtime/session authority state rather than hardcoded motion authority
3. Backend-side telemetry guardrails aligned with motion authority
4. Tests proving:
   - Python-motion mode behavior
   - Unity-motion mode contract visibility
   - existing Python-only path remains intact

## Acceptance criteria

This task is complete when:

- motion authority is explicit in backend/runtime state
- the Unity bootstrap reports real motion authority state rather than a hardcoded value
- Python-motion mode still works unchanged
- the codebase is better prepared for later Unity-motion reconciliation
- Python authority is preserved throughout
- the existing bridge remains the single canonical bridge path

## Practical rule

Prefer:
- additive seams
- explicit authority
- reversible changes
- fallback-safe behavior

Reject:
- giant rewrites
- Unity-owned operational truth
- telemetry that silently becomes authoritative
- premature route-execution logic
- a second competing bridge or motion path