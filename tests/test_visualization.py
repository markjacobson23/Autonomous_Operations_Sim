import json
from pathlib import Path

from autonomous_ops_sim.core.edge import Edge
from autonomous_ops_sim.core.graph import Graph
from autonomous_ops_sim.core.node import Node
from autonomous_ops_sim.io.scenario_loader import load_scenario
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
from autonomous_ops_sim.simulation.scenario_executor import execute_scenario
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization import (
    build_visualization_state,
    build_visualization_state_from_controller,
    build_frame_render_plan,
    export_visualization_json,
    iter_replay_steps,
    load_visualization_json,
    render_frame_plan_to_canvas,
)
from autonomous_ops_sim.visualization.gui_viewer import ReplayController
from autonomous_ops_sim.visualization.viewer import main as viewer_main


class RecordingCanvas:
    def __init__(self) -> None:
        self.operations: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def delete(self, *args: object) -> None:
        self.operations.append(("delete", args, {}))

    def create_line(self, *args: object, **kwargs: object) -> int:
        self.operations.append(("line", args, kwargs))
        return len(self.operations)

    def create_oval(self, *args: object, **kwargs: object) -> int:
        self.operations.append(("oval", args, kwargs))
        return len(self.operations)

    def create_text(self, *args: object, **kwargs: object) -> int:
        self.operations.append(("text", args, kwargs))
        return len(self.operations)


def build_visualization_route_engine() -> SimulationEngine:
    graph = Graph()

    node_1 = Node(1, (0.0, 0.0, 0.0))
    node_2 = Node(2, (10.0, 0.0, 0.0))
    node_3 = Node(3, (18.0, 0.0, 0.0))

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)
    graph.add_edge(Edge(1, node_1, node_2, 10.0, 5.0))
    graph.add_edge(Edge(2, node_2, node_3, 8.0, 4.0))

    simulation_map = Map(
        graph,
        coord_to_id={
            (0.0, 0.0, 0.0): 1,
            (10.0, 0.0, 0.0): 2,
            (18.0, 0.0, 0.0): 3,
        },
    )
    return SimulationEngine(
        simulation_map=simulation_map,
        world_state=WorldState(graph),
        router=Router(),
        seed=11,
    )


def run_visualization_route_engine() -> SimulationEngine:
    engine = build_visualization_route_engine()
    route = engine.execute_vehicle_route(
        vehicle_id=101,
        start_node_id=1,
        destination_node_id=3,
        max_speed=20.0,
    )
    assert route == (1, 2, 3)
    return engine


def build_visualization_controller() -> tuple[SimulationController, Vehicle]:
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
    controller = SimulationController(engine)
    controller.apply_all(
        (
            BlockEdgeCommand(edge_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
            RepositionVehicleCommand(vehicle_id=77, node_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        )
    )
    return controller, vehicle


def test_visualization_state_generation_is_deterministic() -> None:
    state_a = build_visualization_state(run_visualization_route_engine())
    state_b = build_visualization_state(run_visualization_route_engine())

    assert state_a == state_b
    assert export_visualization_json(state_a) == export_visualization_json(state_b)


def test_replay_frame_ordering_is_deterministic_for_command_driven_run() -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)

    assert [
        (
            step.index,
            step.frame.timestamp_s,
            step.frame.trigger.source,
            step.frame.trigger.event_name,
        )
        for step in iter_replay_steps(state)
    ] == [
        (0, 0.0, "initial", "initial_state"),
        (1, 0.0, "command", "block_edge"),
        (2, 0.0, "trace", "behavior_transition"),
        (3, 0.0, "trace", "route_start"),
        (4, 0.0, "trace", "edge_enter"),
        (5, 0.2, "trace", "node_arrival"),
        (6, 0.2, "trace", "edge_enter"),
        (7, 0.4, "trace", "node_arrival"),
        (8, 0.4, "trace", "route_complete"),
        (9, 0.4, "trace", "behavior_transition"),
        (10, 0.4, "command", "reposition_vehicle"),
        (11, 0.4, "trace", "behavior_transition"),
        (12, 0.4, "trace", "route_start"),
        (13, 0.4, "trace", "edge_enter"),
        (14, 0.7, "trace", "node_arrival"),
        (15, 0.7, "trace", "edge_enter"),
        (16, 0.8999999999999999, "trace", "node_arrival"),
        (17, 0.8999999999999999, "trace", "route_complete"),
        (18, 0.8999999999999999, "trace", "behavior_transition"),
    ]


def test_vehicle_and_map_projection_are_stable_for_single_route() -> None:
    state = build_visualization_state(run_visualization_route_engine())

    assert [(node.node_id, node.position) for node in state.map_surface.nodes] == [
        (1, (0.0, 0.0, 0.0)),
        (2, (10.0, 0.0, 0.0)),
        (3, (18.0, 0.0, 0.0)),
    ]
    assert [
        (edge.edge_id, edge.start_node_id, edge.end_node_id)
        for edge in state.map_surface.edges
    ] == [(1, 1, 2), (2, 2, 3)]
    assert state.frames[0].vehicles == (
        state.frames[0].vehicles[0].__class__(
            vehicle_id=101,
            node_id=1,
            position=(0.0, 0.0, 0.0),
            operational_state="idle",
        ),
    )
    assert state.frames[4].vehicles[0].node_id == 2
    assert state.frames[4].vehicles[0].operational_state == "moving"
    assert state.frames[8].vehicles[0].node_id == 3
    assert state.frames[8].vehicles[0].operational_state == "idle"


def test_visualization_state_export_matches_golden_fixture() -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    export_json = export_visualization_json(state)

    golden_path = Path(__file__).parent / "golden" / "step_19_visualization_state.json"

    assert json.loads(export_json) == json.loads(golden_path.read_text())
    assert export_json == golden_path.read_text()


def test_graph_map_visualization_projection_is_stable() -> None:
    scenario = load_scenario(Path("scenarios/step_21_graph_map_realism.json"))
    result = execute_scenario(scenario)
    state = build_visualization_state(result.engine)

    assert [(node.node_id, node.node_type) for node in state.map_surface.nodes] == [
        (10, "depot"),
        (20, "intersection"),
        (30, "loading_zone"),
        (40, "unloading_zone"),
        (50, "job_site"),
    ]
    assert [
        (edge.edge_id, edge.start_node_id, edge.end_node_id)
        for edge in state.map_surface.edges
    ] == [
        (100, 10, 20),
        (101, 20, 10),
        (102, 20, 30),
        (103, 30, 20),
        (104, 30, 40),
        (105, 40, 30),
        (106, 20, 50),
        (107, 50, 40),
    ]
    assert state.frames[-1].vehicles[0].node_id == 40
    assert state.frames[-1].vehicles[0].position == (9.0, 0.0, 0.0)
    assert export_visualization_json(state) == export_visualization_json(
        build_visualization_state(execute_scenario(scenario).engine)
    )


def test_text_viewer_consumes_visualization_state_json(tmp_path, capsys) -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    visualization_path = tmp_path / "visualization.json"
    visualization_path.write_text(
        export_visualization_json(state),
        encoding="utf-8",
    )

    exit_code = viewer_main([str(visualization_path), "--frame-index", "0"])
    captured = capsys.readouterr()
    loaded_state = load_visualization_json(visualization_path)

    assert exit_code == 0
    assert loaded_state == state
    assert captured.out == (
        "Visualization Replay seed=180 final_time_s=0.8999999999999999 frames=19\n"
        "Map nodes=4 edges=5\n"
        "Frame 0 @ 0.0s initial:initial_state\n"
        "blocked_edges=[]\n"
        "vehicle 77 node=1 state=idle position=(0.0, 0.0, 0.0)\n"
    )


def test_graphical_replay_controller_consumes_frames_deterministically() -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    replay = ReplayController(state)

    replay.play()
    observed = [
        (
            replay.current_frame().frame_index,
            replay.current_frame().timestamp_s,
            replay.current_frame().trigger.event_name,
        )
    ]

    while replay.advance_playback():
        frame = replay.current_frame()
        observed.append(
            (
                frame.frame_index,
                frame.timestamp_s,
                frame.trigger.event_name,
            )
        )

    assert replay.is_playing is False
    assert replay.frame_index == len(state.frames) - 1
    assert observed == [
        (frame.frame_index, frame.timestamp_s, frame.trigger.event_name)
        for frame in state.frames
    ]

    replay.reset()
    assert replay.frame_index == 0
    assert replay.current_frame().trigger.event_name == "initial_state"

    replay.next_frame()
    assert replay.frame_index == 1
    assert replay.current_frame().trigger.event_name == "block_edge"


def test_graphical_viewer_render_plan_is_stable_after_json_load(tmp_path) -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    visualization_path = tmp_path / "visualization.json"
    visualization_path.write_text(export_visualization_json(state), encoding="utf-8")

    loaded_state = load_visualization_json(visualization_path)
    original_plan = build_frame_render_plan(state, frame_index=5)
    loaded_plan = build_frame_render_plan(loaded_state, frame_index=5)

    assert loaded_state == state
    assert loaded_plan == original_plan


def test_graphical_viewer_renders_visualization_state_to_canvas_end_to_end(
    tmp_path,
) -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    visualization_path = tmp_path / "visualization.json"
    visualization_path.write_text(export_visualization_json(state), encoding="utf-8")

    loaded_state = load_visualization_json(visualization_path)
    plan = build_frame_render_plan(loaded_state, frame_index=1)
    canvas = RecordingCanvas()
    render_frame_plan_to_canvas(canvas, plan)

    assert canvas.operations[0] == ("delete", ("all",), {})
    assert [operation[0] for operation in canvas.operations].count("line") == 5
    assert [operation[0] for operation in canvas.operations].count("oval") == 5
    assert [operation[0] for operation in canvas.operations].count("text") == 6
    assert any(
        operation[2].get("fill") == "#dc2626"
        for operation in canvas.operations
        if operation[0] == "line"
    )
    assert any(
        operation[2].get("fill") == "#2563eb"
        for operation in canvas.operations
        if operation[0] == "oval"
    )


def test_graphical_viewer_rejects_edges_with_missing_node_projection() -> None:
    controller, _ = build_visualization_controller()
    state = build_visualization_state_from_controller(controller)
    invalid_state = state.__class__(
        schema_version=state.schema_version,
        seed=state.seed,
        final_time_s=state.final_time_s,
        map_surface=state.map_surface.__class__(
            nodes=state.map_surface.nodes[:-1],
            edges=state.map_surface.edges,
        ),
        frames=state.frames,
    )

    try:
        build_frame_render_plan(invalid_state, frame_index=0)
    except ValueError as exc:
        assert str(exc) == (
            "map surface edge references a node that is not present in the node list"
        )
    else:
        raise AssertionError("expected render-plan validation failure")
