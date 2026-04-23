# Autonomous Operations Sim — Operator Workflows

## Purpose

This document defines the workflows the system must support for an operator or technical user.

It is client-agnostic.
A workflow may be supported through a browser operator shell, a Unity-backed operator surface, or another consumer of simulator truth.

## Workflow principles

1. Map/world first  
   The operator should work from the world, not from raw IDs.

2. Selection before form entry  
   Primary workflows should begin with selecting real entities.

3. Preview before commitment  
   Commands with meaningful consequences should be previewable.

4. Explanation near the decision  
   The system should show why something is happening close to where the operator acts.

5. Simulator remains authoritative  
   Clients may compose decisions locally, but command truth and runtime effects remain Python-authoritative.

## Primary workflow categories

- Observe
- Inspect
- Plan
- Act
- Mutate
- Analyze

## 1. Observe

The operator should be able to:

- open a live scenario
- orient quickly
- understand what is moving
- detect emerging issues

A good outcome is fast situational awareness.

## 2. Inspect

The operator should be able to inspect:

- a vehicle
- a road/lane/queue/conflict area
- a hazard or blocked region
- a planned route preview

A good outcome is being able to answer:
- what is this?
- what is it doing?
- why is it doing that?
- what matters right now?

## 3. Plan

The operator should be able to:

- assign a destination
- compare route options
- prepare bounded fleet actions

A good outcome is making decisions through preview and context rather than trial-and-error.

## 4. Act

The operator should be able to:

- commit a destination/route assignment
- reposition a vehicle
- block/unblock a road
- declare/clear a hazard
- spawn/remove a vehicle
- inject a job/task
- control play/pause/step

A good outcome is clear command submission, result feedback, and visible runtime effect.

## 5. Mutate

The operator should be able to make bounded live changes without corrupting simulator truth.

A good outcome is being able to intervene operationally while preserving determinism and inspectability.

## 6. Analyze

The operator should be able to:

- understand why a delay occurred
- inspect congestion and bottlenecks
- compare outcomes
- review anomalies or warnings

A good outcome is grounded understanding, not vague dashboard noise.

## Success standard

A strong operator workflow lets a user:

- find the important thing quickly
- understand it with little friction
- preview a meaningful action
- commit it confidently
- see what changed
- trust the explanation

## Failure modes

Reject workflows that are:

- raw-ID-first
- debug-heavy
- visually cluttered
- disconnected from the world
- weak on feedback after action
- based on client-side invented truth