from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.io.scenario_pack_runner import (
    ScenarioPackAggregateSummary,
    aggregate_summary_to_dict,
    build_scenario_pack_export,
    discover_scenario_pack_paths,
    run_scenario_pack,
)
from autonomous_ops_sim.research.wrapper import (
    InteractionExperimentRun,
    InteractionExperimentSpec,
    ScenarioExperimentRunner,
    build_interaction_experiment_export,
)
from autonomous_ops_sim.simulation.metrics import TraceEventCount


RESEARCH_COMPARISON_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ScenarioPackExperimentResult:
    """Stable result surface for one experiment evaluated across a scenario pack."""

    experiment_name: str
    scenario_runs: tuple[InteractionExperimentRun, ...]
    aggregate_summary: ScenarioPackAggregateSummary


@dataclass(frozen=True)
class ScenarioPackComparisonResult:
    """Stable result surface for one deterministic research pack comparison."""

    pack_directory: str
    baseline_pack_export: dict[str, Any]
    experiment_results: tuple[ScenarioPackExperimentResult, ...]


def compare_interaction_experiments_on_scenario_pack(
    pack_directory: str | Path,
    experiments: tuple[InteractionExperimentSpec, ...]
    | list[InteractionExperimentSpec],
) -> ScenarioPackComparisonResult:
    """Evaluate named interaction experiments across a deterministic scenario pack."""

    pack_root = Path(pack_directory)
    scenario_paths = discover_scenario_pack_paths(pack_root)
    baseline_pack_result = run_scenario_pack(pack_root)
    experiment_results = tuple(
        _run_experiment_for_pack(
            pack_root=pack_root,
            scenario_paths=scenario_paths,
            experiment=experiment,
        )
        for experiment in experiments
    )
    return ScenarioPackComparisonResult(
        pack_directory=pack_root.as_posix(),
        baseline_pack_export=build_scenario_pack_export(baseline_pack_result),
        experiment_results=experiment_results,
    )


def build_scenario_pack_comparison_export(
    result: ScenarioPackComparisonResult,
) -> dict[str, Any]:
    """Return a stable export for one scenario-pack research comparison."""

    return {
        "schema_version": RESEARCH_COMPARISON_SCHEMA_VERSION,
        "pack_directory": result.pack_directory,
        "baseline_pack": result.baseline_pack_export,
        "experiments": [
            {
                "experiment_name": experiment_result.experiment_name,
                "aggregate_summary": aggregate_summary_to_dict(
                    experiment_result.aggregate_summary
                ),
                "scenarios": [
                    build_interaction_experiment_export(run)
                    for run in experiment_result.scenario_runs
                ],
            }
            for experiment_result in result.experiment_results
        ],
    }


def export_scenario_pack_comparison_json(
    result: ScenarioPackComparisonResult,
) -> str:
    """Return deterministic JSON for one scenario-pack research comparison."""

    return json.dumps(
        build_scenario_pack_comparison_export(result),
        indent=2,
        sort_keys=True,
    ) + "\n"


def _run_experiment_for_pack(
    *,
    pack_root: Path,
    scenario_paths: tuple[Path, ...],
    experiment: InteractionExperimentSpec,
) -> ScenarioPackExperimentResult:
    scenario_runs = tuple(
        _run_experiment_for_scenario(
            pack_root=pack_root,
            scenario_path=scenario_path,
            experiment=experiment,
        )
        for scenario_path in scenario_paths
    )
    return ScenarioPackExperimentResult(
        experiment_name=experiment.name,
        scenario_runs=scenario_runs,
        aggregate_summary=_aggregate_experiment_runs(scenario_runs),
    )


def _run_experiment_for_scenario(
    *,
    pack_root: Path,
    scenario_path: Path,
    experiment: InteractionExperimentSpec,
) -> InteractionExperimentRun:
    scenario = load_scenario(scenario_path)
    runner = ScenarioExperimentRunner(scenario)
    return runner.run_experiment(
        experiment,
        scenario_path=scenario_path.relative_to(pack_root).as_posix(),
    )


def _aggregate_experiment_runs(
    scenario_runs: tuple[InteractionExperimentRun, ...],
) -> ScenarioPackAggregateSummary:
    event_counts: Counter[str] = Counter()
    for scenario_run in scenario_runs:
        event_counts.update(
            {
                event_count.event_type: event_count.count
                for event_count in scenario_run.summary.event_counts
            }
        )

    scenario_paths = tuple(
        _require_scenario_path(scenario_run) for scenario_run in scenario_runs
    )
    return ScenarioPackAggregateSummary(
        scenario_count=len(scenario_runs),
        scenario_names=tuple(scenario_run.scenario_name for scenario_run in scenario_runs),
        scenario_paths=scenario_paths,
        total_final_time_s=sum(scenario_run.summary.final_time_s for scenario_run in scenario_runs),
        total_trace_event_count=sum(
            scenario_run.summary.trace_event_count for scenario_run in scenario_runs
        ),
        total_route_count=sum(scenario_run.summary.route_count for scenario_run in scenario_runs),
        total_completed_job_count=sum(
            scenario_run.summary.completed_job_count for scenario_run in scenario_runs
        ),
        total_completed_task_count=sum(
            scenario_run.summary.completed_task_count for scenario_run in scenario_runs
        ),
        total_edge_traversal_count=sum(
            scenario_run.summary.edge_traversal_count for scenario_run in scenario_runs
        ),
        total_node_arrival_count=sum(
            scenario_run.summary.node_arrival_count for scenario_run in scenario_runs
        ),
        total_route_distance=sum(
            scenario_run.summary.total_route_distance for scenario_run in scenario_runs
        ),
        total_service_time_s=sum(
            scenario_run.summary.total_service_time_s for scenario_run in scenario_runs
        ),
        total_resource_wait_time_s=sum(
            scenario_run.summary.total_resource_wait_time_s
            for scenario_run in scenario_runs
        ),
        total_conflict_wait_time_s=sum(
            scenario_run.summary.total_conflict_wait_time_s
            for scenario_run in scenario_runs
        ),
        event_counts=tuple(
            TraceEventCount(event_type=event_type, count=count)
            for event_type, count in sorted(event_counts.items())
        ),
    )


def _require_scenario_path(scenario_run: InteractionExperimentRun) -> str:
    if scenario_run.scenario_path is None:
        raise ValueError("Scenario pack experiments require a stable scenario_path.")
    return scenario_run.scenario_path
