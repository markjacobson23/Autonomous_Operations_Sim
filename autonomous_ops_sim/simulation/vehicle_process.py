from dataclasses import dataclass
import math
from typing import TYPE_CHECKING

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.operations.jobs import Job, JobExecutionResult
from autonomous_ops_sim.operations.tasks import (
    LoadTask,
    MoveTask,
    UnloadTask,
    get_task_type_name,
)
from autonomous_ops_sim.simulation.behavior import (
    InvalidBehaviorTransitionError,
    VehicleBehaviorController,
    VehicleOperationalState,
)
from autonomous_ops_sim.simulation.trace import TraceEventType

if TYPE_CHECKING:
    from autonomous_ops_sim.simulation.engine import SimulationEngine


@dataclass
class VehicleProcess:
    """Single-vehicle route execution over simulated time."""

    vehicle_id: int
    current_node_id: int
    max_speed: float
    payload: float = 0.0
    max_payload: float = math.inf
    behavior: VehicleBehaviorController | None = None

    def __post_init__(self) -> None:
        if self.behavior is None:
            self.behavior = VehicleBehaviorController(vehicle_id=self.vehicle_id)

    def execute_route(
        self,
        *,
        destination_node_id: int,
        engine: "SimulationEngine",
    ) -> tuple[int, ...]:
        """Route to the destination and emit deterministic execution events."""
        try:
            if not math.isfinite(self.max_speed) or self.max_speed <= 0.0:
                raise ValueError("max_speed must be finite and positive")

            _, path = engine.router.route(
                engine.map.graph,
                self.current_node_id,
                destination_node_id,
                world_state=engine.world_state,
            )
            route = tuple(path)
            self._transition_behavior(
                engine=engine,
                to_state=VehicleOperationalState.MOVING,
                reason="route_start",
            )

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.ROUTE_START,
                node_id=self.current_node_id,
                start_node_id=self.current_node_id,
                end_node_id=destination_node_id,
            )

            for start_node_id, end_node_id in zip(route, route[1:]):
                edge = engine.map.get_edge_between(start_node_id, end_node_id)
                if edge is None:
                    raise RuntimeError(
                        "Router returned a path containing a missing map edge: "
                        f"{start_node_id} -> {end_node_id}."
                    )

                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.EDGE_ENTER,
                    edge_id=edge.id,
                    start_node_id=start_node_id,
                    end_node_id=end_node_id,
                )

                engine.run(
                    engine.simulated_time_s + _edge_travel_time_s(edge, self.max_speed)
                )
                self.current_node_id = end_node_id

                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.NODE_ARRIVAL,
                    node_id=end_node_id,
                    start_node_id=start_node_id,
                    end_node_id=end_node_id,
                )

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.ROUTE_COMPLETE,
                node_id=self.current_node_id,
                start_node_id=route[0],
                end_node_id=destination_node_id,
            )
            self._transition_behavior(
                engine=engine,
                to_state=VehicleOperationalState.IDLE,
                reason="route_complete",
            )
            return route
        except Exception as exc:
            self._transition_to_failed(engine=engine, reason=f"route_failed:{type(exc).__name__}")
            raise

    def execute_job(
        self,
        *,
        job: Job,
        engine: "SimulationEngine",
    ) -> JobExecutionResult:
        """Execute an ordered job without introducing dispatcher behavior."""
        try:
            if not math.isfinite(self.payload) or self.payload < 0.0:
                raise ValueError("payload must be finite and non-negative")
            if not math.isfinite(self.max_payload) or self.max_payload <= 0.0:
                raise ValueError("max_payload must be finite and positive")
            if self.payload > self.max_payload:
                raise ValueError("payload cannot exceed max_payload")

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.JOB_START,
                node_id=self.current_node_id,
                job_id=job.id,
            )

            for task_index, task in enumerate(job.tasks):
                task_type = get_task_type_name(task)
                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.TASK_START,
                    node_id=self.current_node_id,
                    job_id=job.id,
                    task_index=task_index,
                    task_type=task_type,
                )

                if isinstance(task, MoveTask):
                    self.execute_route(
                        destination_node_id=task.destination_node_id,
                        engine=engine,
                    )
                elif isinstance(task, LoadTask):
                    self._execute_load_task(
                        task=task,
                        job=job,
                        task_index=task_index,
                        engine=engine,
                    )
                else:
                    self._execute_unload_task(
                        task=task,
                        job=job,
                        task_index=task_index,
                        engine=engine,
                    )

                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.TASK_COMPLETE,
                    node_id=self.current_node_id,
                    job_id=job.id,
                    task_index=task_index,
                    task_type=task_type,
                )

            engine.trace.emit(
                timestamp_s=engine.simulated_time_s,
                vehicle_id=self.vehicle_id,
                event_type=TraceEventType.JOB_COMPLETE,
                node_id=self.current_node_id,
                job_id=job.id,
            )
            return JobExecutionResult(
                job_id=job.id,
                completed_task_count=len(job.tasks),
                final_node_id=self.current_node_id,
                final_payload=self.payload,
            )
        except Exception as exc:
            self._transition_to_failed(engine=engine, reason=f"job_failed:{type(exc).__name__}")
            raise

    def _execute_load_task(
        self,
        *,
        task: LoadTask,
        job: Job,
        task_index: int,
        engine: "SimulationEngine",
    ) -> None:
        self._ensure_at_task_node(task.node_id)
        updated_payload = self.payload + task.amount
        if updated_payload > self.max_payload:
            raise ValueError("load task would exceed vehicle max_payload")
        self._perform_service(
            job=job,
            task_index=task_index,
            task_type="load",
            service_duration_s=task.service_duration_s,
            resource_id=task.resource_id,
            engine=engine,
        )
        self.payload = updated_payload

    def _execute_unload_task(
        self,
        *,
        task: UnloadTask,
        job: Job,
        task_index: int,
        engine: "SimulationEngine",
    ) -> None:
        self._ensure_at_task_node(task.node_id)
        if task.amount > self.payload:
            raise ValueError("unload task would reduce payload below zero")
        self._perform_service(
            job=job,
            task_index=task_index,
            task_type="unload",
            service_duration_s=task.service_duration_s,
            resource_id=task.resource_id,
            engine=engine,
        )
        self.payload -= task.amount

    def _perform_service(
        self,
        *,
        job: Job,
        task_index: int,
        task_type: str,
        service_duration_s: float,
        resource_id: str | None,
        engine: "SimulationEngine",
    ) -> None:
        service_start_time_s = engine.simulated_time_s
        if resource_id is not None:
            self._transition_behavior(
                engine=engine,
                to_state=VehicleOperationalState.RESOURCE_WAIT,
                reason=f"{task_type}_resource_wait",
            )
            reservation = engine.get_resource(resource_id).reserve(
                requested_at_s=engine.simulated_time_s,
                duration_s=service_duration_s,
            )
            if reservation.wait_duration_s > 0.0:
                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.RESOURCE_WAIT_START,
                    node_id=self.current_node_id,
                    job_id=job.id,
                    task_index=task_index,
                    task_type=task_type,
                    resource_id=resource_id,
                    duration_s=reservation.wait_duration_s,
                )
                engine.run(reservation.start_time_s)
                engine.trace.emit(
                    timestamp_s=engine.simulated_time_s,
                    vehicle_id=self.vehicle_id,
                    event_type=TraceEventType.RESOURCE_WAIT_COMPLETE,
                    node_id=self.current_node_id,
                    job_id=job.id,
                    task_index=task_index,
                    task_type=task_type,
                    resource_id=resource_id,
                    duration_s=reservation.wait_duration_s,
                )
            service_start_time_s = reservation.start_time_s

        self._transition_behavior(
            engine=engine,
            to_state=VehicleOperationalState.SERVICING,
            reason=f"{task_type}_service_start",
        )
        engine.trace.emit(
            timestamp_s=service_start_time_s,
            vehicle_id=self.vehicle_id,
            event_type=TraceEventType.SERVICE_START,
            node_id=self.current_node_id,
            job_id=job.id,
            task_index=task_index,
            task_type=task_type,
            resource_id=resource_id,
            duration_s=service_duration_s,
        )
        engine.run(service_start_time_s + service_duration_s)
        engine.trace.emit(
            timestamp_s=engine.simulated_time_s,
            vehicle_id=self.vehicle_id,
            event_type=TraceEventType.SERVICE_COMPLETE,
            node_id=self.current_node_id,
            job_id=job.id,
            task_index=task_index,
            task_type=task_type,
            resource_id=resource_id,
            duration_s=service_duration_s,
        )
        self._transition_behavior(
            engine=engine,
            to_state=VehicleOperationalState.IDLE,
            reason=f"{task_type}_service_complete",
        )

    def _ensure_at_task_node(self, node_id: int) -> None:
        if self.current_node_id != node_id:
            raise RuntimeError(
                f"Vehicle-{self.vehicle_id} must be at Node-{node_id} to execute service task."
            )

    def recover(self, *, engine: "SimulationEngine", reason: str = "manual_recovery") -> None:
        """Return a failed process to idle through the explicit FSM path."""

        self._transition_behavior(
            engine=engine,
            to_state=VehicleOperationalState.IDLE,
            reason=reason,
        )

    def _transition_behavior(
        self,
        *,
        engine: "SimulationEngine",
        to_state: VehicleOperationalState,
        reason: str,
    ) -> None:
        if self.behavior is None:
            raise RuntimeError("vehicle behavior controller is not initialized")

        transition = self.behavior.transition_to(to_state, reason=reason)
        engine.trace.emit(
            timestamp_s=engine.simulated_time_s,
            vehicle_id=self.vehicle_id,
            event_type=TraceEventType.BEHAVIOR_TRANSITION,
            node_id=self.current_node_id,
            from_behavior_state=transition.from_state.value,
            to_behavior_state=transition.to_state.value,
            transition_reason=transition.reason,
        )

    def _transition_to_failed(self, *, engine: "SimulationEngine", reason: str) -> None:
        if self.behavior is None:
            raise RuntimeError("vehicle behavior controller is not initialized")
        if self.behavior.state == VehicleOperationalState.FAILED:
            return

        try:
            self._transition_behavior(
                engine=engine,
                to_state=VehicleOperationalState.FAILED,
                reason=reason,
            )
        except InvalidBehaviorTransitionError:
            raise RuntimeError(
                f"Vehicle-{self.vehicle_id} could not enter failed behavior state."
            ) from None


def _edge_travel_time_s(edge: Edge, max_speed: float) -> float:
    """Return traversal time using both the vehicle and edge constraints."""

    effective_speed = min(max_speed, edge.speed_limit)
    if effective_speed <= 0.0:
        raise ValueError(
            f"Edge-{edge.id} cannot be traversed with effective_speed={effective_speed}."
        )
    return edge.distance / effective_speed
