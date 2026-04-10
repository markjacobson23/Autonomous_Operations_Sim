import math

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
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    build_render_geometry_surface,
    build_vehicle_motion_segments,
    build_visualization_state_from_controller,
    sample_motion,
)


def build_motion_engine() -> SimulationEngine:
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


def build_motion_state():
    controller = SimulationController(build_motion_engine())
    controller.apply_all(
        (
            BlockEdgeCommand(edge_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
            RepositionVehicleCommand(vehicle_id=77, node_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        )
    )
    return build_visualization_state_from_controller(controller)


def test_motion_segments_follow_edge_traversal_order_deterministically() -> None:
    state = build_motion_state()
    segments = build_vehicle_motion_segments(state)

    assert [(segment.vehicle_id, segment.edge_id) for segment in segments] == [
        (77, 3),
        (77, 4),
        (77, 5),
        (77, 4),
    ]
    assert [(segment.start_time_s, segment.end_time_s) for segment in segments] == [
        (0.0, 0.2),
        (0.2, 0.4),
        (0.4, 0.7),
        (0.7, 0.8999999999999999),
    ]
    assert [segment.profile_kind for segment in segments] == [
        "triangle_authoritative",
        "triangle_authoritative",
        "triangle_authoritative",
        "triangle_authoritative",
    ]


def test_motion_sampling_interpolates_position_heading_and_speed() -> None:
    state = build_motion_state()
    sample = sample_motion(state, timestamp_s=0.1)
    vehicle = sample.vehicles[0]

    assert sample.reference_frame_index == 4
    assert vehicle.is_interpolated is True
    assert vehicle.operational_state == "moving"
    assert vehicle.active_edge_id == 3
    assert vehicle.start_node_id == 1
    assert vehicle.end_node_id == 4
    assert vehicle.position == (0.5, 0.5, 0.0)
    assert math.isclose(vehicle.heading_rad, math.pi / 4.0)
    assert math.isclose(vehicle.speed, 10.0)


def test_motion_sampling_clamps_to_authoritative_endpoints_outside_segments() -> None:
    state = build_motion_state()

    initial = sample_motion(state, timestamp_s=-1.0)
    between_routes = sample_motion(state, timestamp_s=0.4)
    final = sample_motion(state, timestamp_s=5.0)

    assert initial.timestamp_s == 0.0
    assert initial.vehicles[0].position == (0.0, 0.0, 0.0)
    assert initial.vehicles[0].is_interpolated is False
    assert between_routes.vehicles[0].position == (1.0, 0.0, 0.0)
    assert between_routes.vehicles[0].is_interpolated is False
    assert final.timestamp_s == state.final_time_s
    assert final.vehicles[0].position == (2.0, 0.0, 0.0)
    assert final.vehicles[0].is_interpolated is False


def test_motion_segments_follow_curved_render_geometry_when_available() -> None:
    graph = Graph()
    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (2.0, 0.0, 0.0))
    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 2.0, 10.0))
    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (2.0, 0.0, 0.0): 2,
        },
        render_geometry={
            "roads": [
                {
                    "id": "curved-road",
                    "edge_ids": [1],
                    "centerline": [[0.0, 0.0, 0.0], [1.0, 1.0, 0.0], [2.0, 0.0, 0.0]],
                    "directionality": "one_way",
                    "lane_count": 1,
                    "width_m": 1.0,
                }
            ]
        },
    )
    engine = SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=181,
        vehicles=(
            Vehicle(
                id=88,
                current_node_id=1,
                position=(0.0, 0.0, 0.0),
                velocity=0.0,
                payload=0.0,
                max_payload=10.0,
                max_speed=5.0,
            ),
        ),
    )
    controller = SimulationController(engine)
    controller.apply(AssignVehicleDestinationCommand(vehicle_id=88, destination_node_id=2))
    state = build_visualization_state_from_controller(controller)
    render_geometry = build_render_geometry_surface(engine.map)
    segments = build_vehicle_motion_segments(state, render_geometry=render_geometry)
    sample = sample_motion(state, timestamp_s=0.2, segments=segments)

    assert len(segments[0].path_points) == 3
    assert sample.vehicles[0].position[1] > 0.0
