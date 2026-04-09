import json
from pathlib import Path

from autonomous_ops_sim.visualization.serious_viewer import build_viewer_foundation_plan


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_viewer_foundation_plan_locks_primary_stack_fallback_and_workspace() -> None:
    plan = build_viewer_foundation_plan()

    assert plan.primary_stack == "react_typescript_vite_svg"
    assert plan.fallback_stack == "standalone_serious_viewer_html"
    assert plan.transport_surface == "simulation_api_bundle_json"
    assert plan.backend_authority == "python_simulator"
    assert plan.frontend_workspace == "frontend/serious_ui"
    assert len(plan.rationale) == 3


def test_frontend_architecture_note_records_locked_direction() -> None:
    architecture_note = (
        REPO_ROOT / "docs" / "frontend_architecture.md"
    ).read_text(encoding="utf-8")

    assert "Primary stack: `React + TypeScript + Vite`" in architecture_note
    assert "Fallback stack: the existing Python-generated standalone serious viewer HTML export path." in architecture_note
    assert "frontend/serious_ui/" in architecture_note
    assert "Python remains authoritative" in architecture_note


def test_serious_ui_workspace_contains_expected_scaffold_files() -> None:
    workspace = REPO_ROOT / "frontend" / "serious_ui"

    expected_files = (
        workspace / "package.json",
        workspace / "tsconfig.json",
        workspace / "tsconfig.app.json",
        workspace / "vite.config.ts",
        workspace / "index.html",
        workspace / "src" / "main.tsx",
        workspace / "src" / "App.tsx",
        workspace / "src" / "app-shell.css",
    )

    for path in expected_files:
        assert path.exists(), f"Expected frontend scaffold file at {path}"


def test_serious_ui_package_json_defines_dev_and_build_scripts() -> None:
    package_json = json.loads(
        (REPO_ROOT / "frontend" / "serious_ui" / "package.json").read_text(
            encoding="utf-8"
        )
    )

    assert package_json["name"] == "autonomous-ops-serious-ui"
    assert package_json["private"] is True
    assert package_json["scripts"]["dev"] == "vite"
    assert package_json["scripts"]["build"] == "tsc -b && vite build"
    assert package_json["dependencies"]["react"].startswith("^18.")


def test_serious_ui_vite_config_uses_relative_base_for_nested_live_launch_path() -> None:
    vite_config = (
        REPO_ROOT / "frontend" / "serious_ui" / "vite.config.ts"
    ).read_text(encoding="utf-8")

    assert 'base: "./"' in vite_config
