# Current Phase

## Active roadmap step
Step 24 — Playback control maturity

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
- Step 24: active
- Step 25: not started

## What already exists
The repository already has:
- deterministic scenario parsing and execution
- operational jobs/resources/dispatch/workloads
- command/control surfaces with deterministic history
- visualization replay state and text viewer
- interaction translation into commands
- graph-map realism
- research comparison tooling
- a first graphical replay viewer consuming visualization state

## Goal of the current phase
Strengthen playback control for the graphical replay viewer so replay becomes easier to inspect and navigate before introducing live runtime interaction.

The main Step 24 objective is:
- improve replay navigation and control
- support richer deterministic playback UX
- preserve the viewer as a consumer of completed replay state
- prepare the viewer for later live-control integration

## In-scope work
Work that is allowed right now:
- extend replay controls with features such as:
  - previous frame
  - jump to first / last frame
  - jump to specific frame index
  - optional speed controls
  - current-frame metadata display improvements
- keep playback deterministic over completed replay frames
- extend the graphical viewer in a narrow way
- add tests for replay navigation and stable controller behavior
- perform additive refactors and targeted normal refactors needed to keep playback logic clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add live runtime manipulation
- inject commands during an active graphical session
- redesign the simulator around a live event loop
- add networking/streaming yet
- bypass replay state to reach directly into engine internals
- build a heavy product UI

## Architectural guidance for this phase
- The viewer still consumes completed replay state only.
- Playback features should remain deterministic and frame-based.
- Keep playback logic separate from future live-runtime control.
- Improve inspectability without overbuilding UI complexity.
- Avoid dangerous rewrites.

## Completion criteria for Step 24
Step 24 is complete when:
- replay controls are meaningfully stronger than the Step 23 baseline
- playback/navigation remains deterministic
- tests/lint/type checks pass
