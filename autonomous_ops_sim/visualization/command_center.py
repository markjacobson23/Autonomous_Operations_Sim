from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.io.exports import trace_event_to_dict
from autonomous_ops_sim.simulation.kinematics import estimate_edge_travel_time_s
from autonomous_ops_sim.simulation import LiveSimulationSession, command_to_dict
from autonomous_ops_sim.visualization.geometry import (
    RenderGeometrySurface,
    build_render_geometry_surface,
)


@dataclass(frozen=True)
class RoutePreviewRequest:
    """Explicit route preview request for one vehicle and destination."""

    vehicle_id: int
    destination_node_id: int


@dataclass(frozen=True)
class RoutePreviewSurface:
    """Stable preview of one candidate command-center route assignment."""

    vehicle_id: int
    destination_node_id: int
    start_node_id: int
    is_actionable: bool
    reason: str | None
    reason_code: str | None
    node_ids: tuple[int, ...]
    edge_ids: tuple[int, ...]
    total_distance: float | None


@dataclass(frozen=True)
class CommandCenterVehicleSurface:
    """Stable command-center summary for one live vehicle."""

    vehicle_id: int
    current_node_id: int
    operational_state: str
    can_assign_destination: bool
    can_reposition: bool


@dataclass(frozen=True)
class VehicleDiagnosticSurface:
    """Deterministic diagnostic hook surfaced to the operator for one vehicle."""

    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class _DeadlockRisk:
    """Internal deadlock-risk summary reused across diagnostics and review surfaces."""

    code: str
    severity: str
    summary: str
    mitigation: str
    vehicle_id: int


@dataclass(frozen=True)
class VehicleInspectionSurface:
    """Stable operator-facing inspection record for one selected vehicle."""

    vehicle_id: int
    current_node_id: int
    exact_position: tuple[float, float, float]
    speed: float
    payload: float
    max_payload: float
    operational_state: str
    current_job_id: str | None
    current_task_index: int | None
    current_task_type: str | None
    assigned_resource_id: str | None
    wait_reason: str | None
    traffic_control_state: str | None
    traffic_control_detail: str | None
    eta_s: float | None
    route_ahead_node_ids: tuple[int, ...]
    route_ahead_edge_ids: tuple[int, ...]
    recent_commands: tuple[dict[str, Any], ...]
    recent_trace_events: tuple[dict[str, Any], ...]
    diagnostics: tuple[VehicleDiagnosticSurface, ...]


@dataclass(frozen=True)
class AIAssistExplanation:
    """Deterministic operator-support explanation over authoritative vehicle state."""

    vehicle_id: int
    reason_code: str
    summary: str
    rationale_codes: tuple[str, ...]


@dataclass(frozen=True)
class AIAssistSuggestion:
    """Deterministic heuristic suggestion derived from runtime truth."""

    suggestion_id: str
    kind: str
    priority: str
    reason_code: str
    summary: str
    proposed_command: dict[str, Any] | None = None
    target_vehicle_id: int | None = None
    target_edge_id: int | None = None


@dataclass(frozen=True)
class AIAssistAnomaly:
    """Deterministic derived anomaly over authoritative state."""

    anomaly_id: str
    severity: str
    reason_code: str
    summary: str
    vehicle_id: int | None = None


@dataclass(frozen=True)
class AIAssistSurface:
    """Deterministic operator-support read-model layered above command-center truth."""

    explanations: tuple[AIAssistExplanation, ...]
    suggestions: tuple[AIAssistSuggestion, ...]
    anomalies: tuple[AIAssistAnomaly, ...]


@dataclass(frozen=True)
class CommandCenterEdgeSurface:
    """Stable operator-facing open/close action summary for one edge."""

    edge_id: int
    is_blocked: bool
    available_action: str


@dataclass(frozen=True)
class CommandCenterSurface:
    """Stable command-center state derived from the authoritative live session."""

    simulated_time_s: float
    selected_vehicle_ids: tuple[int, ...]
    vehicles: tuple[CommandCenterVehicleSurface, ...]
    edges: tuple[CommandCenterEdgeSurface, ...]
    recent_commands: tuple[dict[str, Any], ...]
    route_previews: tuple[RoutePreviewSurface, ...]
    vehicle_inspections: tuple[VehicleInspectionSurface, ...]
    ai_assist: AIAssistSurface


def preview_route_command(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    destination_node_id: int,
) -> RoutePreviewSurface:
    """Build a deterministic route preview without mutating the live session."""

    try:
        vehicle = session.engine.get_vehicle(vehicle_id)
    except KeyError:
        return RoutePreviewSurface(
            vehicle_id=vehicle_id,
            destination_node_id=destination_node_id,
            start_node_id=-1,
            is_actionable=False,
            reason="unknown_vehicle",
            reason_code=_normalize_reason_code("unknown_vehicle"),
            node_ids=(),
            edge_ids=(),
            total_distance=None,
        )

    if not session.engine.map.graph.has_node(destination_node_id):
        return RoutePreviewSurface(
            vehicle_id=vehicle_id,
            destination_node_id=destination_node_id,
            start_node_id=vehicle.current_node_id,
            is_actionable=False,
            reason="unknown_destination",
            reason_code=_normalize_reason_code("unknown_destination"),
            node_ids=(),
            edge_ids=(),
            total_distance=None,
        )

    try:
        total_distance, node_ids = session.engine.router.route(
            session.engine.map.graph,
            vehicle.current_node_id,
            destination_node_id,
            world_state=session.engine.world_state,
        )
    except ValueError:
        return RoutePreviewSurface(
            vehicle_id=vehicle_id,
            destination_node_id=destination_node_id,
            start_node_id=vehicle.current_node_id,
            is_actionable=False,
            reason="no_route",
            reason_code=_normalize_reason_code("no_route"),
            node_ids=(),
            edge_ids=(),
            total_distance=None,
        )

    is_idle = vehicle.operational_state == "idle"
    return RoutePreviewSurface(
        vehicle_id=vehicle_id,
        destination_node_id=destination_node_id,
        start_node_id=vehicle.current_node_id,
        is_actionable=is_idle,
        reason=None if is_idle else "vehicle_not_idle",
        reason_code=None if is_idle else _normalize_reason_code("vehicle_not_idle"),
        node_ids=tuple(node_ids),
        edge_ids=_edge_ids_for_node_path(session, tuple(node_ids)),
        total_distance=total_distance,
    )


def build_live_command_center_surface(
    session: LiveSimulationSession,
    *,
    selected_vehicle_ids: tuple[int, ...] | list[int] = (),
    route_preview_requests: tuple[RoutePreviewRequest, ...]
    | list[RoutePreviewRequest] = (),
) -> CommandCenterSurface:
    """Build the command-center state for one authoritative live session."""

    render_geometry = build_render_geometry_surface(session.engine.map)
    normalized_selection = _normalize_selected_vehicle_ids(
        session,
        selected_vehicle_ids,
    )
    route_previews = tuple(
        preview_route_command(
            session,
            vehicle_id=request.vehicle_id,
            destination_node_id=request.destination_node_id,
        )
        for request in route_preview_requests
    )
    vehicle_inspections = tuple(
        build_vehicle_inspection_surface(
            session,
            vehicle_id=vehicle_id,
            render_geometry=render_geometry,
            route_preview=_preview_for_vehicle(
                vehicle_id=vehicle_id,
                route_previews=route_previews,
            ),
        )
        for vehicle_id in normalized_selection
    )
    return CommandCenterSurface(
        simulated_time_s=session.engine.simulated_time_s,
        selected_vehicle_ids=normalized_selection,
        vehicles=tuple(
            CommandCenterVehicleSurface(
                vehicle_id=vehicle.id,
                current_node_id=vehicle.current_node_id,
                operational_state=vehicle.operational_state,
                can_assign_destination=vehicle.operational_state == "idle",
                can_reposition=vehicle.operational_state == "idle",
            )
            for vehicle in session.engine.vehicles
            if getattr(vehicle, "is_active", True)
        ),
        edges=tuple(
            CommandCenterEdgeSurface(
                edge_id=edge_id,
                is_blocked=session.engine.world_state.is_edge_blocked(edge_id),
                available_action=(
                    "unblock_edge"
                    if session.engine.world_state.is_edge_blocked(edge_id)
                    else "block_edge"
                ),
            )
            for edge_id in sorted(session.engine.map.graph.edges)
        ),
        recent_commands=tuple(
            command_to_dict(record.command)
            for record in session.command_history[-8:]
        ),
        route_previews=route_previews,
        vehicle_inspections=vehicle_inspections,
        ai_assist=build_ai_assist_surface(
            session,
            render_geometry=render_geometry,
            vehicle_inspections=vehicle_inspections,
            route_previews=route_previews,
        ),
    )


def build_vehicle_inspection_surface(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    render_geometry: RenderGeometrySurface | None = None,
    route_preview: RoutePreviewSurface | None = None,
) -> VehicleInspectionSurface:
    """Build one richer inspection record from authoritative session state."""

    vehicle = session.engine.get_vehicle(vehicle_id)
    context = _active_execution_context(session, vehicle_id=vehicle_id)
    traffic_control_state, traffic_control_detail, wait_reason = _traffic_control_wait_state(
        current_node_id=vehicle.current_node_id,
        wait_reason=context["wait_reason"],
        render_geometry=render_geometry,
    )
    targeted_commands = tuple(
        command_to_dict(record.command)
        for record in session.command_history
        if _command_targets_vehicle(record.command, vehicle_id=vehicle_id)
    )
    recent_commands = (
        targeted_commands[-6:]
        if targeted_commands
        else tuple(command_to_dict(record.command) for record in session.command_history[-6:])
    )
    recent_trace_events = tuple(
        trace_event_to_dict(event)
        for event in session.engine.trace.events
        if event.vehicle_id == vehicle_id
    )[-8:]
    return VehicleInspectionSurface(
        vehicle_id=vehicle_id,
        current_node_id=vehicle.current_node_id,
        exact_position=vehicle.position,
        speed=vehicle.velocity,
        payload=vehicle.payload,
        max_payload=vehicle.max_payload,
        operational_state=vehicle.operational_state,
        current_job_id=context["current_job_id"],
        current_task_index=context["current_task_index"],
        current_task_type=context["current_task_type"],
        assigned_resource_id=context["assigned_resource_id"],
        wait_reason=wait_reason,
        traffic_control_state=traffic_control_state,
        traffic_control_detail=traffic_control_detail,
        eta_s=_estimate_eta_s(
            session,
            route_preview=route_preview,
        ),
        route_ahead_node_ids=route_preview.node_ids if route_preview is not None else (),
        route_ahead_edge_ids=route_preview.edge_ids if route_preview is not None else (),
        recent_commands=recent_commands,
        recent_trace_events=recent_trace_events,
        diagnostics=(
            _build_vehicle_diagnostics(
                vehicle_id=vehicle_id,
                vehicle=vehicle,
                route_preview=route_preview,
                wait_reason=wait_reason,
                current_job_id=context["current_job_id"],
            )
            + _build_deadlock_diagnostics(
                session,
                vehicle_id=vehicle_id,
                current_node_id=vehicle.current_node_id,
                current_position=vehicle.position,
                render_geometry=render_geometry,
                route_preview=route_preview,
                wait_reason=wait_reason,
            )
        ),
    )


def route_preview_surface_to_dict(
    preview: RoutePreviewSurface,
) -> dict[str, Any]:
    """Convert one route preview into a stable JSON-ready record."""

    return {
        "vehicle_id": preview.vehicle_id,
        "destination_node_id": preview.destination_node_id,
        "start_node_id": preview.start_node_id,
        "is_actionable": preview.is_actionable,
        "reason": preview.reason,
        "reason_code": preview.reason_code,
        "node_ids": list(preview.node_ids),
        "edge_ids": list(preview.edge_ids),
        "total_distance": preview.total_distance,
    }


def vehicle_inspection_surface_to_dict(
    inspection: VehicleInspectionSurface,
) -> dict[str, Any]:
    """Convert one vehicle inspection into a stable JSON-ready record."""

    return {
        "vehicle_id": inspection.vehicle_id,
        "current_node_id": inspection.current_node_id,
        "exact_position": list(inspection.exact_position),
        "speed": inspection.speed,
        "payload": inspection.payload,
        "max_payload": inspection.max_payload,
        "operational_state": inspection.operational_state,
        "current_job_id": inspection.current_job_id,
        "current_task_index": inspection.current_task_index,
        "current_task_type": inspection.current_task_type,
        "assigned_resource_id": inspection.assigned_resource_id,
        "wait_reason": inspection.wait_reason,
        "traffic_control_state": inspection.traffic_control_state,
        "traffic_control_detail": inspection.traffic_control_detail,
        "eta_s": inspection.eta_s,
        "route_ahead_node_ids": list(inspection.route_ahead_node_ids),
        "route_ahead_edge_ids": list(inspection.route_ahead_edge_ids),
        "recent_commands": list(inspection.recent_commands),
        "recent_trace_events": list(inspection.recent_trace_events),
        "diagnostics": [
            {
                "code": diagnostic.code,
                "severity": diagnostic.severity,
                "message": diagnostic.message,
            }
            for diagnostic in inspection.diagnostics
        ],
    }


def ai_assist_surface_to_dict(surface: AIAssistSurface) -> dict[str, Any]:
    """Convert deterministic operator-support state into a stable JSON-ready record."""

    return {
        "explanations": [
            {
                "vehicle_id": explanation.vehicle_id,
                "reason_code": explanation.reason_code,
                "summary": explanation.summary,
                "rationale_codes": list(explanation.rationale_codes),
            }
            for explanation in surface.explanations
        ],
        "suggestions": [
            {
                "suggestion_id": suggestion.suggestion_id,
                "kind": suggestion.kind,
                "priority": suggestion.priority,
                "reason_code": suggestion.reason_code,
                "summary": suggestion.summary,
                "proposed_command": suggestion.proposed_command,
                "target_vehicle_id": suggestion.target_vehicle_id,
                "target_edge_id": suggestion.target_edge_id,
            }
            for suggestion in surface.suggestions
        ],
        "anomalies": [
            {
                "anomaly_id": anomaly.anomaly_id,
                "severity": anomaly.severity,
                "reason_code": anomaly.reason_code,
                "summary": anomaly.summary,
                "vehicle_id": anomaly.vehicle_id,
            }
            for anomaly in surface.anomalies
        ],
    }


def command_center_surface_to_dict(
    surface: CommandCenterSurface,
) -> dict[str, Any]:
    """Convert command-center state into a stable JSON-ready record."""

    return {
        "simulated_time_s": surface.simulated_time_s,
        "selected_vehicle_ids": list(surface.selected_vehicle_ids),
        "vehicles": [
            {
                "vehicle_id": vehicle.vehicle_id,
                "current_node_id": vehicle.current_node_id,
                "operational_state": vehicle.operational_state,
                "can_assign_destination": vehicle.can_assign_destination,
                "can_reposition": vehicle.can_reposition,
            }
            for vehicle in surface.vehicles
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "is_blocked": edge.is_blocked,
                "available_action": edge.available_action,
            }
            for edge in surface.edges
        ],
        "recent_commands": list(surface.recent_commands),
        "route_previews": [
            route_preview_surface_to_dict(preview)
            for preview in surface.route_previews
        ],
        "vehicle_inspections": [
            vehicle_inspection_surface_to_dict(inspection)
            for inspection in surface.vehicle_inspections
        ],
        "ai_assist": ai_assist_surface_to_dict(surface.ai_assist),
    }


def _normalize_selected_vehicle_ids(
    session: LiveSimulationSession,
    selected_vehicle_ids: tuple[int, ...] | list[int],
) -> tuple[int, ...]:
    ordered_unique: list[int] = []
    seen: set[int] = set()
    for vehicle_id in selected_vehicle_ids:
        if vehicle_id in seen:
            continue
        try:
            vehicle = session.engine.get_vehicle(vehicle_id)
        except KeyError:
            continue
        if not getattr(vehicle, "is_active", True):
            continue
        seen.add(vehicle_id)
        ordered_unique.append(vehicle_id)
    return tuple(ordered_unique)


def _edge_ids_for_node_path(
    session: LiveSimulationSession,
    node_ids: tuple[int, ...],
) -> tuple[int, ...]:
    edge_ids: list[int] = []
    for start_node_id, end_node_id in zip(node_ids, node_ids[1:]):
        edge = session.engine.map.get_edge_between(start_node_id, end_node_id)
        if edge is None:
            raise RuntimeError(
                "Route preview resolved a node path with a missing edge: "
                f"{start_node_id} -> {end_node_id}"
            )
        edge_ids.append(edge.id)
    return tuple(edge_ids)


def _active_execution_context(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
) -> dict[str, Any]:
    current_job_id: str | None = None
    current_task_index: int | None = None
    current_task_type: str | None = None
    assigned_resource_id: str | None = None
    wait_reason: str | None = None

    for event in session.engine.trace.events:
        if event.vehicle_id != vehicle_id:
            continue
        event_type = event.event_type.value
        if event_type == "job_start":
            current_job_id = event.job_id
        elif event_type == "task_start":
            current_task_index = event.task_index
            current_task_type = event.task_type
        elif event_type in {"resource_wait_start", "service_start"}:
            assigned_resource_id = event.resource_id
        elif event_type in {"resource_wait_complete", "service_complete"}:
            assigned_resource_id = None
        elif event_type == "task_complete":
            current_task_index = None
            current_task_type = None
            assigned_resource_id = None
        elif event_type == "job_complete":
            current_job_id = None
        elif event_type == "behavior_transition" and event.to_behavior_state in {
            "conflict_wait",
            "resource_wait",
            "failed",
        }:
            wait_reason = event.wait_reason or event.transition_reason
        elif event_type == "conflict_wait_start" and event.wait_reason is not None:
            wait_reason = event.wait_reason
        elif event_type == "behavior_transition" and event.to_behavior_state in {
            "moving",
            "idle",
            "servicing",
        }:
            wait_reason = None

    return {
        "current_job_id": current_job_id,
        "current_task_index": current_task_index,
        "current_task_type": current_task_type,
        "assigned_resource_id": assigned_resource_id,
        "wait_reason": wait_reason,
    }


def _preview_for_vehicle(
    *,
    vehicle_id: int,
    route_previews: tuple[RoutePreviewSurface, ...],
) -> RoutePreviewSurface | None:
    for preview in reversed(route_previews):
        if preview.vehicle_id == vehicle_id:
            return preview
    return None


def _estimate_eta_s(
    session: LiveSimulationSession,
    *,
    route_preview: RoutePreviewSurface | None,
) -> float | None:
    if route_preview is None or not route_preview.edge_ids:
        return None
    travel_time_s = 0.0
    vehicle = session.engine.get_vehicle(route_preview.vehicle_id)
    for edge_id in route_preview.edge_ids:
        edge = session.engine.map.graph.edges[edge_id]
        travel_time_s += estimate_edge_travel_time_s(
            distance_m=edge.distance,
            speed_limit_mps=edge.speed_limit,
            vehicle_max_speed_mps=vehicle.max_speed,
        )
    return travel_time_s


def _command_targets_vehicle(command: object, *, vehicle_id: int) -> bool:
    command_vehicle_id = getattr(command, "vehicle_id", None)
    return command_vehicle_id == vehicle_id


def _build_vehicle_diagnostics(
    *,
    vehicle_id: int,
    vehicle: object,
    route_preview: RoutePreviewSurface | None,
    wait_reason: str | None,
    current_job_id: str | None,
) -> tuple[VehicleDiagnosticSurface, ...]:
    diagnostics: list[VehicleDiagnosticSurface] = []
    payload = getattr(vehicle, "payload")
    operational_state = getattr(vehicle, "operational_state")

    diagnostics.append(
        VehicleDiagnosticSurface(
            code="payload_state",
            severity=_normalize_diagnostic_severity("info"),
            message=(
                "Vehicle payload is empty."
                if payload == 0.0
                else f"Vehicle carries payload {payload:.2f}."
            ),
        )
    )
    if route_preview is not None:
        diagnostics.append(
            VehicleDiagnosticSurface(
                code="route_preview",
                severity=_normalize_diagnostic_severity(
                    "info" if route_preview.is_actionable else "warning",
                ),
                message=(
                    "Route preview is actionable."
                    if route_preview.is_actionable
                    else f"Route preview is blocked: {route_preview.reason}."
                ),
            )
        )
    if wait_reason is not None:
        diagnostics.append(
            VehicleDiagnosticSurface(
                code="wait_reason",
                severity=_normalize_diagnostic_severity("warning"),
                message=f"Vehicle is waiting because of {wait_reason}.",
            )
        )
    if operational_state == "idle" and current_job_id is None:
        diagnostics.append(
            VehicleDiagnosticSurface(
                code="ready_state",
                severity=_normalize_diagnostic_severity("info"),
                message=f"Vehicle {vehicle_id} is idle and ready for reassignment.",
            )
        )
    return tuple(diagnostics)


def _traffic_control_wait_state(
    *,
    current_node_id: int,
    wait_reason: str | None,
    render_geometry: RenderGeometrySurface | None,
) -> tuple[str | None, str | None, str | None]:
    if wait_reason is None:
        return None, None, None
    if render_geometry is None:
        return None, None, wait_reason

    node_intersection = next(
        (
            intersection
            for intersection in render_geometry.intersections
            if intersection.node_id == current_node_id
        ),
        None,
    )
    if node_intersection is None:
        return None, None, wait_reason

    intersection_id = node_intersection.intersection_id
    road_ids = _controlled_road_ids_for_node(render_geometry, current_node_id)
    road_id_set = set(road_ids)
    stop_line_ids = tuple(
        sorted(
            stop_line.stop_line_id
            for stop_line in render_geometry.stop_lines
            if stop_line.lane_id in _lane_ids_for_road_ids(render_geometry, road_id_set)
        )
    )
    merge_zone_ids = tuple(
        sorted(
            merge_zone.merge_zone_id
            for merge_zone in render_geometry.merge_zones
            if any(
                lane_id in merge_zone.lane_ids
                for lane_id in _lane_ids_for_road_ids(render_geometry, road_id_set)
            )
        )
    )
    if stop_line_ids:
        return "stop_line", f"{intersection_id} stop line", "stop_line"
    if merge_zone_ids:
        return "protected_conflict", f"{intersection_id} protected conflict area", "protected_conflict"
    if len(road_ids) >= 4:
        return "signalized", f"{intersection_id} signalized control", "signal_red"
    if len(road_ids) >= 2:
        return "yield", f"{intersection_id} yield control", "yield"
    return None, None, wait_reason


def _controlled_road_ids_for_node(
    render_geometry: RenderGeometrySurface,
    current_node_id: int,
) -> tuple[str, ...]:
    node_intersection = next(
        (
            intersection
            for intersection in render_geometry.intersections
            if intersection.node_id == current_node_id
        ),
        None,
    )
    if node_intersection is None:
        return ()
    controlled_road_ids: list[str] = []
    for road in render_geometry.roads:
        if not road.centerline:
            continue
        start = road.centerline[0]
        end = road.centerline[-1]
        if node_intersection.polygon and not (
            _point_in_bounds(start, node_intersection.polygon)
            or _point_in_bounds(end, node_intersection.polygon)
        ):
            continue
        controlled_road_ids.append(road.road_id)
    return tuple(sorted(set(controlled_road_ids)))


def _lane_ids_for_road_ids(
    render_geometry: RenderGeometrySurface,
    road_ids: set[str],
) -> set[str]:
    lane_ids: set[str] = set()
    for lane in render_geometry.lanes:
        if lane.road_id in road_ids:
            lane_ids.add(lane.lane_id)
    return lane_ids


def _point_in_bounds(point: tuple[float, float, float], polygon: tuple[tuple[float, float, float], ...]) -> bool:
    min_x = min(p[0] for p in polygon)
    max_x = max(p[0] for p in polygon)
    min_y = min(p[1] for p in polygon)
    max_y = max(p[1] for p in polygon)
    return min_x <= point[0] <= max_x and min_y <= point[1] <= max_y


def build_ai_assist_surface(
    session: LiveSimulationSession,
    *,
    render_geometry: RenderGeometrySurface | None,
    vehicle_inspections: tuple[VehicleInspectionSurface, ...],
    route_previews: tuple[RoutePreviewSurface, ...],
) -> AIAssistSurface:
    """Build deterministic operator-support diagnostics and suggestions."""

    explanations = tuple(
        _build_ai_explanation(inspection) for inspection in vehicle_inspections
    )
    anomalies = tuple(
        anomaly
        for inspection in vehicle_inspections
        for anomaly in _build_ai_anomalies(inspection)
    )
    anomalies += _build_deadlock_anomalies(
        session,
        render_geometry=render_geometry,
        skipped_vehicle_ids=tuple(inspection.vehicle_id for inspection in vehicle_inspections),
    )
    suggestions = tuple(
        suggestion
        for inspection in vehicle_inspections
        for suggestion in _build_ai_suggestions(
            session,
            inspection=inspection,
            route_preview=_preview_for_vehicle(
                vehicle_id=inspection.vehicle_id,
                route_previews=route_previews,
            ),
        )
    )
    suggestions += _build_deadlock_suggestions(
        session,
        render_geometry=render_geometry,
        skipped_vehicle_ids=tuple(inspection.vehicle_id for inspection in vehicle_inspections),
    )
    return AIAssistSurface(
        explanations=explanations,
        suggestions=suggestions,
        anomalies=anomalies,
    )


def _build_ai_explanation(
    inspection: VehicleInspectionSurface,
) -> AIAssistExplanation:
    if inspection.wait_reason is not None:
        return AIAssistExplanation(
            vehicle_id=inspection.vehicle_id,
            reason_code="wait_state",
            summary=(
                f"Vehicle {inspection.vehicle_id} is paused at node "
                f"{inspection.current_node_id} because of {inspection.wait_reason}."
            ),
            rationale_codes=("wait_reason", inspection.operational_state),
        )
    if inspection.current_task_type is not None:
        return AIAssistExplanation(
            vehicle_id=inspection.vehicle_id,
            reason_code="active_task",
            summary=(
                f"Vehicle {inspection.vehicle_id} is working on "
                f"{inspection.current_task_type} task {inspection.current_task_index} "
                f"for job {inspection.current_job_id}."
            ),
            rationale_codes=("active_task", inspection.current_task_type),
        )
    if inspection.route_ahead_node_ids:
        return AIAssistExplanation(
            vehicle_id=inspection.vehicle_id,
            reason_code="route_ready",
            summary=(
                f"Vehicle {inspection.vehicle_id} is positioned to travel "
                f"{' -> '.join(str(node_id) for node_id in inspection.route_ahead_node_ids)}."
            ),
            rationale_codes=("route_ahead", inspection.operational_state),
        )
    return AIAssistExplanation(
        vehicle_id=inspection.vehicle_id,
        reason_code="idle_ready",
        summary=(
            f"Vehicle {inspection.vehicle_id} is idle at node "
            f"{inspection.current_node_id} and available for reassignment."
        ),
        rationale_codes=("idle_ready",),
    )


def _build_ai_anomalies(
    inspection: VehicleInspectionSurface,
) -> tuple[AIAssistAnomaly, ...]:
    anomalies: list[AIAssistAnomaly] = []
    if inspection.wait_reason is not None:
        anomalies.append(
            AIAssistAnomaly(
                anomaly_id=f"vehicle-{inspection.vehicle_id}-wait",
                severity=_normalize_diagnostic_severity("warning"),
                reason_code="wait_state",
                summary=(
                    f"Vehicle {inspection.vehicle_id} is stalled by "
                    f"{inspection.wait_reason}."
                ),
                vehicle_id=inspection.vehicle_id,
            )
        )
    if inspection.operational_state == "failed":
        anomalies.append(
            AIAssistAnomaly(
                anomaly_id=f"vehicle-{inspection.vehicle_id}-failed",
                severity=_normalize_diagnostic_severity("critical"),
                reason_code="vehicle_failed",
                summary=f"Vehicle {inspection.vehicle_id} is in failed state.",
                vehicle_id=inspection.vehicle_id,
            )
        )
    return tuple(anomalies)


def _build_ai_suggestions(
    session: LiveSimulationSession,
    *,
    inspection: VehicleInspectionSurface,
    route_preview: RoutePreviewSurface | None,
) -> tuple[AIAssistSuggestion, ...]:
    suggestions: list[AIAssistSuggestion] = []
    if route_preview is not None and route_preview.is_actionable:
        suggestions.append(
            AIAssistSuggestion(
                suggestion_id=f"assign-{inspection.vehicle_id}-{route_preview.destination_node_id}",
                kind="retask_vehicle",
                priority=_normalize_suggestion_priority("high"),
                reason_code="assign_destination",
                summary=(
                    f"Assign vehicle {inspection.vehicle_id} to destination "
                    f"{route_preview.destination_node_id} using the previewed route."
                ),
                proposed_command={
                    "command_type": "assign_vehicle_destination",
                    "vehicle_id": inspection.vehicle_id,
                    "destination_node_id": route_preview.destination_node_id,
                },
                target_vehicle_id=inspection.vehicle_id,
            )
        )
    elif route_preview is not None and route_preview.reason == "no_route":
        blocked_edge_ids = sorted(session.engine.world_state.blocked_edge_ids)
        if blocked_edge_ids:
            blocked_edge_id = blocked_edge_ids[0]
            suggestions.append(
                AIAssistSuggestion(
                    suggestion_id=f"unblock-{blocked_edge_id}",
                    kind="reopen_edge",
                    priority=_normalize_suggestion_priority("medium"),
                    reason_code="reopen_blocked_edge",
                    summary=(
                        f"Consider reopening blocked edge {blocked_edge_id} to restore "
                        f"routing options for vehicle {inspection.vehicle_id}."
                    ),
                    proposed_command={
                        "command_type": "unblock_edge",
                        "edge_id": blocked_edge_id,
                    },
                    target_vehicle_id=inspection.vehicle_id,
                    target_edge_id=blocked_edge_id,
                )
            )
    if (
        inspection.operational_state == "idle"
        and inspection.current_job_id is None
        and route_preview is None
    ):
        suggestions.append(
            AIAssistSuggestion(
                suggestion_id=f"preview-{inspection.vehicle_id}",
                kind="preview_destination",
                priority=_normalize_suggestion_priority("medium"),
                reason_code="preview_destination",
                summary=(
                    f"Preview a destination for idle vehicle {inspection.vehicle_id} "
                    "before committing a retask command."
                ),
                target_vehicle_id=inspection.vehicle_id,
            )
        )
    return tuple(suggestions)


def _build_deadlock_diagnostics(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    current_node_id: int,
    current_position: tuple[float, float, float],
    render_geometry: RenderGeometrySurface | None,
    route_preview: RoutePreviewSurface | None,
    wait_reason: str | None,
) -> tuple[VehicleDiagnosticSurface, ...]:
    risks = _deadlock_risks_for_vehicle(
        session,
        vehicle_id=vehicle_id,
        current_node_id=current_node_id,
        current_position=current_position,
        render_geometry=render_geometry,
        route_preview=route_preview,
        wait_reason=wait_reason,
    )
    return tuple(
        VehicleDiagnosticSurface(
            code=risk.code,
            severity=risk.severity,
            message=risk.summary,
        )
        for risk in risks
    )


def _build_deadlock_anomalies(
    session: LiveSimulationSession,
    *,
    render_geometry: RenderGeometrySurface | None,
    skipped_vehicle_ids: tuple[int, ...],
) -> tuple[AIAssistAnomaly, ...]:
    skipped_ids = set(skipped_vehicle_ids)
    anomalies: list[AIAssistAnomaly] = []
    for vehicle in sorted(session.engine.vehicles, key=lambda vehicle: vehicle.id):
        if not getattr(vehicle, "is_active", True):
            continue
        if vehicle.id in skipped_ids:
            continue
        context = _active_execution_context(session, vehicle_id=vehicle.id)
        if context["wait_reason"] is None:
            continue
        risks = _deadlock_risks_for_vehicle(
            session,
            vehicle_id=vehicle.id,
            current_node_id=vehicle.current_node_id,
            current_position=vehicle.position,
            render_geometry=render_geometry,
            route_preview=None,
            wait_reason=context["wait_reason"],
        )
        anomalies.extend(
            AIAssistAnomaly(
                anomaly_id=f"vehicle-{vehicle.id}-{risk.code}",
                severity=_normalize_diagnostic_severity(risk.severity),
                reason_code=risk.code,
                summary=risk.summary,
                vehicle_id=vehicle.id,
            )
            for risk in risks
        )
    return tuple(anomalies)


def _build_deadlock_suggestions(
    session: LiveSimulationSession,
    *,
    render_geometry: RenderGeometrySurface | None,
    skipped_vehicle_ids: tuple[int, ...],
) -> tuple[AIAssistSuggestion, ...]:
    skipped_ids = set(skipped_vehicle_ids)
    suggestions: list[AIAssistSuggestion] = []
    for vehicle in sorted(session.engine.vehicles, key=lambda vehicle: vehicle.id):
        if not getattr(vehicle, "is_active", True):
            continue
        if vehicle.id in skipped_ids:
            continue
        context = _active_execution_context(session, vehicle_id=vehicle.id)
        if context["wait_reason"] is None:
            continue
        risks = _deadlock_risks_for_vehicle(
            session,
            vehicle_id=vehicle.id,
            current_node_id=vehicle.current_node_id,
            current_position=vehicle.position,
            render_geometry=render_geometry,
            route_preview=None,
            wait_reason=context["wait_reason"],
        )
        suggestions.extend(
            AIAssistSuggestion(
                suggestion_id=f"{risk.code}-{vehicle.id}",
                kind="avoid_deadlock",
                priority=_normalize_suggestion_priority(
                    "high" if risk.severity == "critical" else "medium",
                ),
                reason_code=risk.code,
                summary=risk.mitigation,
                target_vehicle_id=vehicle.id,
            )
            for risk in risks
        )
    return tuple(suggestions)


def _deadlock_risks_for_vehicle(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    current_node_id: int,
    current_position: tuple[float, float, float],
    render_geometry: RenderGeometrySurface | None,
    route_preview: RoutePreviewSurface | None,
    wait_reason: str | None,
) -> tuple[_DeadlockRisk, ...]:
    if wait_reason is None or render_geometry is None:
        return ()

    waiting_vehicle_states = _waiting_vehicle_states(session)
    waiting_vehicle_ids_at_node = tuple(
        waiting_vehicle_id
        for waiting_vehicle_id, node_id, _position in waiting_vehicle_states
        if node_id == current_node_id
    )
    current_roads = _roads_for_position(render_geometry, current_position)
    current_road_ids = {road.road_id for road in current_roads}
    waiting_vehicle_ids_on_roads = tuple(
        waiting_vehicle_id
        for waiting_vehicle_id, _node_id, position in waiting_vehicle_states
        if {road.road_id for road in _roads_for_position(render_geometry, position)}
        & current_road_ids
    )
    current_areas = _areas_for_position(render_geometry, current_position)
    current_area_ids = {area.area_id for area in current_areas}
    waiting_vehicle_ids_in_areas = tuple(
        waiting_vehicle_id
        for waiting_vehicle_id, _node_id, position in waiting_vehicle_states
        if {area.area_id for area in _areas_for_position(render_geometry, position)}
        & current_area_ids
    )

    risks: list[_DeadlockRisk] = []
    intersection = next(
        (
            intersection
            for intersection in render_geometry.intersections
            if intersection.node_id == current_node_id
        ),
        None,
    )
    if intersection is not None and len(waiting_vehicle_ids_at_node) >= 2:
        risks.append(
            _DeadlockRisk(
                code="deadlock_risk_intersection",
                severity="warning",
                summary=(
                    f"Intersection {intersection.intersection_id} has "
                    f"{len(waiting_vehicle_ids_at_node)} waiting vehicles and may gridlock."
                ),
                mitigation=(
                    f"Sequence departures through {intersection.intersection_id} and "
                    "let one vehicle clear before releasing the next."
                ),
                vehicle_id=vehicle_id,
            )
        )
        return tuple(risks)

    depot_area = next(
        (
            area
            for area in current_areas
            if area.kind in {
                "depot",
                "yard",
                "loading_bay",
                "service_yard",
                "staging_area",
            }
        ),
        None,
    )
    if depot_area is not None and len(waiting_vehicle_ids_in_areas) >= 2:
        risks.append(
            _DeadlockRisk(
                code="deadlock_risk_depot",
                severity="warning",
                summary=(
                    f"Depot area {depot_area.area_id} is holding "
                    f"{len(waiting_vehicle_ids_in_areas)} waiting vehicles and may spill back."
                ),
                mitigation=(
                    f"Pause new departures from {depot_area.area_id} until the lead vehicle clears the exit."
                ),
                vehicle_id=vehicle_id,
            )
        )
        return tuple(risks)

    narrow_roads = tuple(
        road
        for road in current_roads
        if road.lane_count <= 1
    )
    if narrow_roads and len(waiting_vehicle_ids_on_roads) >= 2:
        narrow_road = narrow_roads[0]
        risks.append(
            _DeadlockRisk(
                code="deadlock_risk_corridor",
                severity="warning",
                summary=(
                    f"Narrow corridor {narrow_road.road_id} has "
                    f"{len(waiting_vehicle_ids_on_roads)} waiting vehicles and may spill back."
                ),
                mitigation=(
                    f"Hold upstream departures on {narrow_road.road_id} until the corridor clears."
                ),
                vehicle_id=vehicle_id,
            )
        )
        return tuple(risks)

    if len(waiting_vehicle_ids_at_node) >= 3 or (
        route_preview is not None and route_preview.reason == "no_route"
    ):
        risks.append(
            _DeadlockRisk(
                code="deadlock_risk_queue_spillback",
                severity="critical" if len(waiting_vehicle_ids_at_node) >= 3 else "warning",
                summary=(
                    f"Queue spillback is building around node {current_node_id} and may trap the waiting line."
                ),
                mitigation=(
                    f"Clear the downstream path from node {current_node_id} before dispatching more vehicles."
                ),
                vehicle_id=vehicle_id,
            )
        )
    return tuple(risks)


def _waiting_vehicle_states(
    session: LiveSimulationSession,
) -> tuple[tuple[int, int, tuple[float, float, float]], ...]:
    waiting_states: list[tuple[int, int, tuple[float, float, float]]] = []
    for vehicle in sorted(session.engine.vehicles, key=lambda vehicle: vehicle.id):
        if not getattr(vehicle, "is_active", True):
            continue
        context = _active_execution_context(session, vehicle_id=vehicle.id)
        if context["wait_reason"] is None:
            continue
        waiting_states.append((vehicle.id, vehicle.current_node_id, vehicle.position))
    return tuple(waiting_states)


def _roads_for_position(
    render_geometry: RenderGeometrySurface,
    position: tuple[float, float, float],
) -> tuple[Any, ...]:
    roads = [
        road
        for road in render_geometry.roads
        if _road_touches_position(road.centerline, position)
    ]
    return tuple(sorted(roads, key=lambda road: road.road_id))


def _areas_for_position(
    render_geometry: RenderGeometrySurface,
    position: tuple[float, float, float],
) -> tuple[Any, ...]:
    areas = [
        area
        for area in render_geometry.areas
        if _point_in_bounds(position, area.polygon)
    ]
    return tuple(sorted(areas, key=lambda area: area.area_id))


def _road_touches_position(
    centerline: tuple[tuple[float, float, float], ...],
    position: tuple[float, float, float],
) -> bool:
    if not centerline:
        return False
    if len(centerline) == 1:
        return _distance_xy(centerline[0], position) <= 0.35
    for start, end in zip(centerline, centerline[1:]):
        if _point_distance_to_segment(position, start, end) <= 0.35:
            return True
    return False


def _distance_xy(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return math.hypot(left[0] - right[0], left[1] - right[1])


def _point_distance_to_segment(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    segment_dx = end[0] - start[0]
    segment_dy = end[1] - start[1]
    if segment_dx == 0.0 and segment_dy == 0.0:
        return _distance_xy(point, start)
    projection = (
        (point[0] - start[0]) * segment_dx + (point[1] - start[1]) * segment_dy
    ) / (segment_dx * segment_dx + segment_dy * segment_dy)
    clamped = max(0.0, min(1.0, projection))
    closest_point = (
        start[0] + clamped * segment_dx,
        start[1] + clamped * segment_dy,
        start[2] + clamped * (end[2] - start[2]),
    )
    return _distance_xy(point, closest_point)


def _normalize_reason_code(reason: str | None) -> str | None:
    if reason is None:
        return None
    normalized = reason.strip().lower().replace(" ", "_").replace("-", "_")
    return normalized or None


def _normalize_diagnostic_severity(severity: str, *, fallback: str = "info") -> str:
    normalized = _normalize_reason_code(severity) or fallback
    if normalized in {"info", "warning", "critical"}:
        return normalized
    return fallback


def _normalize_suggestion_priority(priority: str, *, fallback: str = "medium") -> str:
    normalized = _normalize_reason_code(priority) or fallback
    if normalized in {"high", "medium", "low"}:
        return normalized
    return fallback


__all__ = [
    "AIAssistAnomaly",
    "AIAssistExplanation",
    "AIAssistSuggestion",
    "AIAssistSurface",
    "CommandCenterEdgeSurface",
    "CommandCenterSurface",
    "CommandCenterVehicleSurface",
    "RoutePreviewRequest",
    "RoutePreviewSurface",
    "VehicleDiagnosticSurface",
    "VehicleInspectionSurface",
    "ai_assist_surface_to_dict",
    "build_ai_assist_surface",
    "build_vehicle_inspection_surface",
    "build_live_command_center_surface",
    "command_center_surface_to_dict",
    "preview_route_command",
    "route_preview_surface_to_dict",
    "vehicle_inspection_surface_to_dict",
]
