from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    BlockEdgeCommand,
    LiveSimulationSession,
    SimulationEngine,
    UnblockEdgeCommand,
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    RoutePreviewRequest,
    build_live_command_center_surface,
    preview_route_command,
)


def build_command_center_engine() -> SimulationEngine:
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


def test_preview_route_command_builds_non_mutating_route_preview() -> None:
    session = LiveSimulationSession(build_command_center_engine())

    preview = preview_route_command(
        session,
        vehicle_id=77,
        destination_node_id=3,
    )

    assert preview.vehicle_id == 77
    assert preview.start_node_id == 1
    assert preview.destination_node_id == 3
    assert preview.is_actionable is True
    assert preview.reason is None
    assert preview.node_ids == (1, 2, 3)
    assert preview.edge_ids == (1, 2)
    assert preview.total_distance == 2.0
    assert session.command_history == ()


def test_command_center_surface_tracks_selection_edge_openings_and_preview_requests() -> None:
    session = LiveSimulationSession(build_command_center_engine())
    session.apply(BlockEdgeCommand(edge_id=2))

    surface = build_live_command_center_surface(
        session,
        selected_vehicle_ids=(77, 77),
        route_preview_requests=(RoutePreviewRequest(vehicle_id=77, destination_node_id=3),),
    )

    assert surface.selected_vehicle_ids == (77,)
    assert [vehicle.vehicle_id for vehicle in surface.vehicles] == [77]
    assert surface.vehicles[0].can_assign_destination is True
    assert [(edge.edge_id, edge.is_blocked, edge.available_action) for edge in surface.edges] == [
        (1, False, "block_edge"),
        (2, True, "unblock_edge"),
        (3, False, "block_edge"),
        (4, False, "block_edge"),
        (5, False, "block_edge"),
    ]
    assert surface.recent_commands == ({"command_type": "block_edge", "edge_id": 2},)
    assert surface.route_previews[0].is_actionable is True
    assert surface.route_previews[0].reason is None

    session.apply(UnblockEdgeCommand(edge_id=2))
    updated_surface = build_live_command_center_surface(session)
    assert updated_surface.edges[1].is_blocked is False
    assert updated_surface.edges[1].available_action == "block_edge"
