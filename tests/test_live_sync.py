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
    SimulationEngine,
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    AssignSelectedDestinationViewerAction,
    BlockEdgeViewerAction,
    LiveViewerController,
    RepositionSelectedVehicleViewerAction,
    SelectVehicleViewerAction,
    build_live_runtime_snapshot,
    build_live_state_updates,
    build_live_sync_surface,
    build_visualization_state_from_live_session,
    export_live_sync_json,
)


def build_live_sync_engine() -> SimulationEngine:
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


def run_live_sync_session() -> LiveSimulationSession:
    session = LiveSimulationSession(build_live_sync_engine())
    session.advance_to(1.0)
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_by(0.5)
    session.apply(RepositionVehicleCommand(vehicle_id=77, node_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_to(3.0)
    return session


def run_live_sync_viewer() -> LiveViewerController:
    controller = LiveViewerController(LiveSimulationSession(build_live_sync_engine()))
    controller.apply_action(SelectVehicleViewerAction(vehicle_id=77))
    controller.apply_action(BlockEdgeViewerAction(edge_id=2))
    controller.apply_action(RepositionSelectedVehicleViewerAction(node_id=2))
    controller.apply_action(
        AssignSelectedDestinationViewerAction(destination_node_id=3)
    )
    return controller


def test_live_runtime_snapshot_generation_is_deterministic() -> None:
    snapshot_a = build_live_runtime_snapshot(run_live_sync_session())
    snapshot_b = build_live_runtime_snapshot(run_live_sync_session())

    assert snapshot_a == snapshot_b
    assert snapshot_a.simulated_time_s == 3.0
    assert snapshot_a.is_active is True
    assert snapshot_a.blocked_edge_ids == (2,)
    assert snapshot_a.command_count == 4
    assert snapshot_a.session_step_count == 3
    assert snapshot_a.trace_event_count == 16
    assert [
        (vehicle.vehicle_id, vehicle.node_id, vehicle.operational_state)
        for vehicle in snapshot_a.vehicles
    ] == [(77, 3, "idle")]


def test_live_state_updates_are_deterministic_and_match_visualization_frames() -> None:
    session = run_live_sync_session()
    updates = build_live_state_updates(session)
    visualization_state = build_visualization_state_from_live_session(session)

    assert updates == build_live_state_updates(run_live_sync_session())
    assert [update.trigger.source for update in updates[:5]] == [
        "session",
        "command",
        "command",
        "session",
        "command",
    ]
    assert [
        (
            update.update_index,
            update.visualization_frame_index,
            update.timestamp_s,
            update.trigger.source,
            update.trigger.event_name,
        )
        for update in updates
    ] == [
        (
            frame.frame_index - 1,
            frame.frame_index,
            frame.timestamp_s,
            frame.trigger.source,
            frame.trigger.event_name,
        )
        for frame in visualization_state.frames[1:]
    ]


def test_repeated_session_sequences_produce_identical_live_sync_output() -> None:
    surface_a = build_live_sync_surface(run_live_sync_session())
    surface_b = build_live_sync_surface(run_live_sync_session())

    export_a = export_live_sync_json(surface_a)
    export_b = export_live_sync_json(surface_b)

    assert surface_a == surface_b
    assert json.loads(export_a) == json.loads(export_b)
    assert export_a == export_b
    assert [effect.emitted_update_indices for effect in surface_a.command_effects] == [
        (1,),
        (2,),
        (4,),
        (5,),
    ]


def test_live_sync_surface_remains_compatible_with_live_viewer_state_derivation() -> None:
    controller = run_live_sync_viewer()
    surface = build_live_sync_surface(controller.session)
    state = controller.visualization_state

    assert surface.map_surface == state.map_surface
    assert surface.snapshot.blocked_edge_ids == state.frames[-1].blocked_edge_ids
    assert surface.snapshot.vehicles == state.frames[-1].vehicles
    assert [update.trigger for update in surface.updates] == [
        frame.trigger for frame in state.frames[1:]
    ]
    assert surface.snapshot.command_count == len(controller.session.command_history)
    assert surface.snapshot.trace_event_count == len(controller.session.engine.trace.events)
