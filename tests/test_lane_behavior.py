from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, WorldState
from autonomous_ops_sim.vehicles.presentation import build_vehicle_presentation_surface
from autonomous_ops_sim.vehicles.vehicle import Vehicle, VehicleType
from autonomous_ops_sim.visualization import (
    build_render_geometry_surface,
    build_vehicle_motion_segments,
    build_visualization_state,
)


def build_lane_behavior_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (4.0, 0.0, 0.0))
    node_3 = Node(3, (8.0, 0.0, 0.0))
    node_4 = Node(4, (2.0, -2.0, 0.0))

    for node in (node_1, node_2, node_3, node_4):
        graph.add_node(node)

    graph.add_edge(Edge(1, node_1, node_2, 4.0, 6.0))
    graph.add_edge(Edge(2, node_2, node_3, 4.0, 6.0))
    graph.add_edge(Edge(3, node_4, node_2, 2.8, 4.0))
    graph.add_edge(Edge(4, node_2, node_4, 2.8, 4.0))

    render_geometry = {
        "roads": [
            {
                "id": "main-street",
                "edge_ids": [1, 2],
                "centerline": [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [8.0, 0.0, 0.0]],
                "road_class": "arterial",
                "directionality": "one_way",
                "lane_count": 2,
                "width_m": 2.6,
            },
            {
                "id": "merge-ramp",
                "edge_ids": [3, 4],
                "centerline": [[2.0, -2.0, 0.0], [4.0, 0.0, 0.0]],
                "road_class": "ramp",
                "directionality": "one_way",
                "lane_count": 1,
                "width_m": 1.2,
            },
        ],
        "intersections": [
            {
                "id": "merge-junction",
                "node_id": 2,
                "polygon": [[3.1, -0.7, 0.0], [4.9, -0.7, 0.0], [4.9, 0.7, 0.0], [3.1, 0.7, 0.0]],
                "intersection_type": "merge",
            }
        ],
        "areas": [],
        "lanes": [
            {
                "id": "main-street:lane:0",
                "road_id": "main-street",
                "lane_index": 0,
                "directionality": "forward",
                "lane_role": "passing",
                "centerline": [[0.0, 0.55, 0.0], [4.0, 0.55, 0.0], [8.0, 0.55, 0.0]],
                "width_m": 1.0,
            },
            {
                "id": "main-street:lane:1",
                "road_id": "main-street",
                "lane_index": 1,
                "directionality": "forward",
                "lane_role": "keep_lane",
                "centerline": [[0.0, -0.55, 0.0], [4.0, -0.55, 0.0], [8.0, -0.55, 0.0]],
                "width_m": 1.0,
            },
            {
                "id": "merge-ramp:lane:0",
                "road_id": "merge-ramp",
                "lane_index": 0,
                "directionality": "forward",
                "lane_role": "loading_approach",
                "centerline": [[2.0, -2.0, 0.0], [4.0, 0.0, 0.0]],
                "width_m": 1.2,
            },
        ],
        "turn_connectors": [
            {
                "id": "merge-ramp:lane:0->main-street:lane:1",
                "from_lane_id": "merge-ramp:lane:0",
                "to_lane_id": "main-street:lane:1",
                "centerline": [[4.0, 0.0, 0.0], [4.0, -0.55, 0.0]],
            }
        ],
        "stop_lines": [
            {
                "id": "merge-ramp:lane:0:stop",
                "lane_id": "merge-ramp:lane:0",
                "segment": [[3.8, -0.2, 0.0], [4.2, 0.2, 0.0]],
            }
        ],
        "merge_zones": [
            {
                "id": "main-street-merge",
                "lane_ids": ["merge-ramp:lane:0", "main-street:lane:1"],
                "kind": "merge",
                "polygon": [[3.4, -0.8, 0.0], [4.6, -0.8, 0.0], [4.6, 0.5, 0.0], [3.4, 0.5, 0.0]],
            }
        ],
    }

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (4.0, 0.0, 0.0): 2,
            (8.0, 0.0, 0.0): 3,
            (2.0, -2.0, 0.0): 4,
        },
        render_geometry=render_geometry,
    )
    vehicles = (
        Vehicle(
            id=11,
            current_node_id=1,
            position=(0.0, 0.0, 0.0),
            velocity=0.0,
            payload=0.0,
            max_payload=10.0,
            max_speed=6.0,
            vehicle_type=VehicleType.CAR,
        ),
        Vehicle(
            id=22,
            current_node_id=1,
            position=(0.0, 0.0, 0.0),
            velocity=0.0,
            payload=0.0,
            max_payload=30.0,
            max_speed=5.0,
            vehicle_type=VehicleType.HAUL_TRUCK,
        ),
        Vehicle(
            id=33,
            current_node_id=4,
            position=(2.0, -2.0, 0.0),
            velocity=0.0,
            payload=0.0,
            max_payload=8.0,
            max_speed=4.0,
            vehicle_type=VehicleType.FORKLIFT,
        ),
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=73,
        vehicles=vehicles,
    )


def test_lane_choice_prefers_role_specific_lanes_and_merge_approaches() -> None:
    engine = build_lane_behavior_engine()
    engine.execute_vehicle_route(vehicle=engine.get_vehicle(11), destination_node_id=3)
    engine.execute_vehicle_route(vehicle=engine.get_vehicle(22), destination_node_id=3)
    engine.execute_vehicle_route(vehicle=engine.get_vehicle(33), destination_node_id=3)

    state = build_visualization_state(engine)
    render_geometry = build_render_geometry_surface(engine.map)
    vehicle_presentations = tuple(
        build_vehicle_presentation_surface(
            vehicle_id=vehicle.id,
            vehicle_type=vehicle.vehicle_type,
        )
        for vehicle in engine.vehicles
    )
    segments = build_vehicle_motion_segments(
        state,
        render_geometry=render_geometry,
        vehicle_presentations=vehicle_presentations,
    )
    by_vehicle_edge = {(segment.vehicle_id, segment.edge_id): segment for segment in segments}

    assert by_vehicle_edge[(11, 1)].lane_id == "main-street:lane:0"
    assert by_vehicle_edge[(11, 1)].lane_role == "passing"
    assert "passing" in (by_vehicle_edge[(11, 1)].lane_selection_reason or "")
    assert by_vehicle_edge[(22, 1)].lane_id == "main-street:lane:1"
    assert by_vehicle_edge[(22, 1)].lane_role == "keep_lane"
    assert "keep_lane" in (by_vehicle_edge[(22, 1)].lane_selection_reason or "")
    assert by_vehicle_edge[(33, 3)].lane_role == "loading_approach"
    assert "loading_approach" in (by_vehicle_edge[(33, 3)].lane_selection_reason or "")
