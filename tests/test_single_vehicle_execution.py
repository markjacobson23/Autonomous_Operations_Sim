from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, TraceEventType, WorldState


def build_single_vehicle_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (10.0, 0.0, 0.0))
    node_3 = Node(3, (18.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)
    graph.add_edge(Edge(1, node_1, node_2, 10.0, 5.0))
    graph.add_edge(Edge(2, node_2, node_3, 8.0, 4.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (10.0, 0.0, 0.0): 2,
            (18.0, 0.0, 0.0): 3,
        },
    )
    world_state = WorldState(graph)
    router = Router()

    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=world_state,
        router=router,
        seed=11,
    )


def run_single_vehicle_route() -> SimulationEngine:
    engine = build_single_vehicle_engine()
    route = engine.execute_vehicle_route(
        vehicle_id=101,
        start_node_id=1,
        destination_node_id=3,
        max_speed=20.0,
    )

    assert route == (1, 2, 3)
    return engine


def test_trace_timestamps_are_monotone():
    engine = run_single_vehicle_route()

    timestamps = [event.timestamp_s for event in engine.trace.events]

    assert timestamps == sorted(timestamps)


def test_single_vehicle_trace_event_ordering_is_deterministic():
    engine = run_single_vehicle_route()

    non_behavior_events = [
        event
        for event in engine.trace.events
        if event.event_type != TraceEventType.BEHAVIOR_TRANSITION
    ]
    behavior_events = [
        event
        for event in engine.trace.events
        if event.event_type == TraceEventType.BEHAVIOR_TRANSITION
    ]

    assert [event.event_type for event in non_behavior_events] == [
        TraceEventType.ROUTE_START,
        TraceEventType.EDGE_ENTER,
        TraceEventType.NODE_ARRIVAL,
        TraceEventType.EDGE_ENTER,
        TraceEventType.NODE_ARRIVAL,
        TraceEventType.ROUTE_COMPLETE,
    ]
    assert [(event.edge_id, event.node_id) for event in non_behavior_events] == [
        (None, 1),
        (1, None),
        (None, 2),
        (2, None),
        (None, 3),
        (None, 3),
    ]
    assert [
        (
            event.from_behavior_state,
            event.to_behavior_state,
            event.transition_reason,
        )
        for event in behavior_events
    ] == [
        ("idle", "moving", "route_start"),
        ("moving", "idle", "route_complete"),
    ]


def test_single_vehicle_arrival_timing_matches_edge_traversal_time():
    engine = run_single_vehicle_route()

    assert engine.simulated_time_s == 4.0
    assert [event.timestamp_s for event in engine.trace.events] == [
        0.0,
        0.0,
        0.0,
        2.0,
        2.0,
        4.0,
        4.0,
        4.0,
    ]


def test_repeated_runs_with_same_setup_produce_same_trace():
    engine_a = run_single_vehicle_route()
    engine_b = run_single_vehicle_route()

    assert engine_a.trace.events == engine_b.trace.events
