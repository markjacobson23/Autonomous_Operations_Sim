import json
from pathlib import Path

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.exports import build_engine_export, export_engine_json
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    SimulationEngine,
    TraceEventCount,
    TraceEventType,
    WorldState,
    summarize_engine_execution,
)
from autonomous_ops_sim.simulation.engine import MultiVehicleExecutionResult
from autonomous_ops_sim.simulation.reservations import VehicleRouteRequest


GOLDEN_PATH = Path(__file__).parent / "golden" / "step_17_corridor_coordination_export.json"


def build_linear_corridor_engine() -> SimulationEngine:
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


def execute_corridor_conflict_case() -> tuple[SimulationEngine, MultiVehicleExecutionResult]:
    engine = build_linear_corridor_engine()
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
    return engine, result


def test_step_17_corridor_reservation_blocks_head_on_overlap_deterministically():
    _, result = execute_corridor_conflict_case()

    assert [route.vehicle_id for route in result.route_results] == [101, 202]
    assert [route.completion_time_s for route in result.route_results] == [2.0, 4.0]
    assert [len(route.waits) for route in result.route_results] == [0, 1]
    assert result.route_results[1].waits[0].duration_s == 2.0
    assert len(result.reservations.corridor_reservations) == 2
    assert result.reservations.corridor_reservations[0].node_ids == (1, 2, 3)
    assert result.reservations.corridor_reservations[0].start_time_s == 0.0
    assert result.reservations.corridor_reservations[0].end_time_s == 2.0
    assert result.reservations.corridor_reservations[1].node_ids == (3, 2, 1)
    assert result.reservations.corridor_reservations[1].start_time_s == 2.0
    assert result.reservations.corridor_reservations[1].end_time_s == 4.0


def test_step_17_corridor_wait_behavior_is_traceable_in_trace_and_summary():
    engine, result = execute_corridor_conflict_case()

    lower_priority_route = result.route_results[1]
    wait_events = [
        event
        for event in engine.trace.events
        if event.vehicle_id == lower_priority_route.vehicle_id
        and event.event_type
        in {
            TraceEventType.CONFLICT_WAIT_START,
            TraceEventType.CONFLICT_WAIT_COMPLETE,
        }
    ]
    behavior_events = [
        event
        for event in engine.trace.events
        if event.vehicle_id == lower_priority_route.vehicle_id
        and event.event_type == TraceEventType.BEHAVIOR_TRANSITION
    ]
    summary = summarize_engine_execution(engine)
    export_record = build_engine_export(engine, summary=summary)

    assert [event.timestamp_s for event in wait_events] == [0.0, 2.0]
    assert [event.duration_s for event in wait_events] == [2.0, 2.0]
    assert [
        (event.from_behavior_state, event.to_behavior_state, event.transition_reason)
        for event in behavior_events
    ] == [
        ("idle", "conflict_wait", "conflict_wait_start"),
        ("conflict_wait", "moving", "conflict_wait_complete"),
        ("moving", "idle", "route_complete"),
    ]
    assert summary.final_time_s == 4.0
    assert summary.route_count == 2
    assert summary.edge_traversal_count == 4
    assert summary.total_route_distance == 4.0
    assert summary.total_conflict_wait_time_s == 2.0
    assert summary.total_resource_wait_time_s == 0.0
    assert summary.event_counts == (
        TraceEventCount(event_type="behavior_transition", count=5),
        TraceEventCount(event_type="conflict_wait_complete", count=1),
        TraceEventCount(event_type="conflict_wait_start", count=1),
        TraceEventCount(event_type="edge_enter", count=4),
        TraceEventCount(event_type="node_arrival", count=4),
        TraceEventCount(event_type="route_complete", count=2),
        TraceEventCount(event_type="route_start", count=1),
    )
    assert export_record["summary"]["total_conflict_wait_time_s"] == 2.0
    assert export_record["trace"][4]["event_type"] == "conflict_wait_start"
    assert export_record["trace"][10]["event_type"] == "conflict_wait_complete"


def test_step_17_corridor_coordination_repeats_identically():
    engine_a, result_a = execute_corridor_conflict_case()
    engine_b, result_b = execute_corridor_conflict_case()

    summary_a = summarize_engine_execution(engine_a)
    summary_b = summarize_engine_execution(engine_b)
    export_json_a = export_engine_json(engine_a, summary=summary_a)
    export_json_b = export_engine_json(engine_b, summary=summary_b)

    assert result_a.route_results == result_b.route_results
    assert result_a.reservations.node_reservations == result_b.reservations.node_reservations
    assert result_a.reservations.edge_reservations == result_b.reservations.edge_reservations
    assert (
        result_a.reservations.corridor_reservations
        == result_b.reservations.corridor_reservations
    )
    assert engine_a.trace.events == engine_b.trace.events
    assert summary_a == summary_b
    assert export_json_a == export_json_b


def test_step_17_corridor_coordination_export_matches_golden_fixture_exactly():
    engine, _ = execute_corridor_conflict_case()
    summary = summarize_engine_execution(engine)
    export_json = export_engine_json(engine, summary=summary)

    assert json.loads(export_json) == json.loads(GOLDEN_PATH.read_text())
    assert export_json == GOLDEN_PATH.read_text()
