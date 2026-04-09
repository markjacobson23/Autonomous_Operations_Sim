from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from autonomous_ops_sim.simulation.commands import (
    AssignVehicleDestinationCommand,
    command_to_dict,
)
from autonomous_ops_sim.simulation.control import (
    CommandApplicationRecord,
)
from autonomous_ops_sim.simulation.live_session import LiveSimulationSession
from autonomous_ops_sim.visualization.state import (
    FrameTrigger,
    MapSurface,
    VehicleSurfaceState,
    build_visualization_state_from_live_session,
)


LIVE_SYNC_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class LiveRuntimeSnapshot:
    """Stable viewer-facing projection of the current live runtime state."""

    simulated_time_s: float
    is_active: bool
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[VehicleSurfaceState, ...]
    command_count: int
    session_step_count: int
    trace_event_count: int


@dataclass(frozen=True)
class LiveStateUpdate:
    """Stable ordered live-state update for viewer/runtime synchronization."""

    update_index: int
    visualization_frame_index: int
    timestamp_s: float
    trigger: FrameTrigger
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[VehicleSurfaceState, ...]


@dataclass(frozen=True)
class LiveCommandEffect:
    """Stable command publication linked to the ordered updates it produced."""

    sequence: int
    command: dict[str, Any]
    started_at_s: float
    completed_at_s: float
    emitted_update_indices: tuple[int, ...]
    result_timestamp_s: float
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[VehicleSurfaceState, ...]


@dataclass(frozen=True)
class LiveSyncSurface:
    """Transport-agnostic live sync surface between session runtime and viewer."""

    schema_version: int
    seed: int
    map_surface: MapSurface
    snapshot: LiveRuntimeSnapshot
    updates: tuple[LiveStateUpdate, ...]
    command_effects: tuple[LiveCommandEffect, ...]


def build_live_runtime_snapshot(session: LiveSimulationSession) -> LiveRuntimeSnapshot:
    """Build a stable current-state snapshot from one live session."""

    state = build_visualization_state_from_live_session(session)
    latest_frame = state.frames[-1]
    return LiveRuntimeSnapshot(
        simulated_time_s=session.engine.simulated_time_s,
        is_active=session.is_active,
        blocked_edge_ids=latest_frame.blocked_edge_ids,
        vehicles=latest_frame.vehicles,
        command_count=len(session.command_history),
        session_step_count=len(session.progress_history),
        trace_event_count=len(session.engine.trace.events),
    )


def build_live_state_updates(
    session: LiveSimulationSession,
) -> tuple[LiveStateUpdate, ...]:
    """Build ordered viewer-facing updates from one live session."""

    state = build_visualization_state_from_live_session(session)
    return tuple(
        LiveStateUpdate(
            update_index=frame.frame_index - 1,
            visualization_frame_index=frame.frame_index,
            timestamp_s=frame.timestamp_s,
            trigger=frame.trigger,
            blocked_edge_ids=frame.blocked_edge_ids,
            vehicles=frame.vehicles,
        )
        for frame in state.frames[1:]
    )


def build_live_sync_surface(session: LiveSimulationSession) -> LiveSyncSurface:
    """Build the full stable live sync surface from one live session."""

    state = build_visualization_state_from_live_session(session)
    updates = tuple(
        LiveStateUpdate(
            update_index=frame.frame_index - 1,
            visualization_frame_index=frame.frame_index,
            timestamp_s=frame.timestamp_s,
            trigger=frame.trigger,
            blocked_edge_ids=frame.blocked_edge_ids,
            vehicles=frame.vehicles,
        )
        for frame in state.frames[1:]
    )
    return LiveSyncSurface(
        schema_version=LIVE_SYNC_SCHEMA_VERSION,
        seed=state.seed,
        map_surface=state.map_surface,
        snapshot=LiveRuntimeSnapshot(
            simulated_time_s=session.engine.simulated_time_s,
            is_active=session.is_active,
            blocked_edge_ids=state.frames[-1].blocked_edge_ids,
            vehicles=state.frames[-1].vehicles,
            command_count=len(session.command_history),
            session_step_count=len(session.progress_history),
            trace_event_count=len(session.engine.trace.events),
        ),
        updates=updates,
        command_effects=_build_command_effects(
            command_history=session.command_history,
            updates=updates,
        ),
    )


def live_runtime_snapshot_to_dict(snapshot: LiveRuntimeSnapshot) -> dict[str, Any]:
    """Convert one live runtime snapshot into a stable JSON-ready record."""

    return {
        "simulated_time_s": snapshot.simulated_time_s,
        "is_active": snapshot.is_active,
        "blocked_edge_ids": list(snapshot.blocked_edge_ids),
        "vehicles": [_vehicle_surface_state_to_dict(vehicle) for vehicle in snapshot.vehicles],
        "command_count": snapshot.command_count,
        "session_step_count": snapshot.session_step_count,
        "trace_event_count": snapshot.trace_event_count,
    }


def live_state_update_to_dict(update: LiveStateUpdate) -> dict[str, Any]:
    """Convert one live ordered update into a stable JSON-ready record."""

    return {
        "update_index": update.update_index,
        "visualization_frame_index": update.visualization_frame_index,
        "timestamp_s": update.timestamp_s,
        "trigger": _frame_trigger_to_dict(update.trigger),
        "blocked_edge_ids": list(update.blocked_edge_ids),
        "vehicles": [_vehicle_surface_state_to_dict(vehicle) for vehicle in update.vehicles],
    }


def live_command_effect_to_dict(effect: LiveCommandEffect) -> dict[str, Any]:
    """Convert one command effect publication into a stable JSON-ready record."""

    return {
        "sequence": effect.sequence,
        "command": effect.command,
        "started_at_s": effect.started_at_s,
        "completed_at_s": effect.completed_at_s,
        "emitted_update_indices": list(effect.emitted_update_indices),
        "result_timestamp_s": effect.result_timestamp_s,
        "blocked_edge_ids": list(effect.blocked_edge_ids),
        "vehicles": [_vehicle_surface_state_to_dict(vehicle) for vehicle in effect.vehicles],
    }


def live_sync_surface_to_dict(surface: LiveSyncSurface) -> dict[str, Any]:
    """Convert the full live sync surface into a stable JSON-ready record."""

    return {
        "schema_version": surface.schema_version,
        "seed": surface.seed,
        "map_surface": {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "position": list(node.position),
                    "node_type": node.node_type,
                }
                for node in surface.map_surface.nodes
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "start_node_id": edge.start_node_id,
                    "end_node_id": edge.end_node_id,
                    "distance": edge.distance,
                    "speed_limit": edge.speed_limit,
                }
                for edge in surface.map_surface.edges
            ],
        },
        "snapshot": live_runtime_snapshot_to_dict(surface.snapshot),
        "updates": [live_state_update_to_dict(update) for update in surface.updates],
        "command_effects": [
            live_command_effect_to_dict(effect) for effect in surface.command_effects
        ],
    }


def export_live_sync_json(surface: LiveSyncSurface) -> str:
    """Return deterministic JSON for one live sync surface."""

    return json.dumps(
        live_sync_surface_to_dict(surface),
        indent=2,
        sort_keys=True,
    ) + "\n"


def _build_command_effects(
    *,
    command_history: tuple[CommandApplicationRecord, ...],
    updates: tuple[LiveStateUpdate, ...],
) -> tuple[LiveCommandEffect, ...]:
    effects: list[LiveCommandEffect] = []
    for record in command_history:
        emitted_updates = _select_command_updates(record=record, updates=updates)
        if emitted_updates:
            latest_update = emitted_updates[-1]
            emitted_update_indices = tuple(
                update.update_index for update in emitted_updates
            )
            result_timestamp_s = latest_update.timestamp_s
            blocked_edge_ids = latest_update.blocked_edge_ids
            vehicles = latest_update.vehicles
        else:
            emitted_update_indices = ()
            result_timestamp_s = record.completed_at_s
            blocked_edge_ids = ()
            vehicles = ()

        effects.append(
            LiveCommandEffect(
                sequence=record.sequence,
                command=command_to_dict(record.command),
                started_at_s=record.started_at_s,
                completed_at_s=record.completed_at_s,
                emitted_update_indices=emitted_update_indices,
                result_timestamp_s=result_timestamp_s,
                blocked_edge_ids=blocked_edge_ids,
                vehicles=vehicles,
            )
        )
    return tuple(effects)


def _select_command_updates(
    *,
    record: CommandApplicationRecord,
    updates: tuple[LiveStateUpdate, ...],
) -> tuple[LiveStateUpdate, ...]:
    if not isinstance(record.command, AssignVehicleDestinationCommand):
        return tuple(
            update
            for update in updates
            if update.trigger.source == "command"
            and update.trigger.sequence == record.sequence
        )

    return tuple(
        update
        for update in updates
        if update.trigger.source == "trace"
        and update.trigger.trace_event is not None
        and update.trigger.trace_event.get("vehicle_id") == record.command.vehicle_id
        and record.started_at_s <= update.timestamp_s <= record.completed_at_s
    )


def _vehicle_surface_state_to_dict(
    vehicle: VehicleSurfaceState,
) -> dict[str, Any]:
    return {
        "vehicle_id": vehicle.vehicle_id,
        "node_id": vehicle.node_id,
        "position": list(vehicle.position),
        "operational_state": vehicle.operational_state,
    }


def _frame_trigger_to_dict(trigger: FrameTrigger) -> dict[str, Any]:
    payload = {
        "source": trigger.source,
        "sequence": trigger.sequence,
        "timestamp_s": trigger.timestamp_s,
        "event_name": trigger.event_name,
        "trace_event": trigger.trace_event,
        "command": trigger.command,
    }
    if trigger.session_step is not None:
        payload["session_step"] = trigger.session_step
    return payload
