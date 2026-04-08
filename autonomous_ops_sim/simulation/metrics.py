from collections import Counter
from dataclasses import dataclass

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.trace import Trace, TraceEventType


@dataclass(frozen=True)
class TraceEventCount:
    """Stable count for one trace event type."""

    event_type: str
    count: int


@dataclass(frozen=True)
class ExecutionMetricsSummary:
    """Derived, regression-friendly metrics for one simulator run."""

    seed: int
    final_time_s: float
    trace_event_count: int
    vehicle_ids: tuple[int, ...]
    route_count: int
    completed_job_count: int
    completed_task_count: int
    edge_traversal_count: int
    node_arrival_count: int
    total_route_distance: float
    total_service_time_s: float
    total_resource_wait_time_s: float
    total_conflict_wait_time_s: float
    event_counts: tuple[TraceEventCount, ...]


def summarize_engine_execution(engine: SimulationEngine) -> ExecutionMetricsSummary:
    """Build a stable metrics summary from one completed engine run."""

    return summarize_trace(
        trace=engine.trace,
        simulation_map=engine.map,
        seed=engine.seed,
        final_time_s=engine.simulated_time_s,
    )


def summarize_trace(
    *,
    trace: Trace,
    simulation_map: Map,
    seed: int,
    final_time_s: float,
) -> ExecutionMetricsSummary:
    """Build a stable metrics summary from an existing trace surface."""

    event_counts = Counter(event.event_type.value for event in trace.events)
    vehicle_ids = tuple(sorted({event.vehicle_id for event in trace.events}))
    total_route_distance = 0.0
    total_service_time_s = 0.0
    total_resource_wait_time_s = 0.0
    total_conflict_wait_time_s = 0.0

    for event in trace.events:
        if event.event_type == TraceEventType.EDGE_ENTER:
            if event.edge_id is None:
                raise ValueError("edge_enter events must include edge_id")
            total_route_distance += simulation_map.graph.edges[event.edge_id].distance
        elif event.event_type == TraceEventType.SERVICE_COMPLETE:
            total_service_time_s += _required_duration(event_type=event.event_type, duration_s=event.duration_s)
        elif event.event_type == TraceEventType.RESOURCE_WAIT_COMPLETE:
            total_resource_wait_time_s += _required_duration(
                event_type=event.event_type,
                duration_s=event.duration_s,
            )
        elif event.event_type == TraceEventType.CONFLICT_WAIT_COMPLETE:
            total_conflict_wait_time_s += _required_duration(
                event_type=event.event_type,
                duration_s=event.duration_s,
            )

    return ExecutionMetricsSummary(
        seed=seed,
        final_time_s=final_time_s,
        trace_event_count=len(trace.events),
        vehicle_ids=vehicle_ids,
        route_count=event_counts[TraceEventType.ROUTE_COMPLETE.value],
        completed_job_count=event_counts[TraceEventType.JOB_COMPLETE.value],
        completed_task_count=event_counts[TraceEventType.TASK_COMPLETE.value],
        edge_traversal_count=event_counts[TraceEventType.EDGE_ENTER.value],
        node_arrival_count=event_counts[TraceEventType.NODE_ARRIVAL.value],
        total_route_distance=total_route_distance,
        total_service_time_s=total_service_time_s,
        total_resource_wait_time_s=total_resource_wait_time_s,
        total_conflict_wait_time_s=total_conflict_wait_time_s,
        event_counts=tuple(
            TraceEventCount(event_type=event_type, count=count)
            for event_type, count in sorted(event_counts.items())
        ),
    )


def _required_duration(*, event_type: TraceEventType, duration_s: float | None) -> float:
    if duration_s is None:
        raise ValueError(f"{event_type.value} events must include duration_s")
    return duration_s
