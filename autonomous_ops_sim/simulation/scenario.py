from dataclasses import dataclass
from pathlib import Path
from autonomous_ops_sim.vehicles.vehicle import VehicleType

@dataclass(frozen=True)
class MapSpec:
    kind: str
    params: dict[str, object]


@dataclass(frozen=True)
class VehicleSpec:
    id: int
    position: tuple[float, float, float]
    velocity: float
    payload: float
    max_payload: float
    max_speed: float
    vehicle_type: VehicleType | None = None


@dataclass(frozen=True)
class Scenario:
    name: str
    seed: int
    duration_s: float
    map_spec: MapSpec
    vehicles: list[VehicleSpec]
    source_path: Path | None = None