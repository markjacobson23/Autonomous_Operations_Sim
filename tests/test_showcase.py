import json
from pathlib import Path

from autonomous_ops_sim.io.scenario_pack_runner import run_scenario_pack
from autonomous_ops_sim.showcase import (
    DEFAULT_SHOWCASE_PACK_DIRECTORY,
    export_showcase_demo,
    main as showcase_main,
)


def test_showpiece_pack_runs_with_stable_mining_scenarios() -> None:
    result = run_scenario_pack(DEFAULT_SHOWCASE_PACK_DIRECTORY)

    assert [entry.relative_path for entry in result.scenario_results] == [
        "01_mine_ore_shift.json",
        "02_hazard_detour.json",
        "03_tight_turnaround.json",
    ]
    assert [entry.scenario_name for entry in result.scenario_results] == [
        "mine_showpiece_ore_shift",
        "mine_showpiece_hazard_detour",
        "mine_showpiece_tight_turnaround",
    ]
    assert result.aggregate_summary.scenario_count == 3
    assert result.aggregate_summary.total_completed_job_count == 10
    assert result.aggregate_summary.total_completed_task_count == 22
    assert result.aggregate_summary.total_trace_event_count > 0


def test_showcase_export_writes_replay_live_and_pack_artifacts(tmp_path) -> None:
    artifacts = export_showcase_demo(tmp_path)

    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    replay_bundle = json.loads(artifacts.replay_bundle_path.read_text(encoding="utf-8"))
    live_session_bundle = json.loads(
        artifacts.live_session_bundle_path.read_text(encoding="utf-8")
    )
    live_sync_bundle = json.loads(
        artifacts.live_sync_bundle_path.read_text(encoding="utf-8")
    )
    pack_export = json.loads(
        artifacts.scenario_pack_export_path.read_text(encoding="utf-8")
    )

    assert manifest["flagship_scenario"]["name"] == "mine_showpiece_ore_shift"
    assert manifest["scenario_pack"]["aggregate_summary"]["scenario_count"] == 3
    assert replay_bundle["metadata"]["surface_name"] == "replay_bundle"
    assert live_session_bundle["metadata"]["surface_name"] == "live_session_bundle"
    assert live_sync_bundle["metadata"]["surface_name"] == "live_sync_bundle"
    assert live_session_bundle["command_center"]["selected_vehicle_ids"] == [301]
    assert live_session_bundle["command_center"]["route_previews"][0]["reason"] == "no_route"
    assert live_session_bundle["command_center"]["ai_assist"]["suggestions"][0]["kind"] == (
        "reopen_edge"
    )
    assert pack_export["aggregate_summary"]["scenario_names"] == [
        "mine_showpiece_ore_shift",
        "mine_showpiece_hazard_detour",
        "mine_showpiece_tight_turnaround",
    ]
    assert "Mine Operations Replay Showpiece" in artifacts.replay_viewer_path.read_text(
        encoding="utf-8"
    )
    assert "Command Center" in artifacts.live_session_viewer_path.read_text(
        encoding="utf-8"
    )
    assert "AI Assistant" in artifacts.live_sync_viewer_path.read_text(
        encoding="utf-8"
    )


def test_showcase_cli_writes_manifest_path(tmp_path, capsys) -> None:
    exit_code = showcase_main(["--output-dir", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert Path(captured.out.strip()) == tmp_path / "showcase_manifest.json"
