import json
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
