from dataclasses import dataclass
from pathlib import Path

from autonomous_ops_sim.vehicles.vehicle import VehicleType


Position = tuple[float, float, float]


@dataclass(frozen=True)
class MapSpec:
    kind: str
    params: dict[str, object]


@dataclass(frozen=True)
class VehicleSpec:
    id: int
    position: Position
    velocity: float
    payload: float
    max_payload: float
    max_speed: float
    vehicle_type: VehicleType | None = None


@dataclass(frozen=True)
class MoveTaskSpec:
    destination: Position


@dataclass(frozen=True)
class LoadTaskSpec:
    position: Position
    amount: float
    service_duration_s: float
    resource_id: str | None = None


@dataclass(frozen=True)
class UnloadTaskSpec:
    position: Position
    amount: float
    service_duration_s: float
    resource_id: str | None = None


ScenarioTaskSpec = MoveTaskSpec | LoadTaskSpec | UnloadTaskSpec


@dataclass(frozen=True)
class JobSpec:
    id: str
    tasks: tuple[ScenarioTaskSpec, ...]


@dataclass(frozen=True)
class ExecutionSpec:
    kind: str
    vehicle_id: int
    job: JobSpec


@dataclass(frozen=True)
class Scenario:
    name: str
    seed: int
    duration_s: float
    map_spec: MapSpec
    vehicles: list[VehicleSpec]
    execution: ExecutionSpec | None = None
    source_path: Path | None = None
