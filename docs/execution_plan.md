# Autonomous Operations Sim — Execution Plan

## Purpose

This document is the durable roadmap and status record for the current project direction.

The immediate goal was to evolve from a Python-only simulator with browser-oriented derived surfaces into a Python-authoritative system with a Unity runtime for embodied motion, rendering, and future physics/sensor work.

That hybrid foundation is now implemented.

## Locked decisions

1. Python remains authoritative for world truth, runtime truth, commands, routing legality, and deterministic progression.
2. Unity is an execution/runtime layer, not a replacement simulator.
3. The world model remains shared across mining, yard, and city.
4. Operator-facing surfaces remain consumers, not authorities.
5. Motion authority must be explicit rather than implicit.
6. Replay and analysis truth remains backend-owned.

## Completed foundation phases

### Phase 1 — Contract and bridge
Status: complete

Delivered:
- simulator-shaped bootstrap payload
- telemetry payload
- stable vehicle identity mapping
- initial Unity runtime client
- initial HTTP/JSON bridge proving the contract end to end

### Phase 2 — Real simulator bootstrap
Status: complete

Delivered:
- Unity bootstrap derived from live session/runtime data
- vehicle spawning from real scenario state
- initial world geometry/waypoint generation from backend truth

### Phase 3 — Motion authority seam
Status: complete

Delivered:
- Python-motion mode
- Unity-motion mode
- safe runtime ingestion of Unity telemetry
- per-session authority selection
- backend-visible motion authority in the Unity bridge

Guardrail preserved:
- Python motion remains the fallback path

### Phase 4 — Route execution in Unity
Status: complete

Delivered:
- waypoint/route following
- progress reporting
- arrival/completion signals
- failure/blockage reporting
- runtime command feedback

### Phase 5 — Terrain and physics embodiment
Status: complete

Delivered:
- minimal physically meaningful Unity execution
- blockage/collision-aware execution feedback
- backend-visible embodiment state
- exception/blockage feedback to Python
- operational consequences that flow back into backend state

### Phase 6 — Operator integration
Status: complete

Delivered:
- operator-facing `operator_state` read model
- stable live/read-model flow grounded in Python truth
- coherent inspection of Unity-motion sessions from browser/operator surfaces

### Phase 7 — Replay and analysis groundwork
Status: complete

Delivered:
- backend-owned `replay_analysis` surface
- vehicle-level route progress and embodiment history projection
- replay/analysis summaries derived from Python-owned history after Unity ingestion

## Completed stabilization pass

### Cleanup and canonical-surface consolidation
Status: complete

Delivered:
- removal of redundant Unity bootstrap compatibility mirrors
- preservation of canonical nested bootstrap surfaces
- preservation of `operator_state`
- preservation of `replay_analysis`
- reduction of bundle/bridge duplication without changing authority boundaries

## Current stable architecture outcome

The hybrid stack now includes:

- canonical Python ↔ Unity HTTP/JSON bridge
- real simulator-derived Unity bootstrap
- explicit Python-motion and Unity-motion authority modes
- Unity route execution over backend-issued route intent
- backend-owned embodiment and blockage feedback
- operator-facing live inspection through `operator_state`
- backend-owned replay/analysis through `replay_analysis`

## Next candidate tracks

The project no longer needs another mandatory foundation phase before useful work.
Future work should be chosen deliberately from one of these tracks:

### Track A — Recovery and replanning
Possible work:
- backend response to blockage or exception outcomes
- replanning after Unity-reported failure states
- clearer active-route vs pending-route execution state

### Track B — Per-vehicle motion authority
Possible work:
- move from per-session authority selection to selective per-vehicle authority
- preserve the same backend-owned truth boundaries

### Track C — Transport hardening
Possible work:
- polling/coalescing improvements
- higher-frequency bridge updates
- later transport upgrades if actually justified

### Track D — Richer operator analysis
Possible work:
- lightweight replay inspection UI
- richer operator explanations derived from backend-owned state
- better comparison and anomaly review tools

### Track E — Sensors / autonomy experiments
Possible work:
- simulated sensors
- ML/AI runtime experiments
- perception-oriented Unity extensions

### Track F — Richer traffic realism
Possible work:
- lane behavior
- more nuanced conflict/reservation behavior
- more realistic traffic interactions

## Practical rule

At each step, prefer:

- explicit ownership
- reversible changes
- fallback-safe behavior
- canonical surfaces over compatibility clutter

Reject:

- giant rewrites
- Unity-owned operational truth
- client-side shadow truth
- environment-specific hacks
- premature transport complexity
- duplicated read models without a clear consumer