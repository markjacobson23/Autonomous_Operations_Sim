from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.vehicles.vehicle import Position


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
class RenderGeometrySurface:
    """Static rendered geometry layer separate from routing truth."""

    roads: tuple[RoadGeometrySurface, ...]
    intersections: tuple[IntersectionGeometrySurface, ...]
    areas: tuple[AreaGeometrySurface, ...]


def build_render_geometry_surface(simulation_map: Map) -> RenderGeometrySurface:
    """Build rendered geometry from optional map metadata plus sensible defaults."""

    metadata = simulation_map.render_geometry
    if metadata:
        return RenderGeometrySurface(
            roads=_build_roads_from_metadata(simulation_map, metadata),
            intersections=_build_intersections_from_metadata(simulation_map, metadata),
            areas=_build_areas_from_metadata(metadata),
        )
    return RenderGeometrySurface(
        roads=_build_default_roads(simulation_map),
        intersections=_build_default_intersections(simulation_map),
        areas=_build_default_areas(simulation_map),
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
                _position(point) for point in road.get("centerline", _default_centerline_for_road(simulation_map, road))
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


def _build_default_intersections(simulation_map: Map) -> tuple[IntersectionGeometrySurface, ...]:
    intersections: list[IntersectionGeometrySurface] = []
    for node_id in sorted(simulation_map.graph.nodes):
        node = simulation_map.get_node(node_id)
        if len(simulation_map.get_outgoing_edges(node_id)) < 2 and node.node_type.name != "INTERSECTION":
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


__all__ = [
    "AreaGeometrySurface",
    "IntersectionGeometrySurface",
    "RenderGeometrySurface",
    "RoadGeometrySurface",
    "build_render_geometry_surface",
    "render_geometry_surface_to_dict",
]
