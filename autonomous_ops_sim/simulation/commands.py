from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


SimulationCommand = (
    BlockEdgeCommand
    | UnblockEdgeCommand
    | RepositionVehicleCommand
    | AssignVehicleDestinationCommand
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
    return {
        "command_type": command.command_type,
        "vehicle_id": command.vehicle_id,
        "destination_node_id": command.destination_node_id,
    }
