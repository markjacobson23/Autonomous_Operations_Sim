from __future__ import annotations

from pathlib import Path

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_pack_runner import run_scenario_pack
from autonomous_ops_sim.maps.grid_map import make_grid_map
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SimulationEngine,
    WorldState,
)
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.simulation.reservations import ReservationTable, VehicleRouteRequest
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    build_live_sync_surface,
    build_visualization_state,
    export_live_sync_json,
    export_visualization_json,
)

from autonomous_ops_sim.perf.harness import BenchmarkCase, BenchmarkSuiteResult, run_benchmark_suite


DEFAULT_BENCHMARK_SUITE_NAME = "step_29_baseline"


def build_default_benchmark_suite(
    *,
    repetitions: int = 3,
    warmup_iterations: int = 1,
) -> tuple[BenchmarkCase, ...]:
    """Build the narrow default benchmark suite for Step 29."""

    return (
        _build_routing_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
        _build_reservation_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
        _build_scenario_execution_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
        _build_scenario_pack_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
        _build_visualization_export_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
        _build_live_sync_benchmark_case(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
    )


def run_default_benchmark_suite(
    *,
    repetitions: int = 3,
    warmup_iterations: int = 1,
) -> BenchmarkSuiteResult:
    """Execute the default Step 29 benchmark suite."""

    return run_benchmark_suite(
        DEFAULT_BENCHMARK_SUITE_NAME,
        build_default_benchmark_suite(
            repetitions=repetitions,
            warmup_iterations=warmup_iterations,
        ),
    )


def _build_routing_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    simulation_map = make_grid_map(12)
    world_state = WorldState(simulation_map.graph)
    blocked_segments = (
        ((4.0, 4.0, 0.0), (5.0, 4.0, 0.0)),
        ((5.0, 4.0, 0.0), (6.0, 4.0, 0.0)),
        ((6.0, 6.0, 0.0), (6.0, 7.0, 0.0)),
    )
    blocked_edge_ids: list[int] = []
    for start_position, end_position in blocked_segments:
        edge = simulation_map.get_edge_between(
            simulation_map.get_node_id(start_position),
            simulation_map.get_node_id(end_position),
        )
        assert edge is not None
        world_state.block_edge(edge.id)
        blocked_edge_ids.append(edge.id)

    queries = tuple(
        (
            simulation_map.get_node_id(start_position),
            simulation_map.get_node_id(end_position),
        )
        for start_position, end_position in (
            ((0.0, 0.0, 0.0), (11.0, 11.0, 0.0)),
            ((0.0, 11.0, 0.0), (11.0, 0.0, 0.0)),
            ((2.0, 1.0, 0.0), (10.0, 9.0, 0.0)),
            ((1.0, 10.0, 0.0), (9.0, 2.0, 0.0)),
            ((3.0, 3.0, 0.0), (8.0, 8.0, 0.0)),
            ((8.0, 3.0, 0.0), (3.0, 8.0, 0.0)),
        )
    )
    router = Router()

    def workload() -> dict[str, object]:
        path_lengths: list[int] = []
        total_distance = 0.0
        for start_node_id, end_node_id in queries:
            distance, path = router.route(
                simulation_map.graph,
                start_node_id,
                end_node_id,
                world_state,
            )
            total_distance += distance
            path_lengths.append(len(path))

        return {
            "query_count": len(queries),
            "blocked_edge_ids": blocked_edge_ids,
            "total_distance": total_distance,
            "path_lengths": path_lengths,
        }

    return BenchmarkCase(
        name="routing_grid_paths",
        category="routing",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "map_kind": "grid",
            "grid_size": 12,
            "query_count": len(queries),
            "blocked_edge_count": len(blocked_edge_ids),
        },
        workload=workload,
    )


def _build_reservation_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    reservation_table = ReservationTable()
    for offset in range(40):
        reservation_table.reserve_node(
            vehicle_id=100 + offset,
            node_id=2,
            start_time_s=float(offset),
            end_time_s=float(offset) + 1.0,
            reason="benchmark_hold",
        )
        reservation_table.reserve_edge(
            vehicle_id=200 + offset,
            edge_id=500 + offset,
            start_node_id=2,
            end_node_id=3,
            start_time_s=float(offset),
            end_time_s=float(offset) + 0.75,
        )
        reservation_table.reserve_corridor(
            vehicle_id=300 + offset,
            node_ids=(1, 2, 3, 4),
            start_time_s=float(offset),
            end_time_s=float(offset) + 1.5,
        )

    requests = tuple(
        VehicleRouteRequest(
            vehicle_id=10 + index,
            start_node_id=1,
            destination_node_id=4,
            max_speed=1.0,
            priority=index,
        )
        for index in range(6)
    )

    def workload() -> dict[str, object]:
        departures = [
            reservation_table.earliest_departure_time(
                vehicle_id=request.vehicle_id,
                current_node_id=request.start_node_id,
                next_node_id=2,
                not_before_s=float(index),
                travel_time_s=1.0,
                corridor_node_ids=(1, 2, 3, 4),
                corridor_travel_time_s=3.0,
            )
            for index, request in enumerate(requests)
        ]
        return {
            "request_count": len(requests),
            "departure_times_s": departures,
            "total_departure_time_s": sum(departures),
            "node_reservation_count": len(reservation_table.node_reservations),
            "edge_reservation_count": len(reservation_table.edge_reservations),
            "corridor_reservation_count": len(reservation_table.corridor_reservations),
        }

    return BenchmarkCase(
        name="reservation_departure_scan",
        category="coordination",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "request_count": len(requests),
            "node_reservation_count": len(reservation_table.node_reservations),
            "edge_reservation_count": len(reservation_table.edge_reservations),
            "corridor_reservation_count": len(reservation_table.corridor_reservations),
        },
        workload=workload,
    )


def _build_scenario_execution_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    scenario_path = _repo_root() / "scenarios" / "step_21_graph_map_realism.json"
    scenario = load_scenario(scenario_path)

    def workload() -> dict[str, object]:
        result = execute_scenario(scenario)
        return {
            "scenario_name": scenario.name,
            "seed": scenario.seed,
            "final_time_s": result.summary.final_time_s,
            "trace_event_count": result.summary.trace_event_count,
            "route_count": result.summary.route_count,
            "completed_task_count": result.summary.completed_task_count,
        }

    return BenchmarkCase(
        name="scenario_execution_graph_map",
        category="scenario_execution",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "scenario_path": scenario_path.as_posix(),
            "seed": scenario.seed,
        },
        workload=workload,
    )


def _build_scenario_pack_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    pack_path = _repo_root() / "scenarios" / "benchmark_pack"

    def workload() -> dict[str, object]:
        result = run_scenario_pack(pack_path)
        summary = result.aggregate_summary
        return {
            "scenario_count": summary.scenario_count,
            "scenario_names": list(summary.scenario_names),
            "total_final_time_s": summary.total_final_time_s,
            "total_trace_event_count": summary.total_trace_event_count,
            "total_route_count": summary.total_route_count,
            "total_completed_job_count": summary.total_completed_job_count,
        }

    return BenchmarkCase(
        name="scenario_pack_execution_baseline",
        category="scenario_pack_execution",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "pack_path": pack_path.as_posix(),
        },
        workload=workload,
    )


def _build_visualization_export_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    scenario_path = _repo_root() / "scenarios" / "step_21_graph_map_realism.json"
    scenario = load_scenario(scenario_path)
    execution_result = execute_scenario(scenario)

    def workload() -> dict[str, object]:
        state = build_visualization_state(execution_result.engine)
        export_json = export_visualization_json(state)
        return {
            "frame_count": len(state.frames),
            "final_time_s": state.final_time_s,
            "json_size_bytes": len(export_json.encode("utf-8")),
            "last_trigger_event_name": state.frames[-1].trigger.event_name,
        }

    return BenchmarkCase(
        name="visualization_export_graph_map",
        category="visualization_export",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "scenario_path": scenario_path.as_posix(),
            "seed": scenario.seed,
            "trace_event_count": execution_result.summary.trace_event_count,
        },
        workload=workload,
    )


def _build_live_sync_benchmark_case(
    *,
    repetitions: int,
    warmup_iterations: int,
) -> BenchmarkCase:
    session = _build_live_sync_session()

    def workload() -> dict[str, object]:
        surface = build_live_sync_surface(session)
        export_json = export_live_sync_json(surface)
        return {
            "update_count": len(surface.updates),
            "command_effect_count": len(surface.command_effects),
            "command_count": surface.snapshot.command_count,
            "session_step_count": surface.snapshot.session_step_count,
            "json_size_bytes": len(export_json.encode("utf-8")),
        }

    return BenchmarkCase(
        name="live_sync_export_session",
        category="live_sync_export",
        repetitions=repetitions,
        warmup_iterations=warmup_iterations,
        config={
            "seed": session.engine.seed,
            "vehicle_count": len(session.engine.vehicles),
            "command_count": len(session.command_history),
            "session_step_count": len(session.progress_history),
        },
        workload=workload,
    )


def _build_live_sync_session() -> LiveSimulationSession:
    graph = Graph()
    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (2.0, 0.0, 0.0))
    node_4 = Node(4, (1.0, 1.0, 0.0))
    for node in (node_1, node_2, node_3, node_4):
        graph.add_node(node)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 10.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 10.0))
    graph.add_edge(Edge(3, node_1, node_4, 1.0, 10.0))
    graph.add_edge(Edge(4, node_4, node_3, 1.0, 10.0))
    graph.add_edge(Edge(5, node_2, node_4, 1.5, 10.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
            (1.0, 1.0, 0.0): 4,
        },
    )
    vehicle = Vehicle(
        id=77,
        current_node_id=1,
        position=(0.0, 0.0, 0.0),
        velocity=0.0,
        payload=0.0,
        max_payload=10.0,
        max_speed=5.0,
    )
    session = LiveSimulationSession(
        SimulationEngine(
            simulation_map=simulation_map,
            world_state=WorldState(graph),
            router=Router(),
            seed=180,
            vehicles=(vehicle,),
        )
    )
    session.advance_to(1.0)
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_by(0.5)
    session.apply(RepositionVehicleCommand(vehicle_id=77, node_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_to(3.0)
    return session


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
