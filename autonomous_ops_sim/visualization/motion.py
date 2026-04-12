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
from autonomous_ops_sim.vehicles.presentation import (
    VehiclePresentationSurface,
    build_vehicle_presentation_surface,
)
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
    body_length_m: float
    body_width_m: float
    spacing_envelope_m: float
    heading_rad: float
    nominal_speed: float
    peak_speed: float
    acceleration_mps2: float
    deceleration_mps2: float
    profile_kind: str
    road_id: str | None = None
    lane_id: str | None = None
    lane_index: int | None = None
    lane_role: str | None = None
    lane_directionality: str | None = None
    lane_selection_reason: str | None = None


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


@dataclass(frozen=True)
class _SampledVehicleState:
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
    distance_along_path: float
    spacing_envelope_m: float
    path_points: tuple[Position, ...]


@dataclass(frozen=True)
class _LaneUsage:
    lane_id: str
    start_time_s: float
    end_time_s: float


def build_vehicle_motion_segments(
    state: VisualizationState,
    *,
    render_geometry: RenderGeometrySurface | None = None,
    vehicle_presentations: tuple[VehiclePresentationSurface, ...] | None = None,
) -> tuple[VehicleMotionSegment, ...]:
    """Derive edge motion segments from authoritative replay frames."""

    edge_lookup = {edge.edge_id: edge for edge in state.map_surface.edges}
    segments: list[VehicleMotionSegment] = []
    segment_count_by_vehicle: dict[int, int] = {}
    lane_usage_by_road_id: dict[str, list[_LaneUsage]] = {}

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
        if arrival_frame is None:
            arrival_frame = state.frames[-1]
            end_vehicle_state = _vehicle_state_for_frame(
                frame=arrival_frame,
                vehicle_id=vehicle_id,
            )
            end_position = end_vehicle_state.position
            end_node_id = end_vehicle_state.node_id
        else:
            end_position = _node_position(state.map_surface, end_node_id)
        duration_s = max(0.0, arrival_frame.timestamp_s - frame.timestamp_s)
        edge = edge_lookup.get(edge_id)
        distance = edge.distance if edge is not None else _distance(start_position, end_position)
        road = _road_for_edge(render_geometry.roads if render_geometry else (), edge_id)
        vehicle_presentation = _vehicle_presentation_for_segment(
            vehicle_presentations=vehicle_presentations,
            vehicle_id=vehicle_id,
        )
        lane, path_points, lane_selection_reason = _resolve_segment_path_points(
            render_geometry=render_geometry,
            road=road,
            edge_id=edge_id,
            start_position=start_position,
            end_position=end_position,
            vehicle_presentation=vehicle_presentation,
            start_time_s=frame.timestamp_s,
            end_time_s=arrival_frame.timestamp_s,
            lane_usage_by_road_id=lane_usage_by_road_id,
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
        profile_surface = vehicle_presentation
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
                body_length_m=profile_surface.body_length_m,
                body_width_m=profile_surface.body_width_m,
                spacing_envelope_m=_spacing_envelope_m(
                    body_length_m=profile_surface.body_length_m,
                    body_width_m=profile_surface.body_width_m,
                ),
                heading_rad=heading_rad,
                nominal_speed=nominal_speed,
                peak_speed=profile.peak_speed_mps,
                acceleration_mps2=profile.acceleration_mps2,
                deceleration_mps2=profile.deceleration_mps2,
                profile_kind=profile.profile_kind,
                road_id=road.road_id if road is not None else None,
                lane_id=lane.lane_id if lane is not None else None,
                lane_index=lane.lane_index if lane is not None else None,
                lane_role=lane.lane_role if lane is not None else None,
                lane_directionality=lane.directionality if lane is not None else None,
                lane_selection_reason=lane_selection_reason,
            )
        )
        if road is not None and lane is not None:
            lane_usage_by_road_id.setdefault(road.road_id, []).append(
                _LaneUsage(
                    lane_id=lane.lane_id,
                    start_time_s=frame.timestamp_s,
                    end_time_s=arrival_frame.timestamp_s,
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

    sampled_states = _sample_active_vehicle_states(
        motion_segments=motion_segments,
        timestamp_s=bounded_timestamp_s,
    )
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

    for sampled in sampled_states:
        vehicles[sampled.vehicle_id] = InterpolatedVehicleState(
            vehicle_id=sampled.vehicle_id,
            node_id=sampled.node_id,
            position=sampled.position,
            operational_state=sampled.operational_state,
            heading_rad=sampled.heading_rad,
            speed=sampled.speed,
            active_edge_id=sampled.active_edge_id,
            start_node_id=sampled.start_node_id,
            end_node_id=sampled.end_node_id,
            motion_progress=sampled.motion_progress,
            is_interpolated=sampled.is_interpolated,
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
        "road_id": segment.road_id,
        "start_node_id": segment.start_node_id,
        "end_node_id": segment.end_node_id,
        "start_time_s": segment.start_time_s,
        "end_time_s": segment.end_time_s,
        "duration_s": segment.duration_s,
        "distance": segment.distance,
        "start_position": list(segment.start_position),
        "end_position": list(segment.end_position),
        "path_points": [list(point) for point in segment.path_points],
        "body_length_m": segment.body_length_m,
        "body_width_m": segment.body_width_m,
        "spacing_envelope_m": segment.spacing_envelope_m,
        "heading_rad": segment.heading_rad,
        "nominal_speed": segment.nominal_speed,
        "peak_speed": segment.peak_speed,
        "acceleration_mps2": segment.acceleration_mps2,
        "deceleration_mps2": segment.deceleration_mps2,
        "profile_kind": segment.profile_kind,
        "lane_id": segment.lane_id,
        "lane_index": segment.lane_index,
        "lane_role": segment.lane_role,
        "lane_directionality": segment.lane_directionality,
        "lane_selection_reason": segment.lane_selection_reason,
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
    return None


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


def _vehicle_state_for_frame(
    *,
    frame,
    vehicle_id: int,
):
    for vehicle in frame.vehicles:
        if vehicle.vehicle_id == vehicle_id:
            return vehicle
    raise ValueError(f"unknown vehicle_id in visualization frame: {vehicle_id}")


def _distance(start: Position, end: Position) -> float:
    return math.dist(start, end)


def _heading_rad(start: Position, end: Position) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return math.atan2(dy, dx)


def _vehicle_presentation_for_segment(
    *,
    vehicle_presentations: tuple[VehiclePresentationSurface, ...] | None,
    vehicle_id: int,
) -> VehiclePresentationSurface:
    if vehicle_presentations is None:
        return build_vehicle_presentation_surface(
            vehicle_id=vehicle_id,
            vehicle_type=None,
        )
    for presentation in vehicle_presentations:
        if presentation.vehicle_id == vehicle_id:
            return presentation
    return build_vehicle_presentation_surface(vehicle_id=vehicle_id, vehicle_type=None)


def _spacing_envelope_m(*, body_length_m: float, body_width_m: float) -> float:
    return max(body_length_m * 1.35, body_width_m * 2.2, 0.9)


def _sample_active_vehicle_states(
    *,
    motion_segments: tuple[VehicleMotionSegment, ...],
    timestamp_s: float,
) -> tuple[_SampledVehicleState, ...]:
    active_entries: list[_SampledVehicleState] = []

    for segment in motion_segments:
        if not (segment.start_time_s < timestamp_s < segment.end_time_s):
            continue
        if segment.duration_s <= 0.0:
            continue
        elapsed_s = timestamp_s - segment.start_time_s
        profile = _segment_profile(
            distance=segment.distance,
            duration_s=segment.duration_s,
            speed_limit=segment.nominal_speed,
        )
        traversed_distance = sample_profile_distance(profile, elapsed_s)
        progress = min(
            1.0,
            max(
                0.0,
                traversed_distance / segment.distance if segment.distance > 0.0 else 1.0,
            ),
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
        active_entries.append(
            _SampledVehicleState(
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
                distance_along_path=distance_along_path,
                spacing_envelope_m=segment.spacing_envelope_m,
                path_points=segment.path_points,
            )
        )

    if len(active_entries) < 2:
        return tuple(active_entries)

    adjusted_entries: list[_SampledVehicleState] = []
    for edge_id in sorted({entry.active_edge_id for entry in active_entries if entry.active_edge_id is not None}):
        edge_entries = [
            entry for entry in active_entries if entry.active_edge_id == edge_id
        ]
        edge_entries.sort(key=lambda entry: (-entry.distance_along_path, entry.vehicle_id))
        leader_distance: float | None = None
        leader_envelope = 0.0
        for entry in edge_entries:
            final_distance = entry.distance_along_path
            final_speed = entry.speed
            final_state = entry.operational_state
            if leader_distance is not None:
                safe_distance = max(leader_envelope, entry.spacing_envelope_m)
                if final_distance > leader_distance - safe_distance:
                    final_distance = max(0.0, leader_distance - safe_distance)
                    final_speed = 0.0
                    final_state = "waiting"
            position = _sample_path_position(entry.path_points, final_distance)
            heading_rad = _heading_along_path(
                entry.path_points,
                distance_along_path=final_distance,
            )
            adjusted_entries.append(
                _SampledVehicleState(
                    vehicle_id=entry.vehicle_id,
                    node_id=entry.node_id,
                    position=position,
                    operational_state=final_state,
                    heading_rad=heading_rad,
                    speed=final_speed,
                    active_edge_id=entry.active_edge_id,
                    start_node_id=entry.start_node_id,
                    end_node_id=entry.end_node_id,
                    motion_progress=(
                        final_distance / _polyline_length(entry.path_points)
                        if _polyline_length(entry.path_points) > 0.0
                        else entry.motion_progress
                    ),
                    is_interpolated=entry.is_interpolated,
                    distance_along_path=final_distance,
                    spacing_envelope_m=entry.spacing_envelope_m,
                    path_points=entry.path_points,
                )
            )
            leader_distance = final_distance
            leader_envelope = entry.spacing_envelope_m

    adjusted_entries.extend(
        entry
        for entry in active_entries
        if entry.active_edge_id is None
    )
    return tuple(sorted(adjusted_entries, key=lambda entry: entry.vehicle_id))


def _resolve_segment_path_points(
    *,
    render_geometry: RenderGeometrySurface | None,
    road: RoadGeometrySurface | None,
    edge_id: int,
    start_position: Position,
    end_position: Position,
    vehicle_presentation: VehiclePresentationSurface,
    start_time_s: float,
    end_time_s: float,
    lane_usage_by_road_id: dict[str, list[_LaneUsage]],
) -> tuple[LaneGeometrySurface | None, tuple[Position, ...], str]:
    if render_geometry is None:
        return None, (start_position, end_position), "road geometry unavailable"

    if road is None:
        return None, (start_position, end_position), "road geometry unavailable"

    lane, candidate_points, reason = _select_lane_for_road_segment(
        render_geometry=render_geometry,
        road=road,
        start_position=start_position,
        end_position=end_position,
        vehicle_presentation=vehicle_presentation,
        start_time_s=start_time_s,
        end_time_s=end_time_s,
        lane_usage_by_road_id=lane_usage_by_road_id,
    )
    if lane is not None:
        return lane, candidate_points, reason
    return None, candidate_points, reason


def _road_for_edge(
    roads: tuple[RoadGeometrySurface, ...],
    edge_id: int,
) -> RoadGeometrySurface | None:
    for road in roads:
        if edge_id in road.edge_ids:
            return road
    return None


def _select_lane_for_road_segment(
    *,
    render_geometry: RenderGeometrySurface,
    road: RoadGeometrySurface,
    start_position: Position,
    end_position: Position,
    vehicle_presentation: VehiclePresentationSurface,
    start_time_s: float,
    end_time_s: float,
    lane_usage_by_road_id: dict[str, list[_LaneUsage]],
) -> tuple[LaneGeometrySurface | None, tuple[Position, ...], str]:
    candidates = [lane for lane in render_geometry.lanes if lane.road_id == road.road_id]
    if not candidates:
        return None, road.centerline, "road centerline"

    travel_direction = _travel_direction_for_segment(
        road=road,
        start_position=start_position,
        end_position=end_position,
    )
    directional_candidates = [
        lane for lane in candidates if lane.directionality == travel_direction
    ]
    if directional_candidates:
        candidates = directional_candidates

    scored_candidates: list[
        tuple[float, str, LaneGeometrySurface, tuple[Position, ...], str]
    ] = []
    for lane in sorted(candidates, key=lambda lane: lane.lane_id):
        candidate_points, alignment_reason = _lane_path_for_travel(
            lane=lane,
            start_position=start_position,
            end_position=end_position,
        )
        score = _distance(candidate_points[0], start_position) + _distance(
            candidate_points[-1], end_position
        )
        score += _lane_role_bias(
            lane=lane,
            road=road,
            vehicle_presentation=vehicle_presentation,
        )
        score += _lane_occupancy_penalty(
            lane_id=lane.lane_id,
            lane_usage_by_road_id=lane_usage_by_road_id,
            road_id=road.road_id,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
        )
        scored_candidates.append(
            (
                score,
                lane.lane_id,
                lane,
                candidate_points,
                alignment_reason,
            )
        )

    if not scored_candidates:
        return None, road.centerline, "road centerline"

    score, _, lane, candidate_points, alignment_reason = min(
        scored_candidates,
        key=lambda candidate: (candidate[0], candidate[1]),
    )
    selection_reason = (
        f"{road.road_class} · {travel_direction} · {lane.lane_role} · {alignment_reason}"
    )
    if score > 0.0:
        selection_reason = f"{selection_reason} · score={score:.2f}"
    return lane, candidate_points, selection_reason


def _lane_path_for_travel(
    *,
    lane: LaneGeometrySurface,
    start_position: Position,
    end_position: Position,
) -> tuple[tuple[Position, ...], str]:
    forward_points = lane.centerline
    reverse_points = tuple(reversed(lane.centerline))
    forward_score = _distance(forward_points[0], start_position) + _distance(
        forward_points[-1], end_position
    )
    reverse_score = _distance(reverse_points[0], start_position) + _distance(
        reverse_points[-1], end_position
    )
    if forward_score <= reverse_score:
        return forward_points, "forward"
    return reverse_points, "reverse"


def _lane_role_bias(
    *,
    lane: LaneGeometrySurface,
    road: RoadGeometrySurface,
    vehicle_presentation: VehiclePresentationSurface,
) -> float:
    lane_role = lane.lane_role
    if lane_role in {"merge", "loading_approach"}:
        return -0.35
    if lane_role == "passing":
        if vehicle_presentation.presentation_key == "haul_truck":
            return 0.25
        return -0.25 if road.lane_count > 1 else 0.1
    if lane_role == "keep_lane":
        if vehicle_presentation.presentation_key == "haul_truck":
            return -0.2
        return 0.1
    if road.lane_count > 1:
        if vehicle_presentation.presentation_key == "haul_truck":
            return 0.06 * (road.lane_count - lane.lane_index - 1)
        if vehicle_presentation.presentation_key == "car":
            return 0.06 * lane.lane_index
        if vehicle_presentation.presentation_key == "forklift":
            return 0.02 * abs(lane.lane_index - min(1, road.lane_count - 1))
    return 0.0


def _travel_direction_for_segment(
    *,
    road: RoadGeometrySurface,
    start_position: Position,
    end_position: Position,
) -> str:
    if road.directionality != "two_way" or len(road.centerline) < 2:
        return "forward"
    forward_score = _distance(road.centerline[0], start_position) + _distance(
        road.centerline[-1], end_position
    )
    reverse_score = _distance(road.centerline[-1], start_position) + _distance(
        road.centerline[0], end_position
    )
    return "forward" if forward_score <= reverse_score else "reverse"


def _lane_occupancy_penalty(
    *,
    lane_id: str,
    lane_usage_by_road_id: dict[str, list[_LaneUsage]],
    road_id: str,
    start_time_s: float,
    end_time_s: float,
) -> float:
    usage_penalty = 0.0
    for usage in lane_usage_by_road_id.get(road_id, []):
        if not _windows_overlap(
            start_a=start_time_s,
            end_a=end_time_s,
            start_b=usage.start_time_s,
            end_b=usage.end_time_s,
        ):
            continue
        if usage.lane_id == lane_id:
            usage_penalty += 0.8
        else:
            usage_penalty += 0.15
    return usage_penalty


def _windows_overlap(
    *,
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
) -> bool:
    return start_a < end_b and start_b < end_a


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
