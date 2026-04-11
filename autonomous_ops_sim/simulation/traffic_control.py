from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


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


def build_traffic_control_points(
    render_geometry: Any,
) -> tuple[TrafficControlPoint, ...]:
    """Build stable control points from either raw or projected render geometry."""

    roads = tuple(_geometry_records(render_geometry, "roads"))
    intersections = tuple(_geometry_records(render_geometry, "intersections"))
    lanes = tuple(_geometry_records(render_geometry, "lanes"))
    stop_lines = tuple(_geometry_records(render_geometry, "stop_lines"))
    merge_zones = tuple(_geometry_records(render_geometry, "merge_zones"))

    controls: list[TrafficControlPoint] = []
    for intersection in intersections:
        intersection_id = _record_value(intersection, "intersection_id", "id")
        node_id = _required_int(intersection, "node_id")
        polygon = _geometry_polygon(intersection)
        if not polygon:
            continue

        min_x = min(point[0] for point in polygon)
        max_x = max(point[0] for point in polygon)
        min_y = min(point[1] for point in polygon)
        max_y = max(point[1] for point in polygon)
        connected_road_ids = tuple(
            sorted(
                _record_value(road, "road_id", "id")
                for road in roads
                if _road_touches_intersection_bounds(
                    road,
                    min_x=min_x,
                    max_x=max_x,
                    min_y=min_y,
                    max_y=max_y,
                )
            )
        )
        if len(connected_road_ids) < 2:
            continue

        lane_ids_for_roads = {
            _record_value(lane, "lane_id", "id")
            for lane in lanes
            if _record_value(lane, "road_id") in connected_road_ids
        }
        stop_line_ids = tuple(
            sorted(
                _record_value(stop_line, "stop_line_id", "id")
                for stop_line in stop_lines
                if _record_value(stop_line, "lane_id") in lane_ids_for_roads
            )
        )
        protected_conflict_zone_ids = tuple(
            sorted(
                _record_value(merge_zone, "merge_zone_id", "id")
                for merge_zone in merge_zones
                if any(
                    lane_id in _record_lane_ids(merge_zone)
                    for lane_id in lane_ids_for_roads
                )
            )
        )
        if len(connected_road_ids) >= 4 or stop_line_ids:
            control_type = "signalized"
        elif len(connected_road_ids) >= 2:
            control_type = "yield"
        else:
            control_type = "uncontrolled"
        controls.append(
            TrafficControlPoint(
                control_id=f"control-{intersection_id}",
                node_id=node_id,
                control_type=control_type,
                controlled_road_ids=connected_road_ids,
                stop_line_ids=stop_line_ids,
                protected_conflict_zone_ids=protected_conflict_zone_ids,
                signal_ready=bool(stop_line_ids or protected_conflict_zone_ids),
            )
        )
    return tuple(controls)


def traffic_control_points_by_node_id(
    control_points: Iterable[TrafficControlPoint],
) -> dict[int, TrafficControlPoint]:
    """Index rendered control points by node id in deterministic order."""

    return {control.node_id: control for control in control_points}


def _geometry_records(render_geometry: Any, key: str) -> tuple[Any, ...]:
    if render_geometry is None:
        return ()
    if isinstance(render_geometry, dict):
        value = render_geometry.get(key, ())
    else:
        value = getattr(render_geometry, key, ())
    if value is None:
        return ()
    return tuple(value)


def _record_value(record: Any, *keys: str) -> Any:
    for key in keys:
        if isinstance(record, dict) and key in record:
            return record[key]
        if hasattr(record, key):
            return getattr(record, key)
    if len(keys) == 1:
        raise KeyError(keys[0])
    raise KeyError(", ".join(keys))


def _required_int(record: Any, key: str) -> int:
    value = _record_value(record, key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an int")
    return value


def _geometry_polygon(record: Any) -> tuple[tuple[float, float, float], ...]:
    polygon = _record_value(record, "polygon")
    return tuple(
        (float(point[0]), float(point[1]), float(point[2]))
        for point in polygon
    )


def _record_lane_ids(record: Any) -> tuple[str, ...]:
    lane_ids = _record_value(record, "lane_ids")
    return tuple(str(lane_id) for lane_id in lane_ids)


def _road_touches_intersection_bounds(
    road: Any,
    *,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> bool:
    centerline = _record_value(road, "centerline")
    if not centerline:
        return False
    return any(
        min_x <= point[0] <= max_x and min_y <= point[1] <= max_y
        for point in centerline
    )
