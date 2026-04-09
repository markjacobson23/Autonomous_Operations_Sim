from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.io.exports import trace_event_to_dict
from autonomous_ops_sim.simulation import LiveSimulationSession, command_to_dict


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
    """Stable diagnostic hook surfaced to the operator for one vehicle."""

    code: str
    severity: str
    message: str


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
    eta_s: float | None
    route_ahead_node_ids: tuple[int, ...]
    route_ahead_edge_ids: tuple[int, ...]
    recent_commands: tuple[dict[str, Any], ...]
    recent_trace_events: tuple[dict[str, Any], ...]
    diagnostics: tuple[VehicleDiagnosticSurface, ...]


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


def preview_route_command(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    destination_node_id: int,
) -> RoutePreviewSurface:
    """Build a deterministic route preview without mutating the live session."""

    vehicle = session.engine.get_vehicle(vehicle_id)
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

    normalized_selection = _normalize_selected_vehicle_ids(
        session,
        selected_vehicle_ids,
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
        route_previews=tuple(
            preview_route_command(
                session,
                vehicle_id=request.vehicle_id,
                destination_node_id=request.destination_node_id,
            )
            for request in route_preview_requests
        ),
        vehicle_inspections=tuple(
            build_vehicle_inspection_surface(
                session,
                vehicle_id=vehicle_id,
                route_preview=_preview_for_vehicle(
                    session,
                    vehicle_id=vehicle_id,
                    route_preview_requests=route_preview_requests,
                ),
            )
            for vehicle_id in normalized_selection
        ),
    )


def build_vehicle_inspection_surface(
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    route_preview: RoutePreviewSurface | None = None,
) -> VehicleInspectionSurface:
    """Build one richer inspection record from authoritative session state."""

    vehicle = session.engine.get_vehicle(vehicle_id)
    context = _active_execution_context(session, vehicle_id=vehicle_id)
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
        wait_reason=context["wait_reason"],
        eta_s=_estimate_eta_s(
            session,
            route_preview=route_preview,
        ),
        route_ahead_node_ids=route_preview.node_ids if route_preview is not None else (),
        route_ahead_edge_ids=route_preview.edge_ids if route_preview is not None else (),
        recent_commands=recent_commands,
        recent_trace_events=recent_trace_events,
        diagnostics=_build_vehicle_diagnostics(
            vehicle_id=vehicle_id,
            vehicle=vehicle,
            route_preview=route_preview,
            wait_reason=context["wait_reason"],
            current_job_id=context["current_job_id"],
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
        session.engine.get_vehicle(vehicle_id)
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
            wait_reason = event.transition_reason
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
    session: LiveSimulationSession,
    *,
    vehicle_id: int,
    route_preview_requests: tuple[RoutePreviewRequest, ...]
    | list[RoutePreviewRequest],
) -> RoutePreviewSurface | None:
    for request in route_preview_requests:
        if request.vehicle_id != vehicle_id:
            continue
        return preview_route_command(
            session,
            vehicle_id=request.vehicle_id,
            destination_node_id=request.destination_node_id,
        )
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
        travel_time_s += edge.distance / min(vehicle.max_speed, edge.speed_limit)
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
            severity="info",
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
                severity="info" if route_preview.is_actionable else "warning",
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
                severity="warning",
                message=f"Vehicle is waiting because of {wait_reason}.",
            )
        )
    if operational_state == "idle" and current_job_id is None:
        diagnostics.append(
            VehicleDiagnosticSurface(
                code="ready_state",
                severity="info",
                message=f"Vehicle {vehicle_id} is idle and ready for reassignment.",
            )
        )
    return tuple(diagnostics)


__all__ = [
    "CommandCenterEdgeSurface",
    "CommandCenterSurface",
    "CommandCenterVehicleSurface",
    "RoutePreviewRequest",
    "RoutePreviewSurface",
    "VehicleDiagnosticSurface",
    "VehicleInspectionSurface",
    "build_vehicle_inspection_surface",
    "build_live_command_center_surface",
    "command_center_surface_to_dict",
    "preview_route_command",
    "route_preview_surface_to_dict",
    "vehicle_inspection_surface_to_dict",
]
