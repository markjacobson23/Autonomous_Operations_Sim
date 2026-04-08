from dataclasses import dataclass

from autonomous_ops_sim.operations.tasks import JobTask


@dataclass(frozen=True)
class Job:
    """Ordered operational work to execute for a single vehicle."""

    id: str
    tasks: tuple[JobTask, ...]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("job id must be non-empty")
        if not self.tasks:
            raise ValueError("job must contain at least one task")


@dataclass(frozen=True)
class JobExecutionResult:
    """Stable summary of one completed job execution."""

    job_id: str
    completed_task_count: int
    final_node_id: int
    final_payload: float
