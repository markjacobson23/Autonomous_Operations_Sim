import json
from pathlib import Path
from urllib import request
from typing import cast

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.live_app import LiveAppServer, export_live_app_artifacts
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.simulation.scenario import MultiVehicleRouteBatchExecutionSpec


SCENARIO_PATH = Path("scenarios/proof_of_life_pack/01_city_street_proof_of_life.json")


def test_city_street_proof_of_life_scenario_parses_as_a_compact_city_scene() -> None:
    scenario = load_scenario(SCENARIO_PATH)
    params = cast(dict[str, object], scenario.map_spec.params)
    world_model = cast(dict[str, object], params["world_model"])
    execution = cast(MultiVehicleRouteBatchExecutionSpec, scenario.execution)

    assert scenario.name == "city_street_proof_of_life"
    assert scenario.map_spec.kind == "graph"
    assert len(cast(list[object], params["nodes"])) == 12
    assert len(scenario.vehicles) == 6
    assert scenario.execution is not None
    assert execution.kind == "multi_vehicle_route_batches"
    assert len(execution.route_batches) == 4
    assert cast(dict[str, object], world_model["environment"])["family"] == "city_street"
    assert (
        cast(dict[str, object], world_model["environment"])["display_name"]
        == "Proof-of-Life City Street"
    )


def test_city_street_proof_of_life_execution_runs_multiple_vehicle_route_batches() -> None:
    scenario = load_scenario(SCENARIO_PATH)

    first_result = execute_scenario(scenario)
    second_result = execute_scenario(scenario)

    assert first_result.summary == second_result.summary
    assert first_result.export_json == second_result.export_json
    assert first_result.summary.vehicle_ids == (201, 202, 203, 204, 205, 206)
    assert first_result.summary.route_count == 24
    assert first_result.summary.node_arrival_count >= first_result.summary.route_count
    assert first_result.engine.simulated_time_s == first_result.summary.final_time_s
    assert first_result.engine.get_vehicle(201).current_node_id == 100
    assert first_result.engine.get_vehicle(202).current_node_id == 103
    assert first_result.engine.get_vehicle(203).current_node_id == 120
    assert first_result.engine.get_vehicle(204).current_node_id == 123
    assert first_result.engine.get_vehicle(205).current_node_id == 121
    assert first_result.engine.get_vehicle(206).current_node_id == 110


def test_city_street_live_app_bundle_launches_with_multiple_vehicles_and_named_places(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path=SCENARIO_PATH,
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    assert artifacts.launch_mode == "frontend_dist"

    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    try:
        base_url = f"http://{server.host}:{server.port}"
        response = request.urlopen(f"{base_url}/live_session_bundle.json")
        bundle = json.loads(response.read().decode("utf-8"))

        assert bundle["metadata"]["surface_name"] == "live_session_bundle"
        assert bundle["render_geometry"]["world_model"]["environment"]["display_name"] == (
            "Proof-of-Life City Street"
        )
        assert len(bundle["map_surface"]["nodes"]) == 12
        assert len(bundle["snapshot"]["vehicles"]) == 6
        assert len(bundle["command_center"]["vehicles"]) == 6
    finally:
        server.stop()
