from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.vehicles.vehicle import Position
from autonomous_ops_sim.world.model import (
    WorldAssetLayerSurface,
    WorldFeatureGroupSurface,
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
    category: str
    kind: str
    polygon: tuple[Position, ...]
    label: str | None = None
    group_id: str | None = None


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
class SceneBoundsSurface:
    """Axis-aligned scene bounds derived from world and render extents."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    width: float
    height: float


@dataclass(frozen=True)
class SceneExtentSurface:
    """Named extent used to frame a meaningful subset of the scene."""

    extent_id: str
    source: str
    category: str
    label: str
    feature_ids: tuple[str, ...]
    bounds: SceneBoundsSurface


@dataclass(frozen=True)
class SceneFrameSurface:
    """Derived scene framing contract built from simulator-owned truth."""

    frame_id: str
    environment_family: str
    scene_bounds: SceneBoundsSurface
    extents: tuple[SceneExtentSurface, ...]


@dataclass(frozen=True)
class RenderGeometryLayerSurface:
    """Named projection layer bridging world semantics and render-ready geometry."""

    layer_id: str
    source: str
    category: str
    label: str
    feature_ids: tuple[str, ...]


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
    layer_manifest: tuple[RenderGeometryLayerSurface, ...]
    scene_frame: SceneFrameSurface
    world_model: WorldModelSurface


def build_render_geometry_surface(simulation_map: Map) -> RenderGeometrySurface:
    """Build rendered geometry from optional map metadata plus sensible defaults."""

    metadata = simulation_map.render_geometry
    if metadata:
        world_model = build_world_model_surface(simulation_map)
        roads = _build_roads_from_metadata(simulation_map, metadata)
        intersections = _build_intersections_from_metadata(simulation_map, metadata)
        areas = _build_areas_from_metadata(metadata)
        lanes = _build_lanes_from_metadata(metadata, roads=roads)
        turn_connectors = _build_turn_connectors_from_metadata(
            metadata,
            roads=roads,
            lanes=lanes,
        )
        stop_lines = _build_stop_lines_from_metadata(metadata, lanes=lanes)
        merge_zones = _build_merge_zones_from_metadata(
            metadata,
            roads=roads,
            lanes=lanes,
        )
        return RenderGeometrySurface(
            roads=roads,
            intersections=intersections,
            areas=areas,
            lanes=lanes,
            turn_connectors=turn_connectors,
            stop_lines=stop_lines,
            merge_zones=merge_zones,
            layer_manifest=_build_layer_manifest(
                roads=roads,
                intersections=intersections,
                areas=areas,
                lanes=lanes,
                turn_connectors=turn_connectors,
                stop_lines=stop_lines,
                merge_zones=merge_zones,
                world_model=world_model,
            ),
            scene_frame=_build_scene_frame_surface(
                simulation_map=simulation_map,
                world_model=world_model,
                roads=roads,
                intersections=intersections,
                areas=areas,
                lanes=lanes,
                turn_connectors=turn_connectors,
                stop_lines=stop_lines,
                merge_zones=merge_zones,
            ),
            world_model=world_model,
        )

    roads = _build_default_roads(simulation_map)
    intersections = _build_default_intersections(simulation_map)
    areas = _build_default_areas(simulation_map)
    lanes = _build_default_lanes(roads)
    turn_connectors = _build_default_turn_connectors(roads=roads, lanes=lanes)
    stop_lines = _build_default_stop_lines(lanes=lanes)
    merge_zones = _build_default_merge_zones(roads=roads, lanes=lanes)
    world_model = build_world_model_surface(simulation_map)
    return RenderGeometrySurface(
        roads=roads,
        intersections=intersections,
        areas=areas,
        lanes=lanes,
        turn_connectors=turn_connectors,
        stop_lines=stop_lines,
        merge_zones=merge_zones,
        layer_manifest=_build_layer_manifest(
            roads=roads,
            intersections=intersections,
            areas=areas,
            lanes=lanes,
            turn_connectors=turn_connectors,
            stop_lines=stop_lines,
            merge_zones=merge_zones,
            world_model=world_model,
        ),
        scene_frame=_build_scene_frame_surface(
            simulation_map=simulation_map,
            world_model=world_model,
            roads=roads,
            intersections=intersections,
            areas=areas,
            lanes=lanes,
            turn_connectors=turn_connectors,
            stop_lines=stop_lines,
            merge_zones=merge_zones,
        ),
        world_model=world_model,
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
                "category": area.category,
                "kind": area.kind,
                "group_id": area.group_id,
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
        "layer_manifest": [
            {
                "layer_id": layer.layer_id,
                "source": layer.source,
                "category": layer.category,
                "label": layer.label,
                "feature_ids": list(layer.feature_ids),
            }
            for layer in surface.layer_manifest
        ],
        "scene_frame": {
            "frame_id": surface.scene_frame.frame_id,
            "environment_family": surface.scene_frame.environment_family,
            "scene_bounds": _scene_bounds_to_dict(surface.scene_frame.scene_bounds),
            "extents": [
                {
                    "extent_id": extent.extent_id,
                    "source": extent.source,
                    "category": extent.category,
                    "label": extent.label,
                    "feature_ids": list(extent.feature_ids),
                    "bounds": _scene_bounds_to_dict(extent.bounds),
                }
                for extent in surface.scene_frame.extents
            ],
        },
        "world_model": world_model_surface_to_dict(surface.world_model),
    }


def _scene_bounds_to_dict(bounds: SceneBoundsSurface) -> dict[str, Any]:
    return {
        "min_x": bounds.min_x,
        "min_y": bounds.min_y,
        "max_x": bounds.max_x,
        "max_y": bounds.max_y,
        "width": bounds.width,
        "height": bounds.height,
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
    return tuple(_build_area_surface(area) for area in areas)


def _build_area_surface(area: dict[str, object]) -> AreaGeometrySurface:
    category, group_id = _classify_area_kind(str(area["kind"]))
    return AreaGeometrySurface(
        area_id=str(area["id"]),
        category=category,
        kind=str(area["kind"]),
        polygon=tuple(_position(point) for point in area["polygon"]),
        label=str(area["label"]) if area.get("label") is not None else None,
        group_id=group_id,
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
        areas.append(_build_default_area_surface(kind=kind, node_id=node_id, position=node.position))
    return tuple(areas)


def _build_default_area_surface(
    *,
    kind: str,
    node_id: int,
    position: Position,
) -> AreaGeometrySurface:
    x, y, z = position
    size = 0.55
    category, group_id = _classify_area_kind(kind)
    return AreaGeometrySurface(
        area_id=f"{kind}-{node_id}",
        category=category,
        kind=kind,
        polygon=(
            (x - size, y - size, z),
            (x + size, y - size, z),
            (x + size, y + size, z),
            (x - size, y + size, z),
        ),
        label=f"{kind.replace('_', ' ')} {node_id}",
        group_id=group_id,
    )


def _build_layer_manifest(
    *,
    roads: tuple[RoadGeometrySurface, ...],
    intersections: tuple[IntersectionGeometrySurface, ...],
    areas: tuple[AreaGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
    turn_connectors: tuple[TurnConnectorSurface, ...],
    stop_lines: tuple[StopLineSurface, ...],
    merge_zones: tuple[MergeZoneSurface, ...],
    world_model: WorldModelSurface,
) -> tuple[RenderGeometryLayerSurface, ...]:
    layers: list[RenderGeometryLayerSurface] = []
    layers.extend(
        _world_model_layer_to_render_layer(group)
        for group in world_model.feature_groups
    )
    layers.append(
        _render_feature_layer(
            layer_id="render:roads",
            category="mobility",
            label="Roads",
            source="render_geometry",
            feature_ids=tuple(road.road_id for road in roads),
        )
    )
    layers.append(
        _render_feature_layer(
            layer_id="render:intersections",
            category="junction",
            label="Intersections",
            source="render_geometry",
            feature_ids=tuple(intersection.intersection_id for intersection in intersections),
        )
    )
    layers.extend(_area_layers_from_areas(areas))
    layers.append(
        _render_feature_layer(
            layer_id="render:lanes",
            category="lane",
            label="Lanes",
            source="render_geometry",
            feature_ids=tuple(lane.lane_id for lane in lanes),
        )
    )
    layers.append(
        _render_feature_layer(
            layer_id="render:turn_connectors",
            category="control",
            label="Turn Connectors",
            source="render_geometry",
            feature_ids=tuple(connector.connector_id for connector in turn_connectors),
        )
    )
    layers.append(
        _render_feature_layer(
            layer_id="render:stop_lines",
            category="control",
            label="Stop Lines",
            source="render_geometry",
            feature_ids=tuple(stop_line.stop_line_id for stop_line in stop_lines),
        )
    )
    layers.append(
        _render_feature_layer(
            layer_id="render:merge_zones",
            category="conflict",
            label="Merge Zones",
            source="render_geometry",
            feature_ids=tuple(zone.merge_zone_id for zone in merge_zones),
        )
    )
    return tuple(layers)


def _build_scene_frame_surface(
    *,
    simulation_map: Map,
    world_model: WorldModelSurface,
    roads: tuple[RoadGeometrySurface, ...],
    intersections: tuple[IntersectionGeometrySurface, ...],
    areas: tuple[AreaGeometrySurface, ...],
    lanes: tuple[LaneGeometrySurface, ...],
    turn_connectors: tuple[TurnConnectorSurface, ...],
    stop_lines: tuple[StopLineSurface, ...],
    merge_zones: tuple[MergeZoneSurface, ...],
) -> SceneFrameSurface:
    roads_by_id = {road.road_id: road for road in roads}
    intersections_by_id = {intersection.intersection_id: intersection for intersection in intersections}
    areas_by_id = {area.area_id: area for area in areas}
    feature_lookup = {feature.feature_id: feature for feature in world_model.feature_inventory}

    extents: list[SceneExtentSurface] = []

    operational_points = _collect_points(
        *[road.centerline for road in roads],
        *[intersection.polygon for intersection in intersections],
        *[lane.centerline for lane in lanes],
        *[connector.centerline for connector in turn_connectors],
        *[stop_line.segment for stop_line in stop_lines],
        *[zone.polygon for zone in merge_zones],
        *[(simulation_map.get_position(node_id),) for node_id in sorted(simulation_map.graph.nodes)],
    )
    extents.append(
        _build_scene_extent(
            extent_id="scene:operational",
            source="render_geometry",
            category="operational",
            label="Operational Geometry",
            feature_ids=tuple(
                [
                    *(road.road_id for road in roads),
                    *(intersection.intersection_id for intersection in intersections),
                    *(lane.lane_id for lane in lanes),
                    *(connector.connector_id for connector in turn_connectors),
                    *(stop_line.stop_line_id for stop_line in stop_lines),
                    *(zone.merge_zone_id for zone in merge_zones),
                ]
            ),
            points=operational_points,
        )
    )

    for group in world_model.feature_groups:
        group_features = tuple(
            feature_lookup[feature_id]
            for feature_id in group.feature_ids
            if feature_id in feature_lookup
        )
        points = _collect_points(
            *[
                _feature_points_for_scene(feature, roads_by_id, intersections_by_id, areas_by_id)
                for feature in group_features
            ],
        )
        if not points:
            continue
        extents.append(
            _build_scene_extent(
                extent_id=f"world:{group.group_id}",
                source="world_model",
                category=group.category,
                label=group.label,
                feature_ids=group.feature_ids,
                points=points,
            )
        )

    for asset_layer in world_model.asset_layers:
        if not asset_layer.coverage:
            continue
        extents.append(
            _build_scene_extent(
                extent_id=f"world:asset_layer:{asset_layer.layer_id}",
                source="world_model",
                category="asset_layer",
                label=asset_layer.asset_key.replace("_", " ").title(),
                feature_ids=(asset_layer.layer_id,),
                points=asset_layer.coverage,
            )
        )

    scene_bounds = _union_scene_bounds(
        extent.bounds for extent in extents if extent.bounds.width > 0 and extent.bounds.height > 0
    )
    return SceneFrameSurface(
        frame_id="scene-frame",
        environment_family=world_model.environment.family,
        scene_bounds=scene_bounds,
        extents=tuple(extents),
    )


def _build_scene_extent(
    *,
    extent_id: str,
    source: str,
    category: str,
    label: str,
    feature_ids: tuple[str, ...],
    points: tuple[Position, ...],
) -> SceneExtentSurface:
    bounds = _bounds_from_points(points)
    return SceneExtentSurface(
        extent_id=extent_id,
        source=source,
        category=category,
        label=label,
        feature_ids=feature_ids,
        bounds=bounds,
    )


def _feature_points_for_scene(
    feature: WorldFeatureSurface,
    roads_by_id: dict[str, RoadGeometrySurface],
    intersections_by_id: dict[str, IntersectionGeometrySurface],
    areas_by_id: dict[str, AreaGeometrySurface],
) -> tuple[Position, ...]:
    if feature.polygon:
        return feature.polygon
    reference_id = feature.reference_id
    if reference_id is None:
        return ()
    if feature.layer == "roads":
        road = roads_by_id.get(reference_id)
        return road.centerline if road is not None else ()
    if feature.layer == "intersections":
        intersection = intersections_by_id.get(reference_id)
        return intersection.polygon if intersection is not None else ()
    area = areas_by_id.get(reference_id)
    return area.polygon if area is not None else ()


def _collect_points(*groups: tuple[Position, ...]) -> tuple[Position, ...]:
    points: list[Position] = []
    for group in groups:
        points.extend(group)
    return tuple(points)


def _bounds_from_points(points: tuple[Position, ...]) -> SceneBoundsSurface:
    if not points:
        return SceneBoundsSurface(
            min_x=-10.0,
            min_y=-6.0,
            max_x=10.0,
            max_y=6.0,
            width=20.0,
            height=12.0,
        )

    min_x = points[0][0]
    min_y = points[0][1]
    max_x = points[0][0]
    max_y = points[0][1]
    for x, y, _ in points:
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    return SceneBoundsSurface(
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        width=max(max_x - min_x, 1.0),
        height=max(max_y - min_y, 1.0),
    )


def _union_scene_bounds(bounds_list: Iterable[SceneBoundsSurface]) -> SceneBoundsSurface:
    iterator = iter(bounds_list)
    first = next(iterator, None)
    if first is None:
        return SceneBoundsSurface(
            min_x=-10.0,
            min_y=-6.0,
            max_x=10.0,
            max_y=6.0,
            width=20.0,
            height=12.0,
        )

    min_x = first.min_x
    min_y = first.min_y
    max_x = first.max_x
    max_y = first.max_y
    for bounds in iterator:
        min_x = min(min_x, bounds.min_x)
        min_y = min(min_y, bounds.min_y)
        max_x = max(max_x, bounds.max_x)
        max_y = max(max_y, bounds.max_y)
    return SceneBoundsSurface(
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        width=max(max_x - min_x, 1.0),
        height=max(max_y - min_y, 1.0),
    )


def _area_layers_from_areas(
    areas: tuple[AreaGeometrySurface, ...],
) -> tuple[RenderGeometryLayerSurface, ...]:
    grouped: dict[str, list[str]] = {}
    categories: dict[str, str] = {}
    labels: dict[str, str] = {}
    for area in areas:
        group_id = area.group_id or f"area:{area.category}"
        grouped.setdefault(group_id, []).append(area.area_id)
        categories.setdefault(group_id, area.category)
        labels.setdefault(group_id, area.category.replace("_", " ").title())

    return tuple(
        RenderGeometryLayerSurface(
            layer_id=f"render:{group_id}",
            source="render_geometry",
            category=categories[group_id],
            label=label,
            feature_ids=tuple(feature_ids),
        )
        for group_id, feature_ids in grouped.items()
        for label in [labels[group_id]]
    )


def _world_model_layer_to_render_layer(
    group: WorldFeatureGroupSurface,
) -> RenderGeometryLayerSurface:
    return RenderGeometryLayerSurface(
        layer_id=f"world:{group.group_id}",
        source="world_model",
        category=group.category,
        label=group.label,
        feature_ids=group.feature_ids,
    )


def _render_feature_layer(
    *,
    layer_id: str,
    source: str,
    category: str,
    label: str,
    feature_ids: tuple[str, ...],
) -> RenderGeometryLayerSurface:
    return RenderGeometryLayerSurface(
        layer_id=layer_id,
        source=source,
        category=category,
        label=label,
        feature_ids=feature_ids,
    )


def _classify_area_kind(kind: str) -> tuple[str, str]:
    if kind in {"building", "maintenance_building", "office", "warehouse", "crusher", "gatehouse", "wall", "barrier"}:
        return "structure", "structure:buildings"
    if kind in {"berm", "stockpile", "hill", "mountain", "pit", "trench", "embankment", "cut", "basin", "retaining_wall"}:
        return "terrain", "terrain:terrain_forms"
    if kind in {"sidewalk", "walkway", "pedestrian_route", "sidewalk_zone"}:
        return "surface", "surface:sidewalks"
    if kind in {"site_boundary", "boundary", "perimeter", "boundary_surface"}:
        return "boundary", "boundary:boundaries"
    if kind in {"no_go", "no_go_area", "no_go_zone", "hazard_zone", "blast_zone", "hazard_exclusion"}:
        return "hazard", "hazard:no_go_areas"
    return "zone", "zone:zones"


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
    "SceneBoundsSurface",
    "SceneExtentSurface",
    "SceneFrameSurface",
    "RenderGeometryLayerSurface",
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
