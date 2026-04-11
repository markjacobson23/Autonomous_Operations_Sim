# Demo Recovery Plan

## Phase 0 — Acceptance target
The near-term demo is considered successful only when a live launch shows:
- multiple vehicles moving at once
- readable roads and intersections
- named destinations instead of raw node IDs as the primary UX
- at least one visible right-of-way decision
- at least one vehicle waiting for another and then proceeding
- a live ledger showing what each vehicle is doing and carrying

## Phase 1 — Proof-of-life city-street sandbox
Build a compact street-style traffic sandbox.
- 2 to 4 intersections
- named roads and destinations
- 4 to 8 vehicles
- enough density for interactions, but still debuggable

This is the first coding task.

## Phase 2 — Visible motion
Make movement undeniably visible in the UI.
- play visibly advances the scene
- vehicles visibly progress along roads
- moving vs idle state is easy to distinguish
- intersections visibly read as traversal points

## Phase 3 — Intersection decisions
Add stop-controlled right-of-way behavior.
- approach / stop / wait / enter / clear
- conflict or occupancy checks
- queueing when multiple vehicles stack up

## Phase 4 — Human-first operator UX
Replace debug-first interaction with human-first interaction.
- primary controls use names or clicks, not node IDs
- node IDs remain optional debug info only
- selecting a vehicle explains what it is doing in plain language

## Phase 5 — First-class ledger
Expose operational truth clearly.
Per vehicle:
- state
- destination
- current job/task
- payload/cargo amount
- waiting reason
- recent action

System-wide:
- completed deliveries/tasks
- queue/wait events
- route completions
- active conflicts or waits

## Phase 6 — Readability and style pass
Only after the sim is alive and understandable.
- cleaner scene hierarchy
- roads and intersections read correctly
- calmer UI and better contrast
- moving vehicles feel alive

## Phase 7 — Hardening
After the above works:
- regression tests for proof-of-life behavior
- playback tests
- CI expansion where needed
- typing/schema hardening only where it protects real behavior

## Notes
This plan stays aligned with the repo's existing roadmap:
- Python simulator remains authoritative
- UI remains derived from simulator truth
- mining remains the long-term flagship environment
- city-street support is already part of the roadmap
