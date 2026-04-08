import json

from autonomous_ops_sim.simulation.scenario import (
    DispatchVehicleJobsExecutionSpec,
    Scenario,
    SingleVehicleJobExecutionSpec,
)


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
        f"resource_count: {len(scenario.resources)}",
        f"blocked_edge_count: {len(scenario.world_state.blocked_edges)}",
    ]

    if scenario.dispatcher is None:
        lines.append("dispatcher: none")
    else:
        lines.append(f"dispatcher: {scenario.dispatcher.kind}")

    if scenario.execution is None:
        lines.append("execution: none")
    elif isinstance(scenario.execution, SingleVehicleJobExecutionSpec):
        lines.extend(
            [
                f"execution: {scenario.execution.kind}",
                f"execution_vehicle_id: {scenario.execution.vehicle_id}",
                f"execution_job_id: {scenario.execution.job.id}",
                f"execution_task_count: {len(scenario.execution.job.tasks)}",
            ]
        )
    elif isinstance(scenario.execution, DispatchVehicleJobsExecutionSpec):
        lines.extend(
            [
                f"execution: {scenario.execution.kind}",
                f"execution_vehicle_id: {scenario.execution.vehicle_id}",
                f"execution_job_count: {len(scenario.execution.jobs)}",
            ]
        )
    else:
        raise ValueError(
            f"Unsupported scenario execution type: {type(scenario.execution)!r}"
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
