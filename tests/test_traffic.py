from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, WorldState
from autonomous_ops_sim.simulation.reservations import VehicleRouteRequest
from autonomous_ops_sim.visualization import (
    build_render_geometry_surface,
    build_traffic_baseline_surface,
    build_vehicle_motion_segments,
    build_visualization_state,
    sample_traffic_snapshot,
)


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


def build_corridor_traffic_inputs():
    engine = build_corridor_engine()
    engine.execute_multi_vehicle_routes(
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
    state = build_visualization_state(engine)
    render_geometry = build_render_geometry_surface(engine.map)
    motion_segments = build_vehicle_motion_segments(state)
    baseline = build_traffic_baseline_surface(
        state,
        render_geometry=render_geometry,
        motion_segments=motion_segments,
    )
    return render_geometry, motion_segments, baseline


def test_traffic_baseline_derives_control_points_and_conflict_queue_records() -> None:
    _, _, baseline = build_corridor_traffic_inputs()

    assert [
        (control.node_id, control.control_type, control.controlled_road_ids)
        for control in baseline.control_points
    ] == [
        (2, "yield", ("road-1-2", "road-2-3")),
    ]
    assert [
        (
            record.vehicle_id,
            record.node_id,
            record.road_id,
            record.queue_start_s,
            record.queue_end_s,
            record.reason,
        )
        for record in baseline.queue_records
    ] == [
        (202, 3, "road-2-3", 0.0, 2.0, "conflict_wait"),
    ]


def test_traffic_snapshot_reports_active_and_queued_road_states() -> None:
    render_geometry, motion_segments, baseline = build_corridor_traffic_inputs()

    queued_snapshot = sample_traffic_snapshot(
        timestamp_s=1.5,
        render_geometry=render_geometry,
        motion_segments=motion_segments,
        baseline=baseline,
    )
    active_snapshot = sample_traffic_snapshot(
        timestamp_s=2.5,
        render_geometry=render_geometry,
        motion_segments=motion_segments,
        baseline=baseline,
    )

    queued_road_states = {
        road_state.road_id: road_state for road_state in queued_snapshot.road_states
    }
    active_road_states = {
        road_state.road_id: road_state for road_state in active_snapshot.road_states
    }

    assert queued_road_states["road-1-2"].congestion_level == "free"
    assert queued_road_states["road-2-3"].active_vehicle_ids == (101,)
    assert queued_road_states["road-2-3"].queued_vehicle_ids == (202,)
    assert queued_road_states["road-2-3"].occupancy_count == 1
    assert queued_road_states["road-2-3"].congestion_level == "queued"
    assert active_road_states["road-2-3"].active_vehicle_ids == (202,)
    assert active_road_states["road-2-3"].queued_vehicle_ids == ()
    assert active_road_states["road-2-3"].congestion_level == "active"
