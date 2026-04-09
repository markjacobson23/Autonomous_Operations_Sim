import json
from pathlib import Path
import subprocess

from autonomous_ops_sim.cli import main


def test_cli_run_valid_scenario(capsys):
    exit_code = main(["run", "scenarios/example.json"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "scenario: basic_grid_demo" in captured.out
    assert "source: scenarios/example.json" in captured.out
    assert captured.err == ""


def test_cli_run_invalid_scenario_path(capsys):
    exit_code = main(["run", "scenarios/does_not_exist.json"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: failed to load scenario 'scenarios/does_not_exist.json'" in captured.err


def test_cli_run_invalid_scenario_content(tmp_path, capsys):
    bad_path = tmp_path / "invalid.json"
    bad_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    exit_code = main(["run", str(bad_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert f"Error: failed to load scenario '{bad_path}'" in captured.err


def test_cli_run_summary_is_stable_across_repeated_runs(capsys):
    first_exit = main(["run", "scenarios/example.json"])
    first_capture = capsys.readouterr()

    second_exit = main(["run", "scenarios/example.json"])
    second_capture = capsys.readouterr()

    assert first_exit == 0
    assert second_exit == 0
    assert first_capture.out == second_capture.out


def test_module_cli_run_command_works():
    result = subprocess.run(
        ["python3", "-m", "autonomous_ops_sim.cli", "run", "scenarios/example.json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "scenario: basic_grid_demo" in result.stdout


def test_cli_execute_runs_scenario_and_emits_export_json(capsys):
    exit_code = main(["execute", "scenarios/step_12_single_vehicle_job.json"])

    captured = capsys.readouterr()
    export_record = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert export_record["seed"] == 212
    assert export_record["summary"]["completed_job_count"] == 1


def test_module_cli_execute_command_works():
    result = subprocess.run(
        [
            "python3",
            "-m",
            "autonomous_ops_sim.cli",
            "execute",
            "scenarios/step_12_single_vehicle_job.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["final_time_s"] == 6.0


def test_cli_showcase_exports_showpiece_manifest(tmp_path, capsys):
    exit_code = main(["showcase", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    manifest_path = Path(captured.out.strip())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest_path == tmp_path / "showcase_manifest.json"
    assert manifest["flagship_scenario"]["name"] == "mine_showpiece_ore_shift"
    assert manifest["scenario_pack"]["aggregate_summary"]["scenario_count"] == 3
