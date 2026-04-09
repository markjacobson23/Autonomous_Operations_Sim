from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import build_render_geometry_surface


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
    assert len(surface.world_model.roads) == len(surface.roads)
    assert len(surface.world_model.intersections) == len(surface.intersections)
    assert len(surface.world_model.zones) >= 1
    assert len(surface.world_model.no_go_areas) >= 1
