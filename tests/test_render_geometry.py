from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import build_render_geometry_surface


SCENARIO_PATH = Path("scenarios/step_21_graph_map_realism.json")


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
    assert surface.intersections[0].intersection_type == "yard_junction"
    assert [area.kind for area in surface.areas] == [
        "depot",
        "loading_bay",
        "building",
        "no_go_zone",
    ]
