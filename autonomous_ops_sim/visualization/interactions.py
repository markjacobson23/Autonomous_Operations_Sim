from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    CommandApplicationRecord,
    CommandValidationError,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SimulationCommand,
    SimulationController,
    UnblockEdgeCommand,
    command_to_dict,
)
from autonomous_ops_sim.visualization.state import (
    VisualizationState,
    build_visualization_state_from_controller,
    build_visualization_state_from_live_session,
)


class InteractionValidationError(ValueError):
    """Raised when a viewer-facing interaction is invalid."""


@dataclass(frozen=True)
class AssignDestinationInteraction:
    """Viewer-facing intent to route one vehicle to a destination node."""

    vehicle_id: int
    destination_node_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise InteractionValidationError("vehicle_id must be non-negative")
        if self.destination_node_id < 0:
            raise InteractionValidationError(
                "destination_node_id must be non-negative"
            )

    @property
    def interaction_type(self) -> str:
        return "assign_destination"


@dataclass(frozen=True)
class RepositionVehicleInteraction:
    """Viewer-facing intent to reposition one vehicle to an existing node."""

    vehicle_id: int
    node_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise InteractionValidationError("vehicle_id must be non-negative")
        if self.node_id < 0:
            raise InteractionValidationError("node_id must be non-negative")

    @property
    def interaction_type(self) -> str:
        return "reposition_vehicle"


@dataclass(frozen=True)
class BlockEdgeInteraction:
    """Viewer-facing intent to block one runtime edge."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise InteractionValidationError("edge_id must be non-negative")

    @property
    def interaction_type(self) -> str:
        return "block_edge"


@dataclass(frozen=True)
class UnblockEdgeInteraction:
    """Viewer-facing intent to reopen one runtime edge."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise InteractionValidationError("edge_id must be non-negative")

    @property
    def interaction_type(self) -> str:
        return "unblock_edge"


VisualizationInteraction = (
    AssignDestinationInteraction
    | RepositionVehicleInteraction
    | BlockEdgeInteraction
    | UnblockEdgeInteraction
)


def interaction_to_command(
    interaction: VisualizationInteraction,
) -> SimulationCommand:
    """Translate one explicit interaction into one typed simulation command."""

    if isinstance(interaction, BlockEdgeInteraction):
        return BlockEdgeCommand(edge_id=interaction.edge_id)
    if isinstance(interaction, UnblockEdgeInteraction):
        return UnblockEdgeCommand(edge_id=interaction.edge_id)
    if isinstance(interaction, RepositionVehicleInteraction):
        return RepositionVehicleCommand(
            vehicle_id=interaction.vehicle_id,
            node_id=interaction.node_id,
        )
    if isinstance(interaction, AssignDestinationInteraction):
        return AssignVehicleDestinationCommand(
            vehicle_id=interaction.vehicle_id,
            destination_node_id=interaction.destination_node_id,
        )
    raise InteractionValidationError(
        "Unsupported interaction type: "
        f"{type(interaction).__name__}"
    )


def translate_interactions(
    interactions: tuple[VisualizationInteraction, ...]
    | list[VisualizationInteraction],
) -> tuple[SimulationCommand, ...]:
    """Translate interactions in the exact order they are provided."""

    return tuple(interaction_to_command(interaction) for interaction in interactions)


def apply_interaction(
    controller: SimulationController,
    interaction: VisualizationInteraction,
) -> CommandApplicationRecord:
    """Validate and apply one viewer-facing interaction through the controller."""

    command = interaction_to_command(interaction)
    try:
        return controller.apply(command)
    except CommandValidationError as exc:
        raise InteractionValidationError(str(exc)) from exc


def apply_interactions(
    controller: SimulationController,
    interactions: tuple[VisualizationInteraction, ...]
    | list[VisualizationInteraction],
) -> tuple[CommandApplicationRecord, ...]:
    """Apply interactions through the deterministic command surface."""

    return tuple(apply_interaction(controller, interaction) for interaction in interactions)


def apply_interaction_to_live_session(
    session: LiveSimulationSession,
    interaction: VisualizationInteraction,
) -> CommandApplicationRecord:
    """Validate and apply one viewer-facing interaction through a live session."""

    command = interaction_to_command(interaction)
    try:
        return session.apply(command)
    except CommandValidationError as exc:
        raise InteractionValidationError(str(exc)) from exc


def apply_interactions_to_live_session(
    session: LiveSimulationSession,
    interactions: tuple[VisualizationInteraction, ...]
    | list[VisualizationInteraction],
) -> tuple[CommandApplicationRecord, ...]:
    """Apply interactions through the deterministic live session command surface."""

    return tuple(
        apply_interaction_to_live_session(session, interaction)
        for interaction in interactions
    )


def build_visualization_state_from_interactions(
    controller: SimulationController,
    interactions: tuple[VisualizationInteraction, ...]
    | list[VisualizationInteraction],
) -> VisualizationState:
    """Apply interactions and return the resulting visualization replay surface."""

    apply_interactions(controller, interactions)
    return build_visualization_state_from_controller(controller)


def build_visualization_state_from_live_interactions(
    session: LiveSimulationSession,
    interactions: tuple[VisualizationInteraction, ...]
    | list[VisualizationInteraction],
) -> VisualizationState:
    """Apply interactions to a live session and return refreshed visualization state."""

    apply_interactions_to_live_session(session, interactions)
    return build_visualization_state_from_live_session(session)


def interaction_to_dict(interaction: VisualizationInteraction) -> dict[str, Any]:
    """Convert one interaction into a stable export-ready record."""

    command = interaction_to_command(interaction)
    return {
        "interaction_type": interaction.interaction_type,
        "command": command_to_dict(command),
    }
