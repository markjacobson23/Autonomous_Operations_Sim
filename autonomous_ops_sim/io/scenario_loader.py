import json
from pathlib import Path

from autonomous_ops_sim.simulation.scenario import (
    ExecutionSpec,
    JobSpec,
    LoadTaskSpec,
    MapSpec,
    MoveTaskSpec,
    Scenario,
    UnloadTaskSpec,
    VehicleSpec,
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
    if execution_data is not None and not isinstance(execution_data, dict):
        raise ValueError("Scenario 'execution' must be an object if provided.")

    vehicles = [_parse_vehicle_spec(v) for v in vehicles_data]
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

    return Scenario(
        name=name,
        seed=seed,
        duration_s=float(duration_s),
        map_spec=_parse_map_spec(map_data),
        vehicles=vehicles,
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

    if kind != "grid":
        raise ValueError(f"Unsupported map kind: {kind!r}")

    grid_size = params.get("grid_size")
    if not isinstance(grid_size, int):
        raise ValueError("Grid map 'params.grid_size' must be an int.")
    if grid_size <= 0:
        raise ValueError("Grid map 'params.grid_size' must be positive.")

    return MapSpec(kind=kind, params=params)


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
    required_keys = {"kind", "vehicle_id", "job"}
    missing = required_keys - data.keys()
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(
            f"Scenario execution is missing required field(s): {missing_str}"
        )

    kind = data["kind"]
    vehicle_id = data["vehicle_id"]
    job_data = data["job"]

    if kind != "single_vehicle_job":
        raise ValueError(f"Unsupported execution kind: {kind!r}")
    if not isinstance(vehicle_id, int):
        raise ValueError("Scenario execution 'vehicle_id' must be an int.")
    if not isinstance(job_data, dict):
        raise ValueError("Scenario execution 'job' must be an object.")

    return ExecutionSpec(
        kind=kind,
        vehicle_id=vehicle_id,
        job=_parse_job_spec(job_data),
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
    if not isinstance(raw_position, list):
        raise ValueError(f"Scenario task '{field_name}' must be a list.")
    if len(raw_position) != 3:
        raise ValueError(
            f"Scenario task '{field_name}' must have exactly 3 coordinates."
        )
    if not all(isinstance(coord, (int, float)) for coord in raw_position):
        raise ValueError(
            f"Scenario task '{field_name}' coordinates must be numeric."
        )

    return (
        float(raw_position[0]),
        float(raw_position[1]),
        float(raw_position[2]),
    )


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
    if not isinstance(value, (int, float)):
        raise ValueError(f"Scenario task '{field_name}' must be numeric.")
    if float(value) < 0.0:
        raise ValueError(f"Scenario task '{field_name}' must be non-negative.")
    return float(value)


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

