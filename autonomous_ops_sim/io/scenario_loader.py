import json
import math
from pathlib import Path

from autonomous_ops_sim.core.node import NodeType
from autonomous_ops_sim.simulation.scenario import (
    DispatchVehicleJobQueueExecutionSpec,
    BlockedEdgeSpec,
    DispatchVehicleJobsExecutionSpec,
    DispatcherSpec,
    ExecutionSpec,
    JobSpec,
    LoadTaskSpec,
    MapSpec,
    MoveTaskSpec,
    ResourceSpec,
    Scenario,
    SingleVehicleJobExecutionSpec,
    UnloadTaskSpec,
    VehicleSpec,
    WorldStateSpec,
)
from autonomous_ops_sim.vehicles.vehicle import VehicleType


def load_scenario(path: str | Path) -> Scenario:
    """returns a parsed scenario from a JSON file."""

    clean_path = Path(path)
    data = _read_json(clean_path)
    return _parse_scenario(data, source_path=clean_path)


def _read_json(path: Path) -> dict[str, object]:
    """reads a JSON file and returns the raw data."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Scenario file must contain a top-level JSON object.")

    return data


def _parse_scenario(
    data: dict[str, object],
    source_path: Path | None = None,
) -> Scenario:
    """parses raw scenario data into a Scenario object."""

    # Validate the required fields exist.
    required_keys = {"name", "seed", "duration_s", "map", "vehicles"}
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Scenario is missing required field(s): {missing_str}")

    name = data["name"]
    seed = data["seed"]
    duration_s = data["duration_s"]
    map_data = data["map"]
    vehicles_data = data["vehicles"]
    resources_data = data.get("resources", [])
    world_state_data = data.get("world_state")
    dispatcher_data = data.get("dispatcher")
    execution_data = data.get("execution")

    if not isinstance(name, str):
        raise ValueError("Scenario 'name' must be a string.")
    if not isinstance(seed, int):
        raise ValueError("Scenario 'seed' must be an int.")
    if not isinstance(duration_s, (int, float)):
        raise ValueError("Scenario 'duration_s' must be a number.")
    if float(duration_s) <= 0:
        raise ValueError("Scenario 'duration_s' must be positive.")
    if not isinstance(map_data, dict):
        raise ValueError("Scenario 'map' must be an object.")
    if not isinstance(vehicles_data, list):
        raise ValueError("Scenario 'vehicles' must be a list.")
    if not isinstance(resources_data, list):
        raise ValueError("Scenario 'resources' must be a list if provided.")
    if world_state_data is not None and not isinstance(world_state_data, dict):
        raise ValueError("Scenario 'world_state' must be an object if provided.")
    if dispatcher_data is not None and not isinstance(dispatcher_data, dict):
        raise ValueError("Scenario 'dispatcher' must be an object if provided.")
    if execution_data is not None and not isinstance(execution_data, dict):
        raise ValueError("Scenario 'execution' must be an object if provided.")

    vehicles = [_parse_vehicle_spec(v) for v in vehicles_data]
    resources = tuple(_parse_resource_spec(resource) for resource in resources_data)
    world_state = (
        WorldStateSpec()
        if world_state_data is None
        else _parse_world_state_spec(world_state_data)
    )
    dispatcher = (
        None
        if dispatcher_data is None
        else _parse_dispatcher_spec(dispatcher_data)
    )
    execution = (
        None
        if execution_data is None
        else _parse_execution_spec(execution_data)
    )

    if execution is not None:
        vehicle_ids = {vehicle.id for vehicle in vehicles}
        if execution.vehicle_id not in vehicle_ids:
            raise ValueError(
                "Scenario execution 'vehicle_id' must reference a configured vehicle."
            )

    resource_ids = {resource.resource_id for resource in resources}
    if len(resource_ids) != len(resources):
        raise ValueError("Scenario resource ids must be unique.")

    referenced_resource_ids = _collect_referenced_resource_ids(execution)
    unknown_resource_ids = referenced_resource_ids - resource_ids
    if unknown_resource_ids:
        unknown_str = ", ".join(sorted(unknown_resource_ids))
        raise ValueError(
            "Scenario task resource_id values must reference configured resources: "
            f"{unknown_str}"
        )

    if isinstance(
        execution,
        (DispatchVehicleJobsExecutionSpec, DispatchVehicleJobQueueExecutionSpec),
    ) and dispatcher is None:
        raise ValueError(
            "Scenario dispatch execution requires a configured 'dispatcher' section."
        )
    if dispatcher is not None and not isinstance(
        execution,
        (DispatchVehicleJobsExecutionSpec, DispatchVehicleJobQueueExecutionSpec),
    ):
        raise ValueError(
            "Scenario 'dispatcher' is only supported with dispatch-based execution."
        )

    return Scenario(
        name=name,
        seed=seed,
        duration_s=float(duration_s),
        map_spec=_parse_map_spec(map_data),
        vehicles=vehicles,
        resources=resources,
        world_state=world_state,
        dispatcher=dispatcher,
        execution=execution,
        source_path=source_path,
    )


def _parse_map_spec(data: dict[str, object]) -> MapSpec:
    """parses raw map spec data into a MapSpec object."""

    # Validate the required fields exist.
    required_keys = {"kind", "params"}
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Map spec is missing required field(s): {missing_str}")

    kind = data["kind"]
    params = data["params"]

    if not isinstance(kind, str):
        raise ValueError("Map 'kind' must be a string.")
    if not isinstance(params, dict):
        raise ValueError("Map 'params' must be an object.")

    if kind == "grid":
        _validate_grid_map_params(params)
    elif kind == "graph":
        _validate_graph_map_params(params)
    else:
        raise ValueError(f"Unsupported map kind: {kind!r}")

    return MapSpec(kind=kind, params=params)


def _validate_grid_map_params(params: dict[str, object]) -> None:
    grid_size = params.get("grid_size")
    if not isinstance(grid_size, int):
        raise ValueError("Grid map 'params.grid_size' must be an int.")
    if grid_size <= 0:
        raise ValueError("Grid map 'params.grid_size' must be positive.")


def _validate_graph_map_params(params: dict[str, object]) -> None:
    nodes = params.get("nodes")
    edges = params.get("edges")

    if not isinstance(nodes, list):
        raise ValueError("Graph map 'params.nodes' must be a list.")
    if not nodes:
        raise ValueError("Graph map 'params.nodes' must not be empty.")
    if not isinstance(edges, list):
        raise ValueError("Graph map 'params.edges' must be a list.")
    if not edges:
        raise ValueError("Graph map 'params.edges' must not be empty.")

    node_ids: set[int] = set()
    node_positions: set[tuple[float, float, float]] = set()

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"Graph map node[{index}] must be an object.")
        required_keys = {"id", "position"}
        missing = required_keys - node.keys()
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(
                f"Graph map node[{index}] is missing required field(s): {missing_str}"
            )

        node_id = node["id"]
        position = node["position"]
        node_type = node.get("node_type")

        if not isinstance(node_id, int):
            raise ValueError(f"Graph map node[{index}].id must be an int.")
        if node_id in node_ids:
            raise ValueError("Graph map node ids must be unique.")
        node_ids.add(node_id)

        parsed_position = _parse_position_value(
            position,
            context=f"Graph map node[{index}].position",
        )
        if parsed_position in node_positions:
            raise ValueError("Graph map node positions must be unique.")
        node_positions.add(parsed_position)

        if node_type is not None:
            if not isinstance(node_type, str):
                raise ValueError(
                    f"Graph map node[{index}].node_type must be a string if provided."
                )
            if node_type not in NodeType.__members__:
                allowed = ", ".join(member.name for member in NodeType)
                raise ValueError(
                    f"Graph map node[{index}].node_type must be one of: {allowed}"
                )

    edge_ids: set[int] = set()
    edge_pairs: set[tuple[int, int]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError(f"Graph map edge[{index}] must be an object.")
        required_keys = {
            "id",
            "start_node_id",
            "end_node_id",
            "distance",
            "speed_limit",
        }
        missing = required_keys - edge.keys()
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(
                f"Graph map edge[{index}] is missing required field(s): {missing_str}"
            )

        edge_id = edge["id"]
        start_node_id = edge["start_node_id"]
        end_node_id = edge["end_node_id"]
        distance = edge["distance"]
        speed_limit = edge["speed_limit"]

        if not isinstance(edge_id, int):
            raise ValueError(f"Graph map edge[{index}].id must be an int.")
        if edge_id in edge_ids:
            raise ValueError("Graph map edge ids must be unique.")
        edge_ids.add(edge_id)

        if not isinstance(start_node_id, int) or not isinstance(end_node_id, int):
            raise ValueError(
                f"Graph map edge[{index}] start_node_id/end_node_id must be ints."
            )
        if start_node_id not in node_ids or end_node_id not in node_ids:
            raise ValueError(
                f"Graph map edge[{index}] must reference configured node ids."
            )
        if start_node_id == end_node_id:
            raise ValueError(f"Graph map edge[{index}] cannot connect a node to itself.")

        edge_pair = (start_node_id, end_node_id)
        if edge_pair in edge_pairs:
            raise ValueError("Graph map edges must be unique by start/end node pair.")
        edge_pairs.add(edge_pair)

        if not isinstance(distance, (int, float)) or float(distance) <= 0:
            raise ValueError(f"Graph map edge[{index}].distance must be positive.")
        if not isinstance(speed_limit, (int, float)) or float(speed_limit) <= 0:
            raise ValueError(f"Graph map edge[{index}].speed_limit must be positive.")


def _parse_vehicle_spec(data: object) -> VehicleSpec:
    """parses raw vehicle spec data into a VehicleSpec object."""

    # Validate the required fields exist.
    if not isinstance(data, dict):
        raise ValueError("Each vehicle entry must be an object.")

    required_keys = {
        "id",
        "position",
        "velocity",
        "payload",
        "max_payload",
        "max_speed",
    }
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Vehicle spec is missing required fields: {missing_str}")

    vehicle_id = data["id"]
    position = data["position"]
    velocity = data["velocity"]
    payload = data["payload"]
    max_payload = data["max_payload"]
    max_speed = data["max_speed"]
    vehicle_type_raw = data.get("vehicle_type")

    if not isinstance(vehicle_id, int):
        raise ValueError("Vehicle 'id' must be an int.")

    if not isinstance(position, list):
        raise ValueError("Vehicle 'position' must be a list.")
    if len(position) != 3:
        raise ValueError("Vehicle 'position' must have exactly 3 coordinates.")
    if not all(isinstance(coord, (int, float)) for coord in position):
        raise ValueError("Vehicle 'position' coordinates must be numeric.")

    for field_name, value in (
        ("velocity", velocity),
        ("payload", payload),
        ("max_payload", max_payload),
        ("max_speed", max_speed),
    ):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Vehicle '{field_name}' must be numeric.")

    if float(payload) < 0:
        raise ValueError("Vehicle 'payload' cannot be negative.")
    if float(max_payload) < 0:
        raise ValueError("Vehicle 'max_payload' cannot be negative.")
    if float(max_speed) <= 0:
        raise ValueError("Vehicle 'max_speed' must be positive.")


    if vehicle_type_raw is None:
        vehicle_type = None
    else:
        if not isinstance(vehicle_type_raw, str):
            raise ValueError("Vehicle 'vehicle_type' must be a string if provided.")
        try:
            vehicle_type = VehicleType[vehicle_type_raw]
        except KeyError as exc:
            raise ValueError(
                f"Vehicle 'vehicle_type' must be one of: "
                f"{', '.join(member.name for member in VehicleType)}"
            ) from exc

    parsed_position = (
        float(position[0]),
        float(position[1]),
        float(position[2]),
    )

    return VehicleSpec(
        id=vehicle_id,
        position=parsed_position,
        velocity=float(velocity),
        payload=float(payload),
        max_payload=float(max_payload),
        max_speed=float(max_speed),
        vehicle_type=vehicle_type,
    )


def _parse_execution_spec(data: dict[str, object]) -> ExecutionSpec:
    required_keys = {"kind", "vehicle_id"}
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(
            f"Scenario execution is missing required field(s): {missing_str}"
        )

    kind = data["kind"]
    vehicle_id = data["vehicle_id"]

    if kind not in {
        "single_vehicle_job",
        "dispatch_vehicle_jobs",
        "dispatch_vehicle_job_queue",
    }:
        raise ValueError(f"Unsupported execution kind: {kind!r}")
    if not isinstance(vehicle_id, int):
        raise ValueError("Scenario execution 'vehicle_id' must be an int.")

    if kind == "single_vehicle_job":
        job_data = data.get("job")
        if not isinstance(job_data, dict):
            raise ValueError("Scenario execution 'job' must be an object.")
        return SingleVehicleJobExecutionSpec(
            kind=kind,
            vehicle_id=vehicle_id,
            job=_parse_job_spec(job_data),
        )

    jobs_data = data.get("jobs")
    if not isinstance(jobs_data, list):
        raise ValueError("Scenario execution 'jobs' must be a list.")
    if not jobs_data:
        raise ValueError("Scenario dispatch execution must contain at least one job.")
    dispatch_jobs = tuple(_parse_job_spec(job_data) for job_data in jobs_data)
    if kind == "dispatch_vehicle_jobs":
        return DispatchVehicleJobsExecutionSpec(
            kind=kind,
            vehicle_id=vehicle_id,
            jobs=dispatch_jobs,
        )
    return DispatchVehicleJobQueueExecutionSpec(
        kind=kind,
        vehicle_id=vehicle_id,
        jobs=dispatch_jobs,
    )


def _parse_job_spec(data: dict[str, object]) -> JobSpec:
    required_keys = {"id", "tasks"}
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"Scenario job is missing required field(s): {missing_str}")

    job_id = data["id"]
    tasks_data = data["tasks"]

    if not isinstance(job_id, str) or not job_id:
        raise ValueError("Scenario job 'id' must be a non-empty string.")
    if not isinstance(tasks_data, list):
        raise ValueError("Scenario job 'tasks' must be a list.")
    if not tasks_data:
        raise ValueError("Scenario job must contain at least one task.")

    return JobSpec(
        id=job_id,
        tasks=tuple(_parse_task_spec(task_data) for task_data in tasks_data),
    )


def _parse_task_spec(data: object) -> MoveTaskSpec | LoadTaskSpec | UnloadTaskSpec:
    if not isinstance(data, dict):
        raise ValueError("Each scenario task must be an object.")

    kind = data.get("kind")
    if not isinstance(kind, str):
        raise ValueError("Scenario task 'kind' must be a string.")

    if kind == "move":
        destination = _parse_position_field(data, field_name="destination")
        return MoveTaskSpec(destination=destination)
    if kind == "load":
        return LoadTaskSpec(
            position=_parse_position_field(data, field_name="position"),
            amount=_parse_positive_float_field(data, field_name="amount"),
            service_duration_s=_parse_nonnegative_float_field(
                data,
                field_name="service_duration_s",
            ),
            resource_id=_parse_optional_string_field(data, field_name="resource_id"),
        )
    if kind == "unload":
        return UnloadTaskSpec(
            position=_parse_position_field(data, field_name="position"),
            amount=_parse_positive_float_field(data, field_name="amount"),
            service_duration_s=_parse_nonnegative_float_field(
                data,
                field_name="service_duration_s",
            ),
            resource_id=_parse_optional_string_field(data, field_name="resource_id"),
        )

    raise ValueError(f"Unsupported scenario task kind: {kind!r}")


def _parse_position_field(
    data: dict[str, object],
    *,
    field_name: str,
) -> tuple[float, float, float]:
    raw_position = data.get(field_name)
    return _parse_position_value(raw_position, context=f"Scenario task '{field_name}'")


def _parse_position_value(
    value: object,
    *,
    context: str,
) -> tuple[float, float, float]:
    raw_position = value
    if not isinstance(raw_position, list):
        raise ValueError(f"{context} must be a list.")
    if len(raw_position) != 3:
        raise ValueError(f"{context} must have exactly 3 coordinates.")
    if not all(isinstance(coord, (int, float)) for coord in raw_position):
        raise ValueError(f"{context} coordinates must be numeric.")

    return (
        float(raw_position[0]),
        float(raw_position[1]),
        float(raw_position[2]),
    )


def _parse_resource_spec(data: object) -> ResourceSpec:
    if not isinstance(data, dict):
        raise ValueError("Each resource entry must be an object.")

    resource_id = data.get("id")
    capacity = data.get("capacity", 1)
    initial_available_times = data.get("initial_available_times_s")

    if not isinstance(resource_id, str) or not resource_id:
        raise ValueError("Resource 'id' must be a non-empty string.")
    if not isinstance(capacity, int):
        raise ValueError("Resource 'capacity' must be an int if provided.")
    if capacity <= 0:
        raise ValueError("Resource 'capacity' must be positive.")

    parsed_available_times: tuple[float, ...] | None
    if initial_available_times is None:
        parsed_available_times = None
    else:
        if not isinstance(initial_available_times, list):
            raise ValueError("Resource 'initial_available_times_s' must be a list.")
        parsed_available_times = tuple(
            _parse_nonnegative_float_value(
                value,
                context="Resource 'initial_available_times_s' entries",
            )
            for value in initial_available_times
        )
        if len(parsed_available_times) != capacity:
            raise ValueError(
                "Resource 'initial_available_times_s' length must match capacity."
            )

    return ResourceSpec(
        resource_id=resource_id,
        capacity=capacity,
        initial_available_times_s=parsed_available_times,
    )


def _parse_world_state_spec(data: dict[str, object]) -> WorldStateSpec:
    blocked_edges_data = data.get("blocked_edges", [])
    if not isinstance(blocked_edges_data, list):
        raise ValueError("Scenario world_state 'blocked_edges' must be a list.")

    return WorldStateSpec(
        blocked_edges=tuple(
            _parse_blocked_edge_spec(blocked_edge)
            for blocked_edge in blocked_edges_data
        )
    )


def _parse_blocked_edge_spec(data: object) -> BlockedEdgeSpec:
    if not isinstance(data, dict):
        raise ValueError("Each blocked edge entry must be an object.")

    return BlockedEdgeSpec(
        start_position=_parse_position_value(
            data.get("start"),
            context="Scenario blocked edge 'start'",
        ),
        end_position=_parse_position_value(
            data.get("end"),
            context="Scenario blocked edge 'end'",
        ),
    )


def _parse_dispatcher_spec(data: dict[str, object]) -> DispatcherSpec:
    kind = data.get("kind")
    params = data.get("params", {})

    if not isinstance(kind, str) or not kind:
        raise ValueError("Scenario dispatcher 'kind' must be a non-empty string.")
    if not isinstance(params, dict):
        raise ValueError("Scenario dispatcher 'params' must be an object if provided.")
    if kind != "first_feasible":
        raise ValueError(f"Unsupported dispatcher kind: {kind!r}")
    if params:
        raise ValueError(
            "Scenario dispatcher 'first_feasible' does not support custom params."
        )

    return DispatcherSpec(kind=kind, params=params)


def _parse_positive_float_field(
    data: dict[str, object],
    *,
    field_name: str,
) -> float:
    value = data.get(field_name)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Scenario task '{field_name}' must be numeric.")
    if float(value) <= 0.0:
        raise ValueError(f"Scenario task '{field_name}' must be positive.")
    return float(value)


def _parse_nonnegative_float_field(
    data: dict[str, object],
    *,
    field_name: str,
) -> float:
    value = data.get(field_name)
    return _parse_nonnegative_float_value(
        value,
        context=f"Scenario task '{field_name}'",
    )


def _parse_nonnegative_float_value(
    value: object,
    *,
    context: str,
) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{context} must be numeric.")
    parsed_value = float(value)
    if not math.isfinite(parsed_value) or parsed_value < 0.0:
        raise ValueError(f"{context} must be finite and non-negative.")
    return parsed_value


def _parse_optional_string_field(
    data: dict[str, object],
    *,
    field_name: str,
) -> str | None:
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"Scenario task '{field_name}' must be a non-empty string if provided."
        )
    return value


def _collect_referenced_resource_ids(execution: ExecutionSpec | None) -> set[str]:
    if execution is None:
        return set()

    jobs: tuple[JobSpec, ...]
    if isinstance(execution, SingleVehicleJobExecutionSpec):
        jobs = (execution.job,)
    else:
        jobs = execution.jobs

    return {
        task.resource_id
        for job in jobs
        for task in job.tasks
        if isinstance(task, (LoadTaskSpec, UnloadTaskSpec)) and task.resource_id is not None
    }
