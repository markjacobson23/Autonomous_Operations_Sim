# Current Phase

## Active roadmap step
Step 25 — Live control loop bridge

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
- Step 25: active
- Step 26: not started

## What already exists
The repository already has:
- deterministic scenario parsing and execution
- operational jobs/resources/dispatch/workloads
- typed command/control surfaces with deterministic history
- visualization replay state
- text and graphical replay viewers
- viewer-facing interactions translated into commands
- graph-map realism
- optional research comparison tooling

## Goal of the current phase
Bridge the existing command/control surfaces into a more realistic live runtime control loop without breaking determinism or making the viewer the source of simulator truth.

The main Step 25 objective is:
- introduce a narrow live runtime session concept
- support command application during an active controlled session
- preserve deterministic ordering and replayability
- prepare the architecture for later live interactive viewer actions

## In-scope work
Work that is allowed right now:
- add a runtime session / live control bridge layer
- support controlled stepping or bounded live progression of a session
- allow typed commands to be applied during that active session
- ensure resulting trace/command/replay surfaces remain coherent
- add deterministic tests for session progression and command timing/order
- perform additive refactors and targeted normal refactors needed to keep the live control bridge clean

## Out-of-scope work
Do not do any of the following in the current phase:
- add full viewer-side click interaction yet
- bypass the command surface
- redesign the simulator around async/event-loop infrastructure
- build streaming/network architecture yet
- overbuild a generic runtime framework
- turn the graphical viewer into the owner of live state

## Architectural guidance for this phase
- The simulator core remains authoritative.
- Commands must remain explicit and validated.
- A live session should still be deterministic for the same starting state and command sequence.
- Keep the live control bridge separate from future viewer UX concerns.
- Avoid dangerous rewrites.

## Completion criteria for Step 25
Step 25 is complete when:
- a narrow live runtime session/control bridge exists
- typed commands can be applied coherently during a controlled active session
- deterministic replay/export behavior remains intact
- tests/lint/type checks pass
