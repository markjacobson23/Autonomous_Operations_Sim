import math
from typing import Any

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
from autonomous_ops_sim.simulation.behavior import VehicleOperationalState
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import build_render_geometry_surface
from autonomous_ops_sim.visualization import (
    RoutePreviewRequest,
    build_vehicle_inspection_surface,
    build_live_command_center_surface,
    preview_route_command,
)
import autonomous_ops_sim.visualization.command_center as command_center_module


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

    vehicle = Vehicle(
        id=77,
        current_node_id=1,
        position=(0.0, 0.0, 0.0),
        velocity=0.0,
        payload=0.0,
        max_payload=10.0,
        max_speed=5.0,
    )
    return build_command_center_engine_from_graph(
        graph=graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
            (1.0, 1.0, 0.0): 4,
        },
        vehicles=(vehicle,),
    )


def build_intersection_deadlock_engine() -> SimulationEngine:
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

    return build_command_center_engine_from_graph(
        graph=graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
            (1.0, 1.0, 0.0): 4,
        },
        vehicles=(
            Vehicle(
                id=77,
                current_node_id=2,
                position=(1.0, 0.0, 0.0),
                velocity=0.0,
                payload=0.0,
                max_payload=10.0,
                max_speed=5.0,
            ),
            Vehicle(
                id=78,
                current_node_id=2,
                position=(1.0, 0.0, 0.0),
                velocity=0.0,
                payload=0.0,
                max_payload=10.0,
                max_speed=5.0,
            ),
        ),
    )


def build_command_center_engine_from_graph(
    *,
    graph: Graph,
    coord_to_id: dict[tuple[float, float, float], int],
    vehicles: tuple[Vehicle, ...],
) -> SimulationEngine:
    return SimulationEngine(
        simulation_map=Map(
            graph,
            coord_to_id=coord_to_id,
        ),
        world_state=WorldState(graph),
        router=Router(),
        seed=180,
        vehicles=vehicles,
    )


def build_corridor_deadlock_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (2.0, 0.0, 0.0))

    for node in (node_1, node_2, node_3):
        graph.add_node(node)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 10.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 10.0))

    return build_command_center_engine_from_graph(
        graph=graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
        },
        vehicles=(
            Vehicle(
                id=77,
                current_node_id=2,
                position=(1.0, 0.0, 0.0),
                velocity=0.0,
                payload=0.0,
                max_payload=10.0,
                max_speed=5.0,
            ),
            Vehicle(
                id=78,
                current_node_id=1,
                position=(0.0, 0.0, 0.0),
                velocity=0.0,
                payload=0.0,
                max_payload=10.0,
                max_speed=5.0,
            ),
        ),
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
    assert preview.reason_code is None
    assert preview.node_ids == (1, 2, 3)
    assert preview.edge_ids == (1, 2)
    assert preview.total_distance == 2.0
    assert session.command_history == ()


def test_preview_route_command_marks_non_idle_vehicle_as_non_actionable() -> None:
    session = LiveSimulationSession(build_command_center_engine())
    session.engine.get_vehicle(77).behavior.transition_to(
        VehicleOperationalState.MOVING,
        reason="in_transit",
    )

    preview = preview_route_command(
        session,
        vehicle_id=77,
        destination_node_id=3,
    )

    assert preview.is_actionable is False
    assert preview.reason == "vehicle_not_idle"
    assert preview.reason_code == "vehicle_not_idle"
    assert preview.node_ids == (1, 2, 3)
    assert preview.edge_ids == (1, 2)
    assert preview.total_distance == 2.0


def test_preview_route_command_handles_unknown_vehicle_and_destination_explicitly() -> None:
    session = LiveSimulationSession(build_command_center_engine())

    unknown_vehicle_preview = preview_route_command(
        session,
        vehicle_id=999,
        destination_node_id=3,
    )
    assert unknown_vehicle_preview.is_actionable is False
    assert unknown_vehicle_preview.reason == "unknown_vehicle"
    assert unknown_vehicle_preview.reason_code == "unknown_vehicle"
    assert unknown_vehicle_preview.node_ids == ()
    assert unknown_vehicle_preview.edge_ids == ()
    assert unknown_vehicle_preview.total_distance is None

    unknown_destination_preview = preview_route_command(
        session,
        vehicle_id=77,
        destination_node_id=999,
    )
    assert unknown_destination_preview.is_actionable is False
    assert unknown_destination_preview.reason == "unknown_destination"
    assert unknown_destination_preview.reason_code == "unknown_destination"
    assert unknown_destination_preview.node_ids == ()
    assert unknown_destination_preview.edge_ids == ()
    assert unknown_destination_preview.total_distance is None


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
    assert surface.route_previews[0].reason_code is None
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
    assert surface.route_previews[0].reason_code is None

    session.apply(UnblockEdgeCommand(edge_id=2))
    updated_surface = build_live_command_center_surface(session)
    assert updated_surface.edges[1].is_blocked is False
    assert updated_surface.edges[1].available_action == "block_edge"
    assert updated_surface.ai_assist.explanations == ()
    assert updated_surface.ai_assist.suggestions == ()
    assert updated_surface.ai_assist.anomalies == ()
    assert command_center_module.command_center_surface_to_dict(updated_surface)[
        "ai_assist"
    ] == {
        "explanations": [],
        "suggestions": [],
        "anomalies": [],
    }


def test_vehicle_inspection_surface_exposes_payload_route_history_and_diagnostics() -> None:
    session = LiveSimulationSession(build_command_center_engine())
    session.apply(BlockEdgeCommand(edge_id=2))
    preview = preview_route_command(session, vehicle_id=77, destination_node_id=3)

    inspection = build_vehicle_inspection_surface(
        session,
        vehicle_id=77,
        route_preview=preview,
    )

    assert inspection.vehicle_id == 77
    assert inspection.current_node_id == 1
    assert inspection.exact_position == (0.0, 0.0, 0.0)
    assert inspection.speed == 0.0
    assert inspection.payload == 0.0
    assert inspection.max_payload == 10.0
    assert inspection.operational_state == "idle"
    assert inspection.current_job_id is None
    assert inspection.wait_reason is None
    assert inspection.route_ahead_node_ids == (1, 4, 3)
    assert inspection.route_ahead_edge_ids == (3, 4)
    assert inspection.eta_s is not None
    assert math.isclose(inspection.eta_s, 1.632993161855452)
    assert inspection.recent_commands == ({"command_type": "block_edge", "edge_id": 2},)
    assert inspection.recent_trace_events == ()
    assert [diagnostic.code for diagnostic in inspection.diagnostics] == [
        "payload_state",
        "route_preview",
        "ready_state",
    ]


def test_vehicle_inspection_surface_maps_conflict_wait_to_control_state(
    monkeypatch,
) -> None:
    session = LiveSimulationSession(build_command_center_engine())
    vehicle = session.engine.get_vehicle(77)
    vehicle.current_node_id = 2
    vehicle.position = session.engine.map.get_position(2)
    preview = preview_route_command(session, vehicle_id=77, destination_node_id=3)

    monkeypatch.setattr(
        command_center_module,
        "_active_execution_context",
        lambda _session, vehicle_id: {
            "current_job_id": None,
            "current_task_index": None,
            "current_task_type": None,
            "assigned_resource_id": None,
            "wait_reason": "conflict_wait",
        },
    )

    inspection = build_vehicle_inspection_surface(
        session,
        vehicle_id=77,
        render_geometry=build_render_geometry_surface(session.engine.map),
        route_preview=preview,
    )

    assert inspection.wait_reason == "stop_line"
    assert inspection.traffic_control_state == "stop_line"
    assert inspection.traffic_control_detail is not None
    assert "stop line" in inspection.traffic_control_detail
    assert any(diagnostic.code == "wait_reason" for diagnostic in inspection.diagnostics)


def test_ai_assist_surface_provides_explanations_and_actionable_suggestions() -> None:
    session = LiveSimulationSession(build_command_center_engine())

    surface = build_live_command_center_surface(
        session,
        selected_vehicle_ids=(77,),
        route_preview_requests=(RoutePreviewRequest(vehicle_id=77, destination_node_id=3),),
    )

    assert [explanation.summary for explanation in surface.ai_assist.explanations] == [
        "Vehicle 77 is positioned to travel 1 -> 2 -> 3."
    ]
    assert [explanation.reason_code for explanation in surface.ai_assist.explanations] == [
        "route_ready"
    ]
    assert [suggestion.kind for suggestion in surface.ai_assist.suggestions] == [
        "retask_vehicle"
    ]
    assert [suggestion.reason_code for suggestion in surface.ai_assist.suggestions] == [
        "assign_destination"
    ]
    assert surface.ai_assist.suggestions[0].proposed_command == {
        "command_type": "assign_vehicle_destination",
        "vehicle_id": 77,
        "destination_node_id": 3,
    }
    assert surface.ai_assist.anomalies == ()


def test_ai_assist_surface_explains_blocked_route_anomaly_and_reopen_suggestion() -> None:
    session = LiveSimulationSession(build_command_center_engine())
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(BlockEdgeCommand(edge_id=4))

    surface = build_live_command_center_surface(
        session,
        selected_vehicle_ids=(77,),
        route_preview_requests=(RoutePreviewRequest(vehicle_id=77, destination_node_id=3),),
    )

    assert surface.route_previews[0].reason == "no_route"
    assert surface.route_previews[0].reason_code == "no_route"
    assert [suggestion.kind for suggestion in surface.ai_assist.suggestions] == [
        "reopen_edge"
    ]
    assert [suggestion.reason_code for suggestion in surface.ai_assist.suggestions] == [
        "reopen_blocked_edge"
    ]
    assert surface.ai_assist.suggestions[0].proposed_command == {
        "command_type": "unblock_edge",
        "edge_id": 2,
    }
    assert surface.ai_assist.anomalies == ()


def test_command_center_surface_flags_intersection_deadlock_risk() -> None:
    session = LiveSimulationSession(build_intersection_deadlock_engine())

    monkeypatch_context: dict[str, Any] = {
        "current_job_id": None,
        "current_task_index": None,
        "current_task_type": None,
        "assigned_resource_id": None,
        "wait_reason": "conflict_wait",
    }

    original_context = command_center_module._active_execution_context
    def fake_active_execution_context(
        _session: LiveSimulationSession,
        *,
        vehicle_id: int,
    ) -> dict[str, Any]:
        return monkeypatch_context

    command_center_module._active_execution_context = fake_active_execution_context  # type: ignore[assignment]
    try:
        surface = build_live_command_center_surface(
            session,
            selected_vehicle_ids=(77,),
            route_preview_requests=(RoutePreviewRequest(vehicle_id=77, destination_node_id=3),),
        )
    finally:
        command_center_module._active_execution_context = original_context

    assert any(
        diagnostic.code == "deadlock_risk_intersection"
        for diagnostic in surface.vehicle_inspections[0].diagnostics
    )
    assert any(
        anomaly.reason_code == "deadlock_risk_intersection"
        for anomaly in surface.ai_assist.anomalies
    )
    assert any(
        anomaly.vehicle_id == 78 and "intersection" in (anomaly.summary or "")
        for anomaly in surface.ai_assist.anomalies
    )
    assert any(suggestion.kind == "avoid_deadlock" for suggestion in surface.ai_assist.suggestions)
    assert any(suggestion.reason_code == "deadlock_risk_intersection" for suggestion in surface.ai_assist.suggestions)


def test_command_center_surface_flags_narrow_corridor_spillback_risk() -> None:
    session = LiveSimulationSession(build_corridor_deadlock_engine())

    monkeypatch_context: dict[str, Any] = {
        "current_job_id": None,
        "current_task_index": None,
        "current_task_type": None,
        "assigned_resource_id": None,
        "wait_reason": "conflict_wait",
    }

    original_context = command_center_module._active_execution_context
    def fake_active_execution_context(
        _session: LiveSimulationSession,
        *,
        vehicle_id: int,
    ) -> dict[str, Any]:
        return monkeypatch_context

    command_center_module._active_execution_context = fake_active_execution_context  # type: ignore[assignment]
    try:
        surface = build_live_command_center_surface(
            session,
            selected_vehicle_ids=(77,),
            route_preview_requests=(RoutePreviewRequest(vehicle_id=77, destination_node_id=3),),
        )
    finally:
        command_center_module._active_execution_context = original_context

    assert any(
        diagnostic.code == "deadlock_risk_corridor"
        for diagnostic in surface.vehicle_inspections[0].diagnostics
    )
    assert any(
        anomaly.reason_code == "deadlock_risk_corridor"
        for anomaly in surface.ai_assist.anomalies
    )
    assert any(
        anomaly.vehicle_id == 78 and "spill" in (anomaly.summary or "").lower()
        for anomaly in surface.ai_assist.anomalies
    )
    assert any(suggestion.kind == "avoid_deadlock" for suggestion in surface.ai_assist.suggestions)
    assert any(suggestion.reason_code == "deadlock_risk_corridor" for suggestion in surface.ai_assist.suggestions)
