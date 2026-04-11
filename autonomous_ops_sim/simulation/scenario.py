from dataclasses import dataclass, field
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
class ResourceSpec:
    resource_id: str
    capacity: int = 1
    initial_available_times_s: tuple[float, ...] | None = None


@dataclass(frozen=True)
class BlockedEdgeSpec:
    start_position: Position
    end_position: Position


@dataclass(frozen=True)
class WorldStateSpec:
    blocked_edges: tuple[BlockedEdgeSpec, ...] = ()


@dataclass(frozen=True)
class DispatcherSpec:
    kind: str
    params: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SingleVehicleJobExecutionSpec:
    kind: str
    vehicle_id: int
    job: JobSpec


@dataclass(frozen=True)
class DispatchVehicleJobsExecutionSpec:
    kind: str
    vehicle_id: int
    jobs: tuple[JobSpec, ...]


@dataclass(frozen=True)
class DispatchVehicleJobQueueExecutionSpec:
    kind: str
    vehicle_id: int
    jobs: tuple[JobSpec, ...]


@dataclass(frozen=True)
class MultiVehicleRouteRequestSpec:
    vehicle_id: int
    destination: Position
    priority: int | None = None


@dataclass(frozen=True)
class MultiVehicleRouteBatchSpec:
    requests: tuple[MultiVehicleRouteRequestSpec, ...]


@dataclass(frozen=True)
class MultiVehicleRouteBatchExecutionSpec:
    kind: str
    route_batches: tuple[MultiVehicleRouteBatchSpec, ...]


ExecutionSpec = (
    SingleVehicleJobExecutionSpec
    | DispatchVehicleJobsExecutionSpec
    | DispatchVehicleJobQueueExecutionSpec
    | MultiVehicleRouteBatchExecutionSpec
)


@dataclass(frozen=True)
class Scenario:
    name: str
    seed: int
    duration_s: float
    map_spec: MapSpec
    vehicles: list[VehicleSpec]
    resources: tuple[ResourceSpec, ...] = ()
    world_state: WorldStateSpec = field(default_factory=WorldStateSpec)
    dispatcher: DispatcherSpec | None = None
    execution: ExecutionSpec | None = None
    source_path: Path | None = None
