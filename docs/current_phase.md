# Current Phase

## Active roadmap step
Step 26 — Live interactive viewer actions

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
- Step 26: active
- Step 27: not started

## What already exists
The repository already has:
- deterministic scenario parsing and execution
- operational jobs/resources/dispatch/workloads
- typed command/control surfaces with deterministic history
- visualization replay state
- text and graphical replay viewers
- stronger playback controls and frame metadata
- viewer-facing interactions translated into commands
- graph-map realism
- research comparison tooling
- a live simulation session bridge with explicit progression and session-aware replay output

## Goal of the current phase
Add the first real live interactive viewer actions on top of the existing interaction, command, and live-session architecture.

The main Step 26 objective is:
- make the graphical viewer capable of issuing bounded live actions
- route those actions through the existing interaction and command layers
- preserve deterministic session, trace, and replay behavior
- improve the simulator from “watchable” to “manipulable”

## In-scope work
Work that is allowed right now:
- connect the graphical viewer to a live session
- support a narrow initial live action set such as:
  - click/select vehicle
  - assign destination to selected vehicle
  - inject blocked edge / closure
  - bounded reposition workflow if it stays clean
- translate viewer actions into interactions/commands rather than direct engine mutation
- refresh visualization state coherently after live actions
- add deterministic tests for live viewer action handling
- perform additive refactors and targeted normal refactors needed to keep viewer/session boundaries clean

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the simulator around async/networked streaming
- bypass interactions/commands and mutate engine state directly from the GUI
- build a large polished product UI
- introduce broad multi-user or remote control architecture
- start performance/scaling work yet

## Architectural guidance for this phase
- Viewer actions must translate into interactions and then typed commands.
- The live session remains the authoritative runtime host.
- Keep the initial action vocabulary small and explicit.
- Refresh derived visualization state from authoritative runtime/session data.
- Avoid dangerous rewrites.

## Completion criteria for Step 26
Step 26 is complete when:
- the graphical viewer can perform at least one meaningful live action
- those actions flow through interaction/command/session layers coherently
- deterministic replay/export behavior remains intact
- tests/lint/type checks pass
