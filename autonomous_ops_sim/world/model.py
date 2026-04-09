from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.vehicles.vehicle import Position


@dataclass(frozen=True)
class EnvironmentArchetypeSurface:
    family: str
    archetype_id: str
    display_name: str


@dataclass(frozen=True)
class WorldFeatureSurface:
    feature_id: str
    layer: str
    kind: str
    label: str | None = None
    polygon: tuple[Position, ...] = ()
    reference_id: str | None = None


@dataclass(frozen=True)
class WorldAssetLayerSurface:
    layer_id: str
    kind: str
    asset_key: str
    z_index: int
    opacity: float
    coverage: tuple[Position, ...] = ()


@dataclass(frozen=True)
class WorldModelSurface:
    environment: EnvironmentArchetypeSurface
    roads: tuple[WorldFeatureSurface, ...]
    intersections: tuple[WorldFeatureSurface, ...]
    zones: tuple[WorldFeatureSurface, ...]
    buildings: tuple[WorldFeatureSurface, ...]
    sidewalks: tuple[WorldFeatureSurface, ...]
    boundaries: tuple[WorldFeatureSurface, ...]
    no_go_areas: tuple[WorldFeatureSurface, ...]
    asset_layers: tuple[WorldAssetLayerSurface, ...]


def build_world_model_surface(simulation_map: Map) -> WorldModelSurface:
    metadata = simulation_map.world_model
    if metadata:
        return _build_world_model_from_metadata(metadata)
    return _derive_world_model_from_render_geometry(simulation_map)


def world_model_surface_to_dict(surface: WorldModelSurface) -> dict[str, Any]:
    return {
        "environment": {
            "family": surface.environment.family,
            "archetype_id": surface.environment.archetype_id,
            "display_name": surface.environment.display_name,
        },
        "layers": {
            "roads": [_feature_to_dict(feature) for feature in surface.roads],
            "intersections": [_feature_to_dict(feature) for feature in surface.intersections],
            "zones": [_feature_to_dict(feature) for feature in surface.zones],
            "buildings": [_feature_to_dict(feature) for feature in surface.buildings],
            "sidewalks": [_feature_to_dict(feature) for feature in surface.sidewalks],
            "boundaries": [_feature_to_dict(feature) for feature in surface.boundaries],
            "no_go_areas": [_feature_to_dict(feature) for feature in surface.no_go_areas],
        },
        "asset_layers": [
            {
                "layer_id": asset.layer_id,
                "kind": asset.kind,
                "asset_key": asset.asset_key,
                "z_index": asset.z_index,
                "opacity": asset.opacity,
                "coverage": [list(point) for point in asset.coverage],
            }
            for asset in surface.asset_layers
        ],
    }


def _feature_to_dict(feature: WorldFeatureSurface) -> dict[str, Any]:
    return {
        "feature_id": feature.feature_id,
        "layer": feature.layer,
        "kind": feature.kind,
        "label": feature.label,
        "polygon": [list(point) for point in feature.polygon],
        "reference_id": feature.reference_id,
    }


def _build_world_model_from_metadata(metadata: dict[str, object]) -> WorldModelSurface:
    environment = metadata["environment"]
    assert isinstance(environment, dict)
    layers = metadata.get("layers", {})
    assert isinstance(layers, dict)
    asset_layers = metadata.get("asset_layers", [])
    assert isinstance(asset_layers, list)

    return WorldModelSurface(
        environment=EnvironmentArchetypeSurface(
            family=str(environment["family"]),
            archetype_id=str(environment["archetype"]),
            display_name=str(environment.get("display_name", environment["archetype"])),
        ),
        roads=_build_feature_layer(tuple(layers.get("roads", [])), layer_name="roads"),
        intersections=_build_feature_layer(
            tuple(layers.get("intersections", [])),
            layer_name="intersections",
        ),
        zones=_build_feature_layer(tuple(layers.get("zones", [])), layer_name="zones"),
        buildings=_build_feature_layer(
            tuple(layers.get("buildings", [])),
            layer_name="buildings",
        ),
        sidewalks=_build_feature_layer(
            tuple(layers.get("sidewalks", [])),
            layer_name="sidewalks",
        ),
        boundaries=_build_feature_layer(
            tuple(layers.get("boundaries", [])),
            layer_name="boundaries",
        ),
        no_go_areas=_build_feature_layer(
            tuple(layers.get("no_go_areas", [])),
            layer_name="no_go_areas",
        ),
        asset_layers=tuple(_build_asset_layer(asset) for asset in asset_layers),
    )


def _build_feature_layer(
    items: tuple[object, ...],
    *,
    layer_name: str,
) -> tuple[WorldFeatureSurface, ...]:
    return tuple(
        WorldFeatureSurface(
            feature_id=str(item["id"]),
            layer=layer_name,
            kind=str(item["kind"]),
            label=str(item["label"]) if item.get("label") is not None else None,
            polygon=tuple(_position(point) for point in item.get("polygon", [])),
            reference_id=str(item["reference_id"]) if item.get("reference_id") is not None else None,
        )
        for item in items
        if isinstance(item, dict)
    )


def _build_asset_layer(item: object) -> WorldAssetLayerSurface:
    assert isinstance(item, dict)
    return WorldAssetLayerSurface(
        layer_id=str(item["id"]),
        kind=str(item["kind"]),
        asset_key=str(item["asset_key"]),
        z_index=int(item.get("z_index", 0)),
        opacity=float(item.get("opacity", 1.0)),
        coverage=tuple(_position(point) for point in item.get("coverage", [])),
    )


def _derive_world_model_from_render_geometry(simulation_map: Map) -> WorldModelSurface:
    render_geometry = simulation_map.render_geometry
    raw_roads = render_geometry.get("roads", [])
    raw_intersections = render_geometry.get("intersections", [])
    raw_areas = render_geometry.get("areas", [])
    assert isinstance(raw_roads, list)
    assert isinstance(raw_intersections, list)
    assert isinstance(raw_areas, list)

    roads = tuple(
        WorldFeatureSurface(
            feature_id=str(road["id"]),
            layer="roads",
            kind=str(road.get("road_class", "connector")),
            reference_id=str(road["id"]),
        )
        for road in raw_roads
        if isinstance(road, dict)
    )
    intersections = tuple(
        WorldFeatureSurface(
            feature_id=str(intersection["id"]),
            layer="intersections",
            kind=str(intersection.get("intersection_type", "junction")),
            reference_id=str(intersection["id"]),
        )
        for intersection in raw_intersections
        if isinstance(intersection, dict)
    )

    zones: list[WorldFeatureSurface] = []
    buildings: list[WorldFeatureSurface] = []
    sidewalks: list[WorldFeatureSurface] = []
    boundaries: list[WorldFeatureSurface] = []
    no_go_areas: list[WorldFeatureSurface] = []

    for area in raw_areas:
        if not isinstance(area, dict):
            continue
        kind = str(area.get("kind", "zone"))
        feature = WorldFeatureSurface(
            feature_id=str(area["id"]),
            layer=_derive_layer_name(kind),
            kind=kind,
            label=str(area["label"]) if area.get("label") is not None else None,
            polygon=tuple(_position(point) for point in area.get("polygon", [])),
            reference_id=str(area["id"]),
        )
        if feature.layer == "buildings":
            buildings.append(feature)
        elif feature.layer == "sidewalks":
            sidewalks.append(feature)
        elif feature.layer == "boundaries":
            boundaries.append(feature)
        elif feature.layer == "no_go_areas":
            no_go_areas.append(feature)
        else:
            zones.append(feature)

    family = _infer_environment_family(render_geometry)
    display_name = {
        "mine": "Legacy Mine Depot",
        "construction_yard": "Legacy Construction Yard",
        "city_street": "Legacy City Street",
    }[family]
    archetype_id = {
        "mine": "legacy_mine_depot",
        "construction_yard": "legacy_construction_yard",
        "city_street": "legacy_city_street",
    }[family]
    return WorldModelSurface(
        environment=EnvironmentArchetypeSurface(
            family=family,
            archetype_id=archetype_id,
            display_name=display_name,
        ),
        roads=roads,
        intersections=intersections,
        zones=tuple(zones),
        buildings=tuple(buildings),
        sidewalks=tuple(sidewalks),
        boundaries=tuple(boundaries),
        no_go_areas=tuple(no_go_areas),
        asset_layers=(),
    )


def _derive_layer_name(kind: str) -> str:
    if kind in {"building", "maintenance_building", "office", "warehouse"}:
        return "buildings"
    if kind in {"sidewalk", "walkway", "pedestrian_route"}:
        return "sidewalks"
    if kind in {"boundary", "perimeter", "site_boundary"}:
        return "boundaries"
    if kind in {"no_go_zone", "hazard_exclusion", "blast_zone"}:
        return "no_go_areas"
    return "zones"


def _infer_environment_family(render_geometry: dict[str, object]) -> str:
    raw_areas = render_geometry.get("areas", [])
    assert isinstance(raw_areas, list)
    area_kinds = {
        str(area.get("kind"))
        for area in raw_areas
        if isinstance(area, dict)
    }
    if area_kinds & {"depot", "loading_bay", "crusher", "stockpile", "haul_zone"}:
        return "mine"
    if area_kinds & {"staging_zone", "laydown_yard", "office", "warehouse"}:
        return "construction_yard"
    return "city_street"


def _position(value: object) -> Position:
    assert isinstance(value, (list, tuple))
    return (float(value[0]), float(value[1]), float(value[2]))
