from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_step_45_app_shell_source_includes_required_operator_regions() -> None:
    app_source = (
        REPO_ROOT / "frontend" / "serious_ui" / "src" / "App.tsx"
    ).read_text(encoding="utf-8")

    assert "Step 57 Stop Lines, Yielding, and Traffic-Control Logic" in app_source
    assert "Command-Center Region" in app_source
    assert "Inspector Region" in app_source
    assert "Alerts Region" in app_source
    assert "Authoring Region" in app_source
    assert "Timeline Region" in app_source
    assert "Minimap Navigation" in app_source
    assert "Autonomous Ops Command Deck" in app_source
    assert "Fit Scene" in app_source
    assert "Focus Selected" in app_source
    assert "Stop lines and yield controls are now live" in app_source
    assert "Save Scenario" in app_source
    assert "Reload Scenario" in app_source
    assert "turn_connectors" in app_source
    assert "stop_lines" in app_source
    assert "merge_zones" in app_source
    assert "renderVehicleGlyph" in app_source
    assert "motion_segments" in app_source
    assert "formatHeadingDegrees" in app_source
    assert "vehicle-envelope" in app_source
    assert "Min Spacing" in app_source
    assert "Traffic Heatmap" in app_source
    assert "sampleTrafficSnapshot" in app_source
    assert "trafficCongestionIntensity" in app_source
    assert "trafficCongestionLevel" in app_source
    assert "traffic_control_state" in app_source
    assert "protected_conflict_zone_ids" in app_source
    assert "scene-road-heatmap" in app_source
    assert "traffic-summary-chip" in app_source
    assert "scene-legend" in app_source
    assert "selectVehicle" in app_source
    assert "selectRoad" in app_source
    assert "selectArea" in app_source
    assert "selectQueue" in app_source
    assert "selectHazard" in app_source
    assert "scene-edit-handle" in app_source


def test_step_45_app_shell_styles_define_responsive_multi_panel_layout() -> None:
    css_source = (
        REPO_ROOT / "frontend" / "serious_ui" / "src" / "app-shell.css"
    ).read_text(encoding="utf-8")

    assert ".session-bar" in css_source
    assert ".workspace" in css_source
    assert ".stage-grid" in css_source
    assert ".timeline-region" in css_source
    assert ".overview-panel" in css_source
    assert ".scene-toolbar" in css_source
    assert ".layer-toolbar" in css_source
    assert ".minimap" in css_source
    assert ".hover-card" in css_source
    assert ".shell-accent" in css_source
    assert ".scene-rim" in css_source
    assert ".scene-legend" in css_source
    assert ".action-row" in css_source
    assert ".scene-lane" in css_source
    assert ".scene-turn-connector" in css_source
    assert ".scene-stop-line" in css_source
    assert ".scene-merge-zone" in css_source
    assert ".scene-road-heatmap" in css_source
    assert ".traffic-summary-chip" in css_source
    assert ".traffic-heatmap-list" in css_source
    assert ".vehicle-body-haul" in css_source
    assert ".vehicle-body-forklift" in css_source
    assert ".vehicle-body-car" in css_source
    assert ".vehicle-body-generic" in css_source
    assert ".scene-edit-handle" in css_source
    assert ".scene-area.selected" in css_source
    assert ".scene-road.selected" in css_source
    assert ".scene-reservation.selected" in css_source
    assert ".scene-hazard.selected" in css_source
    assert "@keyframes traffic-flow" in css_source
    assert "@media (max-width: 980px)" in css_source
