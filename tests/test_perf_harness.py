import json

import pytest

from autonomous_ops_sim.cli import main
from autonomous_ops_sim.perf import (
    BENCHMARK_SCHEMA_VERSION,
    BenchmarkCase,
    export_benchmark_suite_json,
    run_benchmark_case,
    run_benchmark_suite,
    run_default_benchmark_suite,
)


class FakeClock:
    def __init__(self, values: tuple[int, ...]) -> None:
        self._values = list(values)

    def now_ns(self) -> int:
        if not self._values:
            raise AssertionError("fake clock exhausted")
        return self._values.pop(0)


def test_benchmark_case_uses_repeatable_structural_output_and_timing_summary() -> None:
    counter = {"calls": 0}

    def workload() -> dict[str, object]:
        counter["calls"] += 1
        return {
            "stable_result": {
                "call_count": 99,
                "values": [1, 2, 3],
            }
        }

    result = run_benchmark_case(
        BenchmarkCase(
            name="stable_case",
            category="test",
            repetitions=3,
            warmup_iterations=1,
            config={"size": 3, "kind": "demo"},
            workload=workload,
        ),
        clock=FakeClock((100, 130, 200, 260, 300, 390)),
    )

    assert counter["calls"] == 4
    assert result.name == "stable_case"
    assert result.output_summary == {"stable_result": {"call_count": 99, "values": [1, 2, 3]}}
    assert result.timing.durations_ns == (30, 60, 90)
    assert result.timing.total_duration_ns == 180
    assert result.timing.average_duration_ns == 60


def test_benchmark_case_rejects_inconsistent_structural_output() -> None:
    counter = {"calls": 0}

    def workload() -> dict[str, object]:
        counter["calls"] += 1
        return {"call_count": counter["calls"]}

    with pytest.raises(
        RuntimeError,
        match="produced inconsistent structural output",
    ):
        run_benchmark_case(
            BenchmarkCase(
                name="unstable_case",
                category="test",
                repetitions=2,
                warmup_iterations=0,
                config={"kind": "demo"},
                workload=workload,
            ),
            clock=FakeClock((10, 15, 20, 30)),
        )


def test_benchmark_suite_json_format_is_deterministic_with_fake_clock() -> None:
    suite = (
        BenchmarkCase(
            name="case_a",
            category="alpha",
            repetitions=2,
            warmup_iterations=0,
            config={"size": 2},
            workload=lambda: {"result": {"value": 7}},
        ),
        BenchmarkCase(
            name="case_b",
            category="beta",
            repetitions=1,
            warmup_iterations=0,
            config={"size": 1},
            workload=lambda: {"result": {"value": 11}},
        ),
    )

    first_json = export_benchmark_suite_json(
        run_benchmark_suite(
            "demo_suite",
            suite,
            clock=FakeClock((0, 5, 10, 20, 50, 80)),
        )
    )
    second_json = export_benchmark_suite_json(
        run_benchmark_suite(
            "demo_suite",
            suite,
            clock=FakeClock((0, 5, 10, 20, 50, 80)),
        )
    )

    assert first_json == second_json
    export_record = json.loads(first_json)
    assert export_record["schema_version"] == BENCHMARK_SCHEMA_VERSION
    assert [case["name"] for case in export_record["case_results"]] == ["case_a", "case_b"]
    assert export_record["case_results"][0]["timing"]["durations_ns"] == [5, 10]
    assert export_record["case_results"][1]["output_summary"] == {"result": {"value": 11}}


def test_default_benchmark_suite_produces_structurally_consistent_results() -> None:
    first_result = run_default_benchmark_suite(repetitions=1, warmup_iterations=0)
    second_result = run_default_benchmark_suite(repetitions=1, warmup_iterations=0)

    first_record = json.loads(export_benchmark_suite_json(first_result))
    second_record = json.loads(export_benchmark_suite_json(second_result))

    assert first_record["schema_version"] == BENCHMARK_SCHEMA_VERSION
    assert [case["name"] for case in first_record["case_results"]] == [
        "routing_grid_paths",
        "reservation_departure_scan",
        "scenario_execution_graph_map",
        "scenario_pack_execution_baseline",
        "visualization_export_graph_map",
        "live_sync_export_session",
    ]
    assert [case["name"] for case in second_record["case_results"]] == [
        case["name"] for case in first_record["case_results"]
    ]
    assert [case["config"] for case in second_record["case_results"]] == [
        case["config"] for case in first_record["case_results"]
    ]
    assert [case["output_summary"] for case in second_record["case_results"]] == [
        case["output_summary"] for case in first_record["case_results"]
    ]


def test_cli_benchmark_emits_json_results(capsys) -> None:
    exit_code = main(["benchmark", "--repetitions", "1", "--warmup-iterations", "0"])

    captured = capsys.readouterr()
    export_record = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert export_record["schema_version"] == BENCHMARK_SCHEMA_VERSION
    assert export_record["suite_name"] == "step_29_baseline"
    assert len(export_record["case_results"]) == 6
