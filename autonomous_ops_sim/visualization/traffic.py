from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.visualization.geometry import (
    RenderGeometrySurface,
    RoadGeometrySurface,
)
from autonomous_ops_sim.visualization.motion import VehicleMotionSegment
from autonomous_ops_sim.visualization.state import VisualizationState


@dataclass(frozen=True)
class TrafficControlPoint:
    """Deterministic baseline control rule at one rendered intersection."""

    control_id: str
    node_id: int
    control_type: str
    controlled_road_ids: tuple[str, ...]
    stop_line_ids: tuple[str, ...]
    protected_conflict_zone_ids: tuple[str, ...]
    signal_ready: bool


@dataclass(frozen=True)
class TrafficQueueRecord:
    """Deterministic queued wait derived from authoritative trace behavior."""

    vehicle_id: int
    node_id: int
    road_id: str | None
    queue_start_s: float
    queue_end_s: float
    reason: str


@dataclass(frozen=True)
class TrafficBaselineSurface:
    """Static traffic baseline layer derived from replay, geometry, and waits."""

    control_points: tuple[TrafficControlPoint, ...]
    queue_records: tuple[TrafficQueueRecord, ...]


@dataclass(frozen=True)
class TrafficRoadState:
    """Sampled road traffic state at one viewer time."""

    road_id: str
    active_vehicle_ids: tuple[int, ...]
    queued_vehicle_ids: tuple[int, ...]
    occupancy_count: int
    min_spacing_m: float | None
    congestion_intensity: float
    congestion_level: str
    control_state: str
    stop_line_ids: tuple[str, ...]
    protected_conflict_zone_ids: tuple[str, ...]


@dataclass(frozen=True)
class TrafficSnapshot:
    """Continuous traffic sample for one explicit time."""

    timestamp_s: float
    road_states: tuple[TrafficRoadState, ...]


def build_traffic_baseline_surface(
    state: VisualizationState,
    *,
    render_geometry: RenderGeometrySurface,
    motion_segments: tuple[VehicleMotionSegment, ...],
) -> TrafficBaselineSurface:
    """Build deterministic baseline traffic semantics from existing replay data."""

    return TrafficBaselineSurface(
        control_points=_build_control_points(render_geometry),
        queue_records=_build_queue_records(
            state=state,
            roads=render_geometry.roads,
            motion_segments=motion_segments,
        ),
    )


def sample_traffic_snapshot(
    *,
    timestamp_s: float,
    render_geometry: RenderGeometrySurface,
    motion_segments: tuple[VehicleMotionSegment, ...],
    baseline: TrafficBaselineSurface,
) -> TrafficSnapshot:
    """Sample congestion and queue state at one explicit timestamp."""

    control_by_road_id = _control_points_by_road_id(baseline.control_points)
    road_states: list[TrafficRoadState] = []
    for road in render_geometry.roads:
        active_segments = [
            segment
            for segment in motion_segments
            if segment.edge_id in road.edge_ids
            and segment.start_time_s < timestamp_s < segment.end_time_s
        ]
        active_positions = [
            _segment_position_at_time(segment, timestamp_s) for segment in active_segments
        ]
        queued_vehicle_ids = tuple(
            sorted(
                record.vehicle_id
                for record in baseline.queue_records
                if record.road_id == road.road_id
                and record.queue_start_s <= timestamp_s < record.queue_end_s
            )
        )
        active_vehicle_ids = tuple(
            sorted(segment.vehicle_id for segment in active_segments)
        )
        min_spacing_m = _min_spacing_m(active_positions)
        congestion_level = _congestion_level(
            occupancy_count=len(active_vehicle_ids),
            queue_count=len(queued_vehicle_ids),
            min_spacing_m=min_spacing_m,
        )
        control_state, stop_line_ids, protected_conflict_zone_ids = _road_control_state(
            road_id=road.road_id,
            control_points=control_by_road_id,
        )
        congestion_intensity = _congestion_intensity(
            occupancy_count=len(active_vehicle_ids),
            queue_count=len(queued_vehicle_ids),
            min_spacing_m=min_spacing_m,
        )
        road_states.append(
            TrafficRoadState(
                road_id=road.road_id,
                active_vehicle_ids=active_vehicle_ids,
                queued_vehicle_ids=queued_vehicle_ids,
                occupancy_count=len(active_vehicle_ids),
                min_spacing_m=min_spacing_m,
                congestion_intensity=congestion_intensity,
                congestion_level=congestion_level,
                control_state=control_state,
                stop_line_ids=stop_line_ids,
                protected_conflict_zone_ids=protected_conflict_zone_ids,
            )
        )

    return TrafficSnapshot(
        timestamp_s=timestamp_s,
        road_states=tuple(road_states),
    )


def traffic_baseline_surface_to_dict(
    surface: TrafficBaselineSurface,
) -> dict[str, Any]:
    """Convert baseline traffic semantics into a stable JSON-ready record."""

    return {
        "control_points": [
            {
                "control_id": control.control_id,
                "node_id": control.node_id,
                "control_type": control.control_type,
                "controlled_road_ids": list(control.controlled_road_ids),
            }
            for control in surface.control_points
        ],
        "queue_records": [
            {
                "vehicle_id": record.vehicle_id,
                "node_id": record.node_id,
                "road_id": record.road_id,
                "queue_start_s": record.queue_start_s,
                "queue_end_s": record.queue_end_s,
                "reason": record.reason,
            }
            for record in surface.queue_records
        ],
    }


def traffic_snapshot_to_dict(snapshot: TrafficSnapshot) -> dict[str, Any]:
    """Convert one sampled traffic snapshot into a stable JSON-ready record."""

    return {
        "timestamp_s": snapshot.timestamp_s,
        "road_states": [
            {
                "road_id": road_state.road_id,
                "active_vehicle_ids": list(road_state.active_vehicle_ids),
                "queued_vehicle_ids": list(road_state.queued_vehicle_ids),
                "occupancy_count": road_state.occupancy_count,
                "min_spacing_m": road_state.min_spacing_m,
                "congestion_intensity": road_state.congestion_intensity,
                "congestion_level": road_state.congestion_level,
                "control_state": road_state.control_state,
                "stop_line_ids": list(road_state.stop_line_ids),
                "protected_conflict_zone_ids": list(
                    road_state.protected_conflict_zone_ids
                ),
            }
            for road_state in snapshot.road_states
        ],
    }


def _build_control_points(
    render_geometry: RenderGeometrySurface,
) -> tuple[TrafficControlPoint, ...]:
    controls: list[TrafficControlPoint] = []
    for intersection in render_geometry.intersections:
        min_x = min(point[0] for point in intersection.polygon)
        max_x = max(point[0] for point in intersection.polygon)
        min_y = min(point[1] for point in intersection.polygon)
        max_y = max(point[1] for point in intersection.polygon)
        connected_road_ids = tuple(
            sorted(
                road.road_id
                for road in render_geometry.roads
                if _road_touches_intersection_bounds(
                    road,
                    min_x=min_x,
                    max_x=max_x,
                    min_y=min_y,
                    max_y=max_y,
                )
            )
        )
        stop_line_ids = tuple(
            sorted(
                stop_line.stop_line_id
                for stop_line in render_geometry.stop_lines
                if stop_line.lane_id in {
                    lane.lane_id
                    for lane in render_geometry.lanes
                    if lane.road_id in connected_road_ids
                }
            )
        )
        protected_conflict_zone_ids = tuple(
            sorted(
                merge_zone.merge_zone_id
                for merge_zone in render_geometry.merge_zones
                if any(
                    lane_id in merge_zone.lane_ids
                    for lane_id in (
                        lane.lane_id
                        for lane in render_geometry.lanes
                        if lane.road_id in connected_road_ids
                    )
                )
            )
        )
        if len(connected_road_ids) < 2:
            continue
        if len(connected_road_ids) >= 4 or stop_line_ids:
            control_type = "signalized"
        elif len(connected_road_ids) >= 2:
            control_type = "yield"
        else:
            control_type = "uncontrolled"
        controls.append(
            TrafficControlPoint(
                control_id=f"control-{intersection.intersection_id}",
                node_id=intersection.node_id,
                control_type=control_type,
                controlled_road_ids=connected_road_ids,
                stop_line_ids=stop_line_ids,
                protected_conflict_zone_ids=protected_conflict_zone_ids,
                signal_ready=bool(stop_line_ids or protected_conflict_zone_ids),
            )
        )
    return tuple(controls)


def _control_points_by_road_id(
    control_points: tuple[TrafficControlPoint, ...],
) -> dict[str, tuple[TrafficControlPoint, ...]]:
    by_road_id: dict[str, list[TrafficControlPoint]] = {}
    for control in control_points:
        for road_id in control.controlled_road_ids:
            by_road_id.setdefault(road_id, []).append(control)
    return {
        road_id: tuple(
            sorted(
                controls,
                key=lambda control: (
                    _control_priority(control.control_type),
                    control.control_id,
                ),
                reverse=True,
            )
        )
        for road_id, controls in by_road_id.items()
    }


def _road_control_state(
    *,
    road_id: str,
    control_points: dict[str, tuple[TrafficControlPoint, ...]],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    controls = control_points.get(road_id, ())
    if not controls:
        return "free_flow", (), ()
    primary = controls[0]
    stop_line_ids = tuple(
        sorted({stop_line_id for control in controls for stop_line_id in control.stop_line_ids})
    )
    protected_conflict_zone_ids = tuple(
        sorted(
            {
                zone_id
                for control in controls
                for zone_id in control.protected_conflict_zone_ids
            }
        )
    )
    return primary.control_type, stop_line_ids, protected_conflict_zone_ids


def _control_priority(control_type: str) -> int:
    return {
        "signalized": 3,
        "yield": 2,
        "uncontrolled": 1,
    }.get(control_type, 0)


def _build_queue_records(
    *,
    state: VisualizationState,
    roads: tuple[RoadGeometrySurface, ...],
    motion_segments: tuple[VehicleMotionSegment, ...],
) -> tuple[TrafficQueueRecord, ...]:
    queue_start_events: dict[int, dict[str, Any]] = {}
    records: list[TrafficQueueRecord] = []
    road_by_edge_id = {
        edge_id: road.road_id
        for road in roads
        for edge_id in road.edge_ids
    }

    for frame in state.frames:
        event = frame.trigger.trace_event
        if frame.trigger.source != "trace" or event is None:
            continue
        event_type = event.get("event_type")
        vehicle_id = event.get("vehicle_id")
        if not isinstance(vehicle_id, int):
            continue

        if event_type == "conflict_wait_start":
            node_id = event.get("node_id")
            queue_start_events[vehicle_id] = {
                "node_id": int(node_id) if isinstance(node_id, int) else -1,
                "queue_start_s": frame.timestamp_s,
                "reason": "conflict_wait",
            }
            continue

        if event_type != "conflict_wait_complete":
            continue
        started = queue_start_events.pop(vehicle_id, None)
        if started is None:
            continue
        road_id = _road_id_after_queue(
            vehicle_id=vehicle_id,
            wait_end_s=frame.timestamp_s,
            motion_segments=motion_segments,
            road_by_edge_id=road_by_edge_id,
        )
        records.append(
            TrafficQueueRecord(
                vehicle_id=vehicle_id,
                node_id=started["node_id"],
                road_id=road_id,
                queue_start_s=started["queue_start_s"],
                queue_end_s=frame.timestamp_s,
                reason=started["reason"],
            )
        )

    return tuple(records)


def _road_id_after_queue(
    *,
    vehicle_id: int,
    wait_end_s: float,
    motion_segments: tuple[VehicleMotionSegment, ...],
    road_by_edge_id: dict[int, str],
) -> str | None:
    for segment in motion_segments:
        if segment.vehicle_id != vehicle_id:
            continue
        if segment.start_time_s < wait_end_s:
            continue
        return road_by_edge_id.get(segment.edge_id)
    return None


def _road_touches_intersection_bounds(
    road: RoadGeometrySurface,
    *,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> bool:
    return any(
        min_x <= point[0] <= max_x and min_y <= point[1] <= max_y
        for point in (road.centerline[0], road.centerline[-1])
    )


def _min_spacing_m(active_positions: list[tuple[float, float, float]]) -> float | None:
    if len(active_positions) < 2:
        return None
    minimum: float | None = None
    for index, previous in enumerate(active_positions):
        for current in active_positions[index + 1 :]:
            distance = (
                (current[0] - previous[0]) ** 2
                + (current[1] - previous[1]) ** 2
                + (current[2] - previous[2]) ** 2
            ) ** 0.5
            if minimum is None or distance < minimum:
                minimum = distance
    return minimum


def _segment_position_at_time(
    segment: VehicleMotionSegment,
    timestamp_s: float,
) -> tuple[float, float, float]:
    if segment.duration_s <= 0.0:
        return segment.end_position
    progress = min(
        1.0,
        max(0.0, (timestamp_s - segment.start_time_s) / segment.duration_s),
    )
    return (
        segment.start_position[0]
        + (segment.end_position[0] - segment.start_position[0]) * progress,
        segment.start_position[1]
        + (segment.end_position[1] - segment.start_position[1]) * progress,
        segment.start_position[2]
        + (segment.end_position[2] - segment.start_position[2]) * progress,
    )


def _congestion_level(
    *,
    occupancy_count: int,
    queue_count: int,
    min_spacing_m: float | None,
) -> str:
    if queue_count > 0:
        return "queued"
    if occupancy_count >= 2 and min_spacing_m is not None and min_spacing_m <= 1.5:
        return "congested"
    if occupancy_count >= 1:
        return "active"
    return "free"


def _congestion_intensity(
    *,
    occupancy_count: int,
    queue_count: int,
    min_spacing_m: float | None,
) -> float:
    if occupancy_count <= 0 and queue_count <= 0:
        return 0.0

    spacing_pressure = 0.0
    if min_spacing_m is not None:
        spacing_pressure = max(0.0, min(1.0, (1.8 - min_spacing_m) / 1.8))

    vehicle_pressure = min(1.0, occupancy_count / 4.0)
    queue_pressure = min(1.0, queue_count / 3.0)
    if queue_count > 0:
        return min(
            1.0,
            0.55
            + (queue_pressure * 0.35)
            + (vehicle_pressure * 0.1)
            + (spacing_pressure * 0.2),
        )
    return min(1.0, (vehicle_pressure * 0.55) + (spacing_pressure * 0.45))


__all__ = [
    "TrafficBaselineSurface",
    "TrafficControlPoint",
    "TrafficQueueRecord",
    "TrafficRoadState",
    "TrafficSnapshot",
    "build_traffic_baseline_surface",
    "sample_traffic_snapshot",
    "traffic_baseline_surface_to_dict",
    "traffic_snapshot_to_dict",
]
