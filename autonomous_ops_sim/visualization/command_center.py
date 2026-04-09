from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


__all__ = [
    "CommandCenterEdgeSurface",
    "CommandCenterSurface",
    "CommandCenterVehicleSurface",
    "RoutePreviewRequest",
    "RoutePreviewSurface",
    "build_live_command_center_surface",
    "command_center_surface_to_dict",
    "preview_route_command",
    "route_preview_surface_to_dict",
]
