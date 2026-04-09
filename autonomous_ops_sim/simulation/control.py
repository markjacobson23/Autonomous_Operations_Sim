from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from autonomous_ops_sim.simulation.commands import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    RepositionVehicleCommand,
    SimulationCommand,
    UnblockEdgeCommand,
    command_to_dict,
)
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle


class CommandValidationError(ValueError):
    """Raised when a control command is invalid for the current runtime state."""


@dataclass(frozen=True)
class CommandApplicationRecord:
    """Stable audit record for one applied simulation command."""

    sequence: int
    command: SimulationCommand
    started_at_s: float
    completed_at_s: float


class SimulationController:
    """Apply a narrow deterministic command set to one engine run."""

    def __init__(self, engine: SimulationEngine):
        self._engine = engine
        self._history: list[CommandApplicationRecord] = []

    @property
    def engine(self) -> SimulationEngine:
        """Return the engine owned by this controller."""

        return self._engine

    @property
    def command_history(self) -> tuple[CommandApplicationRecord, ...]:
        """Return all applied commands in stable application order."""

        return tuple(self._history)

    def apply(self, command: SimulationCommand) -> CommandApplicationRecord:
        """Validate and apply one explicit command."""

        self.validate(command)
        started_at_s = self.engine.simulated_time_s

        if isinstance(command, BlockEdgeCommand):
            self.engine.world_state.block_edge(command.edge_id)
        elif isinstance(command, UnblockEdgeCommand):
            self.engine.world_state.unblock_edge(command.edge_id)
        elif isinstance(command, RepositionVehicleCommand):
            vehicle = self.engine.get_vehicle(command.vehicle_id)
            vehicle.move_to_node(
                node_id=command.node_id,
                position=self.engine.map.get_position(command.node_id),
            )
        else:
            vehicle = self.engine.get_vehicle(command.vehicle_id)
            self.engine.execute_vehicle_route(
                vehicle=vehicle,
                destination_node_id=command.destination_node_id,
            )

        record = CommandApplicationRecord(
            sequence=len(self._history),
            command=command,
            started_at_s=started_at_s,
            completed_at_s=self.engine.simulated_time_s,
        )
        self._history.append(record)
        return record

    def apply_all(
        self,
        commands: tuple[SimulationCommand, ...] | list[SimulationCommand],
    ) -> tuple[CommandApplicationRecord, ...]:
        """Apply commands in the exact order they are provided."""

        return tuple(self.apply(command) for command in commands)

    def validate(self, command: SimulationCommand) -> None:
        """Reject invalid commands before mutating runtime state."""

        if isinstance(command, BlockEdgeCommand):
            self._validate_block_edge(command)
            return
        if isinstance(command, UnblockEdgeCommand):
            self._validate_unblock_edge(command)
            return
        if isinstance(command, RepositionVehicleCommand):
            self._validate_reposition_vehicle(command)
            return
        self._validate_assign_vehicle_destination(command)

    def _validate_block_edge(self, command: BlockEdgeCommand) -> None:
        try:
            already_blocked = self.engine.world_state.is_edge_blocked(command.edge_id)
        except KeyError as exc:
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}") from exc
        if already_blocked:
            raise CommandValidationError(
                f"edge_id {command.edge_id} is already blocked"
            )

    def _validate_unblock_edge(self, command: UnblockEdgeCommand) -> None:
        try:
            is_blocked = self.engine.world_state.is_edge_blocked(command.edge_id)
        except KeyError as exc:
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}") from exc
        if not is_blocked:
            raise CommandValidationError(
                f"edge_id {command.edge_id} is not currently blocked"
            )

    def _validate_reposition_vehicle(self, command: RepositionVehicleCommand) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_idle_vehicle(vehicle_id=vehicle.id)
        try:
            self.engine.map.get_position(command.node_id)
        except KeyError as exc:
            raise CommandValidationError(
                f"Unknown node_id: {command.node_id}"
            ) from exc

    def _validate_assign_vehicle_destination(
        self,
        command: AssignVehicleDestinationCommand,
    ) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_idle_vehicle(vehicle_id=vehicle.id)
        try:
            self.engine.map.get_position(command.destination_node_id)
        except KeyError as exc:
            raise CommandValidationError(
                f"Unknown destination_node_id: {command.destination_node_id}"
            ) from exc
        try:
            self.engine.router.route(
                self.engine.map.graph,
                vehicle.current_node_id,
                command.destination_node_id,
                world_state=self.engine.world_state,
            )
        except ValueError as exc:
            raise CommandValidationError(
                "No route exists for vehicle "
                f"{vehicle.id} to destination_node_id {command.destination_node_id}"
            ) from exc

    def _require_vehicle(self, vehicle_id: int) -> Vehicle:
        try:
            return self.engine.get_vehicle(vehicle_id)
        except KeyError as exc:
            raise CommandValidationError(
                f"Unknown vehicle_id: {vehicle_id}"
            ) from exc

    def _require_idle_vehicle(self, *, vehicle_id: int) -> None:
        vehicle = self.engine.get_vehicle(vehicle_id)
        if vehicle.operational_state != "idle":
            raise CommandValidationError(
                f"vehicle_id {vehicle_id} must be idle to accept control commands"
            )


def build_controlled_engine_export(
    controller: SimulationController,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> dict[str, Any]:
    """Return a stable export including engine output and applied commands."""

    from autonomous_ops_sim.io.exports import build_engine_export

    metrics_summary = summary or summarize_engine_execution(controller.engine)
    export_record = build_engine_export(controller.engine, summary=metrics_summary)
    export_record["command_history"] = [
        command_application_to_dict(record) for record in controller.command_history
    ]
    return export_record


def export_controlled_engine_json(
    controller: SimulationController,
    *,
    summary: ExecutionMetricsSummary | None = None,
) -> str:
    """Return deterministic JSON for a command-driven engine run."""

    export_record = build_controlled_engine_export(controller, summary=summary)
    return json.dumps(export_record, indent=2, sort_keys=True) + "\n"


def command_application_to_dict(
    record: CommandApplicationRecord,
) -> dict[str, Any]:
    """Convert one command application record into a stable export record."""

    return {
        "sequence": record.sequence,
        "command": command_to_dict(record.command),
        "started_at_s": record.started_at_s,
        "completed_at_s": record.completed_at_s,
    }
