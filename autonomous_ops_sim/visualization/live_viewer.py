from __future__ import annotations

from dataclasses import dataclass

from autonomous_ops_sim.simulation import (
    CommandApplicationRecord,
    LiveSimulationSession,
)
from autonomous_ops_sim.visualization.interactions import (
    AssignDestinationInteraction,
    BlockEdgeInteraction,
    InteractionValidationError,
    RepositionVehicleInteraction,
    VisualizationInteraction,
    apply_interaction_to_live_session,
)
from autonomous_ops_sim.visualization.state import (
    VisualizationState,
    build_visualization_state_from_live_session,
)


class LiveViewerActionValidationError(ValueError):
    """Raised when a live viewer action is invalid for the current session state."""


@dataclass(frozen=True)
class SelectVehicleViewerAction:
    """Select one existing vehicle for subsequent viewer-driven actions."""

    vehicle_id: int

    def __post_init__(self) -> None:
        if self.vehicle_id < 0:
            raise LiveViewerActionValidationError("vehicle_id must be non-negative")

    @property
    def action_type(self) -> str:
        return "select_vehicle"


@dataclass(frozen=True)
class AssignSelectedDestinationViewerAction:
    """Assign a destination to the currently selected vehicle."""

    destination_node_id: int

    def __post_init__(self) -> None:
        if self.destination_node_id < 0:
            raise LiveViewerActionValidationError(
                "destination_node_id must be non-negative"
            )

    @property
    def action_type(self) -> str:
        return "assign_destination"


@dataclass(frozen=True)
class BlockEdgeViewerAction:
    """Block one edge during a live session."""

    edge_id: int

    def __post_init__(self) -> None:
        if self.edge_id < 0:
            raise LiveViewerActionValidationError("edge_id must be non-negative")

    @property
    def action_type(self) -> str:
        return "block_edge"


@dataclass(frozen=True)
class RepositionSelectedVehicleViewerAction:
    """Reposition the selected vehicle to its current or adjacent node."""

    node_id: int

    def __post_init__(self) -> None:
        if self.node_id < 0:
            raise LiveViewerActionValidationError("node_id must be non-negative")

    @property
    def action_type(self) -> str:
        return "reposition_vehicle"


LiveViewerAction = (
    SelectVehicleViewerAction
    | AssignSelectedDestinationViewerAction
    | BlockEdgeViewerAction
    | RepositionSelectedVehicleViewerAction
)


@dataclass(frozen=True)
class LiveViewerActionResult:
    """Stable result of one viewer action applied to a live session."""

    action: LiveViewerAction
    selected_vehicle_id: int | None
    interaction: VisualizationInteraction | None
    command_record: CommandApplicationRecord | None
    visualization_state: VisualizationState


class LiveViewerController:
    """Drive one live session through explicit viewer actions."""

    def __init__(
        self,
        session: LiveSimulationSession,
        *,
        selected_vehicle_id: int | None = None,
    ) -> None:
        self._session = session
        self._selected_vehicle_id: int | None = None
        self._visualization_state = build_visualization_state_from_live_session(
            session
        )
        if selected_vehicle_id is not None:
            self._require_vehicle_exists(selected_vehicle_id)
            self._selected_vehicle_id = selected_vehicle_id

    @property
    def session(self) -> LiveSimulationSession:
        """Return the authoritative live session."""

        return self._session

    @property
    def selected_vehicle_id(self) -> int | None:
        """Return the currently selected vehicle, if any."""

        return self._selected_vehicle_id

    @property
    def visualization_state(self) -> VisualizationState:
        """Return the latest visualization state derived from the live session."""

        return self._visualization_state

    def refresh(self) -> VisualizationState:
        """Rebuild visualization state from the current authoritative session state."""

        self._visualization_state = build_visualization_state_from_live_session(
            self.session
        )
        return self.visualization_state

    def apply_action(
        self,
        action: LiveViewerAction,
    ) -> LiveViewerActionResult:
        """Apply one explicit viewer action through selection, interaction, and session layers."""

        selected_vehicle_id, interaction = translate_live_viewer_action(
            action,
            session=self.session,
            selected_vehicle_id=self.selected_vehicle_id,
        )

        command_record: CommandApplicationRecord | None = None
        if interaction is not None:
            try:
                command_record = apply_interaction_to_live_session(
                    self.session,
                    interaction,
                )
            except InteractionValidationError as exc:
                raise LiveViewerActionValidationError(str(exc)) from exc

        self._selected_vehicle_id = selected_vehicle_id
        self.refresh()
        return LiveViewerActionResult(
            action=action,
            selected_vehicle_id=self.selected_vehicle_id,
            interaction=interaction,
            command_record=command_record,
            visualization_state=self.visualization_state,
        )

    def _require_vehicle_exists(self, vehicle_id: int) -> None:
        try:
            self.session.engine.get_vehicle(vehicle_id)
        except KeyError as exc:
            raise LiveViewerActionValidationError(
                f"Unknown vehicle_id: {vehicle_id}"
            ) from exc


def translate_live_viewer_action(
    action: LiveViewerAction,
    *,
    session: LiveSimulationSession,
    selected_vehicle_id: int | None,
) -> tuple[int | None, VisualizationInteraction | None]:
    """Translate one live viewer action into selection state and an optional interaction."""

    if isinstance(action, SelectVehicleViewerAction):
        _require_vehicle_exists(session, action.vehicle_id)
        return action.vehicle_id, None

    if isinstance(action, BlockEdgeViewerAction):
        return selected_vehicle_id, BlockEdgeInteraction(edge_id=action.edge_id)

    vehicle_id = _require_selected_vehicle_id(selected_vehicle_id)
    _require_vehicle_exists(session, vehicle_id)

    if isinstance(action, AssignSelectedDestinationViewerAction):
        return vehicle_id, AssignDestinationInteraction(
            vehicle_id=vehicle_id,
            destination_node_id=action.destination_node_id,
        )

    assert isinstance(action, RepositionSelectedVehicleViewerAction)
    _require_bounded_reposition(
        session=session,
        vehicle_id=vehicle_id,
        node_id=action.node_id,
    )
    return vehicle_id, RepositionVehicleInteraction(
        vehicle_id=vehicle_id,
        node_id=action.node_id,
    )


def _require_selected_vehicle_id(selected_vehicle_id: int | None) -> int:
    if selected_vehicle_id is None:
        raise LiveViewerActionValidationError(
            "a vehicle must be selected before issuing this action"
        )
    return selected_vehicle_id


def _require_vehicle_exists(
    session: LiveSimulationSession,
    vehicle_id: int,
) -> None:
    try:
        session.engine.get_vehicle(vehicle_id)
    except KeyError as exc:
        raise LiveViewerActionValidationError(
            f"Unknown vehicle_id: {vehicle_id}"
        ) from exc


def _require_bounded_reposition(
    *,
    session: LiveSimulationSession,
    vehicle_id: int,
    node_id: int,
) -> None:
    vehicle = session.engine.get_vehicle(vehicle_id)
    current_node_id = vehicle.current_node_id
    if node_id == current_node_id:
        return

    adjacent_node_ids = tuple(sorted(session.engine.map.get_neighbors(current_node_id)))
    if node_id not in adjacent_node_ids:
        raise LiveViewerActionValidationError(
            "node_id "
            f"{node_id} must be the selected vehicle's current node "
            "or a direct outgoing neighbor"
        )
