import json
from pathlib import Path

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    CommandValidationError,
    RepositionVehicleCommand,
    SimulationController,
    SimulationEngine,
    WorldState,
    export_controlled_engine_json,
    summarize_engine_execution,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
import pytest


def build_controlled_engine() -> tuple[SimulationEngine, Vehicle]:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (1.0, 0.0, 0.0))
    node_3 = Node(3, (2.0, 0.0, 0.0))
    node_4 = Node(4, (1.0, 1.0, 0.0))

    for node in (node_1, node_2, node_3, node_4):
        graph.add_node(node)

    graph.add_edge(Edge(1, node_1, node_2, 1.0, 10.0))
    graph.add_edge(Edge(2, node_2, node_3, 1.0, 10.0))
    graph.add_edge(Edge(3, node_1, node_4, 1.0, 10.0))
    graph.add_edge(Edge(4, node_4, node_3, 1.0, 10.0))
    graph.add_edge(Edge(5, node_2, node_4, 1.5, 10.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (1.0, 0.0, 0.0): 2,
            (2.0, 0.0, 0.0): 3,
            (1.0, 1.0, 0.0): 4,
        },
    )
    vehicle = Vehicle(
        id=77,
        current_node_id=1,
        position=(0.0, 0.0, 0.0),
        velocity=0.0,
        payload=0.0,
        max_payload=10.0,
        max_speed=5.0,
    )
    engine = SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=180,
        vehicles=(vehicle,),
    )
    return engine, vehicle


def build_command_sequence() -> tuple[
    BlockEdgeCommand,
    AssignVehicleDestinationCommand,
    RepositionVehicleCommand,
    AssignVehicleDestinationCommand,
]:
    return (
        BlockEdgeCommand(edge_id=2),
        AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        RepositionVehicleCommand(vehicle_id=77, node_id=2),
        AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
    )


def run_command_sequence() -> tuple[SimulationController, Vehicle]:
    engine, vehicle = build_controlled_engine()
    controller = SimulationController(engine)
    controller.apply_all(build_command_sequence())
    return controller, vehicle


def test_command_application_is_deterministic_for_same_initial_state() -> None:
    controller_a, vehicle_a = run_command_sequence()
    controller_b, vehicle_b = run_command_sequence()

    assert controller_a.command_history == controller_b.command_history
    assert controller_a.engine.trace.events == controller_b.engine.trace.events
    assert controller_a.engine.world_state.blocked_edge_ids == {2}
    assert controller_b.engine.world_state.blocked_edge_ids == {2}
    assert vehicle_a.current_node_id == 3
    assert vehicle_b.current_node_id == 3
    assert vehicle_a.get_position() == (2.0, 0.0, 0.0)
    assert vehicle_b.get_position() == (2.0, 0.0, 0.0)


def test_engine_public_lookup_methods_expose_runtime_state() -> None:
    engine, _ = build_controlled_engine()

    assert engine.has_vehicle(77) is True
    assert engine.has_node(1) is True
    assert engine.has_edge(2) is True
    assert engine.has_vehicle(999) is False
    assert engine.has_node(999) is False
    assert engine.has_edge(999) is False


@pytest.mark.parametrize(
    ("command", "message"),
    (
        (BlockEdgeCommand(edge_id=999), "Unknown edge_id: 999"),
        (
            RepositionVehicleCommand(vehicle_id=77, node_id=999),
            "Unknown node_id: 999",
        ),
        (
            AssignVehicleDestinationCommand(vehicle_id=999, destination_node_id=3),
            "Unknown vehicle_id: 999",
        ),
    ),
)
def test_invalid_commands_are_rejected_clearly(command: object, message: str) -> None:
    engine, _ = build_controlled_engine()
    controller = SimulationController(engine)

    with pytest.raises(CommandValidationError, match=message):
        controller.apply(command)  # type: ignore[arg-type]


def test_same_command_sequence_replays_identically() -> None:
    controller_a, _ = run_command_sequence()
    controller_b, _ = run_command_sequence()

    summary_a = summarize_engine_execution(controller_a.engine)
    summary_b = summarize_engine_execution(controller_b.engine)
    export_json_a = export_controlled_engine_json(controller_a, summary=summary_a)
    export_json_b = export_controlled_engine_json(controller_b, summary=summary_b)

    assert summary_a == summary_b
    assert export_json_a == export_json_b


def test_command_driven_export_matches_golden_fixture() -> None:
    controller, _ = run_command_sequence()
    summary = summarize_engine_execution(controller.engine)
    export_json = export_controlled_engine_json(controller, summary=summary)

    golden_path = Path(__file__).parent / "golden" / "step_18_control_commands_export.json"

    assert json.loads(export_json) == json.loads(golden_path.read_text())
    assert export_json == golden_path.read_text()


def test_reapplying_same_block_command_is_rejected() -> None:
    engine, _ = build_controlled_engine()
    controller = SimulationController(engine)

    controller.apply(BlockEdgeCommand(edge_id=2))

    with pytest.raises(CommandValidationError, match="edge_id 2 is already blocked"):
        controller.apply(BlockEdgeCommand(edge_id=2))
