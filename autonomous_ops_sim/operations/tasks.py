from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MoveTask:
    """Move a vehicle to a destination node through the existing router."""

    destination_node_id: int

    def __post_init__(self) -> None:
        if self.destination_node_id < 0:
            raise ValueError("destination_node_id must be non-negative")


@dataclass(frozen=True)
class LoadTask:
    """Load payload at the current node, optionally through a shared resource."""

    node_id: int
    amount: float
    service_duration_s: float
    resource_id: str | None = None

    def __post_init__(self) -> None:
        _validate_service_task(
            node_id=self.node_id,
            amount=self.amount,
            service_duration_s=self.service_duration_s,
        )


@dataclass(frozen=True)
class UnloadTask:
    """Unload payload at the current node, optionally through a shared resource."""

    node_id: int
    amount: float
    service_duration_s: float
    resource_id: str | None = None

    def __post_init__(self) -> None:
        _validate_service_task(
            node_id=self.node_id,
            amount=self.amount,
            service_duration_s=self.service_duration_s,
        )


JobTask = MoveTask | LoadTask | UnloadTask


def get_task_type_name(task: JobTask) -> str:
    """Return the stable public task type name for trace output."""

    if isinstance(task, MoveTask):
        return "move"
    if isinstance(task, LoadTask):
        return "load"
    return "unload"


def _validate_service_task(
    *,
    node_id: int,
    amount: float,
    service_duration_s: float,
) -> None:
    if node_id < 0:
        raise ValueError("node_id must be non-negative")
    if not math.isfinite(amount) or amount <= 0.0:
        raise ValueError("amount must be finite and positive")
    if not math.isfinite(service_duration_s) or service_duration_s < 0.0:
        raise ValueError("service_duration_s must be finite and non-negative")
