import json

from autonomous_ops_sim.api import (
    LIVE_SESSION_BUNDLE_SCHEMA_VERSION,
    LIVE_SYNC_BUNDLE_SCHEMA_VERSION,
    REPLAY_BUNDLE_SCHEMA_VERSION,
    SIMULATION_API_VERSION,
    apply_command_with_result,
    build_live_session_bundle,
    build_live_sync_bundle,
    build_replay_bundle_from_controller,
    build_replay_bundle_from_live_session,
    export_live_session_bundle_json,
    export_live_sync_bundle_json,
    export_replay_bundle_json,
)
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
    SimulationController,
    SimulationEngine,
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    build_live_runtime_snapshot,
    build_visualization_state_from_controller,
)


def build_api_engine() -> SimulationEngine:
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


def run_api_controller() -> SimulationController:
    controller = SimulationController(build_api_engine())
    controller.apply_all(
        (
            BlockEdgeCommand(edge_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
            RepositionVehicleCommand(vehicle_id=77, node_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        )
    )
    return controller


def run_api_session() -> LiveSimulationSession:
    session = LiveSimulationSession(build_api_engine())
    session.advance_to(1.0)
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_by(0.5)
    session.apply(RepositionVehicleCommand(vehicle_id=77, node_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_to(3.0)
    return session


def test_replay_bundle_is_versioned_and_matches_existing_replay_surface() -> None:
    controller = run_api_controller()
    bundle = build_replay_bundle_from_controller(controller)
    replay_state = build_visualization_state_from_controller(controller)

    assert bundle.metadata.api_version == SIMULATION_API_VERSION
    assert bundle.metadata.surface_name == "replay_bundle"
    assert bundle.metadata.surface_schema_version == REPLAY_BUNDLE_SCHEMA_VERSION
    assert bundle.map_surface == replay_state.map_surface
    assert bundle.final_frame == replay_state.frames[-1]
    assert bundle.replay_timeline == replay_state.frames
    assert bundle.render_geometry.roads != ()
    assert [result.status for result in bundle.command_results] == [
        "accepted",
        "accepted",
        "accepted",
        "accepted",
    ]
    assert [result.sequence for result in bundle.command_results] == [0, 1, 2, 3]
    assert bundle.command_results[0].blocked_edge_ids == (2,)
    assert [segment.edge_id for segment in bundle.motion_segments] == [3, 4, 5, 4]
    assert bundle.traffic_baseline.control_points != ()
    assert bundle.traffic_baseline.queue_records == ()
    assert [
        (vehicle.vehicle_id, vehicle.node_id, vehicle.operational_state)
        for vehicle in bundle.command_results[-1].vehicles
    ] == [(77, 3, "idle")]


def test_live_session_and_live_sync_bundles_share_one_api_version() -> None:
    session = run_api_session()
    live_bundle = build_live_session_bundle(session)
    sync_bundle = build_live_sync_bundle(session)

    assert live_bundle.metadata.api_version == SIMULATION_API_VERSION
    assert live_bundle.metadata.surface_schema_version == LIVE_SESSION_BUNDLE_SCHEMA_VERSION
    assert sync_bundle.metadata.api_version == SIMULATION_API_VERSION
    assert sync_bundle.metadata.surface_schema_version == LIVE_SYNC_BUNDLE_SCHEMA_VERSION
    assert live_bundle.snapshot == build_live_runtime_snapshot(session)
    assert sync_bundle.snapshot == live_bundle.snapshot
    assert sync_bundle.map_surface == live_bundle.map_surface
    assert [result.sequence for result in live_bundle.command_results] == [0, 1, 2, 3]
    assert [result.sequence for result in sync_bundle.command_results] == [0, 1, 2, 3]
    assert len(live_bundle.motion_segments) == 4
    assert len(sync_bundle.motion_segments) == 4
    assert live_bundle.traffic_baseline == sync_bundle.traffic_baseline
    assert sync_bundle.command_results[1].emitted_update_indices == (
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
    )


def test_apply_command_with_result_returns_stable_rejection_record() -> None:
    controller = SimulationController(build_api_engine())

    result = apply_command_with_result(
        controller,
        AssignVehicleDestinationCommand(vehicle_id=999, destination_node_id=3),
    )

    assert result.status == "rejected"
    assert result.sequence is None
    assert result.message == "Unknown vehicle_id: 999"
    assert result.started_at_s == 0.0
    assert result.completed_at_s == 0.0
    assert result.result_timestamp_s == 0.0
    assert result.emitted_update_indices == ()
    assert controller.command_history == ()


def test_replay_live_and_sync_bundle_exports_are_deterministic() -> None:
    replay_bundle_a = build_replay_bundle_from_live_session(run_api_session())
    replay_bundle_b = build_replay_bundle_from_live_session(run_api_session())
    live_bundle_a = build_live_session_bundle(run_api_session())
    live_bundle_b = build_live_session_bundle(run_api_session())
    sync_bundle_a = build_live_sync_bundle(run_api_session())
    sync_bundle_b = build_live_sync_bundle(run_api_session())

    replay_json_a = export_replay_bundle_json(replay_bundle_a)
    replay_json_b = export_replay_bundle_json(replay_bundle_b)
    live_json_a = export_live_session_bundle_json(live_bundle_a)
    live_json_b = export_live_session_bundle_json(live_bundle_b)
    sync_json_a = export_live_sync_bundle_json(sync_bundle_a)
    sync_json_b = export_live_sync_bundle_json(sync_bundle_b)

    assert replay_json_a == replay_json_b
    assert live_json_a == live_json_b
    assert sync_json_a == sync_json_b
    assert json.loads(replay_json_a) == json.loads(replay_json_b)
    assert json.loads(live_json_a) == json.loads(live_json_b)
    assert json.loads(sync_json_a) == json.loads(sync_json_b)
    assert "traffic_baseline" in json.loads(replay_json_a)
    assert "traffic_baseline" in json.loads(live_json_a)
    assert "traffic_baseline" in json.loads(sync_json_a)
