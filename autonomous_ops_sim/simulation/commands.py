from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask


def _job_task_to_dict(task: object) -> dict[str, Any]:
    if isinstance(task, MoveTask):
        return {
            "kind": "move",
            "destination_node_id": task.destination_node_id,
        }
    if isinstance(task, LoadTask):
        payload = {
            "kind": "load",
            "node_id": task.node_id,
            "amount": task.amount,
            "service_duration_s": task.service_duration_s,
        }
        if task.resource_id is not None:
            payload["resource_id"] = task.resource_id
        return payload
    if isinstance(task, UnloadTask):
        payload = {
            "kind": "unload",
            "node_id": task.node_id,
            "amount": task.amount,
            "service_duration_s": task.service_duration_s,
        }
        if task.resource_id is not None:
            payload["resource_id"] = task.resource_id
        return payload
    raise TypeError(f"Unsupported job task type: {type(task).__name__}")


def job_to_dict(job: Job) -> dict[str, Any]:
    """Convert one typed job into a stable export-ready record."""

    return {
        "id": job.id,
        "tasks": [_job_task_to_dict(task) for task in job.tasks],
    }


def job_from_dict(data: dict[str, Any]) -> Job:
    """Parse one deterministic job record from a JSON-ready payload."""

    job_id = data.get("id")
    tasks = data.get("tasks")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job id must be a non-empty string")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("job tasks must be a non-empty list")

    parsed_tasks: list[MoveTask | LoadTask | UnloadTask] = []
    for task_data in tasks:
        if not isinstance(task_data, dict):
            raise ValueError("job tasks must be objects")
        task_kind = str(task_data.get("kind", "")).strip()
        if task_kind == "move":
            parsed_tasks.append(
                MoveTask(destination_node_id=int(task_data["destination_node_id"]))
            )
            continue
        if task_kind == "load":
            parsed_tasks.append(
                LoadTask(
                    node_id=int(task_data["node_id"]),
                    amount=float(task_data["amount"]),
                    service_duration_s=float(task_data["service_duration_s"]),
                    resource_id=(
                        None
                        if task_data.get("resource_id") is None
                        else str(task_data["resource_id"])
                    ),
                )
            )
            continue
        if task_kind == "unload":
            parsed_tasks.append(
                UnloadTask(
                    node_id=int(task_data["node_id"]),
                    amount=float(task_data["amount"]),
                    service_duration_s=float(task_data["service_duration_s"]),
                    resource_id=(
                        None
                        if task_data.get("resource_id") is None
                        else str(task_data["resource_id"])
                    ),
                )
            )
            continue
        raise ValueError(f"Unsupported job task kind: {task_kind!r}")

    return Job(id=job_id, tasks=tuple(parsed_tasks))

@dataclass(frozen=True)
class BlockEdgeCommand:
    """Block one runtime edge through the existing WorldState surface."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise ValueError("edge_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "block_edge"


@dataclass(frozen=True)
class UnblockEdgeCommand:
    """Reopen one runtime edge through the existing WorldState surface."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise ValueError("edge_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "unblock_edge"


@dataclass(frozen=True)
class RepositionVehicleCommand:
    """Move one runtime vehicle to an existing node without route execution."""

    vehicle_id: int
    node_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise ValueError("vehicle_id must be non-negative")
        if self.node_id < 0:
            raise ValueError("node_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "reposition_vehicle"


@dataclass(frozen=True)
class AssignVehicleDestinationCommand:
    """Route one runtime vehicle to a destination through the engine."""

    vehicle_id: int
    destination_node_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise ValueError("vehicle_id must be non-negative")
        if self.destination_node_id < 0:
            raise ValueError("destination_node_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "assign_vehicle_destination"


@dataclass(frozen=True)
class SpawnVehicleCommand:
    """Add one runtime vehicle to the active live session."""

    vehicle_id: int
    node_id: int
    max_speed: float
    max_payload: float
    vehicle_type: str = "GENERIC"
    payload: float = 0.0
    velocity: float = 0.0

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise ValueError("vehicle_id must be non-negative")
        if self.node_id < 0:
            raise ValueError("node_id must be non-negative")
        if self.max_speed <= 0.0:
            raise ValueError("max_speed must be positive")
        if self.max_payload <= 0.0:
            raise ValueError("max_payload must be positive")
        if self.payload < 0.0:
            raise ValueError("payload must be non-negative")
        if self.payload > self.max_payload:
            raise ValueError("payload cannot exceed max_payload")

    @property
    def command_type(self) -> str:
        return "spawn_vehicle"


@dataclass(frozen=True)
class RemoveVehicleCommand:
    """Retire one runtime vehicle from the active live session."""

    vehicle_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise ValueError("vehicle_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "remove_vehicle"


@dataclass(frozen=True)
class InjectJobCommand:
    """Inject and execute one job for a runtime vehicle."""

    vehicle_id: int
    job: Job

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise ValueError("vehicle_id must be non-negative")
        if not self.job.id:
            raise ValueError("job id must be non-empty")
        if not self.job.tasks:
            raise ValueError("job must contain at least one task")

    @property
    def command_type(self) -> str:
        return "inject_job"


@dataclass(frozen=True)
class DeclareTemporaryHazardCommand:
    """Declare a temporary hazard and close one runtime edge."""

    edge_id: int
    hazard_label: str

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise ValueError("edge_id must be non-negative")
        if not self.hazard_label:
            raise ValueError("hazard_label must be non-empty")

    @property
    def command_type(self) -> str:
        return "declare_temporary_hazard"


@dataclass(frozen=True)
class ClearTemporaryHazardCommand:
    """Clear one temporary hazard and reopen its runtime edge."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise ValueError("edge_id must be non-negative")

    @property
    def command_type(self) -> str:
        return "clear_temporary_hazard"


SimulationCommand = (
    BlockEdgeCommand
    | UnblockEdgeCommand
    | RepositionVehicleCommand
    | AssignVehicleDestinationCommand
    | SpawnVehicleCommand
    | RemoveVehicleCommand
    | InjectJobCommand
    | DeclareTemporaryHazardCommand
    | ClearTemporaryHazardCommand
)


def command_to_dict(command: SimulationCommand) -> dict[str, Any]:
    """Convert one typed command to a stable export-ready record."""

    if isinstance(command, (BlockEdgeCommand, UnblockEdgeCommand)):
        return {
            "command_type": command.command_type,
            "edge_id": command.edge_id,
        }
    if isinstance(command, RepositionVehicleCommand):
        return {
            "command_type": command.command_type,
            "vehicle_id": command.vehicle_id,
            "node_id": command.node_id,
        }
    if isinstance(command, SpawnVehicleCommand):
        return {
            "command_type": command.command_type,
            "vehicle_id": command.vehicle_id,
            "node_id": command.node_id,
            "max_speed": command.max_speed,
            "max_payload": command.max_payload,
            "vehicle_type": command.vehicle_type,
            "payload": command.payload,
            "velocity": command.velocity,
        }
    if isinstance(command, RemoveVehicleCommand):
        return {
            "command_type": command.command_type,
            "vehicle_id": command.vehicle_id,
        }
    if isinstance(command, InjectJobCommand):
        return {
            "command_type": command.command_type,
            "vehicle_id": command.vehicle_id,
            "job": job_to_dict(command.job),
        }
    if isinstance(command, DeclareTemporaryHazardCommand):
        return {
            "command_type": command.command_type,
            "edge_id": command.edge_id,
            "hazard_label": command.hazard_label,
        }
    if isinstance(command, ClearTemporaryHazardCommand):
        return {
            "command_type": command.command_type,
            "edge_id": command.edge_id,
        }
    return {
        "command_type": command.command_type,
        "vehicle_id": command.vehicle_id,
        "destination_node_id": command.destination_node_id,
    }
