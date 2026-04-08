import json
from pathlib import Path

from autonomous_ops_sim.research import (
    InteractionExperimentSpec,
    ScenarioExperimentRunner,
    compare_interaction_experiments_on_scenario_pack,
    export_interaction_experiment_json,
    export_scenario_pack_comparison_json,
)
from autonomous_ops_sim.simulation import SimulationController
from autonomous_ops_sim.visualization import AssignDestinationInteraction


PACK_PATH = Path("tests/fixtures/scenario_pack")
SCENARIO_PATH = PACK_PATH / "02_single_vehicle_job.json"
GOLDEN_PATH = Path(__file__).parent / "golden" / "step_22_research_experiment_export.json"


def park_vehicle_at_origin(
    controller: SimulationController,
) -> tuple[AssignDestinationInteraction, ...]:
    vehicle = controller.engine.vehicles[0]
    target_node_id = min(controller.engine.map.get_all_node_ids())
    return (
        AssignDestinationInteraction(
            vehicle_id=vehicle.id,
            destination_node_id=target_node_id,
        ),
    )


def park_vehicle_at_max_node(
    controller: SimulationController,
) -> tuple[AssignDestinationInteraction, ...]:
    vehicle = controller.engine.vehicles[0]
    target_node_id = max(controller.engine.map.get_all_node_ids())
    return (
        AssignDestinationInteraction(
            vehicle_id=vehicle.id,
            destination_node_id=target_node_id,
        ),
    )


def test_scenario_experiment_runner_is_deterministic() -> None:
    runner = ScenarioExperimentRunner.from_path(SCENARIO_PATH)
    experiment = InteractionExperimentSpec(
        name="park_at_origin",
        policy=park_vehicle_at_origin,
    )

    first_run = runner.run_experiment(experiment)
    second_run = runner.run_experiment(experiment)

    assert first_run == second_run
    assert first_run.baseline_summary.final_time_s == 6.0
    assert first_run.summary.final_time_s == 8.0
    assert export_interaction_experiment_json(first_run) == export_interaction_experiment_json(
        second_run
    )


def test_scenario_pack_comparison_is_deterministic() -> None:
    experiments = (
        InteractionExperimentSpec(
            name="park_at_origin",
            policy=park_vehicle_at_origin,
        ),
        InteractionExperimentSpec(
            name="park_at_max_node",
            policy=park_vehicle_at_max_node,
        ),
    )

    first_result = compare_interaction_experiments_on_scenario_pack(
        PACK_PATH,
        experiments,
    )
    second_result = compare_interaction_experiments_on_scenario_pack(
        PACK_PATH,
        experiments,
    )

    assert first_result == second_result
    assert [entry["scenario_path"] for entry in first_result.baseline_pack_export["scenarios"]] == [
        "01_dispatch_resources_blocked_edges.json",
        "02_single_vehicle_job.json",
    ]
    assert [experiment_result.experiment_name for experiment_result in first_result.experiment_results] == [
        "park_at_origin",
        "park_at_max_node",
    ]
    assert [
        experiment_result.aggregate_summary.scenario_count
        for experiment_result in first_result.experiment_results
    ] == [2, 2]
    assert export_scenario_pack_comparison_json(
        first_result
    ) == export_scenario_pack_comparison_json(second_result)


def test_research_experiment_export_matches_golden_fixture() -> None:
    runner = ScenarioExperimentRunner.from_path(SCENARIO_PATH)
    experiment = InteractionExperimentSpec(
        name="park_at_max_node",
        policy=park_vehicle_at_max_node,
    )

    run = runner.run_experiment(experiment)
    export_json = export_interaction_experiment_json(run)

    assert json.loads(export_json) == json.loads(GOLDEN_PATH.read_text())
    assert export_json == GOLDEN_PATH.read_text()
