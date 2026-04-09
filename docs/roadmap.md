
## `docs/roadmap.md`

```markdown
# Post-Step-22 Expansion Roadmap

The original roadmap through Step 22 is complete.

That roadmap established:
- deterministic scenario execution
- jobs/resources/dispatch/workloads
- vehicle runtime state
- coordination via reservations/corridors
- command/control surfaces
- visualization replay state
- interaction translation
- graph-map realism
- optional research comparison tooling

The next roadmap focuses on three major expansion tracks:

1. real graphical visualization
2. more realistic live interactivity
3. performance/scaling maturity

This roadmap should remain incremental, deterministic, and architecture-first.

---

## Guiding principles

- Preserve the simulator’s identity as an operations/fleet-level simulator, not a physics simulator.
- Keep the Python simulator core authoritative unless profiling or capability needs justify separation.
- Treat viewers and external frontends as consumers of stable simulator surfaces.
- Treat performance/scaling work as benchmark-driven, not assumption-driven.
- Prefer disciplined staging over building UI, performance, and runtime complexity all at once.

---

## Step 23 — Graphical replay viewer foundation

### Goal
Build the first real graphical viewer on top of the existing visualization replay surface.

### Why first
The repo already has deterministic visualization state and a text viewer. The next natural milestone is a real graphical replay viewer that consumes that state without changing simulator ownership. The research specifically identifies interactive UI/streaming as a next major gap, while noting the current replay/state layering is already a strength. :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}

### Expected outcomes
- a real graphical viewer for completed runs
- map rendering from visualization state
- rendered vehicle positions/states over replay frames
- deterministic playback controls over completed runs

### Notes
This should be the smallest version of “real visualization” that is meaningfully better than the text viewer.

---

## Step 24 — Playback control maturity

### Goal
Strengthen replay control beyond static frame rendering.

### Expected outcomes
- play / pause / step / jump-to-frame
- frame indexing and timeline controls
- deterministic playback UX over existing replay frames
- viewer remains a consumer of replay state

### Why it follows Step 23
A graphical viewer is useful first; richer playback control is the next layer before true live runtime manipulation.

---

## Step 25 — Live control loop bridge

### Goal
Bridge the existing command/control layer into a more realistic live runtime control loop.

### Expected outcomes
- a narrow runtime session concept
- controlled application of commands during an active session
- consistent command ordering and replay capture
- no direct viewer mutation of engine internals

### Why it follows playback maturity
The report highlights interactive UI/streaming as a next gap, but the clean way to get there is through the existing command/control architecture, not a UI-first rewrite. :contentReference[oaicite:5]{index=5}

---

## Step 26 — Live interactive viewer actions

### Goal
Support first real live interactions through the graphical viewer.

### Expected outcomes
- click-to-assign destination
- select/reposition vehicle in a bounded way
- inject blocked edges / closures during a live session
- inspect vehicle/state data live

### Why it follows Step 25
A live viewer should sit on top of a mature control loop bridge rather than invent its own runtime semantics.

---

## Step 27 — Streaming/state sync surface

### Goal
Formalize a state/command synchronization surface between simulator runtime and viewer.

### Expected outcomes
- stable runtime snapshot/update surface
- explicit control messages/events
- clearer boundary for future multi-process or mixed-stack visualization
- deterministic replay compatibility

### Why it matters
This is the step where the architecture becomes ready for a cleaner separation between simulator core and richer frontend stacks if needed.

---

## Step 28 — Profiling and benchmark harness

### Goal
Measure performance and scaling behavior before optimization or language splitting.

### Expected outcomes
- routing benchmarks
- reservation/coordination benchmarks
- scenario-pack throughput benchmarks
- replay/export size and generation benchmarks
- stable benchmark reporting

### Why this comes before deep optimization
The report explicitly points to likely bottlenecks in routing, reservation scanning, and replay/export growth, and recommends profiling/benchmarks before major performance work. :contentReference[oaicite:6]{index=6}

---

## Step 29 — Python-side scaling improvements

### Goal
Improve performance inside the existing Python architecture first.

### Expected outcomes
- better reservation data structures
- targeted routing or caching improvements
- replay/export efficiency improvements
- benchmark-backed performance gains

### Why before mixed-language separation
The research recommends algorithmic/data-structure upgrades and profiling before drastic architecture or language changes. :contentReference[oaicite:7]{index=7}

---

## Step 30 — Optional mixed-stack viewer separation

### Goal
If justified, separate the viewer/frontend into a stack better suited for graphical/live interaction.

### Expected outcomes
- simulator core remains authoritative
- frontend consumes stable replay/runtime surfaces
- mixed-language or mixed-runtime boundary is explicit
- no simulator-core rewrite required

### Likely candidates
- web frontend
- richer desktop UI stack

### Why optional
This should only happen if the Python-only viewer path becomes limiting in UX, capability, or development efficiency.

---

## Step 31 — Optional native performance kernel exploration

### Goal
If benchmark data justifies it, isolate one performance-critical subsystem for native acceleration.

### Expected outcomes
- one bounded hotspot selected by profiling
- clear interface between Python orchestration and native kernel
- benchmark comparison proving benefit

### Likely candidates
- reservation/conflict search
- pathfinding/planning kernels
- large-batch evaluation kernels

### Why last
Language separation should be earned by evidence, not assumed.

---

## Recommended order

1. Step 23 — Graphical replay viewer foundation
2. Step 24 — Playback control maturity
3. Step 25 — Live control loop bridge
4. Step 26 — Live interactive viewer actions
5. Step 27 — Streaming/state sync surface
6. Step 28 — Profiling and benchmark harness
7. Step 29 — Python-side scaling improvements
8. Step 30 — Optional mixed-stack viewer separation
9. Step 31 — Optional native performance kernel exploration

---

## Why this order

This sequence follows the current architecture and the research findings:

- the repo already has strong replay/state/control layering, so the first gain should be a real graphical viewer on top of those surfaces :contentReference[oaicite:8]{index=8}
- interactive UI/streaming is a major gap, but it should grow from control/replay surfaces rather than leapfrogging them :contentReference[oaicite:9]{index=9}
- performance/scaling work should be benchmark-driven and comes after the next visualization/control milestones are concrete enough to measure against :contentReference[oaicite:10]{index=10}
- mixed-language separation remains on the table, but only after the architecture and profiling data justify it

---

## How to use this roadmap

At any given time:
- `docs/current_phase.md` defines the active step
- `docs/step-*.md` defines step-specific scope and done criteria
- `AGENTS.md` defines repo-wide development rules

This roadmap should preserve the same disciplined development style as the first 22 steps:
- additive where possible
- explicit where necessary
- backed by deterministic tests, replay surfaces, and stable exports
