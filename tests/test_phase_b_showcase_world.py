from pathlib import Path

from autonomous_ops_sim.api import build_live_session_bundle
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation import LiveSimulationSession
from autonomous_ops_sim.simulation.scenario_executor import build_scenario_engine, execute_scenario
from autonomous_ops_sim.visualization import build_render_geometry_surface


SCENARIO_PATH = Path("scenarios/phase_b_showcase/01_mine_phase_b_showcase.json")


def test_phase_b_showcase_world_is_rich_and_launchable() -> None:
    scenario = load_scenario(SCENARIO_PATH)

    assert scenario.name == "mine_phase_b_showcase"
    result = execute_scenario(scenario)
    surface = build_render_geometry_surface(result.engine.map)

    assert surface.world_model.environment.family == "mine"
    assert surface.world_model.environment.archetype_id == "phase_b_mine_showcase"
    assert surface.scene_frame.environment_family == "mine"
    assert surface.scene_frame.scene_bounds.width > 20.0
    assert surface.scene_frame.scene_bounds.height > 12.0
    assert any(area.category == "zone" for area in surface.areas)
    assert any(area.category == "structure" for area in surface.areas)
    assert any(area.category == "terrain" for area in surface.areas)
    assert any(area.category == "boundary" for area in surface.areas)
    assert any(area.category == "hazard" for area in surface.areas)
    assert any(area.form_type == "structure_mass" for area in surface.areas)
    assert any(area.form_type == "raised" for area in surface.areas)
    assert any(area.form_type == "recessed" for area in surface.areas)
    assert any(area.form_type == "flat" for area in surface.areas)
    assert any(road.road_id == "haul-spine" for road in surface.roads)
    assert any(intersection.intersection_type == "loading_apron" for intersection in surface.intersections)
    assert any(intersection.intersection_type == "staging_junction" for intersection in surface.intersections)
    assert any(extent.source == "world_model" for extent in surface.scene_frame.extents)
    assert any(extent.category == "terrain" for extent in surface.scene_frame.extents)
    assert any(extent.category == "boundary" for extent in surface.scene_frame.extents)

    live_session = LiveSimulationSession(build_scenario_engine(scenario))
    bundle = build_live_session_bundle(live_session, selected_vehicle_ids=[801])

    assert bundle.render_geometry.scene_frame.environment_family == "mine"
    assert bundle.render_geometry.scene_frame.scene_bounds.width > 20.0
    assert bundle.command_center.selected_vehicle_ids == (801,)
