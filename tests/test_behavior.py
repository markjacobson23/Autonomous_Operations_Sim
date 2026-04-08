import pytest

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.operations.jobs import Job
from autonomous_ops_sim.operations.resources import SharedResource
from autonomous_ops_sim.operations.tasks import LoadTask
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import SimulationEngine, TraceEventType, WorldState
from autonomous_ops_sim.simulation.behavior import (
    InvalidBehaviorTransitionError,
    VehicleBehaviorController,
    VehicleOperationalState,
)
from autonomous_ops_sim.simulation.vehicle_process import VehicleProcess


def build_behavior_engine(*, resources: tuple[SharedResource, ...] = ()) -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (5.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_edge(Edge(1, node_1, node_2, 5.0, 5.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (5.0, 0.0, 0.0): 2,
        },
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=23,
        resources=resources,
    )


def test_vehicle_behavior_controller_allows_explicit_valid_transitions():
    controller = VehicleBehaviorController(vehicle_id=7)

    controller.transition_to(VehicleOperationalState.MOVING, reason="route_start")
    controller.transition_to(VehicleOperationalState.CONFLICT_WAIT, reason="yield")
    controller.fail(reason="blocked")
    controller.recover(reason="manual_reset")
    controller.transition_to(VehicleOperationalState.SERVICING, reason="service_start")
    controller.transition_to(VehicleOperationalState.IDLE, reason="service_complete")

    assert controller.state == VehicleOperationalState.IDLE
    assert [
        (transition.from_state, transition.to_state, transition.reason)
        for transition in controller.transition_history
    ] == [
        (VehicleOperationalState.IDLE, VehicleOperationalState.MOVING, "route_start"),
        (
            VehicleOperationalState.MOVING,
            VehicleOperationalState.CONFLICT_WAIT,
            "yield",
        ),
        (
            VehicleOperationalState.CONFLICT_WAIT,
            VehicleOperationalState.FAILED,
            "blocked",
        ),
        (VehicleOperationalState.FAILED, VehicleOperationalState.IDLE, "manual_reset"),
        (
            VehicleOperationalState.IDLE,
            VehicleOperationalState.SERVICING,
            "service_start",
        ),
        (
            VehicleOperationalState.SERVICING,
            VehicleOperationalState.IDLE,
            "service_complete",
        ),
    ]


def test_vehicle_behavior_controller_rejects_invalid_transitions_clearly():
    controller = VehicleBehaviorController(vehicle_id=12)
    controller.transition_to(VehicleOperationalState.FAILED, reason="force_failure")

    with pytest.raises(
        InvalidBehaviorTransitionError,
        match="Invalid behavior transition for Vehicle-12: failed -> servicing",
    ):
        controller.transition_to(VehicleOperationalState.SERVICING, reason="invalid_jump")


def test_process_failure_and_explicit_recovery_are_tracked_through_behavior_state():
    engine = build_behavior_engine()
    process = VehicleProcess(
        vehicle_id=101,
        current_node_id=1,
        max_speed=5.0,
        payload=0.0,
        max_payload=5.0,
    )
    failing_job = Job(
        id="bad-unload",
        tasks=(LoadTask(node_id=2, amount=10.0, service_duration_s=1.0),),
    )

    with pytest.raises(RuntimeError, match="must be at Node-2"):
        process.execute_job(job=failing_job, engine=engine)

    assert process.behavior is not None
    assert process.behavior.state == VehicleOperationalState.FAILED

    process.recover(engine=engine, reason="operator_reset")

    assert process.behavior.state == VehicleOperationalState.IDLE
    assert [
        (event.from_behavior_state, event.to_behavior_state, event.transition_reason)
        for event in engine.trace.events
        if event.event_type == TraceEventType.BEHAVIOR_TRANSITION
    ] == [
        ("idle", "failed", "job_failed:RuntimeError"),
        ("failed", "idle", "operator_reset"),
    ]


def test_behavior_trace_is_deterministic_for_same_resource_wait_setup():
    def run_once() -> tuple[object, ...]:
        engine = build_behavior_engine(
            resources=(SharedResource("loader-1", initial_available_times_s=(3.0,)),)
        )
        job = Job(
            id="load-1",
            tasks=(
                LoadTask(
                    node_id=1,
                    amount=2.0,
                    service_duration_s=2.0,
                    resource_id="loader-1",
                ),
            ),
        )

        engine.execute_job(
            vehicle_id=202,
            start_node_id=1,
            max_speed=5.0,
            job=job,
            max_payload=5.0,
        )
        return tuple(
            event
            for event in engine.trace.events
            if event.event_type == TraceEventType.BEHAVIOR_TRANSITION
        )

    assert run_once() == run_once()
