from dataclasses import dataclass
import math

from autonomous_ops_sim.io.exports import export_engine_json
from autonomous_ops_sim.maps.graph_map import make_graph_map
from autonomous_ops_sim.maps.grid_map import make_grid_map
from autonomous_ops_sim.operations import FirstFeasibleDispatcher
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.operations.tasks import LoadTask, MoveTask, UnloadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation.engine import SimulationEngine
from autonomous_ops_sim.simulation.metrics import (
    ExecutionMetricsSummary,
    summarize_engine_execution,
)
from autonomous_ops_sim.simulation.reservations import VehicleRouteRequest
from autonomous_ops_sim.simulation.scenario import (
    DispatchVehicleJobQueueExecutionSpec,
    DispatchVehicleJobsExecutionSpec,
    DispatcherSpec,
    JobSpec,
    LoadTaskSpec,
    MapSpec,
    MoveTaskSpec,
    MultiVehicleRouteBatchExecutionSpec,
    MultiVehicleRouteBatchSpec,
    MultiVehicleRouteRequestSpec,
    ResourceSpec,
    Scenario,
    ScenarioTaskSpec,
    SingleVehicleJobExecutionSpec,
    WorldStateSpec,
)
from autonomous_ops_sim.simulation.workload_runner import run_dispatch_job_queue
from autonomous_ops_sim.simulation.world_state import WorldState
from autonomous_ops_sim.vehicles.vehicle import Vehicle, VehicleType


@dataclass(frozen=True)
class ScenarioExecutionResult:
    """Stable result surface for one scenario-driven simulator run."""

    engine: SimulationEngine
    summary: ExecutionMetricsSummary
    export_json: str


def build_scenario_engine(scenario: Scenario) -> SimulationEngine:
    """Build an unexecuted engine for one parsed scenario."""

    simulation_map = _build_map(map_spec=scenario.map_spec)
    world_state = _build_world_state(
        simulation_map=simulation_map,
        world_state_spec=scenario.world_state,
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=world_state,
        router=Router(),
        seed=scenario.seed,
        resources=_build_resources(scenario.resources),
        vehicles=_build_runtime_vehicles(
            scenario=scenario,
            simulation_map=simulation_map,
        ),
    )


def execute_scenario(scenario: Scenario) -> ScenarioExecutionResult:
    """Execute one narrow scenario configuration through the real simulator."""

    if scenario.execution is None:
        raise ValueError("Scenario does not define an executable 'execution' section.")

    engine = build_scenario_engine(scenario)

    vehicle = (
        None
        if isinstance(scenario.execution, MultiVehicleRouteBatchExecutionSpec)
        else _get_execution_vehicle(engine=engine, scenario=scenario)
    )
    _execute_configured_work(
        engine=engine,
        scenario=scenario,
        simulation_map=engine.map,
        vehicle=vehicle,
    )

    if engine.simulated_time_s > scenario.duration_s:
        raise ValueError(
            "Scenario execution exceeded configured duration_s: "
            f"{engine.simulated_time_s} > {scenario.duration_s}"
        )
    if not math.isfinite(engine.simulated_time_s):
        raise RuntimeError("Scenario execution produced a non-finite simulated time.")
    if engine.simulated_time_s < 0.0:
        raise RuntimeError("Scenario execution produced a negative simulated time.")

    summary = summarize_engine_execution(engine)
    return ScenarioExecutionResult(
        engine=engine,
        summary=summary,
        export_json=export_engine_json(engine, summary=summary),
    )


def _build_map(*, map_spec: MapSpec):
    if map_spec.kind == "grid":
        grid_size = map_spec.params.get("grid_size")
        if not isinstance(grid_size, int):
            raise ValueError("Grid scenario execution requires integer params.grid_size.")
        return make_grid_map(grid_size)

    if map_spec.kind == "graph":
        nodes = map_spec.params.get("nodes")
        edges = map_spec.params.get("edges")
        render_geometry = map_spec.params.get("render_geometry")
        world_model = map_spec.params.get("world_model")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError(
                "Graph scenario execution requires list params.nodes and params.edges."
            )
        if render_geometry is not None and not isinstance(render_geometry, dict):
            raise ValueError(
                "Graph scenario execution params.render_geometry must be an object if provided."
            )
        if world_model is not None and not isinstance(world_model, dict):
            raise ValueError(
                "Graph scenario execution params.world_model must be an object if provided."
            )
        return make_graph_map(
            nodes=tuple(nodes),
            edges=tuple(edges),
            render_geometry=render_geometry,
            world_model=world_model,
        )

    raise ValueError(f"Unsupported map kind for execution: {map_spec.kind!r}")


def _build_world_state(*, simulation_map, world_state_spec: WorldStateSpec) -> WorldState:
    world_state = WorldState(simulation_map.graph)
    for blocked_edge in world_state_spec.blocked_edges:
        start_node_id = _resolve_node_id(
            simulation_map=simulation_map,
            position=blocked_edge.start_position,
            label="blocked edge start position",
        )
        end_node_id = _resolve_node_id(
            simulation_map=simulation_map,
            position=blocked_edge.end_position,
            label="blocked edge end position",
        )
        edge = simulation_map.get_edge_between(start_node_id, end_node_id)
        if edge is None:
            raise ValueError(
                "Scenario blocked edge "
                f"{blocked_edge.start_position} -> {blocked_edge.end_position} "
                "is not present in the map."
            )
        world_state.block_edge(edge.id)
    return world_state


def _build_resources(resource_specs: tuple[ResourceSpec, ...]) -> tuple[SharedResource, ...]:
    return tuple(
        SharedResource(
            resource_spec.resource_id,
            capacity=resource_spec.capacity,
            initial_available_times_s=resource_spec.initial_available_times_s,
        )
        for resource_spec in resource_specs
    )


def _build_runtime_vehicles(*, scenario: Scenario, simulation_map) -> tuple[Vehicle, ...]:
    return tuple(
        Vehicle(
            id=vehicle_spec.id,
            current_node_id=_resolve_node_id(
                simulation_map=simulation_map,
                position=vehicle_spec.position,
                label=f"vehicle {vehicle_spec.id} start position",
            ),
            position=vehicle_spec.position,
            velocity=vehicle_spec.velocity,
            payload=vehicle_spec.payload,
            max_payload=vehicle_spec.max_payload,
            max_speed=vehicle_spec.max_speed,
            vehicle_type=vehicle_spec.vehicle_type or VehicleType.GENERIC,
        )
        for vehicle_spec in scenario.vehicles
    )


def _get_execution_vehicle(*, engine: SimulationEngine, scenario: Scenario) -> Vehicle:
    assert scenario.execution is not None

    execution = scenario.execution
    if isinstance(
        execution,
        (SingleVehicleJobExecutionSpec, DispatchVehicleJobsExecutionSpec, DispatchVehicleJobQueueExecutionSpec),
    ):
        return engine.get_vehicle(execution.vehicle_id)

    raise ValueError("Scenario execution does not define a single execution vehicle.")


def _execute_configured_work(
    *,
    engine: SimulationEngine,
    scenario: Scenario,
    simulation_map,
    vehicle: Vehicle | None,
) -> None:
    assert scenario.execution is not None

    execution = scenario.execution
    if isinstance(execution, SingleVehicleJobExecutionSpec):
        assert vehicle is not None
        engine.execute_job(
            vehicle=vehicle,
            job=_build_job(
                simulation_map=simulation_map,
                job_spec=execution.job,
            ),
        )
        return

    if isinstance(execution, MultiVehicleRouteBatchExecutionSpec):
        _execute_multi_vehicle_route_batches(
            engine=engine,
            simulation_map=simulation_map,
            route_batches=execution.route_batches,
        )
        return

    if not isinstance(execution, DispatchVehicleJobsExecutionSpec):
        if not isinstance(execution, DispatchVehicleJobQueueExecutionSpec):
            raise ValueError(f"Unsupported scenario execution type: {type(execution)!r}")

        assert vehicle is not None
        workload_result = run_dispatch_job_queue(
            engine=engine,
            dispatcher=_build_dispatcher(dispatcher_spec=scenario.dispatcher),
            pending_jobs=tuple(
                _build_job(simulation_map=simulation_map, job_spec=job_spec)
                for job_spec in execution.jobs
            ),
            vehicle=vehicle,
        )
        if workload_result.remaining_job_ids:
            remaining_jobs_str = ", ".join(workload_result.remaining_job_ids)
            raise ValueError(
                "Scenario workload did not complete all pending jobs: "
                f"{remaining_jobs_str}"
            )
        return

    dispatch_result = engine.dispatch_job(
        dispatcher=_build_dispatcher(dispatcher_spec=scenario.dispatcher),
        pending_jobs=tuple(
            _build_job(simulation_map=simulation_map, job_spec=job_spec)
            for job_spec in execution.jobs
        ),
        vehicle=vehicle,
    )
    if dispatch_result is None:
        raise ValueError("Scenario dispatcher did not assign a feasible job.")


def _execute_multi_vehicle_route_batches(
    *,
    engine: SimulationEngine,
    simulation_map,
    route_batches: tuple[MultiVehicleRouteBatchSpec, ...],
) -> None:
    for route_batch in route_batches:
        requests = tuple(
            _build_vehicle_route_request(
                engine=engine,
                simulation_map=simulation_map,
                request=request_spec,
            )
            for request_spec in route_batch.requests
        )
        result = engine.execute_multi_vehicle_routes(requests=requests)
        for route_result in result.route_results:
            vehicle = engine.get_vehicle(route_result.vehicle_id)
            destination_node_id = route_result.route[-1]
            vehicle.move_to_node(
                node_id=destination_node_id,
                position=simulation_map.get_position(destination_node_id),
            )
            vehicle.set_velocity(0.0)


def _build_vehicle_route_request(
    *,
    engine: SimulationEngine,
    simulation_map,
    request: MultiVehicleRouteRequestSpec,
):
    vehicle = engine.get_vehicle(request.vehicle_id)
    destination_node_id = _resolve_node_id(
        simulation_map=simulation_map,
        position=request.destination,
        label=f"vehicle {request.vehicle_id} route destination",
    )
    return VehicleRouteRequest(
        vehicle_id=request.vehicle_id,
        start_node_id=vehicle.current_node_id,
        destination_node_id=destination_node_id,
        max_speed=vehicle.max_speed,
        priority=request.priority,
    )


def _build_dispatcher(*, dispatcher_spec: DispatcherSpec | None):
    if dispatcher_spec is None:
        raise ValueError("Scenario dispatch execution requires a configured dispatcher.")
    if dispatcher_spec.kind != "first_feasible":
        raise ValueError(
            f"Unsupported dispatcher kind for execution: {dispatcher_spec.kind!r}"
        )
    return FirstFeasibleDispatcher()


def _build_job(*, simulation_map, job_spec: JobSpec) -> Job:
    return Job(
        id=job_spec.id,
        tasks=tuple(
            _build_task(simulation_map=simulation_map, task_spec=task_spec)
            for task_spec in job_spec.tasks
        ),
    )


def _build_task(*, simulation_map, task_spec: ScenarioTaskSpec):
    if isinstance(task_spec, MoveTaskSpec):
        return MoveTask(
            destination_node_id=_resolve_node_id(
                simulation_map=simulation_map,
                position=task_spec.destination,
                label="move task destination",
            )
        )
    if isinstance(task_spec, LoadTaskSpec):
        return LoadTask(
            node_id=_resolve_node_id(
                simulation_map=simulation_map,
                position=task_spec.position,
                label="load task position",
            ),
            amount=task_spec.amount,
            service_duration_s=task_spec.service_duration_s,
            resource_id=task_spec.resource_id,
        )
    return UnloadTask(
        node_id=_resolve_node_id(
            simulation_map=simulation_map,
            position=task_spec.position,
            label="unload task position",
        ),
        amount=task_spec.amount,
        service_duration_s=task_spec.service_duration_s,
        resource_id=task_spec.resource_id,
    )


def _resolve_node_id(*, simulation_map, position: tuple[float, float, float], label: str) -> int:
    try:
        return simulation_map.get_node_id(position)
    except KeyError as exc:
        raise ValueError(f"Scenario {label} {position} is not present in the map.") from exc
