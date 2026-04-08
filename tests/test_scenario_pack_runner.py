import json
from pathlib import Path

from autonomous_ops_sim.io.scenario_pack_runner import (
    SCENARIO_PACK_EXPORT_SCHEMA_VERSION,
    build_scenario_pack_export,
    discover_scenario_pack_paths,
    export_scenario_pack_json,
    run_scenario_pack,
)


PACK_PATH = Path("tests/fixtures/scenario_pack")
GOLDEN_PATH = Path(__file__).parent / "golden" / "step_15_scenario_pack_export.json"


def test_scenario_pack_discovery_order_is_deterministic():
    scenario_paths = discover_scenario_pack_paths(PACK_PATH)

    assert [path.name for path in scenario_paths] == [
        "01_dispatch_resources_blocked_edges.json",
        "02_single_vehicle_job.json",
    ]


def test_scenario_pack_collects_stable_per_scenario_summaries():
    result = run_scenario_pack(PACK_PATH)

    assert [entry.relative_path for entry in result.scenario_results] == [
        "01_dispatch_resources_blocked_edges.json",
        "02_single_vehicle_job.json",
    ]
    assert [entry.scenario_name for entry in result.scenario_results] == [
        "step_13_dispatch_resources_blocked_edges",
        "step_12_single_vehicle_job",
    ]
    assert [entry.summary.seed for entry in result.scenario_results] == [313, 212]
    assert [entry.summary.final_time_s for entry in result.scenario_results] == [8.0, 6.0]
    assert [entry.summary.completed_job_count for entry in result.scenario_results] == [1, 1]
    assert [entry.summary.completed_task_count for entry in result.scenario_results] == [4, 4]


def test_scenario_pack_aggregate_output_is_stable():
    result = run_scenario_pack(PACK_PATH)
    export_record = build_scenario_pack_export(result)

    assert export_record["schema_version"] == SCENARIO_PACK_EXPORT_SCHEMA_VERSION
    assert export_record["aggregate_summary"] == {
        "scenario_count": 2,
        "scenario_names": [
            "step_13_dispatch_resources_blocked_edges",
            "step_12_single_vehicle_job",
        ],
        "scenario_paths": [
            "01_dispatch_resources_blocked_edges.json",
            "02_single_vehicle_job.json",
        ],
        "total_final_time_s": 14.0,
        "total_trace_event_count": 67,
        "total_route_count": 4,
        "total_completed_job_count": 2,
        "total_completed_task_count": 8,
        "total_edge_traversal_count": 6,
        "total_node_arrival_count": 6,
        "total_route_distance": 6.0,
        "total_service_time_s": 7.0,
        "total_resource_wait_time_s": 1.0,
        "total_conflict_wait_time_s": 0.0,
        "event_counts": [
            {"event_type": "behavior_transition", "count": 17},
            {"event_type": "edge_enter", "count": 6},
            {"event_type": "job_complete", "count": 2},
            {"event_type": "job_start", "count": 2},
            {"event_type": "node_arrival", "count": 6},
            {"event_type": "resource_wait_complete", "count": 1},
            {"event_type": "resource_wait_start", "count": 1},
            {"event_type": "route_complete", "count": 4},
            {"event_type": "route_start", "count": 4},
            {"event_type": "service_complete", "count": 4},
            {"event_type": "service_start", "count": 4},
            {"event_type": "task_complete", "count": 8},
            {"event_type": "task_start", "count": 8},
        ],
    }
    assert export_record["scenarios"][0]["summary"]["total_resource_wait_time_s"] == 1.0
    assert export_record["scenarios"][1]["summary"]["total_route_distance"] == 2.0


def test_repeated_scenario_pack_runs_produce_identical_results():
    first_result = run_scenario_pack(PACK_PATH)
    second_result = run_scenario_pack(PACK_PATH)

    assert first_result.aggregate_summary == second_result.aggregate_summary
    assert first_result.scenario_results == second_result.scenario_results
    assert export_scenario_pack_json(first_result) == export_scenario_pack_json(second_result)


def test_scenario_pack_export_matches_golden_fixture_exactly():
    result = run_scenario_pack(PACK_PATH)
    export_json = export_scenario_pack_json(result)

    assert json.loads(export_json) == json.loads(GOLDEN_PATH.read_text())
    assert export_json == GOLDEN_PATH.read_text()
