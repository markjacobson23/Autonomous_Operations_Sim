import json

from autonomous_ops_sim.live_app import (
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

    bundle = json.loads(artifacts.live_session_bundle_path.read_text(encoding="utf-8"))
    assert bundle["metadata"]["surface_name"] == "live_session_bundle"
    assert bundle["seed"] == 3801


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
