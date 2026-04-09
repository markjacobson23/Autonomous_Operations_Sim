from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from autonomous_ops_sim.io.exports import trace_event_to_dict
from autonomous_ops_sim.simulation.commands import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    RepositionVehicleCommand,
    command_to_dict,
)
from autonomous_ops_sim.simulation.control import (
    CommandApplicationRecord,
    SimulationController,
)
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.live_session import (
    LiveSimulationSession,
    SessionAdvanceRecord,
    session_advance_to_dict,
)
from autonomous_ops_sim.simulation.trace import TraceEvent, TraceEventType
from autonomous_ops_sim.vehicles.vehicle import Position


VISUALIZATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class NodeSurface:
    """Stable visualization-facing projection of one map node."""

    node_id: int
    position: Position
    node_type: str


@dataclass(frozen=True)
class EdgeSurface:
    """Stable visualization-facing projection of one map edge."""

    edge_id: int
    start_node_id: int
    end_node_id: int
    distance: float
    speed_limit: float


@dataclass(frozen=True)
class MapSurface:
    """Stable static topology surface for replay/viewers."""

    nodes: tuple[NodeSurface, ...]
    edges: tuple[EdgeSurface, ...]


@dataclass(frozen=True)
class VehicleSurfaceState:
    """Stable projection of one vehicle at one replay frame."""

    vehicle_id: int
    node_id: int
    position: Position
    operational_state: str


@dataclass(frozen=True)
class FrameTrigger:
    """Stable cause for one replay frame transition."""

    source: str
    sequence: int
    timestamp_s: float
    event_name: str
    trace_event: dict[str, Any] | None = None
    command: dict[str, Any] | None = None
    session_step: dict[str, Any] | None = None


@dataclass(frozen=True)
class ReplayFrame:
    """Stable visualization snapshot for one replay point."""

    frame_index: int
    timestamp_s: float
    trigger: FrameTrigger
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[VehicleSurfaceState, ...]


@dataclass(frozen=True)
class VisualizationState:
    """Stable visualization-oriented replay surface for one completed run."""

    schema_version: int
    seed: int
    final_time_s: float
    map_surface: MapSurface
    frames: tuple[ReplayFrame, ...]


@dataclass(frozen=True)
class _TimelineRecord:
    timestamp_s: float
    sort_group: int
    sequence: int
    trace_event: TraceEvent | None = None
    command_record: CommandApplicationRecord | None = None
    session_record: SessionAdvanceRecord | None = None


def build_visualization_state(
    engine: SimulationEngine,
    *,
    command_history: tuple[CommandApplicationRecord, ...]
    | list[CommandApplicationRecord] = (),
    session_history: tuple[SessionAdvanceRecord, ...]
    | list[SessionAdvanceRecord] = (),
) -> VisualizationState:
    """Build a stable visualization replay surface from an engine run."""

    history = tuple(command_history)
    session_progress = tuple(session_history)
    map_surface = _build_map_surface(engine)
    initial_blocked_edge_ids = _infer_initial_blocked_edge_ids(engine, history)
    initial_vehicle_states = _infer_initial_vehicle_states(engine, history)

    mutable_vehicle_states = {
        vehicle_id: VehicleSurfaceState(
            vehicle_id=state.vehicle_id,
            node_id=state.node_id,
            position=state.position,
            operational_state=state.operational_state,
        )
        for vehicle_id, state in initial_vehicle_states.items()
    }
    mutable_blocked_edge_ids = set(initial_blocked_edge_ids)

    frames: list[ReplayFrame] = [
        ReplayFrame(
            frame_index=0,
            timestamp_s=0.0,
            trigger=FrameTrigger(
                source="initial",
                sequence=0,
                timestamp_s=0.0,
                event_name="initial_state",
            ),
            blocked_edge_ids=tuple(sorted(mutable_blocked_edge_ids)),
            vehicles=_sorted_vehicle_states(mutable_vehicle_states.values()),
        )
    ]

    timeline = _build_timeline(
        engine=engine,
        command_history=history,
        session_history=session_progress,
    )
    for record in timeline:
        if record.session_record is not None:
            trigger = FrameTrigger(
                source="session",
                sequence=record.session_record.sequence,
                timestamp_s=record.session_record.completed_at_s,
                event_name="session_advance",
                session_step=session_advance_to_dict(record.session_record),
            )
        elif record.command_record is not None:
            _apply_command_record(
                record.command_record,
                mutable_vehicle_states=mutable_vehicle_states,
                mutable_blocked_edge_ids=mutable_blocked_edge_ids,
                engine=engine,
            )
            trigger = FrameTrigger(
                source="command",
                sequence=record.command_record.sequence,
                timestamp_s=record.command_record.completed_at_s,
                event_name=record.command_record.command.command_type,
                command=command_to_dict(record.command_record.command),
            )
        else:
            assert record.trace_event is not None
            _apply_trace_event(
                record.trace_event,
                mutable_vehicle_states=mutable_vehicle_states,
                engine=engine,
            )
            trigger = FrameTrigger(
                source="trace",
                sequence=record.trace_event.sequence,
                timestamp_s=record.trace_event.timestamp_s,
                event_name=record.trace_event.event_type.value,
                trace_event=trace_event_to_dict(record.trace_event),
            )

        frames.append(
            ReplayFrame(
                frame_index=len(frames),
                timestamp_s=record.timestamp_s,
                trigger=trigger,
                blocked_edge_ids=tuple(sorted(mutable_blocked_edge_ids)),
                vehicles=_sorted_vehicle_states(mutable_vehicle_states.values()),
            )
        )

    return VisualizationState(
        schema_version=VISUALIZATION_SCHEMA_VERSION,
        seed=engine.seed,
        final_time_s=engine.simulated_time_s,
        map_surface=map_surface,
        frames=tuple(frames),
    )


def build_visualization_state_from_controller(
    controller: SimulationController,
) -> VisualizationState:
    """Build visualization state from a command-driven engine run."""

    return build_visualization_state(
        controller.engine,
        command_history=controller.command_history,
    )


def build_visualization_state_from_live_session(
    session: LiveSimulationSession,
) -> VisualizationState:
    """Build visualization state from an explicitly progressed live session."""

    return build_visualization_state(
        session.engine,
        command_history=session.command_history,
        session_history=session.progress_history,
    )


def visualization_state_to_dict(state: VisualizationState) -> dict[str, Any]:
    """Convert visualization state into a stable JSON-ready record."""

    return {
        "schema_version": state.schema_version,
        "seed": state.seed,
        "final_time_s": state.final_time_s,
        "map_surface": {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "position": list(node.position),
                    "node_type": node.node_type,
                }
                for node in state.map_surface.nodes
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "start_node_id": edge.start_node_id,
                    "end_node_id": edge.end_node_id,
                    "distance": edge.distance,
                    "speed_limit": edge.speed_limit,
                }
                for edge in state.map_surface.edges
            ],
        },
        "frames": [
            {
                "frame_index": frame.frame_index,
                "timestamp_s": frame.timestamp_s,
                "trigger": _frame_trigger_to_dict(frame.trigger),
                "blocked_edge_ids": list(frame.blocked_edge_ids),
                "vehicles": [
                    {
                        "vehicle_id": vehicle.vehicle_id,
                        "node_id": vehicle.node_id,
                        "position": list(vehicle.position),
                        "operational_state": vehicle.operational_state,
                    }
                    for vehicle in frame.vehicles
                ],
            }
            for frame in state.frames
        ],
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


def export_visualization_json(state: VisualizationState) -> str:
    """Return deterministic JSON for one visualization replay surface."""

    return json.dumps(
        visualization_state_to_dict(state),
        indent=2,
        sort_keys=True,
    ) + "\n"


def load_visualization_json(path: str | Path) -> VisualizationState:
    """Load visualization state from a deterministic JSON export."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return _visualization_state_from_dict(data)


def _visualization_state_from_dict(data: dict[str, Any]) -> VisualizationState:
    map_surface_data = data["map_surface"]
    frames_data = data["frames"]

    return VisualizationState(
        schema_version=int(data["schema_version"]),
        seed=int(data["seed"]),
        final_time_s=float(data["final_time_s"]),
        map_surface=MapSurface(
            nodes=tuple(
                NodeSurface(
                    node_id=int(node["node_id"]),
                    position=_position_from_iterable(node["position"]),
                    node_type=str(node["node_type"]),
                )
                for node in map_surface_data["nodes"]
            ),
            edges=tuple(
                EdgeSurface(
                    edge_id=int(edge["edge_id"]),
                    start_node_id=int(edge["start_node_id"]),
                    end_node_id=int(edge["end_node_id"]),
                    distance=float(edge["distance"]),
                    speed_limit=float(edge["speed_limit"]),
                )
                for edge in map_surface_data["edges"]
            ),
        ),
        frames=tuple(
            ReplayFrame(
                frame_index=int(frame["frame_index"]),
                timestamp_s=float(frame["timestamp_s"]),
                trigger=FrameTrigger(
                    source=str(frame["trigger"]["source"]),
                    sequence=int(frame["trigger"]["sequence"]),
                    timestamp_s=float(frame["trigger"]["timestamp_s"]),
                    event_name=str(frame["trigger"]["event_name"]),
                    trace_event=frame["trigger"].get("trace_event"),
                    command=frame["trigger"].get("command"),
                    session_step=frame["trigger"].get("session_step"),
                ),
                blocked_edge_ids=tuple(
                    int(edge_id) for edge_id in frame["blocked_edge_ids"]
                ),
                vehicles=tuple(
                    VehicleSurfaceState(
                        vehicle_id=int(vehicle["vehicle_id"]),
                        node_id=int(vehicle["node_id"]),
                        position=_position_from_iterable(vehicle["position"]),
                        operational_state=str(vehicle["operational_state"]),
                    )
                    for vehicle in frame["vehicles"]
                ),
            )
            for frame in frames_data
        ),
    )


def _build_map_surface(engine: SimulationEngine) -> MapSurface:
    graph = engine.map.graph
    return MapSurface(
        nodes=tuple(
            NodeSurface(
                node_id=node_id,
                position=(
                    float(node.position[0]),
                    float(node.position[1]),
                    float(node.position[2]),
                ),
                node_type=node.node_type.name.lower(),
            )
            for node_id, node in sorted(graph.nodes.items(), key=lambda item: item[0])
        ),
        edges=tuple(
            EdgeSurface(
                edge_id=edge_id,
                start_node_id=edge.start_node.id,
                end_node_id=edge.end_node.id,
                distance=float(edge.distance),
                speed_limit=float(edge.speed_limit),
            )
            for edge_id, edge in sorted(graph.edges.items(), key=lambda item: item[0])
        ),
    )


def _infer_initial_blocked_edge_ids(
    engine: SimulationEngine,
    command_history: tuple[CommandApplicationRecord, ...],
) -> tuple[int, ...]:
    final_blocked_edge_ids = set(engine.world_state.blocked_edge_ids)
    command_block_edge_ids = {
        record.command.edge_id
        for record in command_history
        if isinstance(record.command, BlockEdgeCommand)
    }
    return tuple(sorted(final_blocked_edge_ids - command_block_edge_ids))


def _infer_initial_vehicle_states(
    engine: SimulationEngine,
    command_history: tuple[CommandApplicationRecord, ...],
) -> dict[int, VehicleSurfaceState]:
    initial_states: dict[int, VehicleSurfaceState] = {}

    for vehicle_id, node_id, state_name in _iter_vehicle_initial_hints(
        engine=engine,
        command_history=command_history,
    ):
        initial_states.setdefault(
            vehicle_id,
            VehicleSurfaceState(
                vehicle_id=vehicle_id,
                node_id=node_id,
                position=engine.map.get_position(node_id),
                operational_state=state_name,
            ),
        )

    for vehicle in engine.vehicles:
        initial_states.setdefault(
            vehicle.id,
            VehicleSurfaceState(
                vehicle_id=vehicle.id,
                node_id=vehicle.current_node_id,
                position=vehicle.get_position(),
                operational_state=vehicle.operational_state,
            ),
        )

    return initial_states


def _iter_vehicle_initial_hints(
    *,
    engine: SimulationEngine,
    command_history: tuple[CommandApplicationRecord, ...],
) -> tuple[tuple[int, int, str], ...]:
    hints: list[tuple[float, int, int, int, str]] = []

    for record in command_history:
        command = record.command
        if isinstance(command, RepositionVehicleCommand):
            hints.append(
                (
                    record.completed_at_s,
                    record.sequence,
                    command.vehicle_id,
                    command.node_id,
                    "idle",
                )
            )

    for event in engine.trace.events:
        node_id = _event_node_hint(event)
        if node_id is None:
            continue
        initial_state = (
            event.from_behavior_state
            if event.event_type == TraceEventType.BEHAVIOR_TRANSITION
            and event.from_behavior_state is not None
            else "idle"
        )
        hints.append(
            (
                event.timestamp_s,
                event.sequence,
                event.vehicle_id,
                node_id,
                initial_state,
            )
        )

    ordered_hints: list[tuple[int, int, str]] = []
    seen_vehicle_ids: set[int] = set()
    for _, _, vehicle_id, node_id, initial_state in sorted(hints):
        if vehicle_id in seen_vehicle_ids:
            continue
        seen_vehicle_ids.add(vehicle_id)
        ordered_hints.append((vehicle_id, node_id, initial_state))

    return tuple(ordered_hints)


def _event_node_hint(event: TraceEvent) -> int | None:
    if event.node_id is not None:
        return event.node_id
    if event.start_node_id is not None:
        return event.start_node_id
    if event.end_node_id is not None:
        return event.end_node_id
    return None


def _build_timeline(
    *,
    engine: SimulationEngine,
    command_history: tuple[CommandApplicationRecord, ...],
    session_history: tuple[SessionAdvanceRecord, ...],
) -> tuple[_TimelineRecord, ...]:
    if not command_history and not session_history:
        return tuple(
            _TimelineRecord(
                timestamp_s=event.timestamp_s,
                sort_group=2,
                sequence=event.sequence,
                trace_event=event,
            )
            for event in engine.trace.events
        )

    timeline: list[_TimelineRecord] = []
    trace_events = engine.trace.events
    trace_index = 0
    session_index = 0

    def append_pending_session_records(until_timestamp_s: float) -> None:
        nonlocal session_index
        while (
            session_index < len(session_history)
            and session_history[session_index].completed_at_s <= until_timestamp_s
        ):
            session_record = session_history[session_index]
            timeline.append(
                _TimelineRecord(
                    timestamp_s=session_record.completed_at_s,
                    sort_group=0,
                    sequence=session_record.sequence,
                    session_record=session_record,
                )
            )
            session_index += 1

    for record in command_history:
        append_pending_session_records(record.completed_at_s)
        command = record.command
        if isinstance(command, (BlockEdgeCommand, RepositionVehicleCommand)):
            timeline.append(
                _TimelineRecord(
                    timestamp_s=record.completed_at_s,
                    sort_group=1,
                    sequence=record.sequence,
                    command_record=record,
                )
            )
            continue

        assert isinstance(command, AssignVehicleDestinationCommand)
        segment_complete = False
        while trace_index < len(trace_events) and not segment_complete:
            event = trace_events[trace_index]
            timeline.append(
                _TimelineRecord(
                    timestamp_s=event.timestamp_s,
                    sort_group=2,
                    sequence=event.sequence,
                    trace_event=event,
                )
            )
            trace_index += 1
            segment_complete = (
                event.vehicle_id == command.vehicle_id
                and event.event_type == TraceEventType.BEHAVIOR_TRANSITION
                and event.to_behavior_state == "idle"
                and event.transition_reason == "route_complete"
            )

    while trace_index < len(trace_events):
        event = trace_events[trace_index]
        append_pending_session_records(event.timestamp_s)
        timeline.append(
            _TimelineRecord(
                timestamp_s=event.timestamp_s,
                sort_group=2,
                sequence=event.sequence,
                trace_event=event,
            )
        )
        trace_index += 1

    append_pending_session_records(float("inf"))

    return tuple(timeline)


def _apply_command_record(
    record: CommandApplicationRecord,
    *,
    mutable_vehicle_states: dict[int, VehicleSurfaceState],
    mutable_blocked_edge_ids: set[int],
    engine: SimulationEngine,
) -> None:
    command = record.command
    if isinstance(command, BlockEdgeCommand):
        mutable_blocked_edge_ids.add(command.edge_id)
        return

    assert isinstance(command, RepositionVehicleCommand)
    mutable_vehicle_states[command.vehicle_id] = VehicleSurfaceState(
        vehicle_id=command.vehicle_id,
        node_id=command.node_id,
        position=engine.map.get_position(command.node_id),
        operational_state="idle",
    )


def _apply_trace_event(
    event: TraceEvent,
    *,
    mutable_vehicle_states: dict[int, VehicleSurfaceState],
    engine: SimulationEngine,
) -> None:
    state = mutable_vehicle_states.get(event.vehicle_id)
    if state is None:
        node_id = _event_node_hint(event)
        if node_id is None:
            raise RuntimeError(
                "visualization replay cannot infer an initial node for "
                f"vehicle_id {event.vehicle_id}"
            )
        state = VehicleSurfaceState(
            vehicle_id=event.vehicle_id,
            node_id=node_id,
            position=engine.map.get_position(node_id),
            operational_state="idle",
        )

    node_id = state.node_id
    position = state.position
    operational_state = state.operational_state

    if event.event_type == TraceEventType.BEHAVIOR_TRANSITION:
        if event.to_behavior_state is not None:
            operational_state = event.to_behavior_state
        if event.node_id is not None:
            node_id = event.node_id
            position = engine.map.get_position(node_id)
    elif event.event_type == TraceEventType.NODE_ARRIVAL:
        node_id = event.node_id if event.node_id is not None else state.node_id
        position = engine.map.get_position(node_id)
    elif event.node_id is not None:
        node_id = event.node_id
        position = engine.map.get_position(node_id)

    mutable_vehicle_states[event.vehicle_id] = VehicleSurfaceState(
        vehicle_id=event.vehicle_id,
        node_id=node_id,
        position=position,
        operational_state=operational_state,
    )


def _sorted_vehicle_states(
    vehicle_states: Iterable[VehicleSurfaceState],
) -> tuple[VehicleSurfaceState, ...]:
    return tuple(sorted(vehicle_states, key=lambda vehicle: vehicle.vehicle_id))


def _position_from_iterable(value: list[float] | tuple[float, ...]) -> Position:
    return (float(value[0]), float(value[1]), float(value[2]))
