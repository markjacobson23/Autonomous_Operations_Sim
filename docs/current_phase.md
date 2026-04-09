# Current Phase

## Active roadmap step
Step 27 — Streaming/state sync surface

## Step status summary
- Step 1: complete
- Step 2: complete
- Step 3: complete
- Step 4: complete
- Step 5: complete
- Step 6: complete
- Step 7: complete
- Step 8: complete
- Step 9: complete
- Step 10: complete
- Step 11: complete
- Step 12: complete
- Step 13: complete
- Step 14: complete
- Step 15: complete
- Step 16: complete
- Step 17: complete
- Step 18: complete
- Step 19: complete
- Step 20: complete
- Step 21: complete
- Step 22: complete
- Step 23: complete
- Step 24: complete
- Step 25: complete
- Step 26: complete
- Step 27: active
- Step 28: not started

## What already exists
The repository already has:
- deterministic scenario parsing and execution
- operational jobs/resources/dispatch/workloads
- typed command/control surfaces with deterministic history
- visualization replay state
- text and graphical replay viewers
- improved playback controls and frame metadata
- viewer-facing interactions translated into commands
- graph-map realism
- optional research comparison tooling
- a live simulation session bridge
- first real live interactive viewer actions

## Goal of the current phase
Formalize a cleaner live state/command synchronization surface between the simulator runtime and viewer layer.

The main Step 27 objective is:
- define a stable state-sync surface for live viewer consumption
- separate runtime state publication from viewer toolkit details
- preserve deterministic replay compatibility
- prepare for later visual-quality work and possible mixed-stack viewer separation

## In-scope work
Work that is allowed right now:
- add a live state snapshot/update surface
- define stable viewer-facing runtime sync records
- support command/result publication through that sync surface
- reuse live session, command history, and visualization state builders
- add deterministic tests for repeated sync/update sequences
- perform additive refactors and targeted normal refactors needed to clarify viewer/runtime boundaries

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the simulator around networking or async frameworks
- build a full remote protocol
- bypass live session and command surfaces
- focus on visual polish yet
- start performance/scaling work yet
- overbuild a product-grade frontend architecture

## Architectural guidance for this phase
- The simulator core remains authoritative.
- The sync surface should describe runtime state and updates cleanly for viewers.
- Keep it transport-agnostic.
- Preserve deterministic ordering and replay compatibility.
- Make future frontend separation easier, not harder.
- Avoid dangerous rewrites.

## Completion criteria for Step 27
Step 27 is complete when:
- a stable live state/command sync surface exists
- viewers can consume it cleanly without deep runtime coupling
- deterministic behavior and replay compatibility remain intact
- tests/lint/type checks pass
