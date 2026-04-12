from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from autonomous_ops_sim.simulation.commands import (
    AssignVehicleDestinationCommand,
    ClearTemporaryHazardCommand,
    BlockEdgeCommand,
    DeclareTemporaryHazardCommand,
    InjectJobCommand,
    RemoveVehicleCommand,
    RepositionVehicleCommand,
    SimulationCommand,
    SpawnVehicleCommand,
    UnblockEdgeCommand,
    command_to_dict,
)
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)
from autonomous_ops_sim.simulation.trace import TraceEventType
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.vehicles.vehicle import Vehicle, VehicleType


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
        self._temporary_hazards: dict[int, str] = {}

    @property
    def engine(self) -> SimulationEngine:
        """Return the engine owned by this controller."""

        return self._engine

    @property
    def command_history(self) -> tuple[CommandApplicationRecord, ...]:
        """Return all applied commands in stable application order."""

        return tuple(self._history)

    def record_command_application(
        self,
        command: SimulationCommand,
        *,
        started_at_s: float,
        completed_at_s: float,
    ) -> CommandApplicationRecord:
        """Record a validated command application without mutating engine state."""

        record = CommandApplicationRecord(
            sequence=len(self._history),
            command=command,
            started_at_s=started_at_s,
            completed_at_s=completed_at_s,
        )
        self._history.append(record)
        return record

    @property
    def temporary_hazards(self) -> dict[int, str]:
        """Return the current temporary hazard labels keyed by edge id."""

        return dict(self._temporary_hazards)

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
        elif isinstance(command, SpawnVehicleCommand):
            self._apply_spawn_vehicle(command)
        elif isinstance(command, RemoveVehicleCommand):
            self._apply_remove_vehicle(command)
        elif isinstance(command, InjectJobCommand):
            self._apply_inject_job(command)
        elif isinstance(command, DeclareTemporaryHazardCommand):
            self._apply_declare_temporary_hazard(command)
        elif isinstance(command, ClearTemporaryHazardCommand):
            self._apply_clear_temporary_hazard(command)
        elif isinstance(command, AssignVehicleDestinationCommand):
            vehicle = self.engine.get_vehicle(command.vehicle_id)
            self.engine.assign_vehicle_route(
                vehicle=vehicle,
                destination_node_id=command.destination_node_id,
            )
        else:
            raise TypeError(f"Unhandled command type: {type(command)}")

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
        if isinstance(command, SpawnVehicleCommand):
            self._validate_spawn_vehicle(command)
            return
        if isinstance(command, RemoveVehicleCommand):
            self._validate_remove_vehicle(command)
            return
        if isinstance(command, InjectJobCommand):
            self._validate_inject_job(command)
            return
        if isinstance(command, DeclareTemporaryHazardCommand):
            self._validate_declare_temporary_hazard(command)
            return
        if isinstance(command, ClearTemporaryHazardCommand):
            self._validate_clear_temporary_hazard(command)
            return
        self._validate_assign_vehicle_destination(command)

    def _validate_block_edge(self, command: BlockEdgeCommand) -> None:
        if not self.engine.has_edge(command.edge_id):
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}")
        already_blocked = self.engine.world_state.has_blocked_edge(command.edge_id)
        if already_blocked:
            raise CommandValidationError(
                f"edge_id {command.edge_id} is already blocked"
            )

    def _validate_unblock_edge(self, command: UnblockEdgeCommand) -> None:
        if not self.engine.has_edge(command.edge_id):
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}")
        is_blocked = self.engine.world_state.has_blocked_edge(command.edge_id)
        if not is_blocked:
            raise CommandValidationError(
                f"edge_id {command.edge_id} is not currently blocked"
            )

    def _validate_reposition_vehicle(self, command: RepositionVehicleCommand) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_idle_vehicle(vehicle_id=vehicle.id)
        if not self.engine.has_node(command.node_id):
            raise CommandValidationError(f"Unknown node_id: {command.node_id}")

    def _validate_assign_vehicle_destination(
        self,
        command: AssignVehicleDestinationCommand,
    ) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_idle_vehicle(vehicle_id=vehicle.id)
        if not self.engine.has_node(command.destination_node_id):
            raise CommandValidationError(
                f"Unknown destination_node_id: {command.destination_node_id}"
            )
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

    def _validate_spawn_vehicle(self, command: SpawnVehicleCommand) -> None:
        if self.engine.has_vehicle(command.vehicle_id):
            raise CommandValidationError(
                f"vehicle_id {command.vehicle_id} is already registered"
            )
        if not self.engine.has_node(command.node_id):
            raise CommandValidationError(f"Unknown node_id: {command.node_id}")

    def _validate_remove_vehicle(self, command: RemoveVehicleCommand) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_active_vehicle(vehicle=vehicle)
        self._require_idle_vehicle(vehicle_id=vehicle.id)

    def _validate_inject_job(self, command: InjectJobCommand) -> None:
        vehicle = self._require_vehicle(command.vehicle_id)
        self._require_active_vehicle(vehicle=vehicle)
        self._require_idle_vehicle(vehicle_id=vehicle.id)
        current_node_id = vehicle.current_node_id
        projected_payload = vehicle.payload
        for task in command.job.tasks:
            if isinstance(task, MoveTask):
                try:
                    self.engine.router.route(
                        self.engine.map.graph,
                        current_node_id,
                        task.destination_node_id,
                        world_state=self.engine.world_state,
                    )
                except ValueError as exc:
                    raise CommandValidationError(
                        "No route exists for vehicle "
                        f"{vehicle.id} to destination_node_id {task.destination_node_id}"
                    ) from exc
                current_node_id = task.destination_node_id
                continue

            if task.node_id != current_node_id:
                raise CommandValidationError(
                    f"job task node mismatch for vehicle_id {vehicle.id}"
                )
            if isinstance(task, LoadTask):
                projected_payload += task.amount
                if projected_payload > vehicle.max_payload:
                    raise CommandValidationError(
                        "job would exceed vehicle max_payload"
                    )
                continue
            if isinstance(task, UnloadTask):
                if task.amount > projected_payload:
                    raise CommandValidationError(
                        "job would reduce payload below zero"
                    )
                projected_payload -= task.amount
                continue
            raise CommandValidationError(
                f"Unsupported job task type: {type(task).__name__}"
            )

    def _validate_declare_temporary_hazard(
        self,
        command: DeclareTemporaryHazardCommand,
    ) -> None:
        if not self.engine.has_edge(command.edge_id):
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}")
        is_blocked = self.engine.world_state.has_blocked_edge(command.edge_id)
        if is_blocked:
            raise CommandValidationError(
                f"edge_id {command.edge_id} is already blocked"
            )

    def _validate_clear_temporary_hazard(
        self,
        command: ClearTemporaryHazardCommand,
    ) -> None:
        if not self.engine.has_edge(command.edge_id):
            raise CommandValidationError(f"Unknown edge_id: {command.edge_id}")
        is_blocked = self.engine.world_state.has_blocked_edge(command.edge_id)
        if not is_blocked or command.edge_id not in self._temporary_hazards:
            raise CommandValidationError(
                f"edge_id {command.edge_id} does not have an active temporary hazard"
            )

    def _require_vehicle(self, vehicle_id: int) -> Vehicle:
        try:
            return self.engine.get_vehicle(vehicle_id)
        except KeyError as exc:
            raise CommandValidationError(
                f"Unknown vehicle_id: {vehicle_id}"
            ) from exc

    def _require_idle_vehicle(self, *, vehicle_id: int) -> None:
        vehicle = self.engine.get_vehicle(vehicle_id)
        self._require_active_vehicle(vehicle=vehicle)
        if vehicle.operational_state != "idle":
            raise CommandValidationError(
                f"vehicle_id {vehicle_id} must be idle to accept control commands"
            )

    def _require_active_vehicle(self, *, vehicle: Vehicle) -> None:
        if not getattr(vehicle, "is_active", True):
            raise CommandValidationError(
                f"vehicle_id {vehicle.id} is not active in the live session"
            )

    def _apply_spawn_vehicle(self, command: SpawnVehicleCommand) -> None:
        vehicle_type = _parse_vehicle_type(command.vehicle_type)
        vehicle = Vehicle(
            id=command.vehicle_id,
            current_node_id=command.node_id,
            position=self.engine.map.get_position(command.node_id),
            velocity=command.velocity,
            payload=command.payload,
            max_payload=command.max_payload,
            max_speed=command.max_speed,
            vehicle_type=vehicle_type,
        )
        self.engine.add_vehicle(vehicle)
        self.engine.trace.emit(
            timestamp_s=self.engine.simulated_time_s,
            vehicle_id=vehicle.id,
            event_type=TraceEventType.VEHICLE_SPAWNED,
            node_id=vehicle.current_node_id,
        )

    def _apply_remove_vehicle(self, command: RemoveVehicleCommand) -> None:
        vehicle = self.engine.remove_vehicle(command.vehicle_id)
        self.engine.trace.emit(
            timestamp_s=self.engine.simulated_time_s,
            vehicle_id=vehicle.id,
            event_type=TraceEventType.VEHICLE_REMOVED,
            node_id=vehicle.current_node_id,
        )

    def _apply_inject_job(self, command: InjectJobCommand) -> None:
        vehicle = self.engine.get_vehicle(command.vehicle_id)
        result = self.engine.execute_job(vehicle=vehicle, job=command.job)
        self.engine.trace.emit(
            timestamp_s=self.engine.simulated_time_s,
            vehicle_id=vehicle.id,
            event_type=TraceEventType.JOB_INJECTED,
            node_id=result.final_node_id,
            job_id=result.job_id,
        )

    def _apply_declare_temporary_hazard(
        self,
        command: DeclareTemporaryHazardCommand,
    ) -> None:
        self.engine.world_state.block_edge(command.edge_id)
        self._temporary_hazards[command.edge_id] = command.hazard_label

    def _apply_clear_temporary_hazard(
        self,
        command: ClearTemporaryHazardCommand,
    ) -> None:
        self.engine.world_state.unblock_edge(command.edge_id)
        self._temporary_hazards.pop(command.edge_id, None)


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


def _parse_vehicle_type(vehicle_type_name: str) -> VehicleType:
    normalized = vehicle_type_name.strip().upper()
    if not normalized:
        return VehicleType.GENERIC
    try:
        return VehicleType[normalized]
    except KeyError:
        return VehicleType.GENERIC
