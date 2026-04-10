import json
from urllib import request

from autonomous_ops_sim.live_app import (
    LiveAppServer,
    build_live_app_url,
    export_live_app_artifacts,
    launch_live_app,
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
    assert artifacts.launch_path == tmp_path / "output" / "serious_ui" / "index.html"
    assert artifacts.launch_path.exists()
    assert (tmp_path / "output" / "serious_ui" / "assets" / "app.js").exists()
    assert artifacts.launch_relative_url == "/serious_ui/index.html?bundle=/live_session_bundle.json"


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
                        "vehicle_id": vehicle_id,
                        "destination_node_id": destination_node_id,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        assert preview_payload["ok"] is True
        assert preview_payload["bundle"]["command_center"]["route_previews"][0][
            "vehicle_id"
        ] == vehicle_id
        assert preview_payload["bundle"]["command_center"]["route_previews"][0][
            "destination_node_id"
        ] == destination_node_id
        assert preview_payload["bundle"]["command_center"]["vehicle_inspections"][0][
            "route_ahead_node_ids"
        ]
        assert preview_payload["bundle"]["session_control"]["route_preview_endpoint"] == "/api/live/preview"
    finally:
        server.stop()
