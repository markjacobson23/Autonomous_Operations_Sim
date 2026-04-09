# Current Phase

## Active roadmap step
Step 28 — Visual presentation and frontend quality upgrade

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
- Step 27: complete
- Step 28: active
- Step 29: not started

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
- live interactive viewer actions
- a transport-agnostic live state/command sync surface

## Goal of the current phase
Upgrade the quality of the visualization/frontend experience so the simulator becomes significantly more legible, understandable, and pleasant to use.

The main Step 28 objective is:
- materially improve UI/UX quality
- improve visual clarity and readability
- make state, actions, and map context easier to understand
- keep the simulator core authoritative while allowing the viewer/frontend stack to evolve if needed

## In-scope work
Work that is allowed right now:
- improve the visual presentation of the current viewer substantially
- improve layout, styling, labeling, selection, and status presentation
- improve how map, vehicles, blocked edges, and action context are communicated
- evaluate whether the existing Python GUI remains the right implementation vehicle for near-term UI quality
- perform a bounded frontend/viewer refactor if needed to materially improve UX
- reuse the existing live sync, visualization, command, and session surfaces
- add tests for any new stable viewer-facing assumptions where practical

## Out-of-scope work
Do not do any of the following in the current phase:
- redesign the simulator core around the viewer
- weaken determinism or replay stability for UI convenience
- start performance/scaling work yet
- build a full product dashboard
- introduce remote multi-user architecture
- overbuild a frontend framework beyond what is needed for a major quality upgrade

## Architectural guidance for this phase
- Optimize for actual legibility and usability, not just “more features.”
- The best UI/UX quality matters more than keeping the viewer in Python.
- The simulator core, commands, sessions, and sync surfaces remain authoritative.
- The frontend/viewer should consume those surfaces cleanly.
- A bounded viewer-stack change is acceptable if it clearly improves quality.
- Avoid dangerous rewrites.

## Completion criteria for Step 28
Step 28 is complete when:
- the viewer/frontend experience is materially clearer and more usable than the Step 27 baseline
- map, vehicle, selection, blocked-edge, and action context are significantly easier to understand
- simulator/runtime authority remains cleanly separated from presentation
- tests/lint/type checks pass
