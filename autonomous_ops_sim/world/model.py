from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.core.node import NodeType
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
    category: str
    layer: str
    kind: str
    label: str | None = None
    polygon: tuple[Position, ...] = ()
    reference_id: str | None = None
    group_id: str | None = None


@dataclass(frozen=True)
class WorldFeatureGroupSurface:
    group_id: str
    category: str
    layer: str
    label: str
    feature_ids: tuple[str, ...]


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
    feature_inventory: tuple[WorldFeatureSurface, ...]
    feature_groups: tuple[WorldFeatureGroupSurface, ...]
    roads: tuple[WorldFeatureSurface, ...]
    intersections: tuple[WorldFeatureSurface, ...]
    zones: tuple[WorldFeatureSurface, ...]
    buildings: tuple[WorldFeatureSurface, ...]
    structures: tuple[WorldFeatureSurface, ...]
    terrain_forms: tuple[WorldFeatureSurface, ...]
    anchors: tuple[WorldFeatureSurface, ...]
    sidewalks: tuple[WorldFeatureSurface, ...]
    boundaries: tuple[WorldFeatureSurface, ...]
    no_go_areas: tuple[WorldFeatureSurface, ...]
    asset_layers: tuple[WorldAssetLayerSurface, ...]


def build_world_model_surface(simulation_map: Map) -> WorldModelSurface:
    metadata = simulation_map.world_model
    if metadata:
        return _build_world_model_from_metadata(simulation_map, metadata)
    return _derive_world_model_from_render_geometry(simulation_map)


def world_model_surface_to_dict(surface: WorldModelSurface) -> dict[str, Any]:
    return {
        "environment": {
            "family": surface.environment.family,
            "archetype_id": surface.environment.archetype_id,
            "display_name": surface.environment.display_name,
        },
        "feature_inventory": [_feature_to_dict(feature) for feature in surface.feature_inventory],
        "feature_groups": [
            {
                "group_id": group.group_id,
                "category": group.category,
                "layer": group.layer,
                "label": group.label,
                "feature_ids": list(group.feature_ids),
            }
            for group in surface.feature_groups
        ],
        "layers": {
            "roads": [_feature_to_dict(feature) for feature in surface.roads],
            "intersections": [_feature_to_dict(feature) for feature in surface.intersections],
            "zones": [_feature_to_dict(feature) for feature in surface.zones],
            "buildings": [_feature_to_dict(feature) for feature in surface.buildings],
            "structures": [_feature_to_dict(feature) for feature in surface.structures],
            "terrain_forms": [_feature_to_dict(feature) for feature in surface.terrain_forms],
            "anchors": [_feature_to_dict(feature) for feature in surface.anchors],
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
        "category": feature.category,
        "layer": feature.layer,
        "kind": feature.kind,
        "label": feature.label,
        "polygon": [list(point) for point in feature.polygon],
        "reference_id": feature.reference_id,
        "group_id": feature.group_id,
    }


def _build_world_model_from_metadata(
    simulation_map: Map,
    metadata: dict[str, object],
) -> WorldModelSurface:
    environment = metadata["environment"]
    assert isinstance(environment, dict)
    layers = metadata.get("layers", {})
    assert isinstance(layers, dict)
    asset_layers = metadata.get("asset_layers", [])
    assert isinstance(asset_layers, list)

    roads = _build_feature_layer(
        tuple(layers.get("roads", [])),
        category="mobility",
        layer_name="roads",
        group_id="mobility:roads",
    )
    intersections = _build_feature_layer(
        tuple(layers.get("intersections", [])),
        category="junction",
        layer_name="intersections",
        group_id="junction:intersections",
    )
    zones = _build_feature_layer(
        tuple(layers.get("zones", [])),
        category="zone",
        layer_name="zones",
        group_id="zone:zones",
    )
    buildings = _build_feature_layer(
        tuple(layers.get("buildings", [])),
        category="structure",
        layer_name="buildings",
        group_id="structure:buildings",
    )
    structures = buildings
    terrain_forms = _build_feature_layer(
        tuple(layers.get("terrain_forms", [])),
        category="terrain",
        layer_name="terrain_forms",
        group_id="terrain:terrain_forms",
    )
    anchors = _build_feature_layer(
        tuple(layers.get("anchors", [])),
        category="anchor",
        layer_name="anchors",
        group_id="anchor:anchors",
    )
    sidewalks = _build_feature_layer(
        tuple(layers.get("sidewalks", [])),
        category="surface",
        layer_name="sidewalks",
        group_id="surface:sidewalks",
    )
    boundaries = _build_feature_layer(
        tuple(layers.get("boundaries", [])),
        category="boundary",
        layer_name="boundaries",
        group_id="boundary:boundaries",
    )
    no_go_areas = _build_feature_layer(
        tuple(layers.get("no_go_areas", [])),
        category="hazard",
        layer_name="no_go_areas",
        group_id="hazard:no_go_areas",
    )

    if not terrain_forms or not anchors:
        supplemental = _derive_world_model_from_render_geometry(simulation_map)
        terrain_forms = terrain_forms or supplemental.terrain_forms
        anchors = anchors or supplemental.anchors

    return _compose_world_model_surface(
        environment=_build_environment_surface(environment),
        roads=roads,
        intersections=intersections,
        zones=zones,
        buildings=buildings,
        structures=structures,
        terrain_forms=terrain_forms,
        anchors=anchors,
        sidewalks=sidewalks,
        boundaries=boundaries,
        no_go_areas=no_go_areas,
        asset_layers=tuple(_build_asset_layer(asset) for asset in asset_layers),
    )


def _build_feature_layer(
    items: tuple[object, ...],
    *,
    category: str,
    layer_name: str,
    group_id: str,
) -> tuple[WorldFeatureSurface, ...]:
    return tuple(
        WorldFeatureSurface(
            feature_id=str(item["id"]),
            category=category,
            layer=layer_name,
            kind=str(item["kind"]),
            label=str(item["label"]) if item.get("label") is not None else None,
            polygon=tuple(_position(point) for point in item.get("polygon", [])),
            reference_id=str(item["reference_id"]) if item.get("reference_id") is not None else None,
            group_id=group_id,
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
            category="mobility",
            layer="roads",
            kind=str(road.get("road_class", "connector")),
            reference_id=str(road["id"]),
            group_id="mobility:roads",
        )
        for road in raw_roads
        if isinstance(road, dict)
    )
    intersections = tuple(
        WorldFeatureSurface(
            feature_id=str(intersection["id"]),
            category="junction",
            layer="intersections",
            kind=str(intersection.get("intersection_type", "junction")),
            reference_id=str(intersection["id"]),
            group_id="junction:intersections",
        )
        for intersection in raw_intersections
        if isinstance(intersection, dict)
    )

    zones: list[WorldFeatureSurface] = []
    buildings: list[WorldFeatureSurface] = []
    structures: list[WorldFeatureSurface] = []
    terrain_forms: list[WorldFeatureSurface] = []
    sidewalks: list[WorldFeatureSurface] = []
    boundaries: list[WorldFeatureSurface] = []
    no_go_areas: list[WorldFeatureSurface] = []

    for area in raw_areas:
        if not isinstance(area, dict):
            continue
        kind = str(area.get("kind", "zone"))
        layer_name, category, group_id = _classify_area_kind(kind)
        feature = WorldFeatureSurface(
            feature_id=str(area["id"]),
            category=category,
            layer=layer_name,
            kind=kind,
            label=str(area["label"]) if area.get("label") is not None else None,
            polygon=tuple(_position(point) for point in area.get("polygon", [])),
            reference_id=str(area["id"]),
            group_id=group_id,
        )
        if layer_name == "buildings":
            buildings.append(feature)
            structures.append(
                WorldFeatureSurface(
                    feature_id=feature.feature_id,
                    category="structure",
                    layer="structures",
                    kind=feature.kind,
                    label=feature.label,
                    polygon=feature.polygon,
                    reference_id=feature.reference_id,
                    group_id="structure:structures",
                )
            )
        elif layer_name == "terrain_forms":
            terrain_forms.append(feature)
        elif layer_name == "sidewalks":
            sidewalks.append(feature)
        elif layer_name == "boundaries":
            boundaries.append(feature)
        elif layer_name == "no_go_areas":
            no_go_areas.append(feature)
        else:
            zones.append(feature)

    anchors = [
        anchor
        for node_id in sorted(simulation_map.graph.nodes)
        if (anchor := _build_anchor_feature(simulation_map, node_id, simulation_map.get_node(node_id).node_type)) is not None
    ]

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
    return _compose_world_model_surface(
        environment=EnvironmentArchetypeSurface(
            family=family,
            archetype_id=archetype_id,
            display_name=display_name,
        ),
        roads=roads,
        intersections=intersections,
        zones=tuple(zones),
        buildings=tuple(buildings),
        structures=tuple(structures) if structures else tuple(buildings),
        terrain_forms=tuple(terrain_forms),
        anchors=tuple(anchors),
        sidewalks=tuple(sidewalks),
        boundaries=tuple(boundaries),
        no_go_areas=tuple(no_go_areas),
        asset_layers=(),
    )


def _compose_world_model_surface(
    *,
    environment: EnvironmentArchetypeSurface,
    roads: tuple[WorldFeatureSurface, ...],
    intersections: tuple[WorldFeatureSurface, ...],
    zones: tuple[WorldFeatureSurface, ...],
    buildings: tuple[WorldFeatureSurface, ...],
    structures: tuple[WorldFeatureSurface, ...],
    terrain_forms: tuple[WorldFeatureSurface, ...],
    anchors: tuple[WorldFeatureSurface, ...],
    sidewalks: tuple[WorldFeatureSurface, ...],
    boundaries: tuple[WorldFeatureSurface, ...],
    no_go_areas: tuple[WorldFeatureSurface, ...],
    asset_layers: tuple[WorldAssetLayerSurface, ...],
) -> WorldModelSurface:
    feature_groups = _build_feature_groups(
        roads=roads,
        intersections=intersections,
        zones=zones,
        buildings=buildings,
        structures=structures,
        terrain_forms=terrain_forms,
        anchors=anchors,
        sidewalks=sidewalks,
        boundaries=boundaries,
        no_go_areas=no_go_areas,
    )
    feature_inventory = _merge_feature_inventory(
        roads=roads,
        intersections=intersections,
        zones=zones,
        buildings=buildings,
        structures=structures,
        terrain_forms=terrain_forms,
        anchors=anchors,
        sidewalks=sidewalks,
        boundaries=boundaries,
        no_go_areas=no_go_areas,
    )
    return WorldModelSurface(
        environment=environment,
        feature_inventory=feature_inventory,
        feature_groups=feature_groups,
        roads=roads,
        intersections=intersections,
        zones=zones,
        buildings=buildings,
        structures=structures,
        terrain_forms=terrain_forms,
        anchors=anchors,
        sidewalks=sidewalks,
        boundaries=boundaries,
        no_go_areas=no_go_areas,
        asset_layers=asset_layers,
    )


def _build_feature_groups(
    *,
    roads: tuple[WorldFeatureSurface, ...],
    intersections: tuple[WorldFeatureSurface, ...],
    zones: tuple[WorldFeatureSurface, ...],
    buildings: tuple[WorldFeatureSurface, ...],
    structures: tuple[WorldFeatureSurface, ...],
    terrain_forms: tuple[WorldFeatureSurface, ...],
    anchors: tuple[WorldFeatureSurface, ...],
    sidewalks: tuple[WorldFeatureSurface, ...],
    boundaries: tuple[WorldFeatureSurface, ...],
    no_go_areas: tuple[WorldFeatureSurface, ...],
) -> tuple[WorldFeatureGroupSurface, ...]:
    groups: list[WorldFeatureGroupSurface] = []
    for group_id, category, layer, label, features in [
        ("mobility:roads", "mobility", "roads", "Roads", roads),
        ("junction:intersections", "junction", "intersections", "Intersections", intersections),
        ("zone:zones", "zone", "zones", "Zones", zones),
        ("structure:buildings", "structure", "buildings", "Buildings", buildings),
        ("structure:structures", "structure", "structures", "Structures", structures),
        ("terrain:terrain_forms", "terrain", "terrain_forms", "Terrain Forms", terrain_forms),
        ("anchor:anchors", "anchor", "anchors", "Anchors", anchors),
        ("surface:sidewalks", "surface", "sidewalks", "Sidewalks", sidewalks),
        ("boundary:boundaries", "boundary", "boundaries", "Boundaries", boundaries),
        ("hazard:no_go_areas", "hazard", "no_go_areas", "No-Go Areas", no_go_areas),
    ]:
        if not features:
            continue
        groups.append(
            WorldFeatureGroupSurface(
                group_id=group_id,
                category=category,
                layer=layer,
                label=label,
                feature_ids=tuple(feature.feature_id for feature in features),
            )
        )
    return tuple(groups)


def _merge_feature_inventory(
    *,
    roads: tuple[WorldFeatureSurface, ...],
    intersections: tuple[WorldFeatureSurface, ...],
    zones: tuple[WorldFeatureSurface, ...],
    buildings: tuple[WorldFeatureSurface, ...],
    structures: tuple[WorldFeatureSurface, ...],
    terrain_forms: tuple[WorldFeatureSurface, ...],
    anchors: tuple[WorldFeatureSurface, ...],
    sidewalks: tuple[WorldFeatureSurface, ...],
    boundaries: tuple[WorldFeatureSurface, ...],
    no_go_areas: tuple[WorldFeatureSurface, ...],
) -> tuple[WorldFeatureSurface, ...]:
    merged: dict[str, WorldFeatureSurface] = {}
    for feature in (
        *roads,
        *intersections,
        *zones,
        *buildings,
        *structures,
        *terrain_forms,
        *anchors,
        *sidewalks,
        *boundaries,
        *no_go_areas,
    ):
        merged[feature.feature_id] = feature
    return tuple(merged[feature_id] for feature_id in sorted(merged))


def _build_environment_surface(environment: dict[str, object]) -> EnvironmentArchetypeSurface:
    archetype = environment.get("archetype_id", environment.get("archetype"))
    assert archetype is not None
    return EnvironmentArchetypeSurface(
        family=str(environment["family"]),
        archetype_id=str(archetype),
        display_name=str(environment.get("display_name", archetype)),
    )


def _classify_area_kind(kind: str) -> tuple[str, str, str]:
    if kind in {
        "building",
        "maintenance_building",
        "office",
        "warehouse",
        "crusher",
        "gatehouse",
        "wall",
        "barrier",
    }:
        return "buildings", "structure", "structure:buildings"
    if kind in {
        "berm",
        "stockpile",
        "hill",
        "mountain",
        "pit",
        "trench",
        "embankment",
        "cut",
        "basin",
        "retaining_wall",
    }:
        return "terrain_forms", "terrain", "terrain:terrain_forms"
    if kind in {"sidewalk", "walkway", "pedestrian_route", "sidewalk_zone"}:
        return "sidewalks", "surface", "surface:sidewalks"
    if kind in {"site_boundary", "boundary", "perimeter", "boundary_surface"}:
        return "boundaries", "boundary", "boundary:boundaries"
    if kind in {
        "no_go",
        "no_go_area",
        "no_go_zone",
        "hazard_zone",
        "blast_zone",
        "hazard_exclusion",
    }:
        return "no_go_areas", "hazard", "hazard:no_go_areas"
    return "zones", "zone", "zone:zones"


def _build_anchor_feature(
    simulation_map: Map,
    node_id: int,
    node_type: NodeType,
) -> WorldFeatureSurface | None:
    if node_type not in {
        NodeType.DEPOT,
        NodeType.JOB_SITE,
        NodeType.LOADING_ZONE,
        NodeType.UNLOADING_ZONE,
        NodeType.CHARGING_STATION,
    }:
        return None
    position = simulation_map.get_position(node_id)
    size = 0.25
    label = node_type.name.replace("_", " ").title()
    return WorldFeatureSurface(
        feature_id=f"anchor-{node_id}",
        category="anchor",
        layer="anchors",
        kind=node_type.name.lower(),
        label=label,
        polygon=(
            (position[0] - size, position[1] - size, position[2]),
            (position[0] + size, position[1] - size, position[2]),
            (position[0] + size, position[1] + size, position[2]),
            (position[0] - size, position[1] + size, position[2]),
        ),
        reference_id=str(node_id),
        group_id="anchor:anchors",
    )


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
