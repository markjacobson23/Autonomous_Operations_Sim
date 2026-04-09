import json

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.maps.map import Map
from autonomous_ops_sim.routing import Router
from autonomous_ops_sim.simulation import (
    AssignVehicleDestinationCommand,
    BlockEdgeCommand,
    LiveSimulationSession,
    RepositionVehicleCommand,
    SimulationEngine,
    UnblockEdgeCommand,
    WorldState,
    export_live_session_json,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    AssignDestinationInteraction,
    AssignSelectedDestinationViewerAction,
    BlockEdgeInteraction,
    BlockEdgeViewerAction,
    ClearVehicleSelectionViewerAction,
    LiveViewerActionResult,
    LiveViewerActionValidationError,
    LiveViewerController,
    RepositionSelectedVehicleViewerAction,
    RepositionVehicleInteraction,
    SelectVehiclesViewerAction,
    SelectVehicleViewerAction,
    UnblockEdgeInteraction,
    UnblockEdgeViewerAction,
    build_visualization_state_from_live_session,
    export_visualization_json,
    interaction_to_command,
    translate_live_viewer_action,
)
import pytest


def build_live_viewer_engine() -> SimulationEngine:
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
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=180,
        vehicles=(vehicle,),
    )


def build_live_viewer_controller() -> LiveViewerController:
    return LiveViewerController(LiveSimulationSession(build_live_viewer_engine()))


def run_live_viewer_action_sequence() -> tuple[
    LiveViewerController,
    tuple[LiveViewerActionResult, ...],
]:
    controller = build_live_viewer_controller()
    results = (
        controller.apply_action(SelectVehicleViewerAction(vehicle_id=77)),
        controller.apply_action(BlockEdgeViewerAction(edge_id=2)),
        controller.apply_action(RepositionSelectedVehicleViewerAction(node_id=2)),
        controller.apply_action(
            AssignSelectedDestinationViewerAction(destination_node_id=3)
        ),
    )
    return controller, results


def test_live_viewer_action_translation_reuses_interactions_and_commands() -> None:
    session = LiveSimulationSession(build_live_viewer_engine())

    selected_vehicle_id, select_interaction = translate_live_viewer_action(
        SelectVehicleViewerAction(vehicle_id=77),
        session=session,
        selected_vehicle_ids=(),
    )
    assert selected_vehicle_id == (77,)
    assert select_interaction is None

    selected_vehicle_id, block_interaction = translate_live_viewer_action(
        BlockEdgeViewerAction(edge_id=2),
        session=session,
        selected_vehicle_ids=selected_vehicle_id,
    )
    assert block_interaction == BlockEdgeInteraction(edge_id=2)
    assert interaction_to_command(block_interaction) == BlockEdgeCommand(edge_id=2)

    selected_vehicle_id, unblock_interaction = translate_live_viewer_action(
        UnblockEdgeViewerAction(edge_id=2),
        session=session,
        selected_vehicle_ids=selected_vehicle_id,
    )
    assert unblock_interaction == UnblockEdgeInteraction(edge_id=2)
    assert interaction_to_command(unblock_interaction) == UnblockEdgeCommand(edge_id=2)

    selected_vehicle_id, reposition_interaction = translate_live_viewer_action(
        RepositionSelectedVehicleViewerAction(node_id=2),
        session=session,
        selected_vehicle_ids=selected_vehicle_id,
    )
    assert reposition_interaction == RepositionVehicleInteraction(
        vehicle_id=77,
        node_id=2,
    )
    assert interaction_to_command(reposition_interaction) == RepositionVehicleCommand(
        vehicle_id=77,
        node_id=2,
    )

    _, assign_interaction = translate_live_viewer_action(
        AssignSelectedDestinationViewerAction(destination_node_id=3),
        session=session,
        selected_vehicle_ids=selected_vehicle_id,
    )
    assert assign_interaction == AssignDestinationInteraction(
        vehicle_id=77,
        destination_node_id=3,
    )
    assert interaction_to_command(assign_interaction) == (
        AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3)
    )


def test_live_viewer_actions_apply_deterministically_and_refresh_visualization() -> None:
    controller_a, results_a = run_live_viewer_action_sequence()
    controller_b, results_b = run_live_viewer_action_sequence()

    assert results_a == results_b
    assert controller_a.session.command_history == controller_b.session.command_history
    assert controller_a.visualization_state == build_visualization_state_from_live_session(
        controller_a.session
    )
    assert controller_b.visualization_state == build_visualization_state_from_live_session(
        controller_b.session
    )
    assert [result.command_record is None for result in results_a] == [
        True,
        False,
        False,
        False,
    ]
    assert [len(result.visualization_state.frames) for result in results_a] == [
        1,
        2,
        3,
        11,
    ]
    assert results_a[-1].visualization_state.frames[-1].trigger.source == "trace"
    assert (
        results_a[-1].visualization_state.frames[-1].trigger.event_name
        == "behavior_transition"
    )
    assert controller_a.session.engine.world_state.blocked_edge_ids == {2}
    assert controller_a.session.engine.get_vehicle(77).current_node_id == 3
    assert controller_a.selected_vehicle_id == 77
    assert controller_a.selected_vehicle_ids == (77,)


def test_live_viewer_action_sequences_repeat_identical_session_replay_and_export_outputs() -> None:
    controller_a, _ = run_live_viewer_action_sequence()
    controller_b, _ = run_live_viewer_action_sequence()

    session_export_a = export_live_session_json(controller_a.session)
    session_export_b = export_live_session_json(controller_b.session)
    replay_export_a = export_visualization_json(controller_a.visualization_state)
    replay_export_b = export_visualization_json(controller_b.visualization_state)

    assert json.loads(session_export_a) == json.loads(session_export_b)
    assert session_export_a == session_export_b
    assert replay_export_a == replay_export_b


def test_live_viewer_actions_reject_missing_selection_and_out_of_bounds_reposition() -> None:
    controller = build_live_viewer_controller()

    with pytest.raises(
        LiveViewerActionValidationError,
        match="a vehicle must be selected before issuing this action",
    ):
        controller.apply_action(
            AssignSelectedDestinationViewerAction(destination_node_id=3)
        )

    controller.apply_action(SelectVehicleViewerAction(vehicle_id=77))
    with pytest.raises(
        LiveViewerActionValidationError,
        match=(
            "node_id 3 must be the selected vehicle's current node "
            "or a direct outgoing neighbor"
        ),
    ):
        controller.apply_action(
            RepositionSelectedVehicleViewerAction(node_id=3)
        )


def test_live_viewer_supports_multi_selection_preview_and_edge_reopening() -> None:
    controller = build_live_viewer_controller()

    result = controller.apply_action(SelectVehiclesViewerAction(vehicle_ids=(77, 77)))
    preview = controller.preview_destination(3)
    controller.apply_action(BlockEdgeViewerAction(edge_id=2))
    controller.apply_action(UnblockEdgeViewerAction(edge_id=2))
    clear_result = controller.apply_action(ClearVehicleSelectionViewerAction())

    assert result.selected_vehicle_id == 77
    assert result.selected_vehicle_ids == (77,)
    assert preview.node_ids == (1, 2, 3)
    assert preview.edge_ids == (1, 2)
    assert preview.is_actionable is True
    assert controller.session.engine.world_state.blocked_edge_ids == set()
    assert clear_result.selected_vehicle_id is None
    assert clear_result.selected_vehicle_ids == ()
