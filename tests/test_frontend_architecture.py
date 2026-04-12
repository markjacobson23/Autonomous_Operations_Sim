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
    assert plan.frontend_workspace == "frontend/frontend_v2"
    assert len(plan.rationale) == 3


def test_frontend_architecture_note_records_locked_direction() -> None:
    architecture_note = (
        REPO_ROOT / "docs" / "frontend_architecture.md"
    ).read_text(encoding="utf-8")

    assert "Primary stack: `React + TypeScript + Vite`" in architecture_note
    assert "Fallback stack: the existing Python-generated standalone serious viewer HTML export path." in architecture_note
    assert "frontend/frontend_v2/" in architecture_note
    assert "Python remains authoritative" in architecture_note


def test_frontend_v2_workspace_contains_expected_scaffold_files() -> None:
    workspace = REPO_ROOT / "frontend" / "frontend_v2"

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


def test_frontend_v2_package_json_defines_dev_and_build_scripts() -> None:
    package_json = json.loads(
        (REPO_ROOT / "frontend" / "frontend_v2" / "package.json").read_text(
            encoding="utf-8"
        )
    )

    assert package_json["name"] == "autonomous-ops-frontend-v2"
    assert package_json["private"] is True
    assert package_json["scripts"]["dev"] == "vite"
    assert package_json["scripts"]["build"] == "tsc -b && vite build"
    assert package_json["dependencies"]["react"].startswith("^18.")


def test_frontend_v2_vite_config_uses_relative_base_for_nested_live_launch_path() -> None:
    vite_config = (
        REPO_ROOT / "frontend" / "frontend_v2" / "vite.config.ts"
    ).read_text(encoding="utf-8")

    assert 'base: "./"' in vite_config


def test_frontend_v2_shell_is_thin_and_defers_to_adapter_layers() -> None:
    app_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "App.tsx"
    ).read_text(encoding="utf-8")

    assert "useLiveSessionBundle" in app_source
    assert "buildLiveBundleViewModel" in app_source
    assert "useFrontendUiState" in app_source
    assert "FrontendShell" in app_source
    assert "fetch(" not in app_source
    assert "readRecord(" not in app_source
    assert "pointsToPath(" not in app_source


def test_frontend_v2_adapter_and_local_state_layers_exist() -> None:
    expected_files = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "adapters" / "liveBundle.ts",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "adapters" / "mapViewport.ts",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "adapters" / "selectionModel.ts",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "hooks" / "useLiveSessionBundle.ts",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "state" / "frontendUiState.ts",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "FrontendShell.tsx",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "MapShell.tsx",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "MapMinimap.tsx",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "LiveSceneCanvas.tsx",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "SelectionPopup.tsx",
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "OperateRail.tsx",
    )

    for path in expected_files:
        assert path.exists(), f"Expected frontend v2 layer file at {path}"


def test_frontend_v2_map_shell_exposes_camera_and_layer_controls() -> None:
    map_shell_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "MapShell.tsx"
    ).read_text(encoding="utf-8")
    minimap_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "MapMinimap.tsx"
    ).read_text(encoding="utf-8")
    scene_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "LiveSceneCanvas.tsx"
    ).read_text(encoding="utf-8")

    assert "Fit Scene" in map_shell_source
    assert "Focus Selected" in map_shell_source
    assert "Zoom In" in map_shell_source
    assert "Zoom Out" in map_shell_source
    assert "Iso" in map_shell_source
    assert "Birdseye" in map_shell_source
    assert "layer-chip" in map_shell_source
    assert "MapMinimap" in map_shell_source
    assert "viewBox" in minimap_source
    assert "Click to re-center" in minimap_source
    assert "sceneTransform" in scene_source
    assert "layers.roads" in scene_source
    assert "layers.vehicles" in scene_source
    assert "layers.areas" in scene_source
    assert "layers.labels" in scene_source
    assert "selectionTarget" in scene_source
    assert "onSelectVehicle" in scene_source
    assert "onSelectRoad" in scene_source
    assert "onSelectArea" in scene_source


def test_frontend_v2_scene_defaults_are_quiet_and_world_form_readable() -> None:
    scene_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "LiveSceneCanvas.tsx"
    ).read_text(encoding="utf-8")
    ui_state_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "state" / "frontendUiState.ts"
    ).read_text(encoding="utf-8")

    assert "map-ground" in scene_source
    assert "area-surface" in scene_source
    assert "vehicle-label" in scene_source
    assert "layers.labels &&" in scene_source
    assert "<pattern id=\"grid\"" not in scene_source
    assert "areas: true" in ui_state_source
    assert "labels: false" in ui_state_source


def test_frontend_v2_selection_and_inspector_surface_are_wired() -> None:
    selection_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "adapters" / "selectionModel.ts"
    ).read_text(encoding="utf-8")
    map_shell_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "MapShell.tsx"
    ).read_text(encoding="utf-8")
    frontend_shell_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "FrontendShell.tsx"
    ).read_text(encoding="utf-8")
    operate_source = (
        REPO_ROOT / "frontend" / "frontend_v2" / "src" / "components" / "OperateRail.tsx"
    ).read_text(encoding="utf-8")

    assert "SelectionTarget" in selection_source
    assert "buildSelectionPresentation" in selection_source
    assert "focusPointsForSelection" in selection_source
    assert "resolveActiveSelectionTarget" in selection_source
    assert "resolveSelectionVehicleIds" in selection_source
    assert "SelectionPopup" in map_shell_source
    assert "setSelection" in map_shell_source
    assert "setPopup" in map_shell_source
    assert "setInspector" in map_shell_source
    assert "buildSelectionPresentation" in frontend_shell_source
    assert "OperateRail" in frontend_shell_source
    assert "selection-inspector-details" in operate_source
    assert "Preview selected" in operate_source
    assert "Assign destination" in operate_source
    assert "Refresh" in operate_source
    assert "Play" in operate_source
    assert "Pause" in operate_source
    assert "Step" in operate_source
