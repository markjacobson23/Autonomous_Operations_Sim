# Autonomous Operations Sim — Execution Plan

## Purpose

This document is the active roadmap for the current project direction.

The immediate goal is to evolve from a Python-only simulator with browser-oriented derived surfaces into a Python-authoritative system with a Unity runtime for embodied motion, rendering, and future physics/sensor work.

## Locked decisions

1. Python remains authoritative for world truth, runtime truth, commands, routing legality, and deterministic progression.
2. Unity is an execution/runtime layer, not a replacement simulator.
3. The world model remains shared across mining, yard, and city.
4. Old browser/operator surfaces remain consumers, not authorities.
5. Motion authority must become explicit rather than implicit.

## Phase 1 — Contract and bridge

Goal:
- establish the Python ↔ Unity contract

Deliverables:
- simulator-shaped bootstrap payload
- telemetry payload
- stable vehicle identity mapping
- initial Unity runtime client

Done when:
- Python can send target/route intent
- Unity can read it
- Unity can report telemetry back

## Phase 2 — Real simulator bootstrap

Goal:
- replace toy payloads with real simulator-derived surfaces

Deliverables:
- Unity bootstrap derived from live session/runtime data
- vehicle spawning from real scenario state
- initial world geometry/waypoint generation from backend truth

Done when:
- Unity can represent a real simulator scenario without fake bridge data

## Phase 3 — Motion authority seam

Goal:
- make motion ownership explicit

Deliverables:
- Python-motion mode
- Unity-motion mode
- safe runtime ingestion of Unity telemetry
- per-session or per-vehicle authority selection

Done when:
- the same scenario can run in either motion mode

## Phase 4 — Route execution in Unity

Goal:
- move from single targets to backend-issued routes

Deliverables:
- waypoint/route following
- progress reporting
- arrival/completion signals
- runtime command feedback

Done when:
- Unity-controlled vehicles can complete backend-issued routes

## Phase 5 — Terrain and physics embodiment

Goal:
- make Unity execution physically meaningful

Deliverables:
- terrain-aware movement
- collision handling
- richer vehicle representation
- exception/blockage feedback to Python

Done when:
- Unity execution affects real operational outcomes

## Phase 6 — Operator integration

Goal:
- keep operator workflows coherent across clients

Deliverables:
- usable inspection/command surfaces
- stable replay/live/read-model flow
- map/runtime surfaces that remain grounded in Python truth

Done when:
- operators can inspect, preview, command, and understand runs while Unity handles embodiment

## Phase 7 — Future extensions

Possible later phases:
- sensors
- ML/AI runtime experiments
- stronger replay/analysis
- richer traffic realism
- benchmark-guided optimization

## Practical rule

At each step, prefer:
- additive seams
- explicit ownership
- reversible changes
- fallback-safe behavior

Reject:
- giant rewrites
- Unity-owned operational truth
- client-side shadow truth
- environment-specific hacks