from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import (
    build_render_geometry_surface,
    render_geometry_surface_to_dict,
)


SCENARIO_PATH = Path("scenarios/step_21_graph_map_realism.json")
MINE_SAMPLE = Path("scenarios/world_model_samples/01_mine_depot_world.json")
YARD_SAMPLE = Path("scenarios/world_model_samples/02_construction_yard_world.json")
CITY_SAMPLE = Path("scenarios/world_model_samples/03_city_street_world.json")
FLAGSHIP_SAMPLE = Path("scenarios/showpiece_pack/01_mine_ore_shift.json")


def test_graph_map_render_geometry_is_loaded_from_scenario_metadata() -> None:
    scenario = load_scenario(SCENARIO_PATH)
    render_geometry = scenario.map_spec.params.get("render_geometry")

    assert isinstance(render_geometry, dict)
    assert len(render_geometry["roads"]) == 5
    assert len(render_geometry["intersections"]) == 2
    assert len(render_geometry["areas"]) == 4


def test_render_geometry_surface_preserves_graph_and_visual_layers_separately() -> None:
    scenario = load_scenario(SCENARIO_PATH)
    result = execute_scenario(scenario)
    surface = build_render_geometry_surface(result.engine.map)

    assert len(result.engine.map.graph.edges) == 8
    assert [road.road_id for road in surface.roads] == [
        "depot-arterial",
        "loading-curve",
        "haul-east",
        "job-branch",
        "job-return",
    ]
    assert surface.roads[1].centerline[1] == (4.4, 0.3, 0.0)
    assert surface.roads[2].directionality == "two_way"
    assert len(surface.lanes) >= len(surface.roads)
    assert surface.lanes[0].lane_id.startswith("depot-arterial:lane:")
    assert surface.turn_connectors != ()
    assert surface.stop_lines != ()
    assert surface.merge_zones != ()
    assert render_geometry_surface_to_dict(surface)["layer_manifest"]
    assert surface.layer_manifest[0].source == "world_model"
    assert any(layer.layer_id == "render:roads" for layer in surface.layer_manifest)
    assert any(layer.layer_id.startswith("render:zone:") for layer in surface.layer_manifest)
    assert any(area.category == "structure" for area in surface.areas)
    assert surface.intersections[0].intersection_type == "yard_junction"
    assert surface.scene_frame.environment_family == "mine"
    operational_extent = next(
        extent for extent in surface.scene_frame.extents if extent.extent_id == "scene:operational"
    )
    assert (
        surface.scene_frame.scene_bounds.min_x < operational_extent.bounds.min_x
        or surface.scene_frame.scene_bounds.min_y < operational_extent.bounds.min_y
        or surface.scene_frame.scene_bounds.max_x > operational_extent.bounds.max_x
        or surface.scene_frame.scene_bounds.max_y > operational_extent.bounds.max_y
    )
    assert any(extent.source == "world_model" for extent in surface.scene_frame.extents)
    assert any(extent.category != "operational" for extent in surface.scene_frame.extents)
    assert render_geometry_surface_to_dict(surface)["scene_frame"]["scene_bounds"]["min_x"] == surface.scene_frame.scene_bounds.min_x
    assert [area.kind for area in surface.areas] == [
        "depot",
        "loading_bay",
        "building",
        "no_go_zone",
    ]


def test_render_geometry_surface_cleans_contract_for_mine_yard_city_and_flagship() -> None:
    expected = [
        (MINE_SAMPLE, "mine", "mine_depot"),
        (YARD_SAMPLE, "construction_yard", "construction_staging_yard"),
        (CITY_SAMPLE, "city_street", "urban_delivery_corridor"),
        (FLAGSHIP_SAMPLE, "mine", "legacy_mine_depot"),
    ]

    for scenario_path, family, archetype in expected:
        scenario = load_scenario(scenario_path)
        result = execute_scenario(scenario)
        surface = build_render_geometry_surface(result.engine.map)

        assert surface.world_model.environment.family == family
        assert surface.world_model.environment.archetype_id == archetype
        assert surface.world_model.feature_groups
        assert surface.layer_manifest
        assert surface.scene_frame.environment_family == family
        assert surface.scene_frame.scene_bounds.width > 0
        assert surface.scene_frame.scene_bounds.height > 0
        assert surface.scene_frame.extents
        assert any(extent.source == "world_model" for extent in surface.scene_frame.extents)
        assert surface.layer_manifest[0].source == "world_model"
        assert any(layer.source == "render_geometry" for layer in surface.layer_manifest)
        assert any(
            layer.layer_id.startswith("render:area:")
            or layer.layer_id.startswith("render:zone:")
            or layer.layer_id.startswith("render:structure:")
            for layer in surface.layer_manifest
        )
        assert len(surface.roads) >= 1
        assert len(surface.intersections) >= 1
        assert len(surface.areas) >= 1
        assert any(area.form_type in {"flat", "raised", "recessed", "structure_mass"} for area in surface.areas)
