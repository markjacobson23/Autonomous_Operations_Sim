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
from autonomous_ops_sim.simulation.behavior import (
    VehicleBehaviorController,
    VehicleOperationalState,
)
from autonomous_ops_sim.simulation.reservations import (
    ConflictWait,
    ReservationTable,
    VehicleRouteRequest,
)
from autonomous_ops_sim.simulation.trace import Trace
from autonomous_ops_sim.simulation.trace import TraceEventType
from autonomous_ops_sim.simulation.vehicle_process import VehicleProcess
from autonomous_ops_sim.simulation.world_state import WorldState
from autonomous_ops_sim.vehicles.vehicle import Vehicle

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
    from_behavior_state: str | None = None
    to_behavior_state: str | None = None
    transition_reason: str | None = None


class SimulationEngine:
    """Own deterministic state and simulated time for a single run."""

    def __init__(
        self,
        simulation_map: Map,
        world_state: WorldState,
        router: "Router",
        seed: int,
        resources: Iterable[SharedResource] = (),
        vehicles: Iterable[Vehicle] = (),
    ):
        resources_tuple = tuple(resources)
        vehicles_tuple = tuple(vehicles)

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
        self._vehicles = {vehicle.id: vehicle for vehicle in vehicles_tuple}
        if len(self._resources) != len(resources_tuple):
            raise ValueError("resource ids must be unique")
        if len(self._vehicles) != len(vehicles_tuple):
            raise ValueError("vehicle ids must be unique")

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
    def vehicles(self) -> tuple[Vehicle, ...]:
        """Return runtime vehicles available during this run."""

        return tuple(
            vehicle
            for _, vehicle in sorted(self._vehicles.items(), key=lambda item: item[0])
        )

    @property
    def simulated_time_s(self) -> float:
        """Return the current simulated time."""

        return self._simulated_time_s

    def run(self, until_s: float) -> float:
        """Advance the deterministic simulator clock to an explicit target time.

        This engine does not run a continuous physics loop. Higher-level execution
        paths advance simulated time explicitly while emitting deterministic events.
        """

        self._validate_simulated_time_target(until_s)

        self._simulated_time_s = until_s
        return self._simulated_time_s

    def execute_vehicle_route(
        self,
        *,
        vehicle: Vehicle | None = None,
        vehicle_id: int | None = None,
        start_node_id: int | None = None,
        destination_node_id: int,
        max_speed: float | None = None,
    ) -> tuple[int, ...]:
        """Execute one vehicle over one routed path."""

        runtime_vehicle = self._resolve_runtime_vehicle(
            vehicle=vehicle,
            vehicle_id=vehicle_id,
            start_node_id=start_node_id,
            max_speed=max_speed,
        )
        process = VehicleProcess(vehicle=runtime_vehicle)
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
                from_behavior_state=event.from_behavior_state,
                to_behavior_state=event.to_behavior_state,
                transition_reason=event.transition_reason,
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

    def has_vehicle(self, vehicle_id: int) -> bool:
        """Return whether a runtime vehicle is registered for this run."""

        return vehicle_id in self._vehicles

    def has_node(self, node_id: int) -> bool:
        """Return whether the engine map contains the given node."""

        return self._map.graph.has_node(node_id)

    def has_edge(self, edge_id: int) -> bool:
        """Return whether the engine map contains the given edge."""

        return self._map.graph.has_edge(edge_id)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        """Return a configured runtime vehicle by ID."""

        try:
            return self._vehicles[vehicle_id]
        except KeyError as exc:
            raise KeyError(f"Unknown vehicle_id: {vehicle_id}") from exc

    def add_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """Register one runtime vehicle for the active run."""

        existing_vehicle = self._vehicles.get(vehicle.id)
        if existing_vehicle is not None and existing_vehicle is not vehicle:
            raise ValueError(
                f"vehicle_id {vehicle.id} is already registered to a different vehicle"
            )
        vehicle.is_active = True
        self._vehicles[vehicle.id] = vehicle
        return vehicle

    def remove_vehicle(self, vehicle_id: int) -> Vehicle:
        """Retire one runtime vehicle from the active run."""

        vehicle = self.get_vehicle(vehicle_id)
        vehicle.deactivate()
        return vehicle

    def execute_job(
        self,
        *,
        vehicle: Vehicle | None = None,
        vehicle_id: int | None = None,
        start_node_id: int | None = None,
        max_speed: float | None = None,
        job: Job,
        initial_payload: float | None = None,
        max_payload: float | None = None,
    ) -> JobExecutionResult:
        """Execute one ordered job sequence for one vehicle."""

        runtime_vehicle = self._resolve_runtime_vehicle(
            vehicle=vehicle,
            vehicle_id=vehicle_id,
            start_node_id=start_node_id,
            max_speed=max_speed,
            initial_payload=initial_payload,
            max_payload=max_payload,
        )
        process = VehicleProcess(vehicle=runtime_vehicle)
        return process.execute_job(job=job, engine=self)

    def dispatch_job(
        self,
        *,
        dispatcher: Dispatcher,
        pending_jobs: Iterable[Job],
        vehicle: Vehicle | None = None,
        vehicle_id: int | None = None,
        start_node_id: int | None = None,
        max_speed: float | None = None,
        initial_payload: float | None = None,
        max_payload: float | None = None,
    ) -> DispatchExecutionResult | None:
        """Select and execute one pending job through the existing job path."""

        runtime_vehicle = self._resolve_runtime_vehicle(
            vehicle=vehicle,
            vehicle_id=vehicle_id,
            start_node_id=start_node_id,
            max_speed=max_speed,
            initial_payload=initial_payload,
            max_payload=max_payload,
        )
        request = DispatchRequest(vehicle=runtime_vehicle)
        assignment = dispatcher.assign_job(
            pending_jobs=tuple(pending_jobs),
            engine=self,
            request=request,
        )
        if assignment is None:
            return None

        job_result = self.execute_job(
            vehicle=runtime_vehicle,
            job=assignment.job,
        )
        return DispatchExecutionResult(
            assignment=assignment,
            job_result=job_result,
        )

    def _resolve_runtime_vehicle(
        self,
        *,
        vehicle: Vehicle | None,
        vehicle_id: int | None,
        start_node_id: int | None,
        max_speed: float | None,
        initial_payload: float | None = None,
        max_payload: float | None = None,
    ) -> Vehicle:
        if vehicle is not None:
            provided_scalars = (
                vehicle_id,
                start_node_id,
                max_speed,
                initial_payload,
                max_payload,
            )
            if any(value is not None for value in provided_scalars):
                raise ValueError(
                    "vehicle-backed execution does not accept duplicate "
                    "scalar vehicle inputs"
                )
            existing_vehicle = self._vehicles.get(vehicle.id)
            if existing_vehicle is not None and existing_vehicle is not vehicle:
                raise ValueError(
                    f"vehicle_id {vehicle.id} is already registered to a different vehicle"
                )
            self._vehicles.setdefault(vehicle.id, vehicle)
            return self._vehicles[vehicle.id]

        missing_fields = [
            name
            for name, value in (
                ("vehicle_id", vehicle_id),
                ("start_node_id", start_node_id),
                ("max_speed", max_speed),
            )
            if value is None
        ]
        if missing_fields:
            missing_str = ", ".join(missing_fields)
            raise ValueError(
                "scalar vehicle execution requires explicit values for: "
                f"{missing_str}"
            )

        assert vehicle_id is not None
        assert start_node_id is not None
        assert max_speed is not None
        return Vehicle(
            id=vehicle_id,
            current_node_id=start_node_id,
            position=self.map.get_position(start_node_id),
            velocity=0.0,
            payload=0.0 if initial_payload is None else initial_payload,
            max_payload=math.inf if max_payload is None else max_payload,
            max_speed=max_speed,
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
        behavior = VehicleBehaviorController(vehicle_id=request.vehicle_id)

        def schedule(
            *,
            timestamp_s: float,
            event_type: TraceEventType,
            node_id: int | None = None,
            edge_id: int | None = None,
            start_node_id: int | None = None,
            end_node_id: int | None = None,
            duration_s: float | None = None,
            from_behavior_state: str | None = None,
            to_behavior_state: str | None = None,
            transition_reason: str | None = None,
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
                    from_behavior_state=from_behavior_state,
                    to_behavior_state=to_behavior_state,
                    transition_reason=transition_reason,
                )
            )
            local_order += 1

        def transition_behavior(
            *,
            timestamp_s: float,
            node_id: int,
            to_state: VehicleOperationalState,
            reason: str,
        ) -> None:
            transition = behavior.transition_to(to_state, reason=reason)
            schedule(
                timestamp_s=timestamp_s,
                event_type=TraceEventType.BEHAVIOR_TRANSITION,
                node_id=node_id,
                from_behavior_state=transition.from_state.value,
                to_behavior_state=transition.to_state.value,
                transition_reason=transition.reason,
            )

        if len(route) == 1:
            transition_behavior(
                timestamp_s=0.0,
                node_id=request.start_node_id,
                to_state=VehicleOperationalState.MOVING,
                reason="route_start",
            )
            schedule(
                timestamp_s=0.0,
                event_type=TraceEventType.ROUTE_START,
                node_id=request.start_node_id,
                start_node_id=request.start_node_id,
                end_node_id=request.destination_node_id,
            )
            schedule(
                timestamp_s=0.0,
                event_type=TraceEventType.ROUTE_COMPLETE,
                node_id=route[-1],
                start_node_id=route[0],
                end_node_id=request.destination_node_id,
            )
            transition_behavior(
                timestamp_s=0.0,
                node_id=route[-1],
                to_state=VehicleOperationalState.IDLE,
                reason="route_complete",
            )
            reservations.reserve_node(
                vehicle_id=request.vehicle_id,
                node_id=route[-1],
                start_time_s=0.0,
                end_time_s=math.inf,
                reason="route_complete",
            )
            return MultiVehicleRouteResult(
                vehicle_id=request.vehicle_id,
                priority=priority,
                route=route,
                completion_time_s=0.0,
                waits=(),
            )

        active_node_id = request.start_node_id

        for segment_index, (start_node_id, end_node_id) in enumerate(
            zip(route, route[1:])
        ):
            edge = self.map.get_edge_between(start_node_id, end_node_id)
            if edge is None:
                raise RuntimeError(
                    "Router returned a path containing a missing map edge: "
                    f"{start_node_id} -> {end_node_id}."
                )

            travel_time_s = edge.distance / min(request.max_speed, edge.speed_limit)
            corridor_node_ids = self._resolve_corridor_node_ids(
                route=route,
                segment_index=segment_index,
            )
            corridor_travel_time_s = None
            if corridor_node_ids is not None:
                corridor_travel_time_s = self._calculate_path_travel_time(
                    node_ids=corridor_node_ids,
                    max_speed=request.max_speed,
                )
            departure_time_s = reservations.earliest_departure_time(
                vehicle_id=request.vehicle_id,
                current_node_id=start_node_id,
                next_node_id=end_node_id,
                not_before_s=current_time_s,
                travel_time_s=travel_time_s,
                corridor_node_ids=corridor_node_ids,
                corridor_travel_time_s=corridor_travel_time_s,
            )

            if departure_time_s > current_time_s:
                if behavior.state == VehicleOperationalState.IDLE:
                    transition_behavior(
                        timestamp_s=current_time_s,
                        node_id=start_node_id,
                        to_state=VehicleOperationalState.CONFLICT_WAIT,
                        reason="conflict_wait_start",
                    )
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

            if behavior.state == VehicleOperationalState.IDLE:
                transition_behavior(
                    timestamp_s=departure_time_s,
                    node_id=start_node_id,
                    to_state=VehicleOperationalState.MOVING,
                    reason="route_start",
                )
                schedule(
                    timestamp_s=departure_time_s,
                    event_type=TraceEventType.ROUTE_START,
                    node_id=request.start_node_id,
                    start_node_id=request.start_node_id,
                    end_node_id=request.destination_node_id,
                )
            elif behavior.state == VehicleOperationalState.CONFLICT_WAIT:
                transition_behavior(
                    timestamp_s=departure_time_s,
                    node_id=start_node_id,
                    to_state=VehicleOperationalState.MOVING,
                    reason="conflict_wait_complete",
                )

            arrival_time_s = departure_time_s + travel_time_s
            if corridor_node_ids is not None and corridor_travel_time_s is not None:
                reservations.reserve_corridor(
                    vehicle_id=request.vehicle_id,
                    node_ids=corridor_node_ids,
                    start_time_s=departure_time_s,
                    end_time_s=departure_time_s + corridor_travel_time_s,
                )
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
            active_node_id = end_node_id

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
        transition = behavior.transition_to(
            VehicleOperationalState.IDLE,
            reason="route_complete",
        )
        schedule(
            timestamp_s=current_time_s,
            event_type=TraceEventType.BEHAVIOR_TRANSITION,
            node_id=active_node_id,
            from_behavior_state=transition.from_state.value,
            to_behavior_state=transition.to_state.value,
            transition_reason=transition.reason,
        )
        return MultiVehicleRouteResult(
            vehicle_id=request.vehicle_id,
            priority=priority,
            route=route,
            completion_time_s=current_time_s,
            waits=tuple(waits),
        )

    def _resolve_corridor_node_ids(
        self,
        *,
        route: tuple[int, ...],
        segment_index: int,
    ) -> tuple[int, ...] | None:
        corridor_end_index = segment_index + 1

        while corridor_end_index < len(route) - 1 and self._is_corridor_internal_node(
            previous_node_id=route[corridor_end_index - 1],
            node_id=route[corridor_end_index],
            next_node_id=route[corridor_end_index + 1],
        ):
            corridor_end_index += 1

        corridor_node_ids = route[segment_index : corridor_end_index + 1]
        if len(corridor_node_ids) < 3:
            return None
        return corridor_node_ids

    def _is_corridor_internal_node(
        self,
        *,
        previous_node_id: int,
        node_id: int,
        next_node_id: int,
    ) -> bool:
        if previous_node_id == next_node_id:
            return False

        undirected_neighbors = self._get_undirected_neighbor_ids(node_id)
        return len(undirected_neighbors) == 2 and undirected_neighbors == {
            previous_node_id,
            next_node_id,
        }

    def _get_undirected_neighbor_ids(self, node_id: int) -> set[int]:
        neighbor_ids = set(self.map.get_neighbors(node_id))
        for candidate_node_id in self.map.get_all_node_ids():
            if candidate_node_id == node_id:
                continue
            if self.map.get_edge_between(candidate_node_id, node_id) is not None:
                neighbor_ids.add(candidate_node_id)
        return neighbor_ids

    def _calculate_path_travel_time(
        self,
        *,
        node_ids: tuple[int, ...],
        max_speed: float,
    ) -> float:
        travel_time_s = 0.0

        for start_node_id, end_node_id in zip(node_ids, node_ids[1:]):
            edge = self.map.get_edge_between(start_node_id, end_node_id)
            if edge is None:
                raise RuntimeError(
                    "Router returned a path containing a missing map edge: "
                    f"{start_node_id} -> {end_node_id}."
                )
            travel_time_s += edge.distance / min(max_speed, edge.speed_limit)

        return travel_time_s

    def _validate_simulated_time_target(self, until_s: float) -> None:
        """Reject invalid simulator clock targets before mutation."""

        if not math.isfinite(until_s):
            raise ValueError("until_s must be finite")
        if until_s < 0.0:
            raise ValueError("until_s must be non-negative")
        if until_s < self._simulated_time_s:
            raise ValueError(
                "until_s must be greater than or equal to current simulated time"
            )
