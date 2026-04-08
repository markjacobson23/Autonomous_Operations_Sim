import json

from autonomous_ops_sim.simulation.scenario import Scenario


def format_scenario_summary(scenario: Scenario) -> str:
    """Return a deterministic, human-readable scenario summary."""

    map_params_json = json.dumps(scenario.map_spec.params, sort_keys=True)

    lines = [
        f"scenario: {scenario.name}",
        f"source: {scenario.source_path}",
        f"seed: {scenario.seed}",
        f"duration_s: {scenario.duration_s}",
        f"map_kind: {scenario.map_spec.kind}",
        f"map_params: {map_params_json}",
        f"vehicle_count: {len(scenario.vehicles)}",
    ]

    if scenario.execution is None:
        lines.append("execution: none")
    else:
        lines.extend(
            [
                f"execution: {scenario.execution.kind}",
                f"execution_vehicle_id: {scenario.execution.vehicle_id}",
                f"execution_job_id: {scenario.execution.job.id}",
                f"execution_task_count: {len(scenario.execution.job.tasks)}",
            ]
        )

    for index, vehicle in enumerate(scenario.vehicles):
        vehicle_type = vehicle.vehicle_type.name if vehicle.vehicle_type is not None else "none"
        lines.append(
            "vehicle["
            f"{index}] id={vehicle.id} "
            f"type={vehicle_type} "
            f"position={vehicle.position} "
            f"velocity={vehicle.velocity} "
            f"payload={vehicle.payload}/{vehicle.max_payload} "
            f"max_speed={vehicle.max_speed}"
        )

    return "\n".join(lines)
