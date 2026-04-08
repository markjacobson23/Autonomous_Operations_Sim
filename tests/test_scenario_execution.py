import json
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario


SCENARIO_PATH = Path("scenarios/step_12_single_vehicle_job.json")
GOLDEN_PATH = Path(__file__).parent / "golden" / "step_12_scenario_execution_export.json"


def test_scenario_execution_runs_end_to_end_through_existing_engine_surfaces():
    scenario = load_scenario(SCENARIO_PATH)

    result = execute_scenario(scenario)

    assert result.engine.seed == 212
    assert result.summary.seed == 212
    assert result.summary.final_time_s == 6.0
    assert result.summary.completed_job_count == 1
    assert result.summary.completed_task_count == 4
    assert result.summary.route_count == 2
    assert result.summary.vehicle_ids == (7,)
    assert result.summary.trace_event_count > 0
    assert json.loads(result.export_json)["summary"]["completed_job_count"] == 1


def test_repeated_scenario_execution_produces_identical_export_output():
    scenario = load_scenario(SCENARIO_PATH)

    first_result = execute_scenario(scenario)
    second_result = execute_scenario(scenario)

    assert first_result.summary == second_result.summary
    assert first_result.export_json == second_result.export_json


def test_scenario_execution_export_output_is_stable():
    scenario = load_scenario(SCENARIO_PATH)
    result = execute_scenario(scenario)
    export_record = json.loads(result.export_json)

    assert export_record["schema_version"] == 1
    assert export_record["seed"] == 212
    assert export_record["final_time_s"] == 6.0
    assert export_record["summary"]["route_count"] == 2
    assert export_record["summary"]["completed_task_count"] == 4
    assert export_record["summary"]["total_route_distance"] == 2
    assert export_record["summary"]["total_service_time_s"] == 4.0
    assert export_record["trace"][0]["event_type"] == "job_start"
    assert export_record["trace"][-1]["event_type"] == "job_complete"


def test_scenario_execution_export_matches_golden_fixture_exactly():
    scenario = load_scenario(SCENARIO_PATH)
    result = execute_scenario(scenario)

    assert json.loads(result.export_json) == json.loads(GOLDEN_PATH.read_text())
    assert result.export_json == GOLDEN_PATH.read_text()
