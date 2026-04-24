import json
import time
from urllib import error, request

from autonomous_ops_sim.live_app import (
    LiveAppServer,
    build_live_app_url,
    export_live_app_artifacts,
    launch_live_app,
)
from autonomous_ops_sim.simulation.behavior import VehicleOperationalState


def _read_live_bundle(base_url: str) -> dict[str, object]:
    response = request.urlopen(f"{base_url}/live_session_bundle.json")
    payload = json.loads(response.read().decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def _vehicle_by_id(bundle: dict[str, object], vehicle_id: int) -> dict[str, object]:
    vehicles = bundle["snapshot"]["vehicles"]
    assert isinstance(vehicles, list)
    for vehicle in vehicles:
        if vehicle["vehicle_id"] == vehicle_id:
            return vehicle
    raise AssertionError(f"vehicle_id {vehicle_id} not found in bundle snapshot")


def _node_position(bundle: dict[str, object], node_id: int) -> list[float]:
    nodes = bundle["map_surface"]["nodes"]
    assert isinstance(nodes, list)
    for node in nodes:
        if node["node_id"] == node_id:
            return node["position"]
    raise AssertionError(f"node_id {node_id} not found in bundle map_surface")


def _wait_for_live_time(
    base_url: str,
    minimum_time_s: float,
    *,
    timeout_s: float = 5.0,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_s
    latest_bundle: dict[str, object] | None = None
    while time.monotonic() < deadline:
        latest_bundle = _read_live_bundle(base_url)
        simulated_time_s = latest_bundle["simulated_time_s"]
        assert isinstance(simulated_time_s, (int, float))
        if float(simulated_time_s) >= minimum_time_s:
            return latest_bundle
        time.sleep(0.05)
    raise AssertionError(
        f"Live bundle did not reach simulated_time_s >= {minimum_time_s} within {timeout_s}s"
    )


def test_export_live_app_artifacts_falls_back_to_standalone_viewer_when_no_frontend_dist(
    tmp_path,
) -> None:
    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path,
        frontend_dist_directory=tmp_path / "missing_dist",
    )

    assert artifacts.launch_mode == "standalone_viewer_html"
    assert artifacts.launch_path == tmp_path / "live_session.viewer.html"
    assert artifacts.launch_path.exists()
    assert artifacts.live_session_bundle_path.exists()
    assert artifacts.working_scenario_path.exists()

    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    assert bundle["metadata"]["surface_name"] == "live_session_bundle"
    assert bundle["seed"] == 3801
    assert bundle["authoring"]["working_scenario_path"] == str(artifacts.working_scenario_path)
    assert bundle["replay_analysis"]["summary"]["telemetry_sample_count"] == 0
    assert bundle["replay_analysis"]["summary"]["vehicle_count"] == len(
        bundle["snapshot"]["vehicles"]
    )


def test_export_live_app_artifacts_prefers_frontend_dist_when_available(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")
    assets_dir = frontend_dist / "assets"
    assets_dir.mkdir()
    (assets_dir / "app.js").write_text("console.log('boot');", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )

    assert artifacts.launch_mode == "frontend_dist"
    assert artifacts.launch_path == tmp_path / "output" / "frontend_v2" / "index.html"
    assert artifacts.launch_path.exists()
    assert (tmp_path / "output" / "frontend_v2" / "assets" / "app.js").exists()
    assert artifacts.launch_relative_url == "/frontend_v2/index.html?bundle=/live_session_bundle.json"


def test_build_live_app_url_uses_host_port_and_relative_url(tmp_path) -> None:
    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path,
        frontend_dist_directory=tmp_path / "missing_dist",
    )

    assert (
        build_live_app_url(artifacts, host="127.0.0.1", port=4312)
        == "http://127.0.0.1:4312/live_session.viewer.html"
    )


def test_launch_live_app_returns_file_uri_for_fallback_without_opening_browser(tmp_path) -> None:
    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path,
        frontend_dist_directory=tmp_path / "missing_dist",
    )

    result = launch_live_app(artifacts, open_browser=False)

    assert result.served is False
    assert result.launch_target == artifacts.launch_path.resolve().as_uri()


def test_live_app_frontend_server_supports_validate_save_and_reload_authoring_api(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        validate_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/authoring/validate",
                data=json.dumps(
                    {
                        "label": "invalid-node-overlap",
                        "operations": [
                            {
                                "kind": "move_node",
                                "target_id": 100,
                                "position": [3, 0, 0],
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        validate_payload = json.loads(validate_response.read().decode("utf-8"))
        assert validate_payload["ok"] is False
        assert validate_payload["validation_messages"] != []

        save_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/authoring/save",
                data=json.dumps(
                    {
                        "label": "edit-road",
                        "operations": [
                            {
                                "kind": "set_road_centerline",
                                "target_id": "dispatch-spine",
                                "points": [[0, 0, 0], [1.2, 0.4, 0], [3, 0, 0]],
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        save_payload = json.loads(save_response.read().decode("utf-8"))
        assert save_payload["ok"] is True
        assert save_payload["bundle"]["render_geometry"]["roads"][0]["centerline"][1] == [
            1.2,
            0.4,
            0.0,
        ]

        reload_response = request.urlopen(f"{base_url}/api/authoring/reload")
        reload_payload = json.loads(reload_response.read().decode("utf-8"))
        assert reload_payload["ok"] is True
        assert reload_payload["bundle"]["render_geometry"]["roads"][0]["centerline"][1] == [
            1.2,
            0.4,
            0.0,
        ]
    finally:
        server.stop()


def test_live_app_frontend_server_supports_live_commands_and_session_control(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    edge_id = bundle["map_surface"]["edges"][0]["edge_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        command_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "block_edge",
                        "edge_id": edge_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        command_payload = json.loads(command_response.read().decode("utf-8"))
        assert command_payload["ok"] is True
        assert command_payload["command_result"]["status"] == "accepted"
        assert command_payload["bundle"]["command_center"]["recent_commands"][0][
            "command_type"
        ] == "block_edge"
        assert command_payload["bundle"]["command_center"]["recent_commands"][0][
            "edge_id"
        ] == edge_id
        assert command_payload["bundle"]["session_control"]["play_state"] == "paused"

        step_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "step",
                        "delta_s": 0.5,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        step_payload = json.loads(step_response.read().decode("utf-8"))
        assert step_payload["ok"] is True
        assert step_payload["session_advance"]["completed_at_s"] == 0.5
        assert step_payload["bundle"]["simulated_time_s"] == 0.5
        assert step_payload["bundle"]["session_control"]["step_seconds"] == 0.5

        play_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "play",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        play_payload = json.loads(play_response.read().decode("utf-8"))
        assert play_payload["ok"] is True
        assert play_payload["bundle"]["session_control"]["play_state"] == "playing"

        playback_thread = server._runtime.playback_thread
        advanced_bundle = _wait_for_live_time(base_url, 1.0)
        advanced_time_s = advanced_bundle["simulated_time_s"]
        assert isinstance(advanced_time_s, (int, float))
        assert advanced_time_s >= 1.0
        advanced_session_history = advanced_bundle["session_history"]
        assert isinstance(advanced_session_history, list)
        assert len(advanced_session_history) >= 2

        repeated_play_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "play",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        repeated_play_payload = json.loads(repeated_play_response.read().decode("utf-8"))
        assert repeated_play_payload["ok"] is True
        assert repeated_play_payload["bundle"]["session_control"]["play_state"] == "playing"
        assert server._runtime.playback_thread is playback_thread

        repeated_bundle = _wait_for_live_time(base_url, 1.5)
        repeated_time_s = repeated_bundle["simulated_time_s"]
        assert isinstance(repeated_time_s, (int, float))
        assert repeated_time_s >= 1.5
        repeated_session_history = repeated_bundle["session_history"]
        assert isinstance(repeated_session_history, list)
        assert len(repeated_session_history) == len(advanced_session_history) + 1

        try:
            request.urlopen(
                request.Request(
                    url=f"{base_url}/api/live/session/control",
                    data=json.dumps(
                        {
                            "action": "step",
                            "delta_s": 0.5,
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            raise AssertionError("step while playing should be rejected")
        except error.HTTPError as exc:
            assert exc.code == 409
            step_error_payload = json.loads(exc.read().decode("utf-8"))
            assert step_error_payload["ok"] is False
            assert "Cannot step while the session is playing." in step_error_payload["message"]

        pause_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "pause",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        pause_payload = json.loads(pause_response.read().decode("utf-8"))
        assert pause_payload["ok"] is True
        assert pause_payload["bundle"]["session_control"]["play_state"] == "paused"

        paused_bundle = _read_live_bundle(base_url)
        paused_time_s = paused_bundle["simulated_time_s"]
        assert isinstance(paused_time_s, (int, float))
        paused_session_history = paused_bundle["session_history"]
        assert isinstance(paused_session_history, list)
        paused_history_length = len(paused_session_history)
        time.sleep(0.8)
        after_pause_bundle = _read_live_bundle(base_url)
        after_pause_time_s = after_pause_bundle["simulated_time_s"]
        assert isinstance(after_pause_time_s, (int, float))
        assert after_pause_time_s == paused_time_s
        after_pause_session_history = after_pause_bundle["session_history"]
        assert isinstance(after_pause_session_history, list)
        assert len(after_pause_session_history) == paused_history_length
    finally:
        server.stop()


def test_live_app_frontend_server_supports_unity_bootstrap_and_telemetry_bridge(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["snapshot"]["vehicles"][0]["vehicle_id"]
    current_node_id = bundle["snapshot"]["vehicles"][0]["node_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    current_edge_id = bundle["map_surface"]["edges"][0]["edge_id"]
    map_node_count = len(bundle["map_surface"]["nodes"])
    map_road_count = len(bundle["render_geometry"]["roads"])
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "assign_vehicle_destination",
                        "vehicle_id": vehicle_id,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

        bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        bootstrap_payload = json.loads(bootstrap_response.read().decode("utf-8"))
        assert bootstrap_payload["ok"] is True
        assert bootstrap_payload["bootstrap"]["metadata"]["surface_name"] == "unity_bootstrap"
        assert bootstrap_payload["bootstrap"]["metadata"]["bootstrap_schema_version"] == 2
        assert bootstrap_payload["bootstrap"]["metadata"]["bridge_schema_version"] == 1
        assert bootstrap_payload["bootstrap"]["authority"]["motion_authority"] == "python"
        assert bootstrap_payload["bootstrap"]["session"]["motion_authority"] == "python"
        assert server._runtime.motion_authority == "python"
        assert bootstrap_payload["bootstrap"]["session"]["source_scenario_path"].endswith(
            "scenarios/showpiece_pack/01_mine_ore_shift.json"
        )
        assert len(bootstrap_payload["bootstrap"]["world"]["topology"]["nodes"]) == map_node_count
        assert len(bootstrap_payload["bootstrap"]["world"]["render_geometry"]["roads"]) == map_road_count
        assert bootstrap_payload["bootstrap"]["world"]["topology"]["nodes"][0]["node_id"] == bundle["map_surface"]["nodes"][0]["node_id"]
        assert bootstrap_payload["bootstrap"]["runtime"]["vehicle_snapshot"][0][
            "vehicle_id"
        ] == vehicle_id
        assert bootstrap_payload["bootstrap"]["runtime"]["vehicle_identity_map"][0][
            "vehicle_id"
        ] == vehicle_id
        assert bootstrap_payload["bootstrap"]["runtime"]["pending_route_intents"] == [
            {
                "command_type": "assign_vehicle_destination",
                "destination_node_id": destination_node_id,
                "vehicle_id": vehicle_id,
            }
        ]
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "vehicle_id"
        ] == vehicle_id
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "destination_node_id"
        ] == destination_node_id
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "node_ids"
        ][0] == current_node_id
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "waypoints"
        ][0]["node_id"] == current_node_id
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "embodiment_state"
        ] == "inactive"
        assert bootstrap_payload["bootstrap"]["world"]["blocked_edge_ids"] == []
        assert bootstrap_payload["bootstrap"]["bridge"]["schema_version"] == 1
        assert bootstrap_payload["bootstrap"]["bridge"]["bootstrap_endpoint"] == "/api/unity/bootstrap"
        assert bootstrap_payload["bootstrap"]["bridge"]["telemetry_endpoint"] == "/api/unity/telemetry"
        assert bootstrap_payload["bootstrap"]["provenance"]["source_surface_name"] == "live_session_bundle"
        for deprecated_key in (
            "runtime_vehicle_snapshot",
            "vehicle_identity_map",
            "pending_route_intents",
            "route_following_by_vehicle_id",
            "latest_unity_telemetry_by_vehicle_id",
            "latest_unity_route_progress_by_vehicle_id",
            "latest_unity_embodiment_status_by_vehicle_id",
            "bridge_endpoints",
        ):
            assert deprecated_key not in bootstrap_payload["bootstrap"]
        assert "map_surface" not in bootstrap_payload["bootstrap"]["world"]
        assert "embodiment_status" not in bootstrap_payload["bootstrap"]["runtime"]

        telemetry_request_payload = {
            "telemetry": {
                "vehicle_id": vehicle_id,
                "timestamp_s": 12.5,
                "position": [1.0, 2.0, 3.0],
                "speed": 4.25,
                "heading_rad": 1.57,
                "current_node_id": current_node_id,
                "current_edge_id": current_edge_id,
                "route_status": "active",
                "route_progress": 0.4,
                "current_target_node_id": destination_node_id,
                "current_waypoint_index": 1,
                "embodiment_state": "moving",
            }
        }
        telemetry_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/unity/telemetry",
                data=json.dumps(telemetry_request_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        telemetry_payload = json.loads(telemetry_response.read().decode("utf-8"))
        assert telemetry_payload["ok"] is True
        assert telemetry_payload["telemetry"]["telemetry_count"] == 1
        assert telemetry_payload["telemetry"]["motion_authority"] == "python"
        assert telemetry_payload["telemetry"]["guardrails"]["motion_authority"] == "python"
        assert (
            telemetry_payload["telemetry"]["guardrails"]["telemetry_role"]
            == "observational_motion_signal"
        )
        assert "route_status" in telemetry_payload["telemetry"]["guardrails"]["accepted_fields"]
        assert "embodiment_state" in telemetry_payload["telemetry"]["guardrails"]["accepted_fields"]
        assert "latest_unity_embodiment_status_by_vehicle_id" in telemetry_payload["telemetry"][
            "guardrails"
        ]["backend_state_updates"]
        assert "task_identity" in telemetry_payload["telemetry"]["guardrails"][
            "telemetry_must_not_overwrite"
        ]
        assert telemetry_payload["telemetry"]["received_samples"][0]["vehicle_id"] == vehicle_id
        assert telemetry_payload["telemetry"]["received_samples"][0]["position"] == [
            1.0,
            2.0,
            3.0,
        ]
        assert server._runtime.latest_unity_telemetry_by_vehicle_id[vehicle_id][
            "speed"
        ] == 4.25
        assert server._runtime.latest_unity_route_progress_by_vehicle_id[vehicle_id][
            "route_status"
        ] == "active"
        assert server._runtime.latest_unity_route_progress_by_vehicle_id[vehicle_id][
            "current_target_node_id"
        ] == destination_node_id
        assert server._runtime.latest_unity_embodiment_status_by_vehicle_id[vehicle_id][
            "embodiment_state"
        ] == "moving"

        live_bundle_payload = _read_live_bundle(base_url)
        assert live_bundle_payload["operator_state"]["motion_authority"] == "python"
        assert live_bundle_payload["operator_state"]["vehicles"][0]["vehicle_id"] == vehicle_id
        assert live_bundle_payload["operator_state"]["vehicles"][0]["route_status"] == "active"
        assert live_bundle_payload["operator_state"]["vehicles"][0]["embodiment_state"] == "moving"
        assert live_bundle_payload["replay_analysis"]["summary"]["telemetry_sample_count"] == 1
        assert live_bundle_payload["replay_analysis"]["summary"]["route_progress_event_count"] == 1
        assert live_bundle_payload["replay_analysis"]["summary"]["embodiment_event_count"] == 1
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["vehicle_id"] == vehicle_id
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["route_progress_history"][0][
            "route_status"
        ] == "active"
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["outcome"][
            "embodiment_state"
        ] == "moving"

        refreshed_bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        refreshed_bootstrap_payload = json.loads(
            refreshed_bootstrap_response.read().decode("utf-8")
        )
        assert refreshed_bootstrap_payload["bootstrap"][
            "runtime"
        ]["vehicle_snapshot"][0]["vehicle_id"] == vehicle_id
        assert refreshed_bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "route_status"
        ] == "active"
        assert refreshed_bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "embodiment_state"
        ] == "moving"
    finally:
        server.stop()


def test_live_app_frontend_server_exposes_unity_motion_authority_explicitly(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["snapshot"]["vehicles"][0]["vehicle_id"]
    server = LiveAppServer(
        artifacts.output_directory,
        artifacts=artifacts,
        motion_authority="unity",
        port=0,
    )
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        bootstrap_payload = json.loads(bootstrap_response.read().decode("utf-8"))
        assert bootstrap_payload["ok"] is True
        assert bootstrap_payload["bootstrap"]["authority"]["motion_authority"] == "unity"
        assert bootstrap_payload["bootstrap"]["session"]["motion_authority"] == "unity"
        assert bootstrap_payload["bootstrap"]["runtime"]["route_following"] == []
        assert server._runtime.motion_authority == "unity"

        telemetry_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/unity/telemetry",
                data=json.dumps(
                    {
                        "telemetry": {
                            "vehicle_id": vehicle_id,
                            "timestamp_s": 2.0,
                            "position": [0.0, 0.0, 0.0],
                            "speed": 0.0,
                        }
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        telemetry_payload = json.loads(telemetry_response.read().decode("utf-8"))
        assert telemetry_payload["ok"] is True
        assert telemetry_payload["telemetry"]["motion_authority"] == "unity"
        assert telemetry_payload["telemetry"]["guardrails"]["motion_authority"] == "unity"
        assert (
            telemetry_payload["telemetry"]["guardrails"]["telemetry_role"]
            == "unity_embodied_motion_signal"
        )
        assert server._runtime.latest_unity_telemetry_by_vehicle_id[vehicle_id][
            "vehicle_id"
        ] == vehicle_id
        live_bundle_payload = _read_live_bundle(base_url)
        assert live_bundle_payload["operator_state"]["motion_authority"] == "unity"
        assert live_bundle_payload["operator_state"]["vehicles"][0]["motion_authority"] == "unity"
        assert live_bundle_payload["replay_analysis"]["summary"]["telemetry_sample_count"] == 1
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["vehicle_id"] == vehicle_id
    finally:
        server.stop()


def test_live_app_frontend_server_projects_unity_route_completion_back_to_backend(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["snapshot"]["vehicles"][0]["vehicle_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    server = LiveAppServer(
        artifacts.output_directory,
        artifacts=artifacts,
        motion_authority="unity",
        port=0,
    )
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "assign_vehicle_destination",
                        "vehicle_id": vehicle_id,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

        bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        bootstrap_payload = json.loads(bootstrap_response.read().decode("utf-8"))
        route_following = bootstrap_payload["bootstrap"]["runtime"]["route_following"][0]
        assert route_following["route_status"] == "active"
        assert route_following["current_target_node_id"] == route_following["waypoints"][1][
            "node_id"
        ]

        telemetry_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/unity/telemetry",
                data=json.dumps(
                    {
                        "telemetry": {
                            "vehicle_id": vehicle_id,
                            "timestamp_s": 3.5,
                            "position": route_following["waypoints"][-1]["position"],
                            "speed": 0.0,
                            "route_status": "complete",
                            "route_progress": 1.0,
                            "current_target_node_id": destination_node_id,
                            "current_waypoint_index": len(route_following["waypoints"]) - 1,
                            "route_destination_node_id": destination_node_id,
                            "route_completed": True,
                        }
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        telemetry_payload = json.loads(telemetry_response.read().decode("utf-8"))
        assert telemetry_payload["telemetry"]["latest_route_progress_by_vehicle_id"][0][
            "route_status"
        ] == "complete"
        assert telemetry_payload["telemetry"]["latest_route_progress_by_vehicle_id"][0][
            "route_completed"
        ] is True
        assert telemetry_payload["telemetry"]["latest_embodiment_status_by_vehicle_id"][0][
            "embodiment_state"
        ] == "complete"
        assert server._runtime.latest_unity_route_progress_by_vehicle_id[vehicle_id][
            "route_status"
        ] == "complete"
        assert server._runtime.latest_unity_embodiment_status_by_vehicle_id[vehicle_id][
            "embodiment_state"
        ] == "complete"

        refreshed_bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        refreshed_bootstrap_payload = json.loads(
            refreshed_bootstrap_response.read().decode("utf-8")
        )
        assert refreshed_bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "route_status"
        ] == "complete"
        assert refreshed_bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "embodiment_state"
        ] == "complete"
        live_bundle_payload = _read_live_bundle(base_url)
        assert live_bundle_payload["replay_analysis"]["summary"]["completed_vehicle_ids"] == [
            vehicle_id
        ]
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["outcome"][
            "route_status"
        ] == "complete"
    finally:
        server.stop()


def test_live_app_frontend_server_projects_blocked_embodiment_state(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["snapshot"]["vehicles"][0]["vehicle_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    blocker_edge_id = bundle["map_surface"]["edges"][1]["edge_id"]
    server = LiveAppServer(
        artifacts.output_directory,
        artifacts=artifacts,
        motion_authority="unity",
        port=0,
    )
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "assign_vehicle_destination",
                        "vehicle_id": vehicle_id,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

        blocked_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/unity/telemetry",
                data=json.dumps(
                    {
                        "telemetry": {
                            "vehicle_id": vehicle_id,
                            "timestamp_s": 4.2,
                            "position": [0.2, 0.0, 0.1],
                            "speed": 0.0,
                            "route_status": "blocked",
                            "route_progress": 0.1,
                            "blockage_reason": "blocked_edge",
                            "blockage_edge_id": blocker_edge_id,
                            "blockage_node_id": destination_node_id,
                            "exception_code": "movement_blocked",
                            "embodiment_state": "blocked",
                        }
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        blocked_payload = json.loads(blocked_response.read().decode("utf-8"))
        assert blocked_payload["telemetry"]["latest_route_progress_by_vehicle_id"][0][
            "route_status"
        ] == "blocked"
        assert blocked_payload["telemetry"]["latest_route_progress_by_vehicle_id"][0][
            "blockage_edge_id"
        ] == blocker_edge_id
        assert blocked_payload["telemetry"]["latest_route_progress_by_vehicle_id"][0][
            "exception_code"
        ] == "movement_blocked"
        assert blocked_payload["telemetry"]["latest_embodiment_status_by_vehicle_id"][0][
            "blockage_reason"
        ] == "blocked_edge"
        assert blocked_payload["telemetry"]["latest_embodiment_status_by_vehicle_id"][0][
            "embodiment_state"
        ] == "blocked"
        assert server._runtime.latest_unity_route_progress_by_vehicle_id[vehicle_id][
            "blockage_edge_id"
        ] == blocker_edge_id
        assert server._runtime.latest_unity_embodiment_status_by_vehicle_id[vehicle_id][
            "blockage_edge_id"
        ] == blocker_edge_id
        assert server._runtime.unity_embodiment_history[-1]["embodiment_state"] == "blocked"
        live_bundle_payload = _read_live_bundle(base_url)
        assert live_bundle_payload["operator_state"]["motion_authority"] == "unity"
        assert live_bundle_payload["operator_state"]["blocked_vehicle_ids"] == [vehicle_id]
        assert live_bundle_payload["operator_state"]["vehicles"][0]["route_status"] == "blocked"
        assert live_bundle_payload["operator_state"]["vehicles"][0]["embodiment_state"] == "blocked"
        assert live_bundle_payload["replay_analysis"]["summary"]["blocked_vehicle_ids"] == [
            vehicle_id
        ]
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["timeline"][-1][
            "event_type"
        ] in {"route_progress", "embodiment"}
        assert live_bundle_payload["replay_analysis"]["vehicles"][0]["outcome"][
            "exception_code"
        ] == "movement_blocked"

        refreshed_bootstrap_response = request.urlopen(f"{base_url}/api/unity/bootstrap")
        refreshed_bootstrap_payload = json.loads(
            refreshed_bootstrap_response.read().decode("utf-8")
        )
        assert refreshed_bootstrap_payload["bootstrap"][
            "runtime"
        ]["route_following"][0]["embodiment_state"] == "blocked"
        assert refreshed_bootstrap_payload["bootstrap"]["runtime"]["route_following"][0][
            "embodiment_state"
        ] == "blocked"
    finally:
        server.stop()


def test_live_app_defers_assign_destination_until_session_advances(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    initial_bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = initial_bundle["command_center"]["vehicles"][0]["vehicle_id"]
    destination_node_id = initial_bundle["map_surface"]["edges"][0]["end_node_id"]
    initial_vehicle = _vehicle_by_id(initial_bundle, vehicle_id)
    initial_time_s = initial_bundle["simulated_time_s"]
    initial_position = initial_vehicle["position"]
    initial_trace_count = len(initial_bundle["trace_events"])
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        assign_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "assign_vehicle_destination",
                        "vehicle_id": vehicle_id,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assign_payload = json.loads(assign_response.read().decode("utf-8"))
        assert assign_payload["ok"] is True
        assert assign_payload["bundle"]["session_control"]["play_state"] == "paused"
        assert assign_payload["bundle"]["session_control"]["pending_route_commands"] == [
            {
                "command_type": "assign_vehicle_destination",
                "destination_node_id": destination_node_id,
                "vehicle_id": vehicle_id,
            }
        ]

        paused_bundle = _read_live_bundle(base_url)
        paused_vehicle = paused_bundle["snapshot"]["vehicles"][0]
        assert paused_bundle["simulated_time_s"] == initial_time_s
        assert paused_vehicle["position"] == initial_position
        assert paused_vehicle["node_id"] == initial_vehicle["node_id"]
        assert paused_bundle["session_control"]["pending_route_commands"] == [
            {
                "command_type": "assign_vehicle_destination",
                "destination_node_id": destination_node_id,
                "vehicle_id": vehicle_id,
            }
        ]
        assert len(paused_bundle["trace_events"]) == initial_trace_count
        assert all(
            event["event_type"] != "route_complete"
            for event in paused_bundle["trace_events"]
        )

        step_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "step",
                        "delta_s": 0.5,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        step_payload = json.loads(step_response.read().decode("utf-8"))
        assert step_payload["ok"] is True
        assert step_payload["session_advance"]["completed_at_s"] >= initial_time_s
        assert step_payload["bundle"]["simulated_time_s"] >= initial_time_s
        assert step_payload["bundle"]["session_control"]["pending_route_commands"] == []

        stepped_bundle = _read_live_bundle(base_url)
        stepped_vehicle = _vehicle_by_id(stepped_bundle, vehicle_id)
        destination_position = _node_position(stepped_bundle, destination_node_id)
        assert stepped_bundle["simulated_time_s"] >= initial_time_s
        assert stepped_vehicle["position"] != initial_position
        assert stepped_vehicle["position"] != destination_position
        assert not any(
            event["event_type"] == "route_complete"
            and event["vehicle_id"] == vehicle_id
            for event in stepped_bundle["trace_events"]
        )

        completed_bundle = stepped_bundle
        completed_vehicle = stepped_vehicle
        for _ in range(1, 10):
            request.urlopen(
                request.Request(
                    url=f"{base_url}/api/live/session/control",
                    data=json.dumps(
                        {
                            "action": "step",
                            "delta_s": 0.5,
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            completed_bundle = _read_live_bundle(base_url)
            completed_vehicle = _vehicle_by_id(completed_bundle, vehicle_id)
            if any(
                event["event_type"] == "route_complete"
                and event["vehicle_id"] == vehicle_id
                for event in completed_bundle["trace_events"]
            ):
                break

        assert any(
            event["event_type"] == "route_complete"
            and event["vehicle_id"] == vehicle_id
            for event in completed_bundle["trace_events"]
        )
        assert completed_vehicle["position"] == destination_position
    finally:
        server.stop()


def test_live_app_playback_loop_falls_back_to_paused_when_tick_fails(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    original_advance_session = server._runtime.advance_session

    def failing_advance_session(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    server._runtime.advance_session = failing_advance_session  # type: ignore[assignment]
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        play_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/session/control",
                data=json.dumps(
                    {
                        "action": "play",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        play_payload = json.loads(play_response.read().decode("utf-8"))
        assert play_payload["ok"] is True
        assert play_payload["bundle"]["session_control"]["play_state"] == "playing"

        paused_bundle = _wait_for_live_time(base_url, 0.0)
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            session_control = paused_bundle["session_control"]
            assert isinstance(session_control, dict)
            play_state = session_control["play_state"]
            assert isinstance(play_state, str)
            if play_state == "paused":
                break
            time.sleep(0.05)
            paused_bundle = _read_live_bundle(base_url)

        session_control = paused_bundle["session_control"]
        assert isinstance(session_control, dict)
        play_state = session_control["play_state"]
        assert isinstance(play_state, str)
        assert play_state == "paused"
        assert server._runtime.playback_thread is None
        paused_time_s = paused_bundle["simulated_time_s"]
        assert isinstance(paused_time_s, (int, float))
        assert paused_time_s == 0.0
    finally:
        server._runtime.advance_session = original_advance_session  # type: ignore[assignment]
        server.stop()


def test_live_app_frontend_server_supports_route_preview_and_batch_commands(
    tmp_path,
) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_ids = [vehicle["vehicle_id"] for vehicle in bundle["command_center"]["vehicles"][:2]]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "vehicle_ids": vehicle_ids,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        assert preview_payload["ok"] is True
        assert [entry["vehicle_id"] for entry in preview_payload["route_previews"]] == vehicle_ids
        assert preview_payload["bundle"]["command_center"]["selected_vehicle_ids"] == vehicle_ids

        command_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/command",
                data=json.dumps(
                    {
                        "command_type": "assign_vehicle_destination",
                        "vehicle_ids": vehicle_ids,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        command_payload = json.loads(command_response.read().decode("utf-8"))
        assert command_payload["ok"] is True
        assert len(command_payload["command_results"]) == len(vehicle_ids)
        assert [result["command"]["vehicle_id"] for result in command_payload["command_results"]] == vehicle_ids
        assert command_payload["bundle"]["command_center"]["recent_commands"][-1]["vehicle_id"] == vehicle_ids[-1]
    finally:
        server.stop()


def test_live_app_frontend_server_supports_route_preview_endpoint(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["command_center"]["vehicles"][0]["vehicle_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "route_preview_requests": [
                            {
                                "vehicle_id": vehicle_id,
                                "destination_node_id": destination_node_id,
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        assert preview_payload["ok"] is True
        assert preview_payload["route_previews"][0]["vehicle_id"] == vehicle_id
        assert preview_payload["route_previews"][0]["destination_node_id"] == destination_node_id
        assert preview_payload["route_previews"][0]["is_actionable"] is True
        assert preview_payload["bundle"]["command_center"]["route_previews"] == preview_payload["route_previews"]
        assert preview_payload["bundle"]["command_center"]["selected_vehicle_ids"] == [vehicle_id]
        assert preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "route_ahead_node_ids"
        ] == preview_payload["route_previews"][0]["node_ids"]
        assert preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "route_ahead_edge_ids"
        ] == preview_payload["route_previews"][0]["edge_ids"]
        assert preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "eta_s"
        ] is not None
        assert preview_payload["bundle"]["session_control"]["route_preview_endpoint"] == "/api/live/preview"
    finally:
        server.stop()


def test_live_app_frontend_server_rejects_invalid_route_preview_payload(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        try:
            request.urlopen(
                request.Request(
                    url=f"{base_url}/api/live/preview",
                    data=json.dumps(
                        {
                            "route_preview_requests": [
                                {"vehicle_id": 77},
                            ]
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            raise AssertionError("invalid preview payload should be rejected")
        except error.HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read().decode("utf-8"))
            assert payload["ok"] is False
            assert payload["validation_messages"][0]["code"] == "invalid_request"
            assert "destination_node_id" in payload["message"]
    finally:
        server.stop()


def test_live_app_frontend_server_handles_unknown_vehicle_route_preview(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "route_preview_requests": [
                            {
                                "vehicle_id": 999_999,
                                "destination_node_id": 1,
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        preview = preview_payload["route_previews"][0]
        assert preview["is_actionable"] is False
        assert preview["reason"] == "unknown_vehicle"
        assert preview["node_ids"] == []
        assert preview["edge_ids"] == []
        assert preview["total_distance"] is None
    finally:
        server.stop()


def test_live_app_frontend_server_handles_unknown_destination_route_preview(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["command_center"]["vehicles"][0]["vehicle_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "route_preview_requests": [
                            {
                                "vehicle_id": vehicle_id,
                                "destination_node_id": 999_999,
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        preview = preview_payload["route_previews"][0]
        assert preview["vehicle_id"] == vehicle_id
        assert preview["is_actionable"] is False
        assert preview["reason"] == "unknown_destination"
        assert preview["node_ids"] == []
        assert preview["edge_ids"] == []
        assert preview["total_distance"] is None
    finally:
        server.stop()


def test_live_app_frontend_server_handles_blocked_route_preview_as_no_route(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["command_center"]["vehicles"][0]["vehicle_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        for edge in bundle["map_surface"]["edges"]:
            request.urlopen(
                request.Request(
                    url=f"{base_url}/api/live/command",
                    data=json.dumps(
                        {
                            "command_type": "block_edge",
                            "edge_id": edge["edge_id"],
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )

        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "route_preview_requests": [
                            {
                                "vehicle_id": vehicle_id,
                                "destination_node_id": destination_node_id,
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        preview = preview_payload["route_previews"][0]
        assert preview["is_actionable"] is False
        assert preview["reason"] == "no_route"
        assert preview["node_ids"] == []
        assert preview["edge_ids"] == []
        assert preview["total_distance"] is None
    finally:
        server.stop()


def test_live_app_frontend_server_handles_non_idle_vehicle_route_preview(tmp_path) -> None:
    frontend_dist = tmp_path / "dist"
    frontend_dist.mkdir()
    (frontend_dist / "index.html").write_text("<!doctype html><title>Serious UI</title>", encoding="utf-8")

    artifacts = export_live_app_artifacts(
        scenario_path="scenarios/showpiece_pack/01_mine_ore_shift.json",
        output_directory=tmp_path / "output",
        frontend_dist_directory=frontend_dist,
    )
    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    vehicle_id = bundle["command_center"]["vehicles"][0]["vehicle_id"]
    destination_node_id = bundle["map_surface"]["edges"][0]["end_node_id"]
    server = LiveAppServer(artifacts.output_directory, artifacts=artifacts, port=0)
    server.start()
    base_url = f"http://{server.host}:{server.port}"

    try:
        behavior = server._runtime.session.engine.get_vehicle(vehicle_id).behavior
        assert behavior is not None
        behavior.transition_to(
            VehicleOperationalState.MOVING,
            reason="test_setup",
        )
        preview_response = request.urlopen(
            request.Request(
                url=f"{base_url}/api/live/preview",
                data=json.dumps(
                    {
                        "route_preview_requests": [
                            {
                                "vehicle_id": vehicle_id,
                                "destination_node_id": destination_node_id,
                            }
                        ],
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        preview = preview_payload["route_previews"][0]
        assert preview["vehicle_id"] == vehicle_id
        assert preview["is_actionable"] is False
        assert preview["reason"] == "vehicle_not_idle"
        assert preview["node_ids"] == preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "route_ahead_node_ids"
        ]
        assert preview["edge_ids"] == preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "route_ahead_edge_ids"
        ]
        assert preview_payload["bundle"]["command_center"]["vehicle_inspections"][0]["eta_s"] is not None
    finally:
        server.stop()
