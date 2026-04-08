import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autonomous_ops_sim.io.exports import metrics_summary_to_dict
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation.metrics import ExecutionMetricsSummary, TraceEventCount
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario


SCENARIO_PACK_EXPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ScenarioPackScenarioResult:
    """Stable result surface for one scenario within a deterministic pack run."""

    scenario_name: str
    relative_path: str
    summary: ExecutionMetricsSummary
    export_json: str


@dataclass(frozen=True)
class ScenarioPackAggregateSummary:
    """Stable aggregate metrics for a deterministic scenario pack run."""

    scenario_count: int
    scenario_names: tuple[str, ...]
    scenario_paths: tuple[str, ...]
    total_final_time_s: float
    total_trace_event_count: int
    total_route_count: int
    total_completed_job_count: int
    total_completed_task_count: int
    total_edge_traversal_count: int
    total_node_arrival_count: int
    total_route_distance: float
    total_service_time_s: float
    total_resource_wait_time_s: float
    total_conflict_wait_time_s: float
    event_counts: tuple[TraceEventCount, ...]


@dataclass(frozen=True)
class ScenarioPackResult:
    """Stable result surface for one deterministic scenario pack execution."""

    scenario_results: tuple[ScenarioPackScenarioResult, ...]
    aggregate_summary: ScenarioPackAggregateSummary


def discover_scenario_pack_paths(pack_directory: str | Path) -> tuple[Path, ...]:
    """Return pack scenario files in deterministic filename order."""

    clean_directory = Path(pack_directory)
    if not clean_directory.exists():
        raise ValueError(f"Scenario pack directory does not exist: {clean_directory}")
    if not clean_directory.is_dir():
        raise ValueError(f"Scenario pack path must be a directory: {clean_directory}")

    scenario_paths = tuple(
        sorted(
            (
                path
                for path in clean_directory.iterdir()
                if path.is_file() and path.suffix == ".json"
            ),
            key=lambda path: path.name,
        )
    )
    if not scenario_paths:
        raise ValueError(
            f"Scenario pack directory does not contain any .json files: {clean_directory}"
        )
    return scenario_paths


def run_scenario_pack(pack_directory: str | Path) -> ScenarioPackResult:
    """Execute a deterministic directory-backed scenario pack."""

    pack_root = Path(pack_directory)
    scenario_paths = discover_scenario_pack_paths(pack_root)
    scenario_results = tuple(
        _run_one_scenario(pack_root=pack_root, scenario_path=scenario_path)
        for scenario_path in scenario_paths
    )
    return ScenarioPackResult(
        scenario_results=scenario_results,
        aggregate_summary=_aggregate_scenario_results(scenario_results),
    )


def build_scenario_pack_export(result: ScenarioPackResult) -> dict[str, Any]:
    """Return a stable structured export for one scenario pack run."""

    return {
        "schema_version": SCENARIO_PACK_EXPORT_SCHEMA_VERSION,
        "aggregate_summary": aggregate_summary_to_dict(result.aggregate_summary),
        "scenarios": [
            {
                "scenario_name": scenario_result.scenario_name,
                "scenario_path": scenario_result.relative_path,
                "summary": metrics_summary_to_dict(scenario_result.summary),
                "execution": json.loads(scenario_result.export_json),
            }
            for scenario_result in result.scenario_results
        ],
    }


def export_scenario_pack_json(result: ScenarioPackResult) -> str:
    """Return a deterministic JSON export for one scenario pack run."""

    return json.dumps(
        build_scenario_pack_export(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def aggregate_summary_to_dict(
    summary: ScenarioPackAggregateSummary,
) -> dict[str, Any]:
    """Convert a pack aggregate summary into a JSON-ready stable record."""

    return {
        "scenario_count": summary.scenario_count,
        "scenario_names": list(summary.scenario_names),
        "scenario_paths": list(summary.scenario_paths),
        "total_final_time_s": summary.total_final_time_s,
        "total_trace_event_count": summary.total_trace_event_count,
        "total_route_count": summary.total_route_count,
        "total_completed_job_count": summary.total_completed_job_count,
        "total_completed_task_count": summary.total_completed_task_count,
        "total_edge_traversal_count": summary.total_edge_traversal_count,
        "total_node_arrival_count": summary.total_node_arrival_count,
        "total_route_distance": summary.total_route_distance,
        "total_service_time_s": summary.total_service_time_s,
        "total_resource_wait_time_s": summary.total_resource_wait_time_s,
        "total_conflict_wait_time_s": summary.total_conflict_wait_time_s,
        "event_counts": [
            {
                "event_type": event_count.event_type,
                "count": event_count.count,
            }
            for event_count in summary.event_counts
        ],
    }


def _run_one_scenario(
    *,
    pack_root: Path,
    scenario_path: Path,
) -> ScenarioPackScenarioResult:
    scenario = load_scenario(scenario_path)
    execution_result = execute_scenario(scenario)
    return ScenarioPackScenarioResult(
        scenario_name=scenario.name,
        relative_path=scenario_path.relative_to(pack_root).as_posix(),
        summary=execution_result.summary,
        export_json=execution_result.export_json,
    )


def _aggregate_scenario_results(
    scenario_results: tuple[ScenarioPackScenarioResult, ...],
) -> ScenarioPackAggregateSummary:
    event_counts: Counter[str] = Counter()
    for scenario_result in scenario_results:
        event_counts.update(
            {
                event_count.event_type: event_count.count
                for event_count in scenario_result.summary.event_counts
            }
        )

    return ScenarioPackAggregateSummary(
        scenario_count=len(scenario_results),
        scenario_names=tuple(
            scenario_result.scenario_name for scenario_result in scenario_results
        ),
        scenario_paths=tuple(
            scenario_result.relative_path for scenario_result in scenario_results
        ),
        total_final_time_s=sum(
            scenario_result.summary.final_time_s
            for scenario_result in scenario_results
        ),
        total_trace_event_count=sum(
            scenario_result.summary.trace_event_count
            for scenario_result in scenario_results
        ),
        total_route_count=sum(
            scenario_result.summary.route_count for scenario_result in scenario_results
        ),
        total_completed_job_count=sum(
            scenario_result.summary.completed_job_count
            for scenario_result in scenario_results
        ),
        total_completed_task_count=sum(
            scenario_result.summary.completed_task_count
            for scenario_result in scenario_results
        ),
        total_edge_traversal_count=sum(
            scenario_result.summary.edge_traversal_count
            for scenario_result in scenario_results
        ),
        total_node_arrival_count=sum(
            scenario_result.summary.node_arrival_count
            for scenario_result in scenario_results
        ),
        total_route_distance=sum(
            scenario_result.summary.total_route_distance
            for scenario_result in scenario_results
        ),
        total_service_time_s=sum(
            scenario_result.summary.total_service_time_s
            for scenario_result in scenario_results
        ),
        total_resource_wait_time_s=sum(
            scenario_result.summary.total_resource_wait_time_s
            for scenario_result in scenario_results
        ),
        total_conflict_wait_time_s=sum(
            scenario_result.summary.total_conflict_wait_time_s
            for scenario_result in scenario_results
        ),
        event_counts=tuple(
            TraceEventCount(event_type=event_type, count=count)
            for event_type, count in sorted(event_counts.items())
        ),
    )
