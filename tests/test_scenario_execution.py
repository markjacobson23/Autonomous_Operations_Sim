import json
from pathlib import Path

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario


SCENARIO_PATH = Path("scenarios/step_12_single_vehicle_job.json")
GOLDEN_PATH = Path(__file__).parent / "golden" / "step_12_scenario_execution_export.json"
STEP_13_SCENARIO_PATH = Path("scenarios/step_13_dispatch_resources_blocked_edges.json")
STEP_13_GOLDEN_PATH = (
    Path(__file__).parent / "golden" / "step_13_scenario_execution_export.json"
)
STEP_16_SCENARIO_PATH = Path("scenarios/step_16_dispatch_vehicle_job_queue.json")
STEP_16_GOLDEN_PATH = (
    Path(__file__).parent / "golden" / "step_16_scenario_execution_export.json"
)


def test_scenario_execution_runs_end_to_end_through_existing_engine_surfaces():
    scenario = load_scenario(SCENARIO_PATH)

    result = execute_scenario(scenario)
    runtime_vehicle = result.engine.get_vehicle(7)

    assert result.engine.seed == 212
    assert result.summary.seed == 212
    assert result.summary.final_time_s == 6.0
    assert result.summary.completed_job_count == 1
    assert result.summary.completed_task_count == 4
    assert result.summary.route_count == 2
    assert result.summary.vehicle_ids == (7,)
    assert result.summary.trace_event_count > 0
    assert runtime_vehicle.id == 7
    assert runtime_vehicle.current_node_id == 6
    assert runtime_vehicle.payload == 0.0
    assert runtime_vehicle.operational_state == "idle"
    assert json.loads(result.export_json)["summary"]["completed_job_count"] == 1


def test_repeated_scenario_execution_produces_identical_export_output():
    scenario = load_scenario(SCENARIO_PATH)

    first_result = execute_scenario(scenario)
    second_result = execute_scenario(scenario)

    assert first_result.summary == second_result.summary
    assert first_result.export_json == second_result.export_json
    assert first_result.engine.get_vehicle(7).current_node_id == (
        second_result.engine.get_vehicle(7).current_node_id
    )
    assert first_result.engine.get_vehicle(7).payload == second_result.engine.get_vehicle(7).payload


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


def test_step_13_scenario_execution_uses_resources_and_dispatcher():
    scenario = load_scenario(STEP_13_SCENARIO_PATH)

    result = execute_scenario(scenario)
    export_record = json.loads(result.export_json)

    assert result.engine.seed == 313
    assert result.summary.seed == 313
    assert result.summary.final_time_s == 8.0
    assert result.summary.completed_job_count == 1
    assert result.summary.completed_task_count == 4
    assert result.summary.route_count == 2
    assert result.summary.total_route_distance == 4.0
    assert result.summary.total_service_time_s == 3.0
    assert result.summary.total_resource_wait_time_s == 1.0
    assert result.engine.world_state.blocked_edge_ids == {2}
    assert export_record["summary"]["completed_job_count"] == 1
    assert export_record["summary"]["total_resource_wait_time_s"] == 1.0
    assert [
        event["job_id"]
        for event in export_record["trace"]
        if event["event_type"] in {"job_start", "job_complete"}
    ] == ["selected-haul", "selected-haul"]


def test_step_13_scenario_execution_honors_initial_blocked_edges():
    scenario = load_scenario(STEP_13_SCENARIO_PATH)

    result = execute_scenario(scenario)
    edge_ids = [
        event.edge_id
        for event in result.engine.trace.events
        if event.event_type.value == "edge_enter"
    ]

    assert edge_ids == [0, 6, 11, 12]
    assert 2 not in edge_ids


def test_step_13_repeated_scenario_execution_remains_deterministic():
    scenario = load_scenario(STEP_13_SCENARIO_PATH)

    first_result = execute_scenario(scenario)
    second_result = execute_scenario(scenario)

    assert first_result.summary == second_result.summary
    assert first_result.export_json == second_result.export_json


def test_step_13_scenario_execution_export_matches_golden_fixture_exactly():
    scenario = load_scenario(STEP_13_SCENARIO_PATH)
    result = execute_scenario(scenario)

    assert json.loads(result.export_json) == json.loads(STEP_13_GOLDEN_PATH.read_text())
    assert result.export_json == STEP_13_GOLDEN_PATH.read_text()


def test_step_16_scenario_execution_runs_repeated_dispatch_workload():
    scenario = load_scenario(STEP_16_SCENARIO_PATH)

    result = execute_scenario(scenario)
    runtime_vehicle = result.engine.get_vehicle(16)
    export_record = json.loads(result.export_json)

    assert result.engine.seed == 416
    assert result.summary.seed == 416
    assert result.summary.final_time_s == 7.0
    assert result.summary.completed_job_count == 3
    assert result.summary.completed_task_count == 5
    assert result.summary.route_count == 3
    assert result.summary.total_route_distance == 3.0
    assert result.summary.total_service_time_s == 3.0
    assert result.summary.total_resource_wait_time_s == 1.0
    assert runtime_vehicle.position == (0.0, 1.0, 0.0)
    assert runtime_vehicle.payload == 0.0
    assert runtime_vehicle.operational_state == "idle"
    assert [
        event["job_id"]
        for event in export_record["trace"]
        if event["event_type"] == "job_start"
    ] == ["pickup-cycle", "yard-dropoff", "reposition"]


def test_step_16_repeated_scenario_execution_remains_deterministic():
    scenario = load_scenario(STEP_16_SCENARIO_PATH)

    first_result = execute_scenario(scenario)
    second_result = execute_scenario(scenario)

    assert first_result.summary == second_result.summary
    assert first_result.export_json == second_result.export_json
    assert first_result.engine.get_vehicle(16).position == (
        second_result.engine.get_vehicle(16).position
    )
    assert first_result.engine.get_vehicle(16).payload == (
        second_result.engine.get_vehicle(16).payload
    )


def test_step_16_scenario_execution_export_matches_golden_fixture_exactly():
    scenario = load_scenario(STEP_16_SCENARIO_PATH)
    result = execute_scenario(scenario)

    assert json.loads(result.export_json) == json.loads(STEP_16_GOLDEN_PATH.read_text())
    assert result.export_json == STEP_16_GOLDEN_PATH.read_text()
