from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import build_render_geometry_surface
from autonomous_ops_sim.world import build_world_model_surface, world_model_surface_to_dict


MINE_SAMPLE = Path("scenarios/world_model_samples/01_mine_depot_world.json")
YARD_SAMPLE = Path("scenarios/world_model_samples/02_construction_yard_world.json")
CITY_SAMPLE = Path("scenarios/world_model_samples/03_city_street_world.json")
FLAGSHIP_SAMPLE = Path("scenarios/showpiece_pack/01_mine_ore_shift.json")


def test_graph_map_world_model_metadata_loads_for_step_47_and_step_48_samples() -> None:
    scenario = load_scenario(MINE_SAMPLE)
    world_model = scenario.map_spec.params.get("world_model")

    assert isinstance(world_model, dict)
    assert world_model["environment"]["family"] == "mine"
    assert world_model["environment"]["archetype"] == "mine_depot"
    assert len(world_model["asset_layers"]) == 2


def test_world_model_v2_note_locks_phase_b_boundary_language() -> None:
    world_model_note = (Path("docs/world_model_v2.md")).read_text(encoding="utf-8")

    assert "Phase B architecture note" in world_model_note
    assert "Phase B boundary lock" in world_model_note
    assert "Shared taxonomy rule" in world_model_note
    assert "Road / mobility types" in world_model_note
    assert "Intersection / junction types" in world_model_note
    assert "Zone / surface types" in world_model_note
    assert "Structure types" in world_model_note
    assert "Terrain form types" in world_model_note
    assert "Anchor / operational point types" in world_model_note
    assert "render-ready geometry" in world_model_note
    assert "frontend adapters" in world_model_note
    assert "world-model-v2" in world_model_note


def test_world_model_surface_shape_preserves_shared_taxonomy_across_families() -> None:
    expected = [
        (MINE_SAMPLE, "mine", "mine_depot"),
        (YARD_SAMPLE, "construction_yard", "construction_staging_yard"),
        (CITY_SAMPLE, "city_street", "urban_delivery_corridor"),
    ]

    for scenario_path, family, archetype in expected:
        scenario = load_scenario(scenario_path)
        result = execute_scenario(scenario)
        surface = build_world_model_surface(result.engine.map)
        payload = world_model_surface_to_dict(surface)

        assert surface.environment.family == family
        assert surface.environment.archetype_id == archetype
        assert len(surface.feature_inventory) >= len(surface.roads)
        assert len(surface.feature_groups) >= 4
        assert {group.category for group in surface.feature_groups} >= {
            "mobility",
            "junction",
            "zone",
        }
        assert tuple(payload["layers"].keys()) == (
            "roads",
            "intersections",
            "zones",
            "buildings",
            "structures",
            "terrain_forms",
            "anchors",
            "sidewalks",
            "boundaries",
            "no_go_areas",
        )
        assert payload["feature_inventory"][0]["feature_id"]
        assert payload["feature_groups"][0]["group_id"]
        assert len(surface.roads) >= 1
        assert len(surface.intersections) >= 1
        assert len(surface.zones) >= 1
        assert len(surface.anchors) >= 1
        assert isinstance(payload["asset_layers"], list)


def test_render_geometry_surface_embeds_world_model_for_mine_yard_and_city() -> None:
    expected = [
        (MINE_SAMPLE, "mine", "mine_depot"),
        (YARD_SAMPLE, "construction_yard", "construction_staging_yard"),
        (CITY_SAMPLE, "city_street", "urban_delivery_corridor"),
    ]

    observed = []
    for scenario_path, family, archetype in expected:
        scenario = load_scenario(scenario_path)
        result = execute_scenario(scenario)
        surface = build_render_geometry_surface(result.engine.map)
        observed.append(
            (
                surface.world_model.environment.family,
                surface.world_model.environment.archetype_id,
                len(surface.world_model.asset_layers),
            )
        )
        assert surface.world_model.environment.family == family
        assert surface.world_model.environment.archetype_id == archetype
        assert len(surface.world_model.roads) >= 1
        assert len(surface.world_model.intersections) >= 1
        assert len(surface.world_model.zones) >= 1

    assert observed == [
        ("mine", "mine_depot", 2),
        ("construction_yard", "construction_staging_yard", 2),
        ("city_street", "urban_delivery_corridor", 2),
    ]


def test_existing_mining_showpiece_maps_cleanly_to_derived_world_model() -> None:
    scenario = load_scenario(FLAGSHIP_SAMPLE)
    result = execute_scenario(scenario)
    surface = build_render_geometry_surface(result.engine.map)

    assert surface.world_model.environment.family == "mine"
    assert surface.world_model.environment.archetype_id == "legacy_mine_depot"
    assert len(surface.world_model.feature_inventory) >= len(surface.world_model.roads)
    assert {group.category for group in surface.world_model.feature_groups} >= {
        "mobility",
        "junction",
        "zone",
        "anchor",
    }
    assert len(surface.world_model.roads) == len(surface.roads)
    assert len(surface.world_model.intersections) == len(surface.intersections)
    assert len(surface.world_model.zones) >= 1
    assert len(surface.world_model.no_go_areas) >= 1
