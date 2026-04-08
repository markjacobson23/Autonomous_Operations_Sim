# autonomous_ops_sim

`autonomous_ops_sim` is a Python project for building a production-quality autonomous operations and vehicle simulator. The repository has moved well past its initial scenario-loading spine: it now includes deterministic routing, explicit runtime world state, simulated-time execution, jobs and shared resources, baseline dispatching, multi-vehicle conflict handling, a vehicle behavior layer, and stable metrics/export surfaces.

The current active roadmap step is Step 11: scenario packs, metrics, visualization hooks, and outward-facing analysis/export support. The codebase already contains the core simulator layers that Step 11 builds on.

## Current status

What the project can do today:

- Load and validate JSON scenarios into typed dataclasses.
- Build and query directed graph-backed maps, including a grid-map generator for early/testing use.
- Keep immutable map topology separate from runtime blocked-edge state via `WorldState`.
- Compute routes with Dijkstra through a public `Router` surface and injectable cost models.
- Run a deterministic simulation clock through `SimulationEngine`.
- Execute single-vehicle routes and emit ordered trace events.
- Execute jobs made of move/load/unload tasks.
- Model shared operational resources with deterministic waiting behavior.
- Dispatch pending jobs with a baseline deterministic dispatcher.
- Coordinate narrow multi-vehicle route sets with reservation-based conflict avoidance.
- Track vehicle operational state through an explicit FSM-style behavior controller.
- Derive stable execution metrics and export deterministic JSON results.
- Regression-test exports against a golden fixture.

Important current boundary:

- The CLI currently exposes scenario loading/validation and summary output.
- Simulation execution, jobs, dispatcher behavior, conflict handling, metrics, and exports are available through Python APIs and are covered by tests, but they are not yet exposed as first-class CLI subcommands.

## Design goals

The codebase is organized around a few consistent design choices:

- Determinism is a first-class requirement. Seeds are explicit, trace ordering is stable, and repeated runs with the same setup are expected to match.
- Static topology is separate from runtime state. `Map` and `Graph` describe the reusable world asset, while `WorldState` owns dynamic blocked-edge conditions.
- Routing is injectable. The simulator does not hardcode a single cost assumption into the public routing surface.
- Execution is driven by simulated time, not wall clock time.
- Operational layers are additive. Jobs, resources, dispatch, conflict handling, and behavior build on the same core engine and trace surface instead of duplicating execution logic.
- Metrics and exports are derived from stable trace data, which keeps outward-facing analysis surfaces small and regression-friendly.

## Architecture overview

### 1. Core topology

The foundational graph model lives in `autonomous_ops_sim/core/`:

- `Node` and `NodeType` define graph locations and semantic roles.
- `Edge` defines directed traversable segments with `distance` and `speed_limit`.
- `Graph` stores nodes, edges, and adjacency lists, and enforces basic graph integrity.

This is the simulator’s low-level topology layer. It is intentionally local and project-owned; core graph logic does not depend on an external graph library.

### 2. Map layer

The spatial facade lives in `autonomous_ops_sim/maps/`:

- `Map` wraps a `Graph` with coordinate-based lookup, node-type queries, region queries, neighbor lookup, edge lookup, and path validation.
- `make_grid_map()` in `grid_map.py` produces a simple bidirectional grid map for early/testing use.

The grid map is useful today, but it is not treated as the long-term identity of the simulator.

### 3. Scenario/config layer

The scenario/config surface lives across `autonomous_ops_sim/io/` and `autonomous_ops_sim/simulation/scenario.py`:

- `Scenario`, `MapSpec`, and `VehicleSpec` are typed dataclasses.
- `load_scenario()` reads JSON, validates required fields, enforces minimal schema constraints, and returns typed objects.
- `format_scenario_summary()` produces deterministic human-readable summaries for CLI use.

Current scenario support is intentionally narrow and stable:

- Map kind: `grid`
- Required top-level fields: `name`, `seed`, `duration_s`, `map`, `vehicles`
- Vehicle entries include ID, position, velocity, payload, max payload, max speed, and optional `vehicle_type`

### 4. Runtime world state

`autonomous_ops_sim/simulation/world_state.py` provides `WorldState`, which currently owns runtime blocked-edge state.

This split matters because:

- the same static map can be reused across runs,
- runtime changes do not mutate the map asset,
- resetting runtime conditions is explicit and deterministic.

### 5. Routing

Routing lives in `autonomous_ops_sim/routing/`:

- `Router` is the public shortest-path surface.
- `dijkstra()` implements pathfinding.
- `CostModel` is a protocol for edge-cost injection.
- `DistanceCostModel` and `TimeCostModel` are the built-in cost models.

Routing honors `WorldState` blocked edges and validates that injected costs remain non-negative for Dijkstra-based operation.

### 6. Simulation engine and trace

Execution lives in `autonomous_ops_sim/simulation/`:

- `SimulationEngine` owns the static map, runtime world state, router, seed, deterministic RNG, resources, trace, and simulated time.
- `run(until_s)` advances simulated time monotonically.
- `Trace` is append-only and deterministic.
- `TraceEvent` and `TraceEventType` define the stable event surface used by execution, metrics, and exports.

This gives the project a single source of truth for “what happened during the run.”

### 7. Vehicle execution

`VehicleProcess` executes work for a single vehicle over simulated time:

- `execute_route()` performs routing, moves along edges, advances time from edge travel, and emits route/arrival trace events.
- `execute_job()` executes an ordered `Job` through move/load/unload tasks.
- Service tasks can consume simulated time and optionally reserve shared resources.

Travel time is based on both vehicle max speed and edge speed limit.

### 8. Jobs, tasks, resources, and dispatch

The operations layer lives in `autonomous_ops_sim/operations/`:

- `MoveTask`, `LoadTask`, and `UnloadTask` define ordered operational work.
- `Job` packages tasks into a single unit of execution.
- `SharedResource` models finite-capacity deterministic service access.
- `FirstFeasibleDispatcher` selects the first pending feasible job for a vehicle.

Dispatcher behavior is intentionally baseline and deterministic rather than sophisticated.

### 9. Multi-vehicle conflict handling

Deterministic conflict handling lives in `autonomous_ops_sim/simulation/reservations.py` and the multi-vehicle execution path in `SimulationEngine`:

- `VehicleRouteRequest` describes a coordinated route request.
- `ReservationTable` stores node and edge occupancy windows.
- Conflict handling uses deterministic waiting rather than unconstrained simultaneous occupancy.
- The engine can produce a `MultiVehicleExecutionResult` with per-vehicle route outcomes and reservation data.

This is a controlled baseline for shared-space safety and reproducibility.

### 10. Behavior layer

The behavior layer lives in `autonomous_ops_sim/simulation/behavior.py`:

- `VehicleBehaviorController` tracks explicit operational states.
- The current FSM includes `idle`, `moving`, `conflict_wait`, `resource_wait`, `servicing`, and `failed`.
- Transitions are validated and emitted into the trace as behavior events.

This keeps operational state logic explicit and testable without introducing a much larger behavior framework.

### 11. Metrics and export surfaces

Step 11’s outward-facing analysis layer lives in:

- `autonomous_ops_sim/simulation/metrics.py`
- `autonomous_ops_sim/io/exports.py`

Current Step 11 surfaces include:

- `summarize_engine_execution()` for stable derived metrics
- `build_engine_export()` for structured export records
- `export_engine_json()` for deterministic JSON output
- golden-regression coverage via `tests/golden/step_11_metrics_export.json`

Metrics currently summarize things like:

- final simulated time
- vehicles involved
- route, job, and task completion counts
- edge traversals and node arrivals
- total route distance
- total service time
- total resource wait time
- total conflict wait time
- counts per trace event type

## Package structure

```text
autonomous_ops_sim/
  cli.py                    # Thin CLI: scenario load/validate/summary
  core/                     # Graph primitives: Node, Edge, Graph
  io/                       # Scenario loading, summaries, exports
  maps/                     # Map facade and grid-map generator
  operations/               # Jobs, tasks, resources, dispatcher
  routing/                  # Dijkstra, cost models, Router
  simulation/               # Scenario types, world state, engine, trace,
                            # behavior, reservations, metrics, vehicle process
  vehicles/                 # Vehicle types and a minimal Vehicle object
docs/
  roadmap.md
  current_phase.md
  step-11-metrics-exports.md
scenarios/
  example.json
tests/
  ... unit and regression tests across all current layers
```

## Public entrypoints

Today’s most important entrypoints are:

- CLI:
  - `python3 -m autonomous_ops_sim.cli --help`
  - `python3 -m autonomous_ops_sim.cli run scenarios/example.json`
  - `autonomous-ops-sim --help` after editable install
- Routing:
  - `autonomous_ops_sim.routing.Router`
  - `autonomous_ops_sim.routing.DistanceCostModel`
  - `autonomous_ops_sim.routing.TimeCostModel`
- Simulation:
  - `autonomous_ops_sim.simulation.SimulationEngine`
  - `autonomous_ops_sim.simulation.WorldState`
  - `autonomous_ops_sim.simulation.Trace`
  - `autonomous_ops_sim.simulation.summarize_engine_execution`
- Exports:
  - `autonomous_ops_sim.io.exports.build_engine_export`
  - `autonomous_ops_sim.io.exports.export_engine_json`

## Installation

The project requires Python 3.11 or newer.

```bash
python3 -m pip install -e .
```

## CLI usage

Show help:

```bash
python3 -m autonomous_ops_sim.cli --help
```

Validate and summarize the example scenario:

```bash
python3 -m autonomous_ops_sim.cli run scenarios/example.json
```

Installed console script:

```bash
autonomous-ops-sim run scenarios/example.json
```

The current CLI prints a deterministic scenario summary. It does not yet run full simulator executions from scenario files.

## Example scenario

The repository includes `scenarios/example.json`, which demonstrates the current scenario schema:

```json
{
  "name": "basic_grid_demo",
  "seed": 123,
  "duration_s": 1000.0,
  "map": {
    "kind": "grid",
    "params": {
      "grid_size": 5
    }
  },
  "vehicles": [
    {
      "id": 1,
      "position": [0, 0, 0],
      "velocity": 0.0,
      "payload": 0.0,
      "max_payload": 100.0,
      "max_speed": 25.0
    }
  ]
}
```

## Programmatic example

The simulator’s richest capabilities are currently exposed as Python APIs. A minimal example looks like this:

```python
from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.exports import export_engine_json
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, WorldState, summarize_engine_execution

graph = Graph()
node_1 = Node(1, (0.0, 0.0, 0.0))
node_2 = Node(2, (10.0, 0.0, 0.0))
node_3 = Node(3, (15.0, 0.0, 0.0))

graph.add_node(node_1)
graph.add_node(node_2)
graph.add_node(node_3)
graph.add_edge(Edge(1, node_1, node_2, 10.0, 5.0))
graph.add_edge(Edge(2, node_2, node_3, 5.0, 5.0))

simulation_map = Map(
    graph,
    coord_to_id={
        (0.0, 0.0, 0.0): 1,
        (10.0, 0.0, 0.0): 2,
        (15.0, 0.0, 0.0): 3,
    },
)

engine = SimulationEngine(
    simulation_map=simulation_map,
    world_state=WorldState(graph),
    router=Router(),
    seed=117,
)

engine.execute_job(
    vehicle_id=911,
    start_node_id=1,
    max_speed=5.0,
    job=Job(
        id="example-job",
        tasks=(
            MoveTask(destination_node_id=2),
            LoadTask(node_id=2, amount=4.0, service_duration_s=3.0),
            MoveTask(destination_node_id=3),
            UnloadTask(node_id=3, amount=4.0, service_duration_s=1.0),
        ),
    ),
    max_payload=8.0,
)

summary = summarize_engine_execution(engine)
print(summary)
print(export_engine_json(engine, summary=summary))
```

## Determinism and testing

The project is heavily test-driven around deterministic behavior. Tests currently cover:

- graph and map behavior
- grid map generation
- scenario parsing and validation
- CLI scenario loading
- world-state separation from static maps
- routing and cost-model behavior
- simulation engine time behavior
- single-vehicle route execution
- jobs, tasks, and shared resources
- dispatcher selection and execution
- multi-vehicle conflict handling
- behavior-state transitions and failure/recovery
- metrics/export stability and golden regression output

Repository quality commands:

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy autonomous_ops_sim tests
```

If you change CLI behavior, also verify:

```bash
python3 -m autonomous_ops_sim.cli --help
python3 -m pip install -e .
autonomous-ops-sim --help
```

## Current limitations

The README should be honest about what is not here yet:

- Scenario files are currently validated and summarized, but not yet turned into end-to-end executable simulator runs through the CLI.
- The supported scenario map kind is currently `grid`.
- The `Vehicle` class exists but is still minimal; most execution flows currently use explicit scalar inputs and typed specs rather than a richer persistent vehicle entity.
- Visualization hooks are still minimal.
- There is no large dashboard, animation layer, or broad external environment wrapper yet.

## Roadmap alignment

The source-of-truth planning docs are:

- `docs/current_phase.md`
- `docs/step-11-metrics-exports.md`
- `docs/roadmap.md`

Development is intended to stay roadmap-aligned, additive, and production-like: avoid speculative rewrites, avoid smuggling later architecture into earlier phases, and prefer clear responsibility boundaries over convenience abstractions.
