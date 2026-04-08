import math
import random
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.dispatcher import (
    DispatchExecutionResult,
    DispatchRequest,
    Dispatcher,
)
from autonomous_ops_sim.operations.jobs import Job, JobExecutionResult
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.simulation.reservations import (
    ConflictWait,
    ReservationTable,
    VehicleRouteRequest,
)
from autonomous_ops_sim.simulation.trace import Trace
from autonomous_ops_sim.simulation.trace import TraceEventType
from autonomous_ops_sim.simulation.vehicle_process import VehicleProcess
from autonomous_ops_sim.simulation.world_state import WorldState

if TYPE_CHECKING:
    from autonomous_ops_sim.routing.router import Router


@dataclass(frozen=True)
class MultiVehicleRouteResult:
    """Deterministic execution summary for one coordinated vehicle route."""

    vehicle_id: int
    priority: int
    route: tuple[int, ...]
    completion_time_s: float
    waits: tuple[ConflictWait, ...]


@dataclass(frozen=True)
class MultiVehicleExecutionResult:
    """Stable summary for one coordinated multi-vehicle run."""

    route_results: tuple[MultiVehicleRouteResult, ...]
    reservations: ReservationTable


@dataclass(frozen=True)
class _ScheduledTraceEvent:
    timestamp_s: float
    priority: int
    vehicle_id: int
    local_order: int
    event_type: TraceEventType
    node_id: int | None = None
    edge_id: int | None = None
    start_node_id: int | None = None
    end_node_id: int | None = None
    duration_s: float | None = None


class SimulationEngine:
    """Own deterministic state and simulated time for a single run."""

    def __init__(
        self,
        simulation_map: Map,
        world_state: WorldState,
        router: "Router",
        seed: int,
        resources: Iterable[SharedResource] = (),
    ):
        resources_tuple = tuple(resources)

        self._map = simulation_map
        self._world_state = world_state
        self._router = router
        self._seed = seed
        self._rng = random.Random(seed)
        self._simulated_time_s = 0.0
        self._trace = Trace()
        self._resources = {
            resource.resource_id: resource for resource in resources_tuple
        }
        if len(self._resources) != len(resources_tuple):
            raise ValueError("resource ids must be unique")

    @property
    def map(self) -> Map:
        """Return the static map used for this run."""

        return self._map

    @property
    def world_state(self) -> WorldState:
        """Return the runtime world state used for this run."""

        return self._world_state

    @property
    def router(self) -> "Router":
        """Return the router used for this run."""

        return self._router

    @property
    def seed(self) -> int:
        """Return the engine-owned deterministic seed."""

        return self._seed

    @property
    def trace(self) -> Trace:
        """Return the execution trace for this run."""

        return self._trace

    @property
    def rng(self) -> random.Random:
        """Return the engine-owned deterministic random stream."""

        return self._rng

    @property
    def resources(self) -> tuple[SharedResource, ...]:
        """Return shared resources available during this run."""

        return tuple(self._resources.values())

    @property
    def simulated_time_s(self) -> float:
        """Return the current simulated time."""

        return self._simulated_time_s

    def run(self, until_s: float) -> float:
        """Advance the engine's simulated time to the requested point."""

        if not math.isfinite(until_s):
            raise ValueError("until_s must be finite")
        if until_s < 0.0:
            raise ValueError("until_s must be non-negative")
        if until_s < self._simulated_time_s:
            raise ValueError(
                "until_s must be greater than or equal to current simulated time"
            )

        self._simulated_time_s = until_s
        return self._simulated_time_s

    def execute_vehicle_route(
        self,
        *,
        vehicle_id: int,
        start_node_id: int,
        destination_node_id: int,
        max_speed: float,
    ) -> tuple[int, ...]:
        """Execute one vehicle over one routed path."""

        process = VehicleProcess(
            vehicle_id=vehicle_id,
            current_node_id=start_node_id,
            max_speed=max_speed,
        )
        return process.execute_route(
            destination_node_id=destination_node_id,
            engine=self,
        )

    def execute_multi_vehicle_routes(
        self,
        *,
        requests: Iterable[VehicleRouteRequest],
    ) -> MultiVehicleExecutionResult:
        """Execute a narrow deterministic multi-vehicle route set."""

        ordered_requests = tuple(
            sorted(requests, key=lambda request: request.effective_priority)
        )
        if not ordered_requests:
            return MultiVehicleExecutionResult(
                route_results=(),
                reservations=ReservationTable(),
            )

        reservations = ReservationTable()
        route_results: list[MultiVehicleRouteResult] = []
        scheduled_events: list[_ScheduledTraceEvent] = []

        for ordered_index, request in enumerate(ordered_requests):
            route_results.append(
                self._plan_multi_vehicle_route(
                    request=request,
                    priority=ordered_index,
                    reservations=reservations,
                    scheduled_events=scheduled_events,
                )
            )

        scheduled_events.sort(
            key=lambda event: (
                event.timestamp_s,
                event.priority,
                event.vehicle_id,
                event.local_order,
            )
        )
        for event in scheduled_events:
            self.trace.emit(
                timestamp_s=event.timestamp_s,
                vehicle_id=event.vehicle_id,
                event_type=event.event_type,
                node_id=event.node_id,
                edge_id=event.edge_id,
                start_node_id=event.start_node_id,
                end_node_id=event.end_node_id,
                duration_s=event.duration_s,
            )

        completion_time_s = max(
            result.completion_time_s for result in route_results
        )
        self.run(completion_time_s)
        return MultiVehicleExecutionResult(
            route_results=tuple(route_results),
            reservations=reservations,
        )

    def get_resource(self, resource_id: str) -> SharedResource:
        """Return a configured shared resource by ID."""

        try:
            return self._resources[resource_id]
        except KeyError as exc:
            raise KeyError(f"Unknown resource_id: {resource_id}") from exc

    def execute_job(
        self,
        *,
        vehicle_id: int,
        start_node_id: int,
        max_speed: float,
        job: Job,
        initial_payload: float = 0.0,
        max_payload: float = math.inf,
    ) -> JobExecutionResult:
        """Execute one ordered job sequence for one vehicle."""

        process = VehicleProcess(
            vehicle_id=vehicle_id,
            current_node_id=start_node_id,
            max_speed=max_speed,
            payload=initial_payload,
            max_payload=max_payload,
        )
        return process.execute_job(job=job, engine=self)

    def dispatch_job(
        self,
        *,
        dispatcher: Dispatcher,
        pending_jobs: Iterable[Job],
        vehicle_id: int,
        start_node_id: int,
        max_speed: float,
        initial_payload: float = 0.0,
        max_payload: float = math.inf,
    ) -> DispatchExecutionResult | None:
        """Select and execute one pending job through the existing job path."""

        request = DispatchRequest(
            vehicle_id=vehicle_id,
            start_node_id=start_node_id,
            max_speed=max_speed,
            initial_payload=initial_payload,
            max_payload=max_payload,
        )
        assignment = dispatcher.assign_job(
            pending_jobs=tuple(pending_jobs),
            engine=self,
            request=request,
        )
        if assignment is None:
            return None

        job_result = self.execute_job(
            vehicle_id=vehicle_id,
            start_node_id=start_node_id,
            max_speed=max_speed,
            job=assignment.job,
            initial_payload=initial_payload,
            max_payload=max_payload,
        )
        return DispatchExecutionResult(
            assignment=assignment,
            job_result=job_result,
        )

    def _plan_multi_vehicle_route(
        self,
        *,
        request: VehicleRouteRequest,
        priority: int,
        reservations: ReservationTable,
        scheduled_events: list[_ScheduledTraceEvent],
    ) -> MultiVehicleRouteResult:
        if not math.isfinite(request.max_speed) or request.max_speed <= 0.0:
            raise ValueError("max_speed must be finite and positive")

        _, path = self.router.route(
            self.map.graph,
            request.start_node_id,
            request.destination_node_id,
            world_state=self.world_state,
        )
        route = tuple(path)
        current_time_s = 0.0
        waits: list[ConflictWait] = []
        local_order = 0

        def schedule(
            *,
            timestamp_s: float,
            event_type: TraceEventType,
            node_id: int | None = None,
            edge_id: int | None = None,
            start_node_id: int | None = None,
            end_node_id: int | None = None,
            duration_s: float | None = None,
        ) -> None:
            nonlocal local_order
            scheduled_events.append(
                _ScheduledTraceEvent(
                    timestamp_s=timestamp_s,
                    priority=priority,
                    vehicle_id=request.vehicle_id,
                    local_order=local_order,
                    event_type=event_type,
                    node_id=node_id,
                    edge_id=edge_id,
                    start_node_id=start_node_id,
                    end_node_id=end_node_id,
                    duration_s=duration_s,
                )
            )
            local_order += 1

        schedule(
            timestamp_s=0.0,
            event_type=TraceEventType.ROUTE_START,
            node_id=request.start_node_id,
            start_node_id=request.start_node_id,
            end_node_id=request.destination_node_id,
        )

        for start_node_id, end_node_id in zip(route, route[1:]):
            edge = self.map.get_edge_between(start_node_id, end_node_id)
            if edge is None:
                raise RuntimeError(
                    "Router returned a path containing a missing map edge: "
                    f"{start_node_id} -> {end_node_id}."
                )

            travel_time_s = edge.distance / min(request.max_speed, edge.speed_limit)
            departure_time_s = reservations.earliest_departure_time(
                current_node_id=start_node_id,
                next_node_id=end_node_id,
                not_before_s=current_time_s,
                travel_time_s=travel_time_s,
            )

            if departure_time_s > current_time_s:
                wait = ConflictWait(
                    node_id=start_node_id,
                    start_time_s=current_time_s,
                    end_time_s=departure_time_s,
                )
                waits.append(wait)
                reservations.reserve_node(
                    vehicle_id=request.vehicle_id,
                    node_id=start_node_id,
                    start_time_s=current_time_s,
                    end_time_s=departure_time_s,
                    reason="conflict_wait",
                )
                schedule(
                    timestamp_s=wait.start_time_s,
                    event_type=TraceEventType.CONFLICT_WAIT_START,
                    node_id=start_node_id,
                    duration_s=wait.duration_s,
                )
                schedule(
                    timestamp_s=wait.end_time_s,
                    event_type=TraceEventType.CONFLICT_WAIT_COMPLETE,
                    node_id=start_node_id,
                    duration_s=wait.duration_s,
                )

            arrival_time_s = departure_time_s + travel_time_s
            reservations.reserve_edge(
                vehicle_id=request.vehicle_id,
                edge_id=edge.id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                start_time_s=departure_time_s,
                end_time_s=arrival_time_s,
            )
            schedule(
                timestamp_s=departure_time_s,
                event_type=TraceEventType.EDGE_ENTER,
                edge_id=edge.id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
            )
            schedule(
                timestamp_s=arrival_time_s,
                event_type=TraceEventType.NODE_ARRIVAL,
                node_id=end_node_id,
                start_node_id=start_node_id,
                end_node_id=end_node_id,
            )
            current_time_s = arrival_time_s

        reservations.reserve_node(
            vehicle_id=request.vehicle_id,
            node_id=route[-1],
            start_time_s=current_time_s,
            end_time_s=math.inf,
            reason="route_complete",
        )
        schedule(
            timestamp_s=current_time_s,
            event_type=TraceEventType.ROUTE_COMPLETE,
            node_id=route[-1],
            start_node_id=route[0],
            end_node_id=request.destination_node_id,
        )
        return MultiVehicleRouteResult(
            vehicle_id=request.vehicle_id,
            priority=priority,
            route=route,
            completion_time_s=current_time_s,
            waits=tuple(waits),
        )
