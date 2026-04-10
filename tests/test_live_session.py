import json

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SessionStateError,
    SimulationEngine,
    WorldState,
    export_live_session_json,
    summarize_engine_execution,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    build_visualization_state_from_live_session,
    export_visualization_json,
)
import pytest


def build_live_session_engine() -> SimulationEngine:
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
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=180,
        vehicles=(vehicle,),
    )


def run_live_session() -> LiveSimulationSession:
    session = LiveSimulationSession(build_live_session_engine())
    session.advance_to(1.0)
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_by(0.5)
    session.apply(RepositionVehicleCommand(vehicle_id=77, node_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_to(3.0)
    return session


def test_live_session_progression_is_deterministic() -> None:
    session_a = run_live_session()
    session_b = run_live_session()

    assert session_a.progress_history == session_b.progress_history
    assert [
        (record.started_at_s, record.completed_at_s)
        for record in session_a.progress_history
    ] == [
        (0.0, 1.0),
        (1.4, 1.9),
        (2.4, 3.0),
    ]
    assert [record.sequence for record in session_a.progress_history] == [0, 1, 2]
    assert all(
        record.started_at_s <= record.completed_at_s
        for record in session_a.progress_history
    )
    assert session_a.engine.simulated_time_s == 3.0
    assert session_b.engine.simulated_time_s == 3.0


def test_typed_commands_apply_deterministically_during_live_session() -> None:
    session_a = run_live_session()
    session_b = run_live_session()

    assert session_a.command_history == session_b.command_history
    assert [record.started_at_s for record in session_a.command_history] == [
        1.0,
        1.0,
        1.9,
        1.9,
    ]
    assert [record.completed_at_s for record in session_a.command_history] == [
        1.0,
        1.4,
        1.9,
        2.4,
    ]
    assert session_a.engine.world_state.blocked_edge_ids == {2}
    assert session_b.engine.world_state.blocked_edge_ids == {2}
    assert session_a.engine.get_vehicle(77).current_node_id == 3
    assert session_b.engine.get_vehicle(77).current_node_id == 3


def test_trace_and_replay_ordering_remain_stable_after_session_control() -> None:
    session = run_live_session()
    state = build_visualization_state_from_live_session(session)

    assert [event.sequence for event in session.engine.trace.events] == list(
        range(len(session.engine.trace.events))
    )
    assert [record.sequence for record in session.command_history] == [0, 1, 2, 3]
    assert [record.sequence for record in session.progress_history] == [0, 1, 2]
    assert [
        (
            frame.frame_index,
            frame.timestamp_s,
            frame.trigger.source,
            frame.trigger.event_name,
        )
        for frame in state.frames
    ] == [
        (0, 0.0, "initial", "initial_state"),
        (1, 1.0, "session", "session_advance"),
        (2, 1.0, "command", "block_edge"),
        (3, 1.0, "trace", "behavior_transition"),
        (4, 1.0, "trace", "route_start"),
        (5, 1.0, "trace", "edge_enter"),
        (6, 1.2, "trace", "node_arrival"),
        (7, 1.2, "trace", "edge_enter"),
        (8, 1.4, "trace", "node_arrival"),
        (9, 1.4, "trace", "route_complete"),
        (10, 1.4, "trace", "behavior_transition"),
        (11, 1.9, "session", "session_advance"),
        (12, 1.9, "command", "reposition_vehicle"),
        (13, 1.9, "trace", "behavior_transition"),
        (14, 1.9, "trace", "route_start"),
        (15, 1.9, "trace", "edge_enter"),
        (16, 2.1999999999999997, "trace", "node_arrival"),
        (17, 2.1999999999999997, "trace", "edge_enter"),
        (18, 2.4, "trace", "node_arrival"),
        (19, 2.4, "trace", "route_complete"),
        (20, 2.4, "trace", "behavior_transition"),
        (21, 3.0, "session", "session_advance"),
    ]


def test_repeated_live_session_runs_produce_identical_export_and_replay() -> None:
    session_a = run_live_session()
    session_b = run_live_session()

    summary_a = summarize_engine_execution(session_a.engine)
    summary_b = summarize_engine_execution(session_b.engine)
    export_json_a = export_live_session_json(session_a, summary=summary_a)
    export_json_b = export_live_session_json(session_b, summary=summary_b)
    replay_json_a = export_visualization_json(
        build_visualization_state_from_live_session(session_a)
    )
    replay_json_b = export_visualization_json(
        build_visualization_state_from_live_session(session_b)
    )

    assert summary_a == summary_b
    assert json.loads(export_json_a) == json.loads(export_json_b)
    assert export_json_a == export_json_b
    assert replay_json_a == replay_json_b


def test_closed_live_session_rejects_future_progression_and_commands() -> None:
    session = LiveSimulationSession(build_live_session_engine())
    session.close()

    with pytest.raises(SessionStateError, match="live session is not active"):
        session.advance_to(1.0)

    with pytest.raises(SessionStateError, match="live session is not active"):
        session.apply(BlockEdgeCommand(edge_id=1))


def test_live_session_rejects_backward_progression_targets() -> None:
    session = LiveSimulationSession(build_live_session_engine())

    session.advance_to(1.0)

    with pytest.raises(
        ValueError,
        match="until_s must be greater than or equal to current simulated time",
    ):
        session.advance_to(0.5)

    assert [
        (record.started_at_s, record.completed_at_s)
        for record in session.progress_history
    ] == [(0.0, 1.0)]
