# autonomous_ops_sim

`autonomous_ops_sim` is a production-structured Python simulator for autonomous operations and vehicle workflows. It has moved far beyond early scenario loading and grid routing: the repository now includes deterministic scenario execution, jobs and shared resources, multi-vehicle reservation-based coordination, stable replay/live API bundles, a serious viewer/export path, command-center and vehicle-inspection surfaces, AI-assist read models, benchmark tooling, a mining showcase flow, and optional native acceleration for reservation departure scans.

This README is intended to reflect the project through **Step 40** of the roadmap.

## Current status

What the project can do today:

- Load and validate JSON scenarios into typed dataclasses.
- Build graph-backed maps, including both simple grid maps and richer graph maps with render geometry.
- Keep immutable topology separate from runtime blocked-edge state through `WorldState`.
- Route with Dijkstra through a public `Router` surface and multiple cost models.
- Execute deterministic simulated-time runs through `SimulationEngine`.
- Execute jobs built from move/load/unload tasks.
- Model shared operational resources and deterministic waiting.
- Dispatch pending jobs with baseline deterministic dispatch logic.
- Coordinate narrow multi-vehicle route sets with reservation-based conflict avoidance.
- Track operational behavior through explicit vehicle state transitions and trace events.
- Build stable execution metrics and deterministic JSON exports.
- Execute scenario files from the CLI and emit deterministic export JSON.
- Run scenario packs and aggregate their results.
- Build stable replay, live-session, and live-sync **Simulation API** bundles.
- Derive render geometry, motion segments, traffic baseline state, command-center state, vehicle inspections, and AI-assist read models from authoritative simulator truth.
- Export standalone serious-viewer HTML files from Simulation API bundles.
- Generate a mining showpiece package with replay/live/live-sync viewers and a manifest.
- Run a repeatable benchmark suite from the CLI.
- Use an optional native accelerator for reservation departure scanning when the toolchain supports it.

Important current boundary:

- The simulator backend is already substantial.
- The serious viewer and showcase flow are real and useful, but they are still a **foundation-stage frontend**, not yet the final high-end live UI described in the longer-term roadmap.
- Traffic, AI assist, command center, and inspection are present as strong baseline layers, but not yet the final depth of realism or UX the project ultimately aims for.

## Design goals

The codebase is organized around a few consistent choices:

- **Determinism first.** Seeds are explicit, trace ordering is stable, and repeated runs should match.
- **Topology is separate from runtime state.** `Map` and `Graph` describe reusable world structure; `WorldState` owns dynamic blocked-edge conditions.
- **Simulator authority stays centralized.** Replay/live/viewer surfaces are derived from authoritative execution rather than becoming competing runtime models.
- **Execution is simulated time, not wall clock.**
- **Operational layers are additive.** Jobs, resources, dispatch, reservations, behavior, visualization, command-center state, and AI-assist layers all build on the same engine and trace surfaces.
- **Public surfaces are versioned.** Viewer-facing and tool-facing bundle surfaces are treated as explicit contracts.
- **Performance work should be measured.** Python-side optimizations come first; native acceleration is narrow, optional, and benchmark-justified.

## Architecture overview

### 1. Core topology

The foundational graph model lives in `autonomous_ops_sim/core/`:

- `Node` and `NodeType` define graph locations and semantic roles.
- `Edge` defines directed traversable segments with `distance` and `speed_limit`.
- `Graph` stores nodes, edges, and adjacency, and enforces basic graph integrity.

This is intentionally local, project-owned infrastructure rather than an external graph dependency.

### 2. Map and geometry layers

Spatial structure lives in `autonomous_ops_sim/maps/` and `autonomous_ops_sim/visualization/geometry.py`:

- `Map` wraps a `Graph` with coordinate-based lookup, neighbor queries, edge lookup, and path validation.
- `make_grid_map()` remains available for early/testing use.
- Graph-backed scenarios can now carry richer render geometry such as roads, intersections, and areas.
- Visualization geometry is deliberately separated from routing truth so the map can become visually richer without corrupting operational semantics.

### 3. Scenario/config layer

Scenario/config support lives across `autonomous_ops_sim/io/` and `autonomous_ops_sim/simulation/scenario.py`:

- `Scenario` and related spec dataclasses define typed scenario structure.
- `load_scenario()` reads JSON and validates required schema fields.
- Scenarios can now drive actual execution, not just summary output.
- Scenario packs support running grouped scenario suites and aggregating their results.

The project is no longer limited to scenario validation and summary: scenario execution is now part of the supported CLI surface.

### 4. Runtime world state

`autonomous_ops_sim/simulation/world_state.py` provides `WorldState`, which owns runtime blocked-edge state.

This matters because:

- the same map can be reused across runs,
- runtime changes do not mutate the map asset,
- resetting runtime conditions stays explicit and deterministic.

### 5. Routing

Routing lives in `autonomous_ops_sim/routing/`:

- `Router` is the public pathfinding surface.
- `dijkstra()` implements pathfinding.
- `CostModel` allows injected edge-cost logic.
- `DistanceCostModel` and `TimeCostModel` are built-in.

Routing respects runtime blocked-edge state and remains intentionally simple, deterministic, and testable.

### 6. Simulation engine, trace, and behavior

Execution lives in `autonomous_ops_sim/simulation/`:

- `SimulationEngine` owns the map, world state, router, seed, resources, trace, and simulated time.
- `Trace` is append-only and deterministic.
- `TraceEvent` and `TraceEventType` define the stable event surface used by metrics, visualization, and bundle exports.
- The behavior layer tracks explicit vehicle operational states such as idle, moving, conflict wait, resource wait, servicing, and failure-like states.

This gives the project one source of truth for what actually happened during a run.

### 7. Jobs, tasks, resources, and dispatch

The operations layer lives in `autonomous_ops_sim/operations/`:

- `MoveTask`, `LoadTask`, and `UnloadTask` define ordered work.
- `Job` packages tasks into a unit of execution.
- `SharedResource` models finite-capacity service access.
- Dispatcher behavior is deterministic and intentionally baseline rather than “smart” by default.

### 8. Multi-vehicle coordination and reservations

Deterministic multi-vehicle coordination lives in `autonomous_ops_sim/simulation/reservations.py` and the engine’s multi-vehicle execution path:

- `VehicleRouteRequest` describes coordinated route execution requests.
- `ReservationTable` stores node, edge, and corridor occupancy windows.
- Conflict handling uses deterministic waiting rather than uncontrolled simultaneous occupancy.
- Reservation scans are optimized in Python and can optionally use a narrow native accelerator for departure-time scanning.

### 9. Metrics, exports, and public API bundles

Outward-facing analysis/export support now includes:

- engine execution summaries
- deterministic engine export JSON
- replay-oriented visualization state
- versioned **Simulation API** bundles for:
  - replay
  - live session
  - live sync

These bundles carry rich derived surfaces such as:

- static map surface
- render geometry
- motion segments
- traffic baseline
- command results
- command-center state
- vehicle inspections
- AI-assist read models

### 10. Visualization, serious viewer, and operator surfaces

Visualization support now spans multiple layers:

- replay/frame-oriented visualization state
- render geometry for roads/intersections/areas
- interpolated motion segments for smoother playback
- baseline traffic/control/queue surfaces
- command-center surfaces for selection, previews, and edge actions
- richer vehicle inspection surfaces
- AI-assist explanation/suggestion/anomaly surfaces
- a **serious viewer** that renders standalone HTML from Simulation API bundles

This is the current serious frontend foundation. It is intentionally derived from simulator truth and still leaves room for a later higher-end live UI.

### 11. Showcase and benchmark layers

The repository now includes:

- a mining-focused showpiece export flow that produces replay/live/live-sync viewers and a manifest
- a repeatable benchmark suite covering routing, reservations, scenario execution, scenario packs, visualization export, and live-sync export
- optional native reservation acceleration that is benchmark-aware and parity-tested against the Python path

## Public entrypoints

### CLI

After editable install:

```bash
autonomous-ops-sim --help
```

Current top-level CLI subcommands include:

```bash
autonomous-ops-sim run scenarios/example.json
autonomous-ops-sim execute scenarios/step_12_single_vehicle_job.json
autonomous-ops-sim benchmark --repetitions 1 --warmup-iterations 0
autonomous-ops-sim showcase --output-dir showcase_output
```

### Serious viewer

Generate or obtain a Simulation API bundle JSON, then render it through the serious viewer:

```bash
autonomous-ops-serious-viewer path/to/bundle.json
```

### Showcase exporter

The mining showcase can also be exported directly through its dedicated entrypoint:

```bash
autonomous-ops-showcase --output-dir showcase_output
```

## Installation

The project requires Python 3.11 or newer.

```bash
python3 -m pip install -e .
```

If you are working on the optional native reservation accelerator, a working C toolchain is helpful but not strictly required: the project is designed to fall back to the Python path when native compilation/loading is unavailable.

## Common workflows

### 1. Validate and summarize a scenario

```bash
python3 -m autonomous_ops_sim.cli run scenarios/example.json
```

### 2. Execute a scenario and emit deterministic export JSON

```bash
python3 -m autonomous_ops_sim.cli execute scenarios/step_12_single_vehicle_job.json
```

### 3. Run the benchmark suite

```bash
python3 -m autonomous_ops_sim.cli benchmark --repetitions 1 --warmup-iterations 0
```

### 4. Export the mining showcase artifacts

```bash
python3 -m autonomous_ops_sim.cli showcase --output-dir showcase_output
```

This writes a manifest plus replay/live/live-sync bundles and standalone viewer HTML files for the flagship mining scenario and its supporting scenario pack.

## Showcase flow

The project now includes a real mining-oriented showpiece flow.

The showcase exporter produces:

- replay bundle JSON
- replay viewer HTML
- live session bundle JSON
- live session viewer HTML
- live sync bundle JSON
- live sync viewer HTML
- scenario pack export JSON
- manifest JSON

This is currently the easiest built-in way to see a richer end-to-end project slice without writing custom scripts.

## Benchmarking and native acceleration

The benchmark suite covers a narrow but important set of current workloads:

- routing
- reservation departure scans
- scenario execution
- scenario-pack execution
- visualization export
- live-sync export

The reservation benchmark includes both:

- Python reservation departure scanning
- optional native reservation departure scanning

The native path is intentionally narrow:

- it is used only for a bounded hotspot,
- it preserves Python fallback behavior,
- it is parity-tested against the Python implementation,
- it is not intended as a broad rewrite of the simulator into native code.

## Package structure

```text
autonomous_ops_sim/
  api.py                    # Versioned replay/live/live-sync Simulation API bundles
  cli.py                    # Main CLI: run, execute, benchmark, showcase
  core/                     # Graph primitives: Node, Edge, Graph
  io/                       # Scenario loading, summaries, exports, scenario-pack support
  maps/                     # Map facade and generators/builders
  native/                   # Optional native reservation acceleration
  operations/               # Jobs, tasks, resources, dispatcher
  perf/                     # Benchmark harness and default suite
  routing/                  # Dijkstra, cost models, Router
  showcase.py               # Mining showpiece export flow
  simulation/               # Engine, scenario execution, world state, trace,
                            # behavior, reservations, live session, control surfaces
  vehicles/                 # Vehicle entities and types
  visualization/            # Replay state, geometry, motion, traffic,
                            # command center, inspections, AI assist,
                            # serious viewer, GUI viewer prototypes
scenarios/
  ... example scenarios, benchmark packs, and showpiece mining scenarios
tests/
  ... unit, integration, export, showcase, and perf-related tests
```

## Programmatic example

A minimal example that executes a scenario and emits deterministic export JSON:

```python
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario

scenario = load_scenario(Path("scenarios/step_12_single_vehicle_job.json"))
result = execute_scenario(scenario)

print(result.summary)
print(result.export_json)
```

A minimal example that exports the built-in mining showcase:

```python
from autonomous_ops_sim.showcase import export_showcase_demo

artifacts = export_showcase_demo("showcase_output")
print(artifacts.manifest_path)
```

## Determinism and testing

The project remains heavily test-driven around deterministic behavior. Coverage now spans:

- graph and map behavior
- scenario parsing and validation
- scenario execution
- CLI run/execute/benchmark/showcase paths
- world-state behavior
- routing and cost-model behavior
- simulation engine time behavior
- jobs, tasks, resources, and dispatch
- multi-vehicle reservations and conflict handling
- behavior-state transitions
- metrics/export stability
- Simulation API bundle stability
- serious viewer export behavior
- command-center and live-viewer workflows
- traffic baseline derivation
- showcase artifact generation
- benchmark harness structure
- native reservation acceleration parity and fallback stability

Repository quality commands:

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
```

Useful manual checks:

```bash
python3 -m autonomous_ops_sim.cli --help
python3 -m autonomous_ops_sim.cli benchmark --repetitions 1 --warmup-iterations 0
python3 -m autonomous_ops_sim.cli showcase --output-dir showcase_output
python3 -m pip install -e .
autonomous-ops-sim --help
autonomous-ops-showcase --help
```

## Current limitations

This README should stay honest about what is not here yet:

- The serious viewer is now real and useful, but it is still a **foundation-stage frontend**, not yet the final polished live operations UI.
- Traffic realism is present as a baseline (queues, control points, congestion sampling, command-center overlays), but it is not yet the final lane-level, signal-rich, overtaking-capable realism target.
- Vehicle motion is materially better than frame-snapping, but still short of the final realism target for acceleration, lane behavior, and high-fidelity turning.
- AI assist is currently a grounded read-model layer; it is not yet a full planner/copilot system.
- The mining showpiece is the strongest environment today; broader environment richness and a higher-end cross-platform frontend are still roadmap work.
- Native acceleration is intentionally narrow and optional; the simulator is still primarily a Python system.

## Roadmap alignment

The repo now contains work well beyond the early planning docs referenced in the old README. At a high level, the project through Step 40 now includes:

- scenario execution and packs
- metrics and export surfaces
- visualization and replay state
- live session/live sync support
- serious viewer foundation
- motion interpolation
- render geometry and map realism baseline
- traffic baseline surfaces
- command-center baseline
- vehicle inspection baseline
- AI-assist baseline
- showcase/demo export flow
- Python-side performance work
- optional native reservation acceleration

The next major phase is no longer “can the simulator execute and export?”
It is primarily about:

- stronger frontend quality
- richer map/world realism
- deeper traffic and vehicle realism
- more live operator interaction
- better showpiece polish across mining, construction-yard, and city-street environments
