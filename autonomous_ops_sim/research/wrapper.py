from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from autonomous_ops_sim.io.exports import metrics_summary_to_dict
from autonomous_ops_sim.io.scenario_loader import load_scenario
from autonomous_ops_sim.simulation import (
    ExecutionMetricsSummary,
    SimulationController,
    export_controlled_engine_json,
    summarize_engine_execution,
)
from autonomous_ops_sim.simulation.scenario import Scenario
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.visualization import (
    VisualizationInteraction,
    apply_interactions,
    build_visualization_state_from_controller,
    export_visualization_json,
    interaction_to_dict,
)


InteractionPolicy = Callable[
    [SimulationController],
    Sequence[VisualizationInteraction],
]


@dataclass(frozen=True)
class InteractionExperimentSpec:
    """Named deterministic interaction policy for research comparisons."""

    name: str
    policy: InteractionPolicy

    def build_interactions(
        self,
        controller: SimulationController,
    ) -> tuple[VisualizationInteraction, ...]:
        return tuple(self.policy(controller))


@dataclass(frozen=True)
class InteractionExperimentRun:
    """Stable result surface for one scenario-backed interaction experiment."""

    experiment_name: str
    scenario_name: str
    scenario_path: str | None
    interactions: tuple[VisualizationInteraction, ...]
    baseline_summary: ExecutionMetricsSummary
    summary: ExecutionMetricsSummary
    controlled_export_json: str
    visualization_export_json: str


class ScenarioExperimentRunner:
    """Run one narrow deterministic interaction experiment on a scenario."""

    def __init__(self, scenario: Scenario):
        self._scenario = scenario

    @classmethod
    def from_path(cls, scenario_path: str | Path) -> ScenarioExperimentRunner:
        return cls(load_scenario(scenario_path))

    @property
    def scenario(self) -> Scenario:
        return self._scenario

    def run_interactions(
        self,
        *,
        experiment_name: str,
        interactions: Sequence[VisualizationInteraction],
        scenario_path: str | None = None,
    ) -> InteractionExperimentRun:
        execution_result = execute_scenario(self.scenario)
        controller = SimulationController(execution_result.engine)
        normalized_interactions = tuple(interactions)
        apply_interactions(controller, normalized_interactions)
        summary = summarize_engine_execution(controller.engine)
        visualization_state = build_visualization_state_from_controller(controller)
        return InteractionExperimentRun(
            experiment_name=experiment_name,
            scenario_name=self.scenario.name,
            scenario_path=scenario_path or _default_scenario_path(self.scenario),
            interactions=normalized_interactions,
            baseline_summary=execution_result.summary,
            summary=summary,
            controlled_export_json=export_controlled_engine_json(
                controller,
                summary=summary,
            ),
            visualization_export_json=export_visualization_json(visualization_state),
        )

    def run_experiment(
        self,
        experiment: InteractionExperimentSpec,
        *,
        scenario_path: str | None = None,
    ) -> InteractionExperimentRun:
        execution_result = execute_scenario(self.scenario)
        controller = SimulationController(execution_result.engine)
        interactions = experiment.build_interactions(controller)
        apply_interactions(controller, interactions)
        summary = summarize_engine_execution(controller.engine)
        visualization_state = build_visualization_state_from_controller(controller)
        return InteractionExperimentRun(
            experiment_name=experiment.name,
            scenario_name=self.scenario.name,
            scenario_path=scenario_path or _default_scenario_path(self.scenario),
            interactions=interactions,
            baseline_summary=execution_result.summary,
            summary=summary,
            controlled_export_json=export_controlled_engine_json(
                controller,
                summary=summary,
            ),
            visualization_export_json=export_visualization_json(visualization_state),
        )


def build_interaction_experiment_export(
    run: InteractionExperimentRun,
) -> dict[str, Any]:
    """Return a stable export for one scenario interaction experiment."""

    return {
        "experiment_name": run.experiment_name,
        "scenario_name": run.scenario_name,
        "scenario_path": run.scenario_path,
        "interactions": [
            interaction_to_dict(interaction) for interaction in run.interactions
        ],
        "baseline_summary": metrics_summary_to_dict(run.baseline_summary),
        "summary": metrics_summary_to_dict(run.summary),
        "controlled_execution": json.loads(run.controlled_export_json),
        "visualization": json.loads(run.visualization_export_json),
    }


def export_interaction_experiment_json(
    run: InteractionExperimentRun,
) -> str:
    """Return deterministic JSON for one scenario interaction experiment."""

    return json.dumps(
        build_interaction_experiment_export(run),
        indent=2,
        sort_keys=True,
    ) + "\n"


def _default_scenario_path(scenario: Scenario) -> str | None:
    if scenario.source_path is None:
        return None
    return scenario.source_path.as_posix()
