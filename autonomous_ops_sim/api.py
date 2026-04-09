from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from autonomous_ops_sim.io.exports import (
    metrics_summary_to_dict,
    trace_event_to_dict,
)
from autonomous_ops_sim.simulation.commands import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    RepositionVehicleCommand,
    SimulationCommand,
    UnblockEdgeCommand,
    command_to_dict,
)
from autonomous_ops_sim.simulation.control import (
    CommandApplicationRecord,
    CommandValidationError,
    SimulationController,
)
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.live_session import (
    LiveSimulationSession,
    SessionAdvanceRecord,
    session_advance_to_dict,
)
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization.command_center import (
    CommandCenterSurface,
    RoutePreviewRequest,
    build_live_command_center_surface,
    command_center_surface_to_dict,
)
from autonomous_ops_sim.visualization.live_sync import (
    LiveRuntimeSnapshot,
    LiveStateUpdate,
    build_live_runtime_snapshot,
    build_live_sync_surface,
    live_runtime_snapshot_to_dict,
    live_state_update_to_dict,
)
from autonomous_ops_sim.visualization.geometry import (
    RenderGeometrySurface,
    build_render_geometry_surface,
    render_geometry_surface_to_dict,
)
from autonomous_ops_sim.visualization.motion import (
    VehicleMotionSegment,
    build_vehicle_motion_segments,
    motion_segment_to_dict,
)
from autonomous_ops_sim.visualization.traffic import (
    TrafficBaselineSurface,
    build_traffic_baseline_surface,
    traffic_baseline_surface_to_dict,
)
from autonomous_ops_sim.visualization.state import (
    FrameTrigger,
    MapSurface,
    ReplayFrame,
    VehicleSurfaceState,
    build_visualization_state,
    build_visualization_state_from_live_session,
)


SIMULATION_API_VERSION = 1
REPLAY_BUNDLE_SCHEMA_VERSION = 4
LIVE_SESSION_BUNDLE_SCHEMA_VERSION = 6
LIVE_SYNC_BUNDLE_SCHEMA_VERSION = 6


@dataclass(frozen=True)
class SimulationApiMetadata:
    """Stable version descriptor for one public simulator-facing surface."""

    api_version: int
    surface_name: str
    surface_schema_version: int


@dataclass(frozen=True)
class SimulationCommandResult:
    """Stable viewer-facing acknowledgement for one command attempt."""

    status: str
    command: dict[str, Any]
    sequence: int | None
    started_at_s: float
    completed_at_s: float
    result_timestamp_s: float
    emitted_update_indices: tuple[int, ...]
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[VehicleSurfaceState, ...]
    message: str | None = None


@dataclass(frozen=True)
class ReplayBundle:
    """Versioned replay-oriented API surface derived from authoritative state."""

    metadata: SimulationApiMetadata
    seed: int
    final_time_s: float
    summary: ExecutionMetricsSummary
    map_surface: MapSurface
    render_geometry: RenderGeometrySurface
    final_frame: ReplayFrame
    replay_timeline: tuple[ReplayFrame, ...]
    trace_events: tuple[dict[str, Any], ...]
    command_results: tuple[SimulationCommandResult, ...]
    session_history: tuple[SessionAdvanceRecord, ...]
    motion_segments: tuple[VehicleMotionSegment, ...]
    traffic_baseline: TrafficBaselineSurface


@dataclass(frozen=True)
class LiveSessionBundle:
    """Versioned live-session API surface for authoritative runtime control."""

    metadata: SimulationApiMetadata
    seed: int
    simulated_time_s: float
    summary: ExecutionMetricsSummary
    map_surface: MapSurface
    render_geometry: RenderGeometrySurface
    snapshot: LiveRuntimeSnapshot
    trace_events: tuple[dict[str, Any], ...]
    session_history: tuple[SessionAdvanceRecord, ...]
    command_results: tuple[SimulationCommandResult, ...]
    motion_segments: tuple[VehicleMotionSegment, ...]
    traffic_baseline: TrafficBaselineSurface
    command_center: CommandCenterSurface


@dataclass(frozen=True)
class LiveSyncBundle:
    """Versioned transport-agnostic live sync bundle for viewers."""

    metadata: SimulationApiMetadata
    seed: int
    map_surface: MapSurface
    render_geometry: RenderGeometrySurface
    snapshot: LiveRuntimeSnapshot
    updates: tuple[LiveStateUpdate, ...]
    command_results: tuple[SimulationCommandResult, ...]
    motion_segments: tuple[VehicleMotionSegment, ...]
    traffic_baseline: TrafficBaselineSurface
    command_center: CommandCenterSurface


def apply_command_with_result(
    target: SimulationController | LiveSimulationSession,
    command: SimulationCommand,
) -> SimulationCommandResult:
    """Apply one command and return a stable acknowledgement result."""

    started_at_s = target.engine.simulated_time_s
    try:
        record = target.apply(command)
    except CommandValidationError as exc:
        return SimulationCommandResult(
            status="rejected",
            command=command_to_dict(command),
            sequence=None,
            started_at_s=started_at_s,
            completed_at_s=started_at_s,
            result_timestamp_s=started_at_s,
            emitted_update_indices=(),
            blocked_edge_ids=(),
            vehicles=(),
            message=str(exc),
        )

    return _build_current_command_result(
        engine=target.engine,
        record=record,
    )


def build_replay_bundle(
    engine: SimulationEngine,
    *,
    command_history: tuple[CommandApplicationRecord, ...]
    | list[CommandApplicationRecord] = (),
    session_history: tuple[SessionAdvanceRecord, ...]
    | list[SessionAdvanceRecord] = (),
    summary: ExecutionMetricsSummary | None = None,
) -> ReplayBundle:
    """Build the versioned replay bundle for one authoritative engine run."""

    metrics_summary = summary or summarize_engine_execution(engine)
    replay_state = build_visualization_state(
        engine,
        command_history=command_history,
        session_history=session_history,
    )
    motion_segments = build_vehicle_motion_segments(replay_state)
    render_geometry = build_render_geometry_surface(engine.map)
    command_results = _build_replay_command_results(
        command_history=tuple(command_history),
        frames=replay_state.frames,
    )
    return ReplayBundle(
        metadata=SimulationApiMetadata(
            api_version=SIMULATION_API_VERSION,
            surface_name="replay_bundle",
            surface_schema_version=REPLAY_BUNDLE_SCHEMA_VERSION,
        ),
        seed=engine.seed,
        final_time_s=engine.simulated_time_s,
        summary=metrics_summary,
        map_surface=replay_state.map_surface,
        render_geometry=render_geometry,
        final_frame=replay_state.frames[-1],
        replay_timeline=replay_state.frames,
        trace_events=tuple(
            trace_event_to_dict(event) for event in engine.trace.events
        ),
        command_results=command_results,
        session_history=tuple(session_history),
        motion_segments=motion_segments,
        traffic_baseline=build_traffic_baseline_surface(
            replay_state,
            render_geometry=render_geometry,
            motion_segments=motion_segments,
        ),
    )


def build_replay_bundle_from_controller(
    controller: SimulationController,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> ReplayBundle:
    """Build the replay bundle from a deterministic command-driven run."""

    return build_replay_bundle(
        controller.engine,
        command_history=controller.command_history,
        summary=summary,
    )


def build_replay_bundle_from_live_session(
    session: LiveSimulationSession,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> ReplayBundle:
    """Build the replay bundle from one explicit live session."""

    return build_replay_bundle(
        session.engine,
        command_history=session.command_history,
        session_history=session.progress_history,
        summary=summary,
    )


def build_live_session_bundle(
    session: LiveSimulationSession,
    *,
    summary: ExecutionMetricsSummary | None = None,
    selected_vehicle_ids: tuple[int, ...] | list[int] = (),
    route_preview_requests: tuple[RoutePreviewRequest, ...]
    | list[RoutePreviewRequest] = (),
) -> LiveSessionBundle:
    """Build the versioned live-session API surface."""

    metrics_summary = summary or summarize_engine_execution(session.engine)
    replay_state = build_visualization_state_from_live_session(session)
    motion_segments = build_vehicle_motion_segments(replay_state)
    render_geometry = build_render_geometry_surface(session.engine.map)
    return LiveSessionBundle(
        metadata=SimulationApiMetadata(
            api_version=SIMULATION_API_VERSION,
            surface_name="live_session_bundle",
            surface_schema_version=LIVE_SESSION_BUNDLE_SCHEMA_VERSION,
        ),
        seed=session.engine.seed,
        simulated_time_s=session.engine.simulated_time_s,
        summary=metrics_summary,
        map_surface=replay_state.map_surface,
        render_geometry=render_geometry,
        snapshot=build_live_runtime_snapshot(session),
        trace_events=tuple(
            trace_event_to_dict(event) for event in session.engine.trace.events
        ),
        session_history=session.progress_history,
        command_results=_build_replay_command_results(
            command_history=session.command_history,
            frames=replay_state.frames,
        ),
        motion_segments=motion_segments,
        traffic_baseline=build_traffic_baseline_surface(
            replay_state,
            render_geometry=render_geometry,
            motion_segments=motion_segments,
        ),
        command_center=build_live_command_center_surface(
            session,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        ),
    )


def build_live_sync_bundle(
    session: LiveSimulationSession,
    *,
    selected_vehicle_ids: tuple[int, ...] | list[int] = (),
    route_preview_requests: tuple[RoutePreviewRequest, ...]
    | list[RoutePreviewRequest] = (),
) -> LiveSyncBundle:
    """Build the versioned live sync bundle for transport-agnostic viewers."""

    surface = build_live_sync_surface(session)
    replay_state = build_visualization_state_from_live_session(session)
    motion_segments = build_vehicle_motion_segments(replay_state)
    render_geometry = build_render_geometry_surface(session.engine.map)
    return LiveSyncBundle(
        metadata=SimulationApiMetadata(
            api_version=SIMULATION_API_VERSION,
            surface_name="live_sync_bundle",
            surface_schema_version=LIVE_SYNC_BUNDLE_SCHEMA_VERSION,
        ),
        seed=surface.seed,
        map_surface=surface.map_surface,
        render_geometry=build_render_geometry_surface(session.engine.map),
        snapshot=surface.snapshot,
        updates=surface.updates,
        command_results=tuple(
            SimulationCommandResult(
                status="accepted",
                command=effect.command,
                sequence=effect.sequence,
                started_at_s=effect.started_at_s,
                completed_at_s=effect.completed_at_s,
                result_timestamp_s=effect.result_timestamp_s,
                emitted_update_indices=effect.emitted_update_indices,
                blocked_edge_ids=effect.blocked_edge_ids,
                vehicles=effect.vehicles,
            )
            for effect in surface.command_effects
        ),
        motion_segments=motion_segments,
        traffic_baseline=build_traffic_baseline_surface(
            replay_state,
            render_geometry=render_geometry,
            motion_segments=motion_segments,
        ),
        command_center=build_live_command_center_surface(
            session,
            selected_vehicle_ids=selected_vehicle_ids,
            route_preview_requests=route_preview_requests,
        ),
    )


def simulation_api_metadata_to_dict(
    metadata: SimulationApiMetadata,
) -> dict[str, Any]:
    """Convert one API descriptor into a stable JSON-ready record."""

    return {
        "api_version": metadata.api_version,
        "surface_name": metadata.surface_name,
        "surface_schema_version": metadata.surface_schema_version,
    }


def simulation_command_result_to_dict(
    result: SimulationCommandResult,
) -> dict[str, Any]:
    """Convert one command acknowledgement into a stable JSON-ready record."""

    payload = {
        "status": result.status,
        "command": result.command,
        "sequence": result.sequence,
        "started_at_s": result.started_at_s,
        "completed_at_s": result.completed_at_s,
        "result_timestamp_s": result.result_timestamp_s,
        "emitted_update_indices": list(result.emitted_update_indices),
        "blocked_edge_ids": list(result.blocked_edge_ids),
        "vehicles": [_vehicle_surface_state_to_dict(vehicle) for vehicle in result.vehicles],
    }
    if result.message is not None:
        payload["message"] = result.message
    return payload


def replay_bundle_to_dict(bundle: ReplayBundle) -> dict[str, Any]:
    """Convert one replay bundle into a stable JSON-ready record."""

    return {
        "metadata": simulation_api_metadata_to_dict(bundle.metadata),
        "seed": bundle.seed,
        "final_time_s": bundle.final_time_s,
        "summary": metrics_summary_to_dict(bundle.summary),
        "map_surface": _map_surface_to_dict(bundle.map_surface),
        "render_geometry": render_geometry_surface_to_dict(bundle.render_geometry),
        "final_frame": _replay_frame_to_dict(bundle.final_frame),
        "replay_timeline": [
            _replay_frame_to_dict(frame) for frame in bundle.replay_timeline
        ],
        "trace_events": list(bundle.trace_events),
        "command_results": [
            simulation_command_result_to_dict(result)
            for result in bundle.command_results
        ],
        "session_history": [
            session_advance_to_dict(record) for record in bundle.session_history
        ],
        "motion_segments": [
            motion_segment_to_dict(segment) for segment in bundle.motion_segments
        ],
        "traffic_baseline": traffic_baseline_surface_to_dict(bundle.traffic_baseline),
    }


def live_session_bundle_to_dict(bundle: LiveSessionBundle) -> dict[str, Any]:
    """Convert one live-session bundle into a stable JSON-ready record."""

    return {
        "metadata": simulation_api_metadata_to_dict(bundle.metadata),
        "seed": bundle.seed,
        "simulated_time_s": bundle.simulated_time_s,
        "summary": metrics_summary_to_dict(bundle.summary),
        "map_surface": _map_surface_to_dict(bundle.map_surface),
        "render_geometry": render_geometry_surface_to_dict(bundle.render_geometry),
        "snapshot": live_runtime_snapshot_to_dict(bundle.snapshot),
        "trace_events": list(bundle.trace_events),
        "session_history": [
            session_advance_to_dict(record) for record in bundle.session_history
        ],
        "command_results": [
            simulation_command_result_to_dict(result)
            for result in bundle.command_results
        ],
        "motion_segments": [
            motion_segment_to_dict(segment) for segment in bundle.motion_segments
        ],
        "traffic_baseline": traffic_baseline_surface_to_dict(bundle.traffic_baseline),
        "command_center": command_center_surface_to_dict(bundle.command_center),
    }


def live_sync_bundle_to_dict(bundle: LiveSyncBundle) -> dict[str, Any]:
    """Convert one live sync bundle into a stable JSON-ready record."""

    return {
        "metadata": simulation_api_metadata_to_dict(bundle.metadata),
        "seed": bundle.seed,
        "map_surface": _map_surface_to_dict(bundle.map_surface),
        "render_geometry": render_geometry_surface_to_dict(bundle.render_geometry),
        "snapshot": live_runtime_snapshot_to_dict(bundle.snapshot),
        "updates": [live_state_update_to_dict(update) for update in bundle.updates],
        "command_results": [
            simulation_command_result_to_dict(result)
            for result in bundle.command_results
        ],
        "motion_segments": [
            motion_segment_to_dict(segment) for segment in bundle.motion_segments
        ],
        "traffic_baseline": traffic_baseline_surface_to_dict(bundle.traffic_baseline),
        "command_center": command_center_surface_to_dict(bundle.command_center),
    }


def export_replay_bundle_json(bundle: ReplayBundle) -> str:
    """Return deterministic JSON for one replay bundle."""

    return json.dumps(replay_bundle_to_dict(bundle), indent=2, sort_keys=True) + "\n"


def export_live_session_bundle_json(bundle: LiveSessionBundle) -> str:
    """Return deterministic JSON for one live-session bundle."""

    return (
        json.dumps(live_session_bundle_to_dict(bundle), indent=2, sort_keys=True)
        + "\n"
    )


def export_live_sync_bundle_json(bundle: LiveSyncBundle) -> str:
    """Return deterministic JSON for one live sync bundle."""

    return json.dumps(live_sync_bundle_to_dict(bundle), indent=2, sort_keys=True) + "\n"


def _build_replay_command_result(
    *,
    record: CommandApplicationRecord,
    frame: ReplayFrame,
) -> SimulationCommandResult:
    return SimulationCommandResult(
        status="accepted",
        command=command_to_dict(record.command),
        sequence=record.sequence,
        started_at_s=record.started_at_s,
        completed_at_s=record.completed_at_s,
        result_timestamp_s=frame.timestamp_s,
        emitted_update_indices=(),
        blocked_edge_ids=frame.blocked_edge_ids,
        vehicles=frame.vehicles,
    )


def _build_replay_command_results(
    *,
    command_history: tuple[CommandApplicationRecord, ...],
    frames: tuple[ReplayFrame, ...],
) -> tuple[SimulationCommandResult, ...]:
    results: list[SimulationCommandResult] = []
    frame_index = 1

    for record in command_history:
        frame, frame_index = _select_replay_result_frame(
            record=record,
            frames=frames,
            start_index=frame_index,
        )
        results.append(_build_replay_command_result(record=record, frame=frame))

    return tuple(results)


def _select_replay_result_frame(
    *,
    record: CommandApplicationRecord,
    frames: tuple[ReplayFrame, ...],
    start_index: int,
) -> tuple[ReplayFrame, int]:
    candidate: ReplayFrame | None = None
    frame_index = start_index

    while frame_index < len(frames):
        frame = frames[frame_index]
        frame_index += 1

        if isinstance(
            record.command,
            (BlockEdgeCommand, RepositionVehicleCommand, UnblockEdgeCommand),
        ):
            if (
                frame.trigger.source == "command"
                and frame.trigger.sequence == record.sequence
            ):
                return frame, frame_index
            continue

        assert isinstance(record.command, AssignVehicleDestinationCommand)
        trace_event = frame.trigger.trace_event
        if (
            frame.trigger.source != "trace"
            or trace_event is None
            or trace_event.get("vehicle_id") != record.command.vehicle_id
            or not (record.started_at_s <= frame.timestamp_s <= record.completed_at_s)
        ):
            continue

        candidate = frame
        if (
            trace_event.get("event_type") == "behavior_transition"
            and trace_event.get("to_behavior_state") == "idle"
            and trace_event.get("transition_reason") == "route_complete"
        ):
            return frame, frame_index

    if candidate is not None:
        return candidate, frame_index

    raise ValueError(
        "could not resolve a replay result frame for command "
        f"sequence {record.sequence}"
    )


def _build_current_command_result(
    *,
    engine: SimulationEngine,
    record: CommandApplicationRecord,
) -> SimulationCommandResult:
    return SimulationCommandResult(
        status="accepted",
        command=command_to_dict(record.command),
        sequence=record.sequence,
        started_at_s=record.started_at_s,
        completed_at_s=record.completed_at_s,
        result_timestamp_s=engine.simulated_time_s,
        emitted_update_indices=(),
        blocked_edge_ids=tuple(sorted(engine.world_state.blocked_edge_ids)),
        vehicles=_build_current_vehicle_surface_states(engine),
    )


def _build_current_vehicle_surface_states(
    engine: SimulationEngine,
) -> tuple[VehicleSurfaceState, ...]:
    return tuple(
        _vehicle_to_surface_state(vehicle) for vehicle in engine.vehicles
    )


def _map_surface_to_dict(map_surface: MapSurface) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "node_id": node.node_id,
                "position": list(node.position),
                "node_type": node.node_type,
            }
            for node in map_surface.nodes
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "start_node_id": edge.start_node_id,
                "end_node_id": edge.end_node_id,
                "distance": edge.distance,
                "speed_limit": edge.speed_limit,
            }
            for edge in map_surface.edges
        ],
    }


def _replay_frame_to_dict(frame: ReplayFrame) -> dict[str, Any]:
    return {
        "frame_index": frame.frame_index,
        "timestamp_s": frame.timestamp_s,
        "trigger": _frame_trigger_to_dict(frame.trigger),
        "blocked_edge_ids": list(frame.blocked_edge_ids),
        "vehicles": [_vehicle_surface_state_to_dict(vehicle) for vehicle in frame.vehicles],
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


def _vehicle_surface_state_to_dict(vehicle: VehicleSurfaceState) -> dict[str, Any]:
    return {
        "vehicle_id": vehicle.vehicle_id,
        "node_id": vehicle.node_id,
        "position": list(vehicle.position),
        "operational_state": vehicle.operational_state,
    }


def _vehicle_to_surface_state(vehicle: Vehicle) -> VehicleSurfaceState:
    return VehicleSurfaceState(
        vehicle_id=vehicle.id,
        node_id=vehicle.current_node_id,
        position=vehicle.get_position(),
        operational_state=vehicle.operational_state,
    )


__all__ = [
    "LIVE_SESSION_BUNDLE_SCHEMA_VERSION",
    "LIVE_SYNC_BUNDLE_SCHEMA_VERSION",
    "REPLAY_BUNDLE_SCHEMA_VERSION",
    "SIMULATION_API_VERSION",
    "LiveSessionBundle",
    "LiveSyncBundle",
    "ReplayBundle",
    "SimulationApiMetadata",
    "SimulationCommandResult",
    "apply_command_with_result",
    "build_live_session_bundle",
    "build_live_sync_bundle",
    "build_replay_bundle",
    "build_replay_bundle_from_controller",
    "build_replay_bundle_from_live_session",
    "export_live_session_bundle_json",
    "export_live_sync_bundle_json",
    "export_replay_bundle_json",
    "live_session_bundle_to_dict",
    "live_sync_bundle_to_dict",
    "replay_bundle_to_dict",
    "simulation_api_metadata_to_dict",
    "simulation_command_result_to_dict",
]
