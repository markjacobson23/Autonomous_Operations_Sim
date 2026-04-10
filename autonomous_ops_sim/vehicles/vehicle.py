from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autonomous_ops_sim.simulation.behavior import VehicleBehaviorController


Position = tuple[float, float, float]


class VehicleType(Enum):
    GENERIC = auto()
    HAUL_TRUCK = auto()
    FORKLIFT = auto()
    CAR = auto()


@dataclass
class Vehicle:
    """Execution-facing runtime vehicle state for one simulator run."""

    id: int
    current_node_id: int
    position: Position
    velocity: float
    payload: float
    max_payload: float
    max_speed: float
    vehicle_type: VehicleType = VehicleType.GENERIC
    behavior: VehicleBehaviorController | None = None

    def __post_init__(self) -> None:
        from autonomous_ops_sim.simulation.behavior import VehicleBehaviorController

        self.position = _normalize_position(self.position)
        if self.behavior is None:
            self.behavior = VehicleBehaviorController(vehicle_id=self.id)
        self._validate_runtime_state()

    @property
    def operational_state(self) -> str:
        if self.behavior is None:
            raise RuntimeError("vehicle behavior controller is not initialized")
        return self.behavior.state.value

    def get_position(self) -> Position:
        return self.position

    def get_velocity(self) -> float:
        return self.velocity

    def get_payload(self) -> float:
        return self.payload

    def get_cost_context(self) -> dict[str, float]:
        return {"current_payload": self.payload}

    def move_to_node(self, *, node_id: int, position: Position) -> None:
        self.current_node_id = node_id
        self.position = _normalize_position(position)

    def update_position(self, new_position: Position) -> None:
        self.position = _normalize_position(new_position)

    def set_payload(self, new_payload: float) -> None:
        if not math.isfinite(new_payload) or new_payload < 0.0:
            raise ValueError("payload must be finite and non-negative")
        if new_payload > self.max_payload:
            raise ValueError("payload cannot exceed max_payload")
        self.payload = new_payload

    def set_velocity(self, new_velocity: float) -> None:
        if not math.isfinite(new_velocity):
            raise ValueError("velocity must be finite")
        self.velocity = new_velocity

    def load_payload(self, amount: float) -> None:
        self.set_payload(self.payload + amount)

    def unload_payload(self, amount: float) -> None:
        if amount > self.payload:
            raise ValueError("unload task would reduce payload below zero")
        self.set_payload(self.payload - amount)

    def _validate_runtime_state(self) -> None:
        if not isinstance(self.current_node_id, int):
            raise ValueError("current_node_id must be an int")
        if not math.isfinite(self.velocity):
            raise ValueError("velocity must be finite")
        if not math.isfinite(self.payload) or self.payload < 0.0:
            raise ValueError("payload must be finite and non-negative")
        if math.isnan(self.max_payload) or self.max_payload < 0.0:
            raise ValueError("max_payload must be non-negative")
        if self.payload > self.max_payload:
            raise ValueError("payload cannot exceed max_payload")
        if not math.isfinite(self.max_speed) or self.max_speed <= 0.0:
            raise ValueError("max_speed must be finite and positive")


def _normalize_position(position: Position) -> Position:
    return (float(position[0]), float(position[1]), float(position[2]))
