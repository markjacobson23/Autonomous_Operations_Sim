from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Protocol

from autonomous_ops_sim.operations.jobs import Job, JobExecutionResult
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask
from autonomous_ops_sim.vehicles.vehicle import Vehicle

if TYPE_CHECKING:
    from autonomous_ops_sim.simulation.engine import SimulationEngine


@dataclass(frozen=True)
class DispatchRequest:
    """Stable vehicle execution inputs used during dispatcher selection."""

    vehicle: Vehicle

    @property
    def vehicle_id(self) -> int:
        return self.vehicle.id

    @property
    def start_node_id(self) -> int:
        return self.vehicle.current_node_id

    @property
    def max_speed(self) -> float:
        return self.vehicle.max_speed

    @property
    def initial_payload(self) -> float:
        return self.vehicle.payload

    @property
    def max_payload(self) -> float:
        return self.vehicle.max_payload


@dataclass(frozen=True)
class DispatchAssignment:
    """Dispatcher-selected job assignment for one vehicle."""

    vehicle_id: int
    job: Job


@dataclass(frozen=True)
class DispatchExecutionResult:
    """Stable summary of one dispatched job executed by the engine."""

    assignment: DispatchAssignment
    job_result: JobExecutionResult


class Dispatcher(Protocol):
    """Select a pending job for a vehicle without executing it."""

    def assign_job(
        self,
        *,
        pending_jobs: tuple[Job, ...],
        engine: "SimulationEngine",
        request: DispatchRequest,
    ) -> DispatchAssignment | None:
        """Return one selected job assignment or None if no job is feasible."""


class FirstFeasibleDispatcher:
    """Deterministically assign the first pending job that is feasible."""

    def assign_job(
        self,
        *,
        pending_jobs: tuple[Job, ...],
        engine: "SimulationEngine",
        request: DispatchRequest,
    ) -> DispatchAssignment | None:
        _validate_dispatch_request(request)

        for job in pending_jobs:
            if self._is_job_feasible(job=job, engine=engine, request=request):
                return DispatchAssignment(vehicle_id=request.vehicle_id, job=job)
        return None

    def _is_job_feasible(
        self,
        *,
        job: Job,
        engine: "SimulationEngine",
        request: DispatchRequest,
    ) -> bool:
        projected_node_id = request.start_node_id
        projected_payload = request.initial_payload

        for task in job.tasks:
            if isinstance(task, MoveTask):
                try:
                    engine.router.route(
                        engine.map.graph,
                        projected_node_id,
                        task.destination_node_id,
                        world_state=engine.world_state,
                    )
                except ValueError:
                    return False
                projected_node_id = task.destination_node_id
                continue

            if projected_node_id != task.node_id:
                return False

            if isinstance(task, LoadTask):
                projected_payload += task.amount
                if projected_payload > request.max_payload:
                    return False
                continue

            if task.amount > projected_payload:
                return False
            projected_payload -= task.amount

        return True


def _validate_dispatch_request(request: DispatchRequest) -> None:
    if not math.isfinite(request.max_speed) or request.max_speed <= 0.0:
        raise ValueError("max_speed must be finite and positive")
    if not math.isfinite(request.initial_payload) or request.initial_payload < 0.0:
        raise ValueError("initial_payload must be finite and non-negative")
    if not math.isfinite(request.max_payload) or request.max_payload <= 0.0:
        raise ValueError("max_payload must be finite and positive")
    if request.initial_payload > request.max_payload:
        raise ValueError("initial_payload cannot exceed max_payload")
