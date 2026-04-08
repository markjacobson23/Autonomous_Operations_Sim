import json
from pathlib import Path
from typing import Callable

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    RepositionVehicleCommand,
    SimulationController,
    SimulationEngine,
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    AssignDestinationInteraction,
    BlockEdgeInteraction,
    InteractionValidationError,
    RepositionVehicleInteraction,
    apply_interaction,
    build_visualization_state_from_interactions,
    export_visualization_json,
    interaction_to_dict,
    translate_interactions,
)
import pytest


def build_interaction_controller() -> tuple[SimulationController, Vehicle]:
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
    return SimulationController(engine), vehicle


def build_interaction_sequence() -> tuple[
    BlockEdgeInteraction,
    AssignDestinationInteraction,
    RepositionVehicleInteraction,
    AssignDestinationInteraction,
]:
    return (
        BlockEdgeInteraction(edge_id=2),
        AssignDestinationInteraction(vehicle_id=77, destination_node_id=3),
        RepositionVehicleInteraction(vehicle_id=77, node_id=2),
        AssignDestinationInteraction(vehicle_id=77, destination_node_id=3),
    )


def run_interaction_sequence() -> tuple[SimulationController, Vehicle]:
    controller, vehicle = build_interaction_controller()
    build_visualization_state_from_interactions(controller, build_interaction_sequence())
    return controller, vehicle


def test_interaction_translation_is_deterministic() -> None:
    interactions = build_interaction_sequence()

    translated_once = translate_interactions(interactions)
    translated_twice = translate_interactions(interactions)

    assert translated_once == translated_twice
    assert translated_once == (
        BlockEdgeCommand(edge_id=2),
        AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        RepositionVehicleCommand(vehicle_id=77, node_id=2),
        AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
    )
    assert [interaction_to_dict(interaction) for interaction in interactions] == [
        {
            "interaction_type": "block_edge",
            "command": {"command_type": "block_edge", "edge_id": 2},
        },
        {
            "interaction_type": "assign_destination",
            "command": {
                "command_type": "assign_vehicle_destination",
                "vehicle_id": 77,
                "destination_node_id": 3,
            },
        },
        {
            "interaction_type": "reposition_vehicle",
            "command": {
                "command_type": "reposition_vehicle",
                "vehicle_id": 77,
                "node_id": 2,
            },
        },
        {
            "interaction_type": "assign_destination",
            "command": {
                "command_type": "assign_vehicle_destination",
                "vehicle_id": 77,
                "destination_node_id": 3,
            },
        },
    ]


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (lambda: BlockEdgeInteraction(edge_id=-1), "edge_id must be non-negative"),
        (
            lambda: AssignDestinationInteraction(vehicle_id=77, destination_node_id=-1),
            "destination_node_id must be non-negative",
        ),
        (
            lambda: RepositionVehicleInteraction(vehicle_id=77, node_id=-1),
            "node_id must be non-negative",
        ),
    ),
)
def test_invalid_interaction_construction_is_rejected(
    factory: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(InteractionValidationError, match=message):
        factory()


def test_invalid_interaction_application_is_rejected() -> None:
    controller, _ = build_interaction_controller()

    with pytest.raises(InteractionValidationError, match="Unknown node_id: 999"):
        apply_interaction(
            controller,
            RepositionVehicleInteraction(vehicle_id=77, node_id=999),
        )


def test_repeated_interaction_sequences_produce_identical_results() -> None:
    controller_a, vehicle_a = run_interaction_sequence()
    controller_b, vehicle_b = run_interaction_sequence()

    state_a = build_visualization_state_from_interactions(
        controller_a,
        (),
    )
    state_b = build_visualization_state_from_interactions(
        controller_b,
        (),
    )

    assert controller_a.command_history == controller_b.command_history
    assert controller_a.engine.trace.events == controller_b.engine.trace.events
    assert export_visualization_json(state_a) == export_visualization_json(state_b)
    assert vehicle_a.current_node_id == 3
    assert vehicle_b.current_node_id == 3
    assert vehicle_a.get_position() == (2.0, 0.0, 0.0)
    assert vehicle_b.get_position() == (2.0, 0.0, 0.0)


def test_interaction_driven_visualization_export_matches_golden_fixture() -> None:
    controller, _ = build_interaction_controller()
    state = build_visualization_state_from_interactions(
        controller,
        build_interaction_sequence(),
    )
    export_json = export_visualization_json(state)

    golden_path = (
        Path(__file__).parent / "golden" / "step_19_visualization_state.json"
    )

    assert json.loads(export_json) == json.loads(golden_path.read_text())
    assert export_json == golden_path.read_text()
