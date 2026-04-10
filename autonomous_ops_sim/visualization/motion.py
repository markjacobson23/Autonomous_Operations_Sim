from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from autonomous_ops_sim.simulation.kinematics import (
    KinematicTraversalProfile,
    build_kinematic_profile,
    sample_profile_distance,
    sample_profile_speed,
)
from autonomous_ops_sim.vehicles.vehicle import Position
from autonomous_ops_sim.visualization.geometry import (
    LaneGeometrySurface,
    RenderGeometrySurface,
    RoadGeometrySurface,
)
from autonomous_ops_sim.visualization.state import (
    MapSurface,
    VisualizationState,
)


@dataclass(frozen=True)
class VehicleMotionSegment:
    """Deterministic motion segment derived from authoritative replay events."""

    vehicle_id: int
    segment_index: int
    edge_id: int
    start_node_id: int
    end_node_id: int
    start_time_s: float
    end_time_s: float
    duration_s: float
    distance: float
    start_position: Position
    end_position: Position
    path_points: tuple[Position, ...]
    heading_rad: float
    nominal_speed: float
    peak_speed: float
    acceleration_mps2: float
    deceleration_mps2: float
    profile_kind: str


@dataclass(frozen=True)
class InterpolatedVehicleState:
    """Viewer-facing sampled vehicle state between authoritative state changes."""

    vehicle_id: int
    node_id: int
    position: Position
    operational_state: str
    heading_rad: float
    speed: float
    active_edge_id: int | None
    start_node_id: int | None
    end_node_id: int | None
    motion_progress: float
    is_interpolated: bool


@dataclass(frozen=True)
class MotionSample:
    """Continuous viewer sample built from stable replay plus derived motion."""

    timestamp_s: float
    reference_frame_index: int
    blocked_edge_ids: tuple[int, ...]
    vehicles: tuple[InterpolatedVehicleState, ...]


def build_vehicle_motion_segments(
    state: VisualizationState,
    *,
    render_geometry: RenderGeometrySurface | None = None,
) -> tuple[VehicleMotionSegment, ...]:
    """Derive edge motion segments from authoritative replay frames."""

    edge_lookup = {edge.edge_id: edge for edge in state.map_surface.edges}
    segments: list[VehicleMotionSegment] = []
    segment_count_by_vehicle: dict[int, int] = {}

    for index, frame in enumerate(state.frames):
        trigger = frame.trigger
        event = trigger.trace_event
        if (
            trigger.source != "trace"
            or event is None
            or event.get("event_type") != "edge_enter"
            or event.get("edge_id") is None
            or event.get("vehicle_id") is None
            or event.get("start_node_id") is None
            or event.get("end_node_id") is None
        ):
            continue

        vehicle_id = int(event["vehicle_id"])
        edge_id = int(event["edge_id"])
        start_node_id = int(event["start_node_id"])
        end_node_id = int(event["end_node_id"])
        arrival_frame = _find_matching_arrival_frame(
            state=state,
            start_index=index + 1,
            vehicle_id=vehicle_id,
            end_node_id=end_node_id,
        )
        start_position = _node_position(state.map_surface, start_node_id)
        end_position = _node_position(state.map_surface, end_node_id)
        duration_s = max(0.0, arrival_frame.timestamp_s - frame.timestamp_s)
        edge = edge_lookup.get(edge_id)
        distance = edge.distance if edge is not None else _distance(start_position, end_position)
        path_points = _resolve_segment_path_points(
            render_geometry=render_geometry,
            edge_id=edge_id,
            start_position=start_position,
            end_position=end_position,
        )
        heading_rad = _heading_along_path(path_points, distance_along_path=0.0)
        nominal_speed = distance / duration_s if duration_s > 0.0 else 0.0
        profile = _segment_profile(
            distance=distance,
            duration_s=duration_s,
            speed_limit=edge.speed_limit if edge is not None else nominal_speed,
        )
        segment_index = segment_count_by_vehicle.get(vehicle_id, 0)
        segment_count_by_vehicle[vehicle_id] = segment_index + 1
        segments.append(
            VehicleMotionSegment(
                vehicle_id=vehicle_id,
                segment_index=segment_index,
                edge_id=edge_id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                start_time_s=frame.timestamp_s,
                end_time_s=arrival_frame.timestamp_s,
                duration_s=duration_s,
                distance=distance,
                start_position=start_position,
                end_position=end_position,
                path_points=path_points,
                heading_rad=heading_rad,
                nominal_speed=nominal_speed,
                peak_speed=profile.peak_speed_mps,
                acceleration_mps2=profile.acceleration_mps2,
                deceleration_mps2=profile.deceleration_mps2,
                profile_kind=profile.profile_kind,
            )
        )

    return tuple(segments)


def sample_motion(
    state: VisualizationState,
    *,
    timestamp_s: float,
    segments: tuple[VehicleMotionSegment, ...] | None = None,
) -> MotionSample:
    """Sample continuous motion at one explicit replay timestamp."""

    if not math.isfinite(timestamp_s):
        raise ValueError("timestamp_s must be finite")

    bounded_timestamp_s = min(max(timestamp_s, 0.0), state.final_time_s)
    motion_segments = segments or build_vehicle_motion_segments(state)
    reference_frame = _reference_frame_for_time(state, bounded_timestamp_s)

    vehicles = {
        vehicle.vehicle_id: InterpolatedVehicleState(
            vehicle_id=vehicle.vehicle_id,
            node_id=vehicle.node_id,
            position=vehicle.position,
            operational_state=vehicle.operational_state,
            heading_rad=0.0,
            speed=0.0,
            active_edge_id=None,
            start_node_id=None,
            end_node_id=None,
            motion_progress=1.0,
            is_interpolated=False,
        )
        for vehicle in reference_frame.vehicles
    }

    for segment in motion_segments:
        if not (segment.start_time_s < bounded_timestamp_s < segment.end_time_s):
            continue
        if segment.duration_s <= 0.0:
            continue
        elapsed_s = bounded_timestamp_s - segment.start_time_s
        profile = _segment_profile(
            distance=segment.distance,
            duration_s=segment.duration_s,
            speed_limit=segment.nominal_speed,
        )
        traversed_distance = sample_profile_distance(profile, elapsed_s)
        progress = min(
            1.0,
            max(0.0, traversed_distance / segment.distance if segment.distance > 0.0 else 1.0),
        )
        speed = sample_profile_speed(profile, elapsed_s)
        path_length = _polyline_length(segment.path_points)
        distance_along_path = (
            path_length * progress if path_length > 0.0 else segment.distance * progress
        )
        position = _sample_path_position(segment.path_points, distance_along_path)
        heading_rad = _heading_along_path(
            segment.path_points,
            distance_along_path=distance_along_path,
        )
        vehicles[segment.vehicle_id] = InterpolatedVehicleState(
            vehicle_id=segment.vehicle_id,
            node_id=segment.start_node_id,
            position=position,
            operational_state="moving",
            heading_rad=heading_rad,
            speed=speed,
            active_edge_id=segment.edge_id,
            start_node_id=segment.start_node_id,
            end_node_id=segment.end_node_id,
            motion_progress=progress,
            is_interpolated=True,
        )

    return MotionSample(
        timestamp_s=bounded_timestamp_s,
        reference_frame_index=reference_frame.frame_index,
        blocked_edge_ids=reference_frame.blocked_edge_ids,
        vehicles=tuple(sorted(vehicles.values(), key=lambda vehicle: vehicle.vehicle_id)),
    )


def motion_segment_to_dict(segment: VehicleMotionSegment) -> dict[str, Any]:
    """Convert one motion segment into a stable JSON-ready record."""

    return {
        "vehicle_id": segment.vehicle_id,
        "segment_index": segment.segment_index,
        "edge_id": segment.edge_id,
        "start_node_id": segment.start_node_id,
        "end_node_id": segment.end_node_id,
        "start_time_s": segment.start_time_s,
        "end_time_s": segment.end_time_s,
        "duration_s": segment.duration_s,
        "distance": segment.distance,
        "start_position": list(segment.start_position),
        "end_position": list(segment.end_position),
        "path_points": [list(point) for point in segment.path_points],
        "heading_rad": segment.heading_rad,
        "nominal_speed": segment.nominal_speed,
        "peak_speed": segment.peak_speed,
        "acceleration_mps2": segment.acceleration_mps2,
        "deceleration_mps2": segment.deceleration_mps2,
        "profile_kind": segment.profile_kind,
    }


def interpolated_vehicle_state_to_dict(
    vehicle: InterpolatedVehicleState,
) -> dict[str, Any]:
    """Convert one sampled vehicle state into a stable JSON-ready record."""

    return {
        "vehicle_id": vehicle.vehicle_id,
        "node_id": vehicle.node_id,
        "position": list(vehicle.position),
        "operational_state": vehicle.operational_state,
        "heading_rad": vehicle.heading_rad,
        "speed": vehicle.speed,
        "active_edge_id": vehicle.active_edge_id,
        "start_node_id": vehicle.start_node_id,
        "end_node_id": vehicle.end_node_id,
        "motion_progress": vehicle.motion_progress,
        "is_interpolated": vehicle.is_interpolated,
    }


def motion_sample_to_dict(sample: MotionSample) -> dict[str, Any]:
    """Convert one continuous motion sample into a stable JSON-ready record."""

    return {
        "timestamp_s": sample.timestamp_s,
        "reference_frame_index": sample.reference_frame_index,
        "blocked_edge_ids": list(sample.blocked_edge_ids),
        "vehicles": [
            interpolated_vehicle_state_to_dict(vehicle) for vehicle in sample.vehicles
        ],
    }


def _find_matching_arrival_frame(
    *,
    state: VisualizationState,
    start_index: int,
    vehicle_id: int,
    end_node_id: int,
):
    for frame in state.frames[start_index:]:
        event = frame.trigger.trace_event
        if (
            frame.trigger.source == "trace"
            and event is not None
            and event.get("event_type") == "node_arrival"
            and event.get("vehicle_id") is not None
            and event.get("node_id") is not None
            and int(event["vehicle_id"]) == vehicle_id
            and int(event["node_id"]) == end_node_id
        ):
            return frame
    raise ValueError(
        "could not resolve node_arrival frame for motion segment "
        f"vehicle_id={vehicle_id} end_node_id={end_node_id}"
    )


def _reference_frame_for_time(
    state: VisualizationState,
    timestamp_s: float,
):
    reference_frame = state.frames[0]
    for frame in state.frames:
        if frame.timestamp_s > timestamp_s:
            break
        reference_frame = frame
    return reference_frame


def _node_position(map_surface: MapSurface, node_id: int) -> Position:
    for node in map_surface.nodes:
        if node.node_id == node_id:
            return node.position
    raise ValueError(f"unknown node_id in map_surface: {node_id}")


def _distance(start: Position, end: Position) -> float:
    return math.dist(start, end)


def _heading_rad(start: Position, end: Position) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return math.atan2(dy, dx)


def _resolve_segment_path_points(
    *,
    render_geometry: RenderGeometrySurface | None,
    edge_id: int,
    start_position: Position,
    end_position: Position,
) -> tuple[Position, ...]:
    if render_geometry is None:
        return (start_position, end_position)

    road = _road_for_edge(render_geometry.roads, edge_id)
    if road is None:
        return (start_position, end_position)

    lane = _lane_for_road_segment(render_geometry.lanes, road, start_position, end_position)
    candidate_points = lane.centerline if lane is not None else road.centerline
    if _distance(candidate_points[0], start_position) + _distance(
        candidate_points[-1], end_position
    ) <= _distance(candidate_points[0], end_position) + _distance(
        candidate_points[-1], start_position
    ):
        return candidate_points
    return tuple(reversed(candidate_points))


def _road_for_edge(
    roads: tuple[RoadGeometrySurface, ...],
    edge_id: int,
) -> RoadGeometrySurface | None:
    for road in roads:
        if edge_id in road.edge_ids:
            return road
    return None


def _lane_for_road_segment(
    lanes: tuple[LaneGeometrySurface, ...],
    road: RoadGeometrySurface,
    start_position: Position,
    end_position: Position,
) -> LaneGeometrySurface | None:
    candidates = [lane for lane in lanes if lane.road_id == road.road_id]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda lane: min(
            _distance(lane.centerline[0], start_position)
            + _distance(lane.centerline[-1], end_position),
            _distance(lane.centerline[0], end_position)
            + _distance(lane.centerline[-1], start_position),
        ),
    )


def _polyline_length(points: tuple[Position, ...]) -> float:
    return sum(_distance(start, end) for start, end in zip(points, points[1:]))


def _sample_path_position(
    points: tuple[Position, ...],
    distance_along_path: float,
) -> Position:
    if len(points) < 2:
        return points[0]
    remaining = min(max(distance_along_path, 0.0), _polyline_length(points))
    for start, end in zip(points, points[1:]):
        segment_length = _distance(start, end)
        if segment_length <= 0.0:
            continue
        if remaining <= segment_length:
            progress = remaining / segment_length
            return (
                start[0] + (end[0] - start[0]) * progress,
                start[1] + (end[1] - start[1]) * progress,
                start[2] + (end[2] - start[2]) * progress,
            )
        remaining -= segment_length
    return points[-1]


def _heading_along_path(
    points: tuple[Position, ...],
    *,
    distance_along_path: float,
) -> float:
    if len(points) < 2:
        return 0.0
    bounded_distance = min(max(distance_along_path, 0.0), _polyline_length(points))
    remaining = bounded_distance
    for start, end in zip(points, points[1:]):
        segment_length = _distance(start, end)
        if segment_length <= 0.0:
            continue
        if remaining <= segment_length:
            return _heading_rad(start, end)
        remaining -= segment_length
    return _heading_rad(points[-2], points[-1])


def _segment_profile(
    *,
    distance: float,
    duration_s: float,
    speed_limit: float,
) -> KinematicTraversalProfile:
    if duration_s <= 0.0:
        return build_kinematic_profile(
            distance_m=distance,
            speed_limit_mps=max(speed_limit, 0.001),
            vehicle_max_speed_mps=max(speed_limit, 0.001),
            duration_s=0.0,
        )
    return build_kinematic_profile(
        distance_m=distance,
        speed_limit_mps=max(speed_limit, 0.001),
        vehicle_max_speed_mps=max(speed_limit, 0.001),
        duration_s=duration_s,
    )


__all__ = [
    "InterpolatedVehicleState",
    "MotionSample",
    "VehicleMotionSegment",
    "build_vehicle_motion_segments",
    "interpolated_vehicle_state_to_dict",
    "motion_sample_to_dict",
    "motion_segment_to_dict",
    "sample_motion",
]
