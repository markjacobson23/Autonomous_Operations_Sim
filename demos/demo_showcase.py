from __future__ import annotations

from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_pack_runner import run_scenario_pack
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import (
    build_visualization_state_from_controller,
    export_visualization_json,
)
from autonomous_ops_sim.visualization.viewer import render_replay_text

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    RepositionVehicleCommand,
    SimulationController,
    SimulationEngine,
    VehicleRouteRequest,
    WorldState,
    summarize_engine_execution,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle


LINE = "=" * 88
SUBLINE = "-" * 88


def section(title: str) -> None:
    print(f"\n{LINE}")
    print(title)
    print(LINE)


def subsection(title: str) -> None:
    print(f"\n{title}")
    print(SUBLINE)


def kv(label: str, value: object) -> None:
    print(f"{label:<28} {value}")


def demo_scenario_pack() -> None:
    section("1. SCENARIO PACK EVALUATION")

    pack_result = run_scenario_pack("tests/fixtures/scenario_pack")
    aggregate = pack_result.aggregate_summary

    subsection("Aggregate results")
    kv("scenario count", aggregate.scenario_count)
    kv("scenario names", aggregate.scenario_names)
    kv("total final time", aggregate.total_final_time_s)
    kv("completed jobs", aggregate.total_completed_job_count)
    kv("completed tasks", aggregate.total_completed_task_count)
    kv("route count", aggregate.total_route_count)
    kv("route distance", aggregate.total_route_distance)
    kv("service time", aggregate.total_service_time_s)
    kv("resource wait time", aggregate.total_resource_wait_time_s)
    kv("trace event count", aggregate.total_trace_event_count)

    subsection("Per-scenario summaries")
    for result in pack_result.scenario_results:
        print(
            f"{result.scenario_name:<40} "
            f"time={result.summary.final_time_s:<5} "
            f"jobs={result.summary.completed_job_count:<2} "
            f"tasks={result.summary.completed_task_count:<2} "
            f"distance={result.summary.total_route_distance}"
        )


def demo_repeated_workload() -> None:
    section("2. RICHER OPERATIONS WORKLOAD")

    scenario = load_scenario("scenarios/step_16_dispatch_vehicle_job_queue.json")
    result = execute_scenario(scenario)
    vehicle = result.engine.get_vehicle(16)

    kv("scenario", scenario.name)
    kv("final simulated time", result.summary.final_time_s)
    kv("completed jobs", result.summary.completed_job_count)
    kv("completed tasks", result.summary.completed_task_count)
    kv("route count", result.summary.route_count)
    kv("route distance", result.summary.total_route_distance)
    kv("service time", result.summary.total_service_time_s)
    kv("resource wait time", result.summary.total_resource_wait_time_s)
    kv("vehicle final node", vehicle.current_node_id)
    kv("vehicle final position", vehicle.position)
    kv("vehicle final payload", vehicle.payload)
    kv("vehicle final state", vehicle.operational_state)

    job_start_ids = [
        event.job_id
        for event in result.engine.trace.events
        if event.event_type.value == "job_start"
    ]

    subsection("Observed job execution order")
    for index, job_id in enumerate(job_start_ids, start=1):
        print(f"{index:>2}. {job_id}")


def build_corridor_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (2.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)
    graph.add_edge(Edge(1, node_1, node_2, 1.0, 1.0))
    graph.add_edge(Edge(2, node_2, node_1, 1.0, 1.0))
    graph.add_edge(Edge(3, node_2, node_3, 1.0, 1.0))
    graph.add_edge(Edge(4, node_3, node_2, 1.0, 1.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
        },
    )

    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=17,
    )


def demo_corridor_coordination() -> None:
    section("3. CORRIDOR-AWARE MULTI-VEHICLE COORDINATION")

    engine = build_corridor_engine()
    result = engine.execute_multi_vehicle_routes(
        requests=(
            VehicleRouteRequest(
                vehicle_id=202,
                start_node_id=3,
                destination_node_id=1,
                max_speed=1.0,
            ),
            VehicleRouteRequest(
                vehicle_id=101,
                start_node_id=1,
                destination_node_id=3,
                max_speed=1.0,
            ),
        )
    )

    summary = summarize_engine_execution(engine)

    subsection("Route outcomes")
    for route_result in result.route_results:
        wait_durations = [wait.duration_s for wait in route_result.waits]
        print(
            f"vehicle {route_result.vehicle_id:<4} "
            f"route={route_result.route} "
            f"completion={route_result.completion_time_s:<4} "
            f"waits={wait_durations}"
        )

    subsection("Corridor reservations")
    for reservation in result.reservations.corridor_reservations:
        print(
            f"vehicle {reservation.vehicle_id:<4} "
            f"nodes={reservation.node_ids} "
            f"window=({reservation.start_time_s}, {reservation.end_time_s})"
        )

    subsection("Coordination summary")
    kv("final simulated time", summary.final_time_s)
    kv("route count", summary.route_count)
    kv("edge traversal count", summary.edge_traversal_count)
    kv("route distance", summary.total_route_distance)
    kv("conflict wait time", summary.total_conflict_wait_time_s)


def build_controlled_engine() -> tuple[SimulationController, Vehicle]:
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

    engine = SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=180,
        vehicles=(vehicle,),
    )

    controller = SimulationController(engine)
    controller.apply_all(
        (
            BlockEdgeCommand(edge_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
            RepositionVehicleCommand(vehicle_id=77, node_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        )
    )
    return controller, vehicle


def demo_control_and_visualization() -> None:
    section("4. CONTROL COMMANDS + VISUALIZATION REPLAY")

    controller, vehicle = build_controlled_engine()
    summary = summarize_engine_execution(controller.engine)

    subsection("Final controlled-run state")
    kv("final simulated time", summary.final_time_s)
    kv("blocked edges", sorted(controller.engine.world_state.blocked_edge_ids))
    kv("vehicle final node", vehicle.current_node_id)
    kv("vehicle final position", vehicle.position)
    kv("vehicle final state", vehicle.operational_state)
    kv("trace event count", summary.trace_event_count)

    subsection("Command history")
    for record in controller.command_history:
        print(
            f"seq={record.sequence:<2} "
            f"type={record.command.command_type:<26} "
            f"start={record.started_at_s:<6} "
            f"end={record.completed_at_s}"
        )

    state = build_visualization_state_from_controller(controller)
    visualization_json = export_visualization_json(state)

    output_path = Path("demo_visualization_state.json")
    output_path.write_text(visualization_json, encoding="utf-8")

    subsection("Visualization replay surface")
    kv("frame count", len(state.frames))
    kv("visualization export", output_path)

    subsection("Replay preview")
    print(render_replay_text(state, frame_index=0), end="")
    print(render_replay_text(state, frame_index=1), end="")
    print(render_replay_text(state, frame_index=len(state.frames) - 1), end="")


def main() -> None:
    print(LINE)
    print("AUTONOMOUS OPS SIM — POST-FOUNDATION SHOWCASE")
    print(LINE)
    print("This demo walks through the strongest currently supported capabilities.")
    print("")

    demo_scenario_pack()
    demo_repeated_workload()
    demo_corridor_coordination()
    demo_control_and_visualization()

    print(f"\n{LINE}")
    print("SHOWCASE COMPLETE")
    print(LINE)


if __name__ == "__main__":
    main()