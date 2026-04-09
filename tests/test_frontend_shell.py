from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_step_43_app_shell_source_includes_required_operator_regions() -> None:
    app_source = (
        REPO_ROOT / "frontend" / "serious_ui" / "src" / "App.tsx"
    ).read_text(encoding="utf-8")

    assert "Step 44 Navigation Shell" in app_source
    assert "Command-Center Region" in app_source
    assert "Inspector Region" in app_source
    assert "Alerts Region" in app_source
    assert "Timeline Region" in app_source
    assert "Minimap Navigation" in app_source
    assert "Autonomous Ops Command Deck" in app_source
    assert "Fit Scene" in app_source
    assert "Focus Selected" in app_source


def test_step_43_app_shell_styles_define_responsive_multi_panel_layout() -> None:
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
    assert "@media (max-width: 980px)" in css_source
