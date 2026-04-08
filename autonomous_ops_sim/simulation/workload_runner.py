from dataclasses import dataclass

from autonomous_ops_sim.operations.dispatcher import Dispatcher
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.vehicles.vehicle import Vehicle

if False:  # pragma: no cover
    from autonomous_ops_sim.simulation.engine import SimulationEngine


@dataclass(frozen=True)
class DispatchWorkloadResult:
    """Stable summary for one repeated single-vehicle dispatch workload."""

    completed_job_ids: tuple[str, ...]
    remaining_job_ids: tuple[str, ...]


def run_dispatch_job_queue(
    *,
    engine: "SimulationEngine",
    dispatcher: Dispatcher,
    pending_jobs: tuple[Job, ...],
    vehicle: Vehicle,
) -> DispatchWorkloadResult:
    """Repeatedly dispatch pending jobs for one persistent vehicle."""

    remaining_jobs = pending_jobs
    completed_job_ids: list[str] = []

    while remaining_jobs:
        dispatch_result = engine.dispatch_job(
            dispatcher=dispatcher,
            pending_jobs=remaining_jobs,
            vehicle=vehicle,
        )
        if dispatch_result is None:
            break

        completed_job_ids.append(dispatch_result.assignment.job.id)
        remaining_jobs = _remove_selected_job(
            pending_jobs=remaining_jobs,
            selected_job=dispatch_result.assignment.job,
        )

    return DispatchWorkloadResult(
        completed_job_ids=tuple(completed_job_ids),
        remaining_job_ids=tuple(job.id for job in remaining_jobs),
    )


def _remove_selected_job(
    *,
    pending_jobs: tuple[Job, ...],
    selected_job: Job,
) -> tuple[Job, ...]:
    remaining_jobs: list[Job] = []
    removed = False

    for job in pending_jobs:
        if not removed and job is selected_job:
            removed = True
            continue
        remaining_jobs.append(job)

    if not removed:
        raise RuntimeError("Dispatcher selected a job that was not in the pending queue.")

    return tuple(remaining_jobs)
