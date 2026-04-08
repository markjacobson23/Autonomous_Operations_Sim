from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, TraceEventType, WorldState
from autonomous_ops_sim.simulation.engine import MultiVehicleExecutionResult
from autonomous_ops_sim.simulation.reservations import VehicleRouteRequest


def build_two_vehicle_conflict_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 1.0, 1.0))
    graph.add_edge(Edge(2, node_2, node_1, 1.0, 1.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
        },
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=9,
    )


def execute_default_conflict_case() -> tuple[SimulationEngine, MultiVehicleExecutionResult]:
    engine = build_two_vehicle_conflict_engine()
    result = engine.execute_multi_vehicle_routes(
        requests=(
            VehicleRouteRequest(
                vehicle_id=20,
                start_node_id=2,
                destination_node_id=1,
                max_speed=1.0,
            ),
            VehicleRouteRequest(
                vehicle_id=10,
                start_node_id=1,
                destination_node_id=2,
                max_speed=1.0,
            ),
        )
    )
    return engine, result


def test_multi_vehicle_conflict_case_prevents_double_occupancy_on_reserved_segment():
    _, result = execute_default_conflict_case()

    edge_reservations = result.reservations.edge_reservations

    assert len(edge_reservations) == 2
    assert edge_reservations[0].segment_key == edge_reservations[1].segment_key
    assert edge_reservations[0].end_time_s <= edge_reservations[1].start_time_s


def test_multi_vehicle_priority_order_is_deterministic_and_configurable():
    engine = build_two_vehicle_conflict_engine()

    result = engine.execute_multi_vehicle_routes(
        requests=(
            VehicleRouteRequest(
                vehicle_id=50,
                start_node_id=2,
                destination_node_id=1,
                max_speed=1.0,
                priority=0,
            ),
            VehicleRouteRequest(
                vehicle_id=10,
                start_node_id=1,
                destination_node_id=2,
                max_speed=1.0,
                priority=5,
            ),
        )
    )

    assert [route.vehicle_id for route in result.route_results] == [50, 10]
    assert [len(route.waits) for route in result.route_results] == [0, 1]
    assert engine.trace.events[1].vehicle_id == 50


def test_multi_vehicle_conflict_response_uses_deterministic_waiting():
    engine, result = execute_default_conflict_case()

    lower_priority_route = result.route_results[1]
    wait = lower_priority_route.waits[0]
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

    assert wait.start_time_s == 0.0
    assert wait.end_time_s == 1.0
    assert wait.duration_s == 1.0
    assert [event.event_type for event in wait_events] == [
        TraceEventType.CONFLICT_WAIT_START,
        TraceEventType.CONFLICT_WAIT_COMPLETE,
    ]
    assert [event.timestamp_s for event in wait_events] == [0.0, 1.0]


def test_multi_vehicle_runs_repeat_with_same_deterministic_outcome():
    engine_a, result_a = execute_default_conflict_case()
    engine_b, result_b = execute_default_conflict_case()

    assert result_a.route_results == result_b.route_results
    assert result_a.reservations.edge_reservations == result_b.reservations.edge_reservations
    assert result_a.reservations.node_reservations == result_b.reservations.node_reservations
    assert engine_a.trace.events == engine_b.trace.events
