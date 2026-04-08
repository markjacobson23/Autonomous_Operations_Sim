
## `docs/roadmap.md`

```markdown
# Expansion Roadmap

This roadmap begins after completion of the original foundation roadmap through Step 11.

The foundation phase established:
- deterministic topology/runtime separation
- routing and cost-model injection
- simulated-time execution
- jobs/tasks/resources
- baseline dispatch
- multi-vehicle reservation-based conflict handling
- vehicle behavior FSM
- metrics/export/golden regression

The purpose of this roadmap is to grow that deterministic simulator core into a more executable, extensible, and eventually interactive simulation platform without losing clean boundaries.

---

## Guiding principles

- Determinism remains first-class.
- Trace-centered metrics/export remain the stable outward-facing analysis surface.
- Static topology remains separate from runtime state.
- Prefer additive, production-style evolution over rewrites.
- Introduce visualization and interactivity only after the runtime/control surfaces are strong enough to support them cleanly.

---

## Step 12 — Executable scenario harness

### Goal
Turn scenario files into real executable simulator runs rather than validation-only inputs.

### Why this comes first
The simulator already has execution, metrics, and exports, but scenario JSON currently stops at validation/summary rather than driving a full run. This is the highest immediate-value gap because it converts the system from a library-oriented simulator core into a runnable scenario platform. :contentReference[oaicite:1]{index=1}

### Expected outcomes
- scenario files can drive real simulator runs
- CLI can execute scenarios, not just summarize them
- scenario-driven runs produce deterministic export JSON
- at least one scenario-run golden regression fixture exists

### Main likely modules
- scenario execution/orchestration layer
- CLI integration
- minimal scenario schema extension only if needed

### Out of scope
- visualization
- live interactive control
- vehicle model consolidation
- coordination redesign

---

## Step 13 — Scenario schema for operations

### Goal
Expand scenario/config schema so scenarios can express operational work, not just map + vehicles.

### Why it follows Step 12
First establish a working execution harness. Then expand what scenarios can describe.

### Expected outcomes
- scenario schema can express:
  - initial world conditions
  - jobs/tasks
  - resources
  - dispatcher choice/config
- deterministic parsing into runtime-ready structures
- scenario-driven runs cover more of the simulator without requiring handwritten Python setup

### Main likely modules
- `simulation/scenario.py`
- `io/scenario_loader.py`
- scenario execution/orchestration layer
- docs and example scenarios

### Out of scope
- large schema generalization
- visualization
- control-command layer

---

## Step 14 — Persistent vehicle entity model

### Goal
Promote a real persistent vehicle/entity model instead of threading scalar vehicle inputs through many execution paths.

### Why it follows Step 13
Once scenarios can drive real runs, the next pressure point is the still-minimal `Vehicle` model and scattered scalar vehicle state. The research identified this as a major likely refactor target. :contentReference[oaicite:2]{index=2}

### Expected outcomes
- a persistent `Vehicle` entity becomes the main execution-facing representation
- vehicle state relates cleanly to:
  - `VehicleProcess`
  - `VehicleBehaviorController`
  - trace
  - runtime manipulation
- reduced scalar argument threading

### Main likely modules
- `vehicles/vehicle.py`
- `simulation/vehicle_process.py`
- `simulation/engine.py`
- behavior integration points

### Out of scope
- visualization
- interactive control UI
- full fleet-management optimization

---

## Step 15 — Evaluation and scenario-pack harness

### Goal
Support scenario packs, batch execution, and benchmark-style comparisons.

### Why it follows Step 14
Once scenarios run end-to-end and vehicles have stronger runtime identity, batch execution becomes much more useful and stable.

### Expected outcomes
- batch scenario execution
- stable summary aggregation across runs
- deterministic comparison harness
- multiple golden-style scenario packs

### Main likely modules
- scenario pack runner
- metrics aggregation utilities
- export/report conventions

### Out of scope
- dashboard/UI
- interactive control

---

## Step 16 — Richer operations realism

### Goal
Move from isolated jobs to richer ongoing fleet/operations studies.

### Expected outcomes
- multiple jobs over time
- stronger workload modeling
- utilization-oriented metrics
- repeated haul-cycle style simulation
- richer resource-network realism

### Why it comes here
This is where the simulator becomes more like a true operations-study platform, but it should come after executable scenarios, stronger entity modeling, and batch evaluation support.

### Out of scope
- advanced coordination algorithm redesign
- live UI-first development

---

## Step 17 — Coordination upgrade

### Goal
Improve multi-vehicle coordination beyond the narrow deterministic reservation baseline.

### Expected outcomes
- stronger reservation indexing/scalability
- better deadlock observability/prevention
- bounded replanning or corridor/intersection semantics
- deterministic regression cases for upgraded coordination

### Why it comes after evaluation growth
Coordination upgrades are high-risk and easy to destabilize. They should be introduced only after the simulator has strong scenario and regression harnesses to measure the change properly. The research explicitly warns that coordination upgrades are costly and can break determinism if introduced too early. :contentReference[oaicite:3]{index=3}

### Out of scope
- full optimal MAPF for all use cases
- giant algorithmic framework rewrites

---

## Step 18 — Control-command surface

### Goal
Add a replayable command/event surface for controlling a run.

### Why this must come before interactive UI
Real-time interaction should not directly mutate engine state arbitrarily. A control-command surface is the clean architectural bridge between deterministic simulation and interactive tooling. The research explicitly recommends a control command/event interface for replayability and auditability. :contentReference[oaicite:4]{index=4}

### Expected outcomes
- explicit commands such as:
  - assign destination
  - inject closure
  - reposition vehicle
  - pause/resume/step
- commands recorded in a replayable form
- deterministic offline mode and interactive mode can share the same runtime contract

### Out of scope
- polished end-user viewer
- full UI framework commitment unless justified

---

## Step 19 — Visualization state surface and first viewer

### Goal
Make the simulator watchable in real time through a thin visualization surface.

### Expected outcomes
- visualization/state stream or snapshot surface
- minimal viewer that can:
  - display map/topology
  - display vehicle positions/state
  - play/pause/step playback
- deterministic replay of previously executed runs

### Why it follows the command surface
Visualization should consume stable simulator state/control surfaces rather than forcing architecture from the UI downward.

### Out of scope
- large dashboard
- heavy animation framework
- broad product UI

---

## Step 20 — Interactive manipulation layer

### Goal
Support live interaction with running simulations.

### Expected outcomes
- click-to-assign destination
- drag/reposition vehicle
- inject closures/blocked edges during execution
- inspect vehicle/job/resource state live
- preserve replayability through recorded control commands

### Why it follows visualization
Once the simulator can be watched and controlled through explicit surfaces, live manipulation becomes a natural extension rather than a source of architectural chaos.

---

## Step 21 — Environment/map realism expansion

### Goal
Expand beyond the current narrow map semantics and grid-first scenario assumptions.

### Expected outcomes
- richer map/environment semantics
- zones/work areas/site metadata
- better import/export paths for non-grid network data
- stronger domain realism for specific operational settings

### Why it is later
Map realism is valuable, but the research ranked it below scenario execution and entity/harness work because execution/control surfaces need to be stronger first. :contentReference[oaicite:5]{index=5}

---

## Step 22 — Optional research wrapper

### Goal
Add a minimal external experimentation wrapper only if it remains clearly optional.

### Possible outcomes
- policy comparison harness
- optional Gymnasium-style wrapper
- research-oriented control experiments

### Constraints
This should remain an adapter on top of stable simulator surfaces, not a redesign of the simulator around a research framework.

---

## Recommended implementation order

1. Step 12 — Executable scenario harness
2. Step 13 — Scenario schema for operations
3. Step 14 — Persistent vehicle entity model
4. Step 15 — Evaluation and scenario-pack harness
5. Step 16 — Richer operations realism
6. Step 17 — Coordination upgrade
7. Step 18 — Control-command surface
8. Step 19 — Visualization state surface and first viewer
9. Step 20 — Interactive manipulation layer
10. Step 21 — Environment/map realism expansion
11. Step 22 — Optional research wrapper

---

## How to use this roadmap

At any given time:
- `docs/current_phase.md` defines the active step
- `docs/step-*.md` defines the specific scope and done criteria for that step
- `AGENTS.md` defines repo-wide development rules

The intent is to keep future growth as disciplined as the original foundation roadmap:
- additive where possible
- explicit where necessary
- measurable by deterministic tests, metrics, and regression fixtures
