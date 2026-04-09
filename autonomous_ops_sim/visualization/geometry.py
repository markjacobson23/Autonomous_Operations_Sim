from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.vehicles.vehicle import Position
from autonomous_ops_sim.world.model import (
    WorldAssetLayerSurface,
    WorldFeatureSurface,
    WorldModelSurface,
    build_world_model_surface,
    world_model_surface_to_dict,
)


@dataclass(frozen=True)
class RoadGeometrySurface:
    """Rendered road segment layered on top of routing-edge semantics."""

    road_id: str
    edge_ids: tuple[int, ...]
    centerline: tuple[Position, ...]
    road_class: str
    directionality: str
    lane_count: int
    width_m: float


@dataclass(frozen=True)
class IntersectionGeometrySurface:
    """Rendered intersection footprint for richer viewer semantics."""

    intersection_id: str
    node_id: int
    polygon: tuple[Position, ...]
    intersection_type: str


@dataclass(frozen=True)
class AreaGeometrySurface:
    """Rendered non-road contextual area such as depots or buildings."""

    area_id: str
    kind: str
    polygon: tuple[Position, ...]
    label: str | None = None


@dataclass(frozen=True)
class LaneGeometrySurface:
    """Lane-level centerline layered on top of one rendered road."""

    lane_id: str
    road_id: str
    lane_index: int
    directionality: str
    lane_role: str
    centerline: tuple[Position, ...]
    width_m: float


@dataclass(frozen=True)
class TurnConnectorSurface:
    """Turn/transition connector between two explicit lanes."""

    connector_id: str
    from_lane_id: str
    to_lane_id: str
    connector_type: str
    centerline: tuple[Position, ...]


@dataclass(frozen=True)
class StopLineSurface:
    """Stop-line marker near a lane terminal."""

    stop_line_id: str
    lane_id: str
    control_kind: str
    segment: tuple[Position, Position]


@dataclass(frozen=True)
class MergeZoneSurface:
    """Merge/conflict zone footprint tied to one or more lanes."""

    merge_zone_id: str
    lane_ids: tuple[str, ...]
    kind: str
    polygon: tuple[Position, ...]


@dataclass(frozen=True)
class RenderGeometrySurface:
    """Static rendered geometry layer separate from routing truth."""

    roads: tuple[RoadGeometrySurface, ...]
    intersections: tuple[IntersectionGeometrySurface, ...]
    areas: tuple[AreaGeometrySurface, ...]
    lanes: tuple[LaneGeometrySurface, ...]
    turn_connectors: tuple[TurnConnectorSurface, ...]
    stop_lines: tuple[StopLineSurface, ...]
    merge_zones: tuple[MergeZoneSurface, ...]
    world_model: WorldModelSurface


def build_render_geometry_surface(simulation_map: Map) -> RenderGeometrySurface:
    """Build rendered geometry from optional map metadata plus sensible defaults."""

    metadata = simulation_map.render_geometry
    if metadata:
        roads = _build_roads_from_metadata(simulation_map, metadata)
        intersections = _build_intersections_from_metadata(simulation_map, metadata)
        areas = _build_areas_from_metadata(metadata)
        lanes = _build_lanes_from_metadata(metadata, roads=roads)
        return RenderGeometrySurface(
            roads=roads,
            intersections=intersections,
            areas=areas,
            lanes=lanes,
            turn_connectors=_build_turn_connectors_from_metadata(
                metadata,
                roads=roads,
                lanes=lanes,
            ),
            stop_lines=_build_stop_lines_from_metadata(metadata, lanes=lanes),
            merge_zones=_build_merge_zones_from_metadata(
                metadata,
                roads=roads,
                lanes=lanes,
            ),
            world_model=build_world_model_surface(simulation_map),
        )

    roads = _build_default_roads(simulation_map)
    intersections = _build_default_intersections(simulation_map)
    areas = _build_default_areas(simulation_map)
    lanes = _build_default_lanes(roads)
    return RenderGeometrySurface(
        roads=roads,
        intersections=intersections,
        areas=areas,
        lanes=lanes,
        turn_connectors=_build_default_turn_connectors(roads=roads, lanes=lanes),
        stop_lines=_build_default_stop_lines(lanes=lanes),
        merge_zones=_build_default_merge_zones(roads=roads, lanes=lanes),
        world_model=build_world_model_surface(simulation_map),
    )


def render_geometry_surface_to_dict(
    surface: RenderGeometrySurface,
) -> dict[str, Any]:
    """Convert rendered geometry into a stable JSON-ready record."""

    return {
        "roads": [
            {
                "road_id": road.road_id,
                "edge_ids": list(road.edge_ids),
                "centerline": [list(point) for point in road.centerline],
                "road_class": road.road_class,
                "directionality": road.directionality,
                "lane_count": road.lane_count,
                "width_m": road.width_m,
            }
            for road in surface.roads
        ],
        "intersections": [
            {
                "intersection_id": intersection.intersection_id,
                "node_id": intersection.node_id,
                "polygon": [list(point) for point in intersection.polygon],
                "intersection_type": intersection.intersection_type,
            }
            for intersection in surface.intersections
        ],
        "areas": [
            {
                "area_id": area.area_id,
                "kind": area.kind,
                "polygon": [list(point) for point in area.polygon],
                "label": area.label,
            }
            for area in surface.areas
        ],
        "lanes": [
            {
                "lane_id": lane.lane_id,
                "road_id": lane.road_id,
                "lane_index": lane.lane_index,
                "directionality": lane.directionality,
                "lane_role": lane.lane_role,
                "centerline": [list(point) for point in lane.centerline],
                "width_m": lane.width_m,
            }
            for lane in surface.lanes
        ],
        "turn_connectors": [
            {
                "connector_id": connector.connector_id,
                "from_lane_id": connector.from_lane_id,
                "to_lane_id": connector.to_lane_id,
                "connector_type": connector.connector_type,
                "centerline": [list(point) for point in connector.centerline],
            }
            for connector in surface.turn_connectors
        ],
        "stop_lines": [
            {
                "stop_line_id": stop_line.stop_line_id,
                "lane_id": stop_line.lane_id,
                "control_kind": stop_line.control_kind,
                "segment": [list(point) for point in stop_line.segment],
            }
            for stop_line in surface.stop_lines
        ],
        "merge_zones": [
            {
                "merge_zone_id": merge_zone.merge_zone_id,
                "lane_ids": list(merge_zone.lane_ids),
                "kind": merge_zone.kind,
                "polygon": [list(point) for point in merge_zone.polygon],
            }
            for merge_zone in surface.merge_zones
        ],
        "world_model": world_model_surface_to_dict(surface.world_model),
    }


def _build_roads_from_metadata(
    simulation_map: Map,
    metadata: dict[str, object],
) -> tuple[RoadGeometrySurface, ...]:
    roads = metadata.get("roads", [])
    assert isinstance(roads, list)
    return tuple(
        RoadGeometrySurface(
            road_id=str(road["id"]),
            edge_ids=tuple(int(edge_id) for edge_id in road["edge_ids"]),
            centerline=tuple(
                _position(
                    point
                )
                for point in road.get(
                    "centerline",
                    _default_centerline_for_road(simulation_map, road),
                )
            ),
            road_class=str(road.get("road_class", "connector")),
            directionality=str(road.get("directionality", "one_way")),
            lane_count=int(road.get("lane_count", 1)),
            width_m=float(road.get("width_m", 1.0)),
        )
        for road in roads
    )


def _build_intersections_from_metadata(
    simulation_map: Map,
    metadata: dict[str, object],
) -> tuple[IntersectionGeometrySurface, ...]:
    intersections = metadata.get("intersections", [])
    assert isinstance(intersections, list)
    return tuple(
        IntersectionGeometrySurface(
            intersection_id=str(intersection["id"]),
            node_id=int(intersection["node_id"]),
            polygon=tuple(_position(point) for point in intersection["polygon"]),
            intersection_type=str(intersection.get("intersection_type", "junction")),
        )
        for intersection in intersections
    )


def _build_areas_from_metadata(
    metadata: dict[str, object],
) -> tuple[AreaGeometrySurface, ...]:
    areas = metadata.get("areas", [])
    assert isinstance(areas, list)
    return tuple(
        AreaGeometrySurface(
            area_id=str(area["id"]),
            kind=str(area["kind"]),
            polygon=tuple(_position(point) for point in area["polygon"]),
            label=str(area["label"]) if area.get("label") is not None else None,
        )
        for area in areas
    )


def _build_lanes_from_metadata(
    metadata: dict[str, object],
    *,
    roads: tuple[RoadGeometrySurface, ...],
) -> tuple[LaneGeometrySurface, ...]:
    lanes = metadata.get("lanes")
    if isinstance(lanes, list):
        return tuple(
            LaneGeometrySurface(
                lane_id=str(lane["id"]),
                road_id=str(lane["road_id"]),
                lane_index=int(lane.get("lane_index", 0)),
                directionality=str(lane.get("directionality", "forward")),
                lane_role=str(lane.get("lane_role", "travel")),
                centerline=tuple(_position(point) for point in lane["centerline"]),
                width_m=float(lane.get("width_m", 0.5)),
            )
            for lane in lanes
        )
    return _build_default_lanes(roads)


def _build_turn_connectors_from_metadata(
    metadata: dict[str, object],
    *,
    roads: tuple[RoadGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[TurnConnectorSurface, ...]:
    connectors = metadata.get("turn_connectors")
    if isinstance(connectors, list):
        return tuple(
            TurnConnectorSurface(
                connector_id=str(connector["id"]),
                from_lane_id=str(connector["from_lane_id"]),
                to_lane_id=str(connector["to_lane_id"]),
                connector_type=str(connector.get("connector_type", "turn")),
                centerline=tuple(_position(point) for point in connector["centerline"]),
            )
            for connector in connectors
        )
    return _build_default_turn_connectors(roads=roads, lanes=lanes)


def _build_stop_lines_from_metadata(
    metadata: dict[str, object],
    *,
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[StopLineSurface, ...]:
    stop_lines = metadata.get("stop_lines")
    if isinstance(stop_lines, list):
        return tuple(
            StopLineSurface(
                stop_line_id=str(stop_line["id"]),
                lane_id=str(stop_line["lane_id"]),
                control_kind=str(stop_line.get("control_kind", "yield")),
                segment=(
                    _position(stop_line["segment"][0]),
                    _position(stop_line["segment"][1]),
                ),
            )
            for stop_line in stop_lines
        )
    return _build_default_stop_lines(lanes=lanes)


def _build_merge_zones_from_metadata(
    metadata: dict[str, object],
    *,
    roads: tuple[RoadGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[MergeZoneSurface, ...]:
    merge_zones = metadata.get("merge_zones")
    if isinstance(merge_zones, list):
        return tuple(
            MergeZoneSurface(
                merge_zone_id=str(zone["id"]),
                lane_ids=tuple(str(lane_id) for lane_id in zone["lane_ids"]),
                kind=str(zone.get("kind", "merge")),
                polygon=tuple(_position(point) for point in zone["polygon"]),
            )
            for zone in merge_zones
        )
    return _build_default_merge_zones(roads=roads, lanes=lanes)


def _build_default_roads(simulation_map: Map) -> tuple[RoadGeometrySurface, ...]:
    roads: list[RoadGeometrySurface] = []
    seen_pairs: set[tuple[int, int]] = set()
    for edge in sorted(simulation_map.graph.edges.values(), key=lambda edge: edge.id):
        pair = tuple(sorted((edge.start_node.id, edge.end_node.id)))
        normalized_pair = (pair[0], pair[1])
        if normalized_pair in seen_pairs:
            continue
        seen_pairs.add(normalized_pair)
        reverse = simulation_map.get_edge_between(edge.end_node.id, edge.start_node.id)
        directionality = "two_way" if reverse is not None else "one_way"
        edge_ids = (
            tuple(sorted((edge.id, reverse.id))) if reverse is not None else (edge.id,)
        )
        roads.append(
            RoadGeometrySurface(
                road_id=f"road-{normalized_pair[0]}-{normalized_pair[1]}",
                edge_ids=edge_ids,
                centerline=(
                    simulation_map.get_position(edge.start_node.id),
                    simulation_map.get_position(edge.end_node.id),
                ),
                road_class="connector",
                directionality=directionality,
                lane_count=2 if directionality == "two_way" else 1,
                width_m=1.0 if directionality == "one_way" else 1.4,
            )
        )
    return tuple(roads)


def _build_default_lanes(
    roads: tuple[RoadGeometrySurface, ...],
) -> tuple[LaneGeometrySurface, ...]:
    lanes: list[LaneGeometrySurface] = []
    for road in roads:
        lane_total = max(road.lane_count, 1)
        for lane_index in range(lane_total):
            if road.directionality == "two_way" and lane_total > 1:
                directionality = "forward" if lane_index < lane_total / 2 else "reverse"
            else:
                directionality = "forward"
            centered_offset = ((lane_index + 0.5) - (lane_total / 2.0)) * (
                road.width_m / lane_total
            )
            source_points = (
                tuple(reversed(road.centerline))
                if directionality == "reverse"
                else road.centerline
            )
            lanes.append(
                LaneGeometrySurface(
                    lane_id=f"{road.road_id}:lane:{lane_index}",
                    road_id=road.road_id,
                    lane_index=lane_index,
                    directionality=directionality,
                    lane_role=(
                        "loading_approach"
                        if road.road_class in {"ramp", "yard_lane"}
                        else "travel"
                    ),
                    centerline=_offset_polyline(source_points, centered_offset),
                    width_m=max(road.width_m / lane_total, 0.45),
                )
            )
    return tuple(lanes)


def _build_default_turn_connectors(
    *,
    roads: tuple[RoadGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[TurnConnectorSurface, ...]:
    road_lookup = {road.road_id: road for road in roads}
    connectors: list[TurnConnectorSurface] = []
    for incoming in lanes:
        incoming_road = road_lookup.get(incoming.road_id)
        if incoming_road is None:
            continue
        incoming_end = incoming.centerline[-1]
        for outgoing in lanes:
            if incoming.lane_id == outgoing.lane_id:
                continue
            if incoming.road_id == outgoing.road_id:
                continue
            outgoing_end = outgoing.centerline[0]
            if _distance_xy(incoming_end, outgoing_end) > 2.6:
                continue
            connectors.append(
                TurnConnectorSurface(
                    connector_id=f"{incoming.lane_id}->{outgoing.lane_id}",
                    from_lane_id=incoming.lane_id,
                    to_lane_id=outgoing.lane_id,
                    connector_type="turn",
                    centerline=(incoming_end, outgoing_end),
                )
            )
    return tuple(sorted(connectors, key=lambda connector: connector.connector_id))


def _build_default_stop_lines(
    *,
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[StopLineSurface, ...]:
    return tuple(
        StopLineSurface(
            stop_line_id=f"{lane.lane_id}:stop",
            lane_id=lane.lane_id,
            control_kind="stop",
            segment=_build_stop_line_segment(lane.centerline),
        )
        for lane in lanes
    )


def _build_default_merge_zones(
    *,
    roads: tuple[RoadGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
) -> tuple[MergeZoneSurface, ...]:
    lane_ids_by_road: dict[str, list[str]] = {}
    for lane in lanes:
        lane_ids_by_road.setdefault(lane.road_id, []).append(lane.lane_id)

    zones: list[MergeZoneSurface] = []
    for road in roads:
        lane_ids = tuple(sorted(lane_ids_by_road.get(road.road_id, ())))
        if len(lane_ids) < 2:
            continue
        anchor = road.centerline[len(road.centerline) // 2]
        half_width = max(road.width_m * 0.45, 0.45)
        zones.append(
            MergeZoneSurface(
                merge_zone_id=f"{road.road_id}:merge",
                lane_ids=lane_ids,
                kind="merge",
                polygon=(
                    (anchor[0] - half_width, anchor[1] - half_width, anchor[2]),
                    (anchor[0] + half_width, anchor[1] - half_width, anchor[2]),
                    (anchor[0] + half_width, anchor[1] + half_width, anchor[2]),
                    (anchor[0] - half_width, anchor[1] + half_width, anchor[2]),
                ),
            )
        )
    return tuple(zones)


def _build_default_intersections(simulation_map: Map) -> tuple[IntersectionGeometrySurface, ...]:
    intersections: list[IntersectionGeometrySurface] = []
    for node_id in sorted(simulation_map.graph.nodes):
        node = simulation_map.get_node(node_id)
        if (
            len(simulation_map.get_outgoing_edges(node_id)) < 2
            and node.node_type.name != "INTERSECTION"
        ):
            continue
        x, y, z = node.position
        size = 0.35
        intersections.append(
            IntersectionGeometrySurface(
                intersection_id=f"intersection-{node_id}",
                node_id=node_id,
                polygon=(
                    (x - size, y - size, z),
                    (x + size, y - size, z),
                    (x + size, y + size, z),
                    (x - size, y + size, z),
                ),
                intersection_type=node.node_type.name.lower(),
            )
        )
    return tuple(intersections)


def _build_default_areas(simulation_map: Map) -> tuple[AreaGeometrySurface, ...]:
    areas: list[AreaGeometrySurface] = []
    for node_id in sorted(simulation_map.graph.nodes):
        node = simulation_map.get_node(node_id)
        kind = node.node_type.name.lower()
        if kind == "intersection":
            continue
        x, y, z = node.position
        size = 0.55
        areas.append(
            AreaGeometrySurface(
                area_id=f"{kind}-{node_id}",
                kind=kind,
                polygon=(
                    (x - size, y - size, z),
                    (x + size, y - size, z),
                    (x + size, y + size, z),
                    (x - size, y + size, z),
                ),
                label=f"{kind.replace('_', ' ')} {node_id}",
            )
        )
    return tuple(areas)


def _default_centerline_for_road(
    simulation_map: Map,
    road_record: dict[str, object],
) -> list[Position]:
    edge_ids = road_record["edge_ids"]
    assert isinstance(edge_ids, list)
    first_edge = simulation_map.graph.edges[int(edge_ids[0])]
    last_edge = simulation_map.graph.edges[int(edge_ids[-1])]
    return [
        simulation_map.get_position(first_edge.start_node.id),
        simulation_map.get_position(last_edge.end_node.id),
    ]


def _position(value: object) -> Position:
    assert isinstance(value, (list, tuple))
    return (float(value[0]), float(value[1]), float(value[2]))


def _offset_polyline(
    points: tuple[Position, ...],
    offset_m: float,
) -> tuple[Position, ...]:
    if abs(offset_m) < 1e-9 or len(points) < 2:
        return tuple(points)
    offset_points: list[Position] = []
    for index, point in enumerate(points):
        previous_point = points[index - 1] if index > 0 else points[index]
        next_point = points[index + 1] if index < len(points) - 1 else points[index]
        dx = next_point[0] - previous_point[0]
        dy = next_point[1] - previous_point[1]
        length = max((dx * dx + dy * dy) ** 0.5, 1e-9)
        normal_x = -dy / length
        normal_y = dx / length
        offset_points.append(
            (
                point[0] + normal_x * offset_m,
                point[1] + normal_y * offset_m,
                point[2],
            )
        )
    return tuple(offset_points)


def _build_stop_line_segment(
    points: tuple[Position, ...],
) -> tuple[Position, Position]:
    end_point = points[-1]
    previous_point = points[-2] if len(points) > 1 else points[-1]
    dx = end_point[0] - previous_point[0]
    dy = end_point[1] - previous_point[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1e-9)
    normal_x = -dy / length
    normal_y = dx / length
    half_width = 0.22
    return (
        (
            end_point[0] - normal_x * half_width,
            end_point[1] - normal_y * half_width,
            end_point[2],
        ),
        (
            end_point[0] + normal_x * half_width,
            end_point[1] + normal_y * half_width,
            end_point[2],
        ),
    )


def _distance_xy(start: Position, end: Position) -> float:
    return ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5


__all__ = [
    "AreaGeometrySurface",
    "IntersectionGeometrySurface",
    "LaneGeometrySurface",
    "MergeZoneSurface",
    "RenderGeometrySurface",
    "RoadGeometrySurface",
    "StopLineSurface",
    "TurnConnectorSurface",
    "WorldAssetLayerSurface",
    "WorldFeatureSurface",
    "WorldModelSurface",
    "build_render_geometry_surface",
    "render_geometry_surface_to_dict",
]
