import json
from pathlib import Path

from autonomous_ops_sim.api import (
    build_live_session_bundle,
    build_live_sync_bundle,
    build_replay_bundle_from_controller,
    export_live_session_bundle_json,
    export_live_sync_bundle_json,
    export_replay_bundle_json,
)
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
    SimulationController,
    SimulationEngine,
    WorldState,
)
from autonomous_ops_sim.vehicles.vehicle import Vehicle
from autonomous_ops_sim.visualization.serious_viewer import (
    build_serious_viewer_html,
    build_viewer_foundation_plan,
    load_simulation_api_bundle,
    main as serious_viewer_main,
)


def build_serious_viewer_engine() -> SimulationEngine:
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


def run_serious_viewer_controller() -> SimulationController:
    controller = SimulationController(build_serious_viewer_engine())
    controller.apply_all(
        (
            BlockEdgeCommand(edge_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
            RepositionVehicleCommand(vehicle_id=77, node_id=2),
            AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3),
        )
    )
    return controller


def run_serious_viewer_session() -> LiveSimulationSession:
    session = LiveSimulationSession(build_serious_viewer_engine())
    session.advance_to(1.0)
    session.apply(BlockEdgeCommand(edge_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_by(0.5)
    session.apply(RepositionVehicleCommand(vehicle_id=77, node_id=2))
    session.apply(AssignVehicleDestinationCommand(vehicle_id=77, destination_node_id=3))
    session.advance_to(3.0)
    return session


def test_viewer_foundation_plan_commits_to_web_client_path() -> None:
    plan = build_viewer_foundation_plan()

    assert plan.recommended_stack == "web_client"
    assert plan.rendering_strategy == "responsive_svg_scene"
    assert plan.transport_surface == "simulation_api_bundle_json"
    assert len(plan.rationale) == 3


def test_serious_viewer_html_renders_replay_bundle_controls_and_embedded_data() -> None:
    bundle = json.loads(
        export_replay_bundle_json(
            build_replay_bundle_from_controller(run_serious_viewer_controller())
        )
    )

    html_output = build_serious_viewer_html(bundle)

    assert "Serious Viewer Foundation" in html_output
    assert "simulation-api-bundle" in html_output
    assert "viewerScene" in html_output
    assert "timelineInput" in html_output
    assert "playButton" in html_output
    assert "web_client" in html_output
    assert "replay_bundle" in html_output
    assert "motion_segments" in html_output


def test_serious_viewer_html_supports_live_session_and_live_sync_bundles() -> None:
    live_session_bundle = json.loads(
        export_live_session_bundle_json(
            build_live_session_bundle(run_serious_viewer_session())
        )
    )
    live_sync_bundle = json.loads(
        export_live_sync_bundle_json(
            build_live_sync_bundle(run_serious_viewer_session())
        )
    )

    live_session_html = build_serious_viewer_html(live_session_bundle)
    live_sync_html = build_serious_viewer_html(live_sync_bundle)

    assert "live_session_bundle" in live_session_html
    assert "live_sync_bundle" in live_sync_html
    assert "live snapshot" in live_session_html
    assert "live snapshot" in live_sync_html
    assert "motion_segments" in live_session_html
    assert "motion_segments" in live_sync_html


def test_serious_viewer_cli_loads_bundle_and_writes_html(tmp_path, capsys) -> None:
    bundle_path = tmp_path / "replay_bundle.json"
    bundle_path.write_text(
        export_replay_bundle_json(
            build_replay_bundle_from_controller(run_serious_viewer_controller())
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "viewer.html"

    exit_code = serious_viewer_main(
        [str(bundle_path), "--output", str(output_path), "--title", "Viewer Test"]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert Path(captured.out.strip()) == output_path
    assert output_path.exists()
    assert "Viewer Test" in output_path.read_text(encoding="utf-8")
    assert load_simulation_api_bundle(bundle_path)["metadata"]["surface_name"] == (
        "replay_bundle"
    )
