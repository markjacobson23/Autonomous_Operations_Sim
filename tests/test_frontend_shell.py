from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_serious_ui_shell_source_includes_finished_operator_regions() -> None:
    shell_source = "\n".join(
        (
            REPO_ROOT / "frontend" / "serious_ui" / "src" / path
        ).read_text(encoding="utf-8")
        for path in (
            "App.tsx",
            "components/WorkspaceShell.tsx",
            "components/SceneViewport.tsx",
            "components/tabs/OperateTab.tsx",
            "components/tabs/FleetTab.tsx",
            "components/tabs/EditorTab.tsx",
            "components/tabs/TrafficTab.tsx",
            "components/tabs/AnalyzeTab.tsx",
            "viewModel.tsx",
            "app-shell.css",
        )
    )
    assert "Final UI cleanup pass" in shell_source
    assert "Operate" in shell_source
    assert "Traffic" in shell_source
    assert "Fleet" in shell_source
    assert "Editor" in shell_source
    assert "Analyze" in shell_source
    assert "Primary Operator Workflow" in shell_source
    assert "Session Status" in shell_source
    assert "Traffic Region" in shell_source
    assert "Fleet Control" in shell_source
    assert "Selected Fleet" in shell_source
    assert "Batch Actions" in shell_source
    assert "Runtime Controls" in shell_source
    assert "Inspection Context" in shell_source
    assert "Selected Vehicles" in shell_source
    assert "Recent Commands" in shell_source
    assert "Scenario Authoring" in shell_source
    assert "Working scenario controls, staged geometry, and validation live together here." in shell_source
    assert "Authoring Controls" in shell_source
    assert "Working Scenario" in shell_source
    assert "Validation clean" in shell_source
    assert "Validation blocked" in shell_source
    assert "Diagnostics and AI Review" in shell_source
    assert "Urgent issues" in shell_source
    assert "Recommended actions" in shell_source
    assert "Supporting Context" in shell_source
    assert "Recent Commands" in shell_source
    assert "Current target" in shell_source
    assert "Route Planning" in shell_source
    assert "Route Preview" in shell_source
    assert "Preview Route" in shell_source
    assert "Waiting for route preview" in shell_source
    assert "Assign Destination" in shell_source
    assert "Reposition Vehicle" in shell_source
    assert "Select Visible" in shell_source
    assert "Clear Selection" in shell_source
    assert "Spawn Vehicle" in shell_source
    assert "Remove Vehicle" in shell_source
    assert "Inject Job" in shell_source
    assert "Declare Hazard" in shell_source
    assert "Clear Hazard" in shell_source
    assert "Edit Scene" in shell_source
    assert "Save Scenario" in shell_source
    assert "Reload Scenario" in shell_source
    assert "Single-Step" in shell_source
    assert "Batch mode activates" in shell_source
    assert "Traffic Region" in shell_source
    assert "Traffic Control" in shell_source
    assert "Congestion Overview" in shell_source
    assert "Active Road Conditions" in shell_source
    assert "Queue and Reservation Detail" in shell_source
    assert "Blocked Edge Watch" in shell_source
    assert "Suggestions" in shell_source
    assert "Anomalies" in shell_source
    assert "Supporting Context" in shell_source
    assert "analysis-chip-alert" in shell_source
    assert "analyze-review-section-urgent" in shell_source
    assert "review-card-urgent" in shell_source
    assert "review-command-item" in shell_source
    assert "review-diagnostic-pill" in shell_source
    assert "operate-session-controls" in shell_source
    assert "operate-route-planning" in shell_source
    assert "fleet-pane" in shell_source
    assert "editor-pane" in shell_source
    assert "traffic-pane" in shell_source
    assert "traffic-monitor-board" in shell_source
    assert "traffic-alert-grid" in shell_source
    assert "traffic-alert-card-congestion" in shell_source
    assert "traffic-alert-card-hazard" in shell_source
    assert "traffic-road-state-pane" in shell_source
    assert "traffic-road-card-grid" in shell_source
    assert "traffic-road-card-spotlight" in shell_source
    assert "traffic-reservation-grid" in shell_source
    assert "traffic-reservation-card-spotlight" in shell_source
    assert "traffic-hazard-focus" in shell_source
    assert "traffic-context-strip" in shell_source
    assert "analyze-pane" in shell_source
    assert "analyze-ai-feedback" in shell_source
    assert "workspace-tabs" in shell_source
    assert "workspace-tab-active" in shell_source
    assert "shell-editor-focused" in shell_source
    assert "editor-mode-banner" in shell_source
    assert "editor-status-grid" in shell_source
    assert "editor-detail-grid" in shell_source
    assert "bundle-status-strip" in shell_source
    assert "state-callout" in shell_source
    assert "fleet-control-grid" in shell_source
    assert "fleet-summary-card" in shell_source
    assert "fleet-batch-card" in shell_source
    assert "fleet-admin-card" in shell_source
    assert "fleet-inspection-card" in shell_source
    assert "fleet-vehicle-pill" in shell_source
    assert "fleet-inspection-spotlight" in shell_source
    assert "fleet-inspection-grid" in shell_source
    assert "fleet-empty-state" in shell_source
    assert "scene-road-heatmap" in shell_source
    assert "scene-route-endpoint" in shell_source
    assert "scene-destination-threshold" in shell_source
    assert "toSmoothPathString" in shell_source
    assert "vehiclePresentationBadge" in shell_source
    assert "vehicle-selection-ring" in shell_source
    assert "vehicle-label-text" in shell_source
    assert "traffic-summary-chip" in shell_source
    assert "scene-legend" in shell_source
    assert "scene-overlay-shell" in shell_source
    assert "scene-overlay-primary" in shell_source
    assert "scene-overlay-secondary" in shell_source
    assert "scene-button-primary" in shell_source
    assert "overview-card-minimap" in shell_source
    assert "minimap-card-head" in shell_source
    assert "minimap-context-strip" in shell_source
    assert "minimap-orientation-pill" in shell_source
    assert "minimap-caption" in shell_source
    assert "minimap-hazard" in shell_source
    assert "minimap-vehicle-halo" in shell_source
    assert "minimap-viewport-shadow" in shell_source
    assert "route-planning-grid" in shell_source
    assert "route-preview-summary" in shell_source
    assert "selectVehicle" in shell_source
    assert "selectRoad" in shell_source
    assert "selectArea" in shell_source
    assert "selectQueue" in shell_source
    assert "selectHazard" in shell_source
    assert "scene-edit-handle" in shell_source


def test_serious_ui_shell_styles_define_final_multi_panel_layout() -> None:
    css_source = (
        REPO_ROOT / "frontend" / "serious_ui" / "src" / "app-shell.css"
    ).read_text(encoding="utf-8")

    assert ".session-bar" in css_source
    assert ".bundle-status-strip" in css_source
    assert ".workspace-tabs" in css_source
    assert ".workspace-tab" in css_source
    assert ".workspace-tab-active" in css_source
    assert ".workspace" in css_source
    assert ".shell-tab-operate .sidebar" in css_source
    assert ".shell-tab-traffic .workspace" in css_source
    assert ".shell-tab-fleet .workspace" in css_source
    assert ".shell-tab-fleet .fleet-pane" in css_source
    assert ".shell-tab-editor .workspace" in css_source
    assert ".shell-tab-analyze .workspace" in css_source
    assert ".stage-grid" in css_source
    assert ".timeline-region" in css_source
    assert ".overview-panel" in css_source
    assert ".shell-editor-focused .masthead" in css_source
    assert ".state-callout" in css_source
    assert ".state-callout-loading" in css_source
    assert ".state-callout-error" in css_source
    assert ".workspace-tab-editor" in css_source
    assert ".shell-tab-editor .workspace-tabs" in css_source
    assert ".shell-tab-editor .editor-pane" in css_source
    assert ".editor-mode-banner" in css_source
    assert ".editor-status-grid" in css_source
    assert ".editor-detail-grid" in css_source
    assert ".editor-validation-item" in css_source
    assert ".editor-draft-item" in css_source
    assert ".scene-toolbar" in css_source
    assert ".layer-toolbar" in css_source
    assert ".scene-overlay-shell" in css_source
    assert ".scene-overlay-primary" in css_source
    assert ".scene-overlay-secondary" in css_source
    assert ".minimap" in css_source
    assert ".overview-card-minimap" in css_source
    assert ".minimap-card-head" in css_source
    assert ".minimap-context-strip" in css_source
    assert ".minimap-orientation-pill" in css_source
    assert ".minimap-caption" in css_source
    assert ".minimap-hazard" in css_source
    assert ".minimap-vehicle-core" in css_source
    assert ".minimap-vehicle-halo" in css_source
    assert ".minimap-viewport-shadow" in css_source
    assert ".hover-card" in css_source
    assert ".shell-accent" in css_source
    assert ".scene-rim" in css_source
    assert ".scene-legend" in css_source
    assert ".action-row" in css_source
    assert ".fleet-control-grid" in css_source
    assert ".fleet-summary-card" in css_source
    assert ".fleet-batch-card" in css_source
    assert ".fleet-admin-card" in css_source
    assert ".fleet-inspection-card" in css_source
    assert ".fleet-summary-grid" in css_source
    assert ".fleet-state-pill" in css_source
    assert ".fleet-vehicle-pill" in css_source
    assert ".fleet-admin-grid" in css_source
    assert ".fleet-admin-group" in css_source
    assert ".fleet-command-grid-vehicle" in css_source
    assert ".fleet-command-grid-job" in css_source
    assert ".fleet-command-grid-hazard" in css_source
    assert ".fleet-inspection-spotlight" in css_source
    assert ".fleet-inspection-grid" in css_source
    assert ".fleet-inspection-panel" in css_source
    assert ".fleet-inspection-list" in css_source
    assert ".fleet-empty-state" in css_source
    assert ".scene-lane" in css_source
    assert ".scene-turn-connector" in css_source
    assert ".scene-stop-line" in css_source
    assert ".scene-merge-zone" in css_source
    assert ".scene-road-heatmap" in css_source
    assert ".traffic-summary-chip" in css_source
    assert ".traffic-pane" in css_source
    assert ".traffic-monitor-board" in css_source
    assert ".traffic-alert-grid" in css_source
    assert ".traffic-alert-card-congestion" in css_source
    assert ".traffic-alert-card-hazard" in css_source
    assert ".traffic-road-state-pane" in css_source
    assert ".traffic-road-card-grid" in css_source
    assert ".traffic-road-card-spotlight" in css_source
    assert ".traffic-reservation-grid" in css_source
    assert ".traffic-reservation-card-spotlight" in css_source
    assert ".traffic-hazard-focus" in css_source
    assert ".traffic-context-strip" in css_source
    assert ".analyze-review-stack" in css_source
    assert ".analyze-review-section-urgent" in css_source
    assert ".analysis-chip-alert" in css_source
    assert ".review-card" in css_source
    assert ".review-card-urgent" in css_source
    assert ".review-metric-grid" in css_source
    assert ".review-command-list" in css_source
    assert ".review-explanation-card" in css_source
    assert ".vehicle-body-haul" in css_source
    assert ".vehicle-body-forklift" in css_source
    assert ".vehicle-body-car" in css_source
    assert ".vehicle-body-generic" in css_source
    assert ".vehicle-wheel" in css_source
    assert ".vehicle-selection-ring" in css_source
    assert ".vehicle-motion-trail" in css_source
    assert ".vehicle-label-bg" in css_source
    assert ".vehicle-label-text" in css_source
    assert ".vehicle-label-secondary" in css_source
    assert ".scene-edit-handle" in css_source
    assert ".scene-area.selected" in css_source
    assert ".scene-road.selected" in css_source
    assert ".scene-reservation.selected" in css_source
    assert ".scene-route-preview.selected" in css_source
    assert ".scene-route-endpoint" in css_source
    assert ".scene-destination" in css_source
    assert ".scene-queue-overlay.preview" in css_source
    assert ".minimap-destination" in css_source
    assert ".selection-strip" in css_source
    assert ".selection-pill" in css_source
    assert ".scene-hazard.selected" in css_source
    assert ".scene-vehicle.moving" in css_source
    assert ".scene-vehicle.route-following" in css_source
    assert ".shell-tab-editor .scene-edit-handle" in css_source
    assert ".operate-pane" in css_source
    assert ".editor-pane" in css_source
    assert ".fleet-pane" in css_source
    assert ".analyze-pane" in css_source
    assert ".operate-session-controls" in css_source
    assert ".scene-button-primary" in css_source
    assert ".route-planning-grid" in css_source
    assert ".route-primary-actions" in css_source
    assert ".route-preview-summary" in css_source
    assert ".traffic-monitor-board" in css_source
    assert ".traffic-alert-grid" in css_source
    assert ".traffic-road-card-grid" in css_source
    assert ".traffic-reservation-grid" in css_source
    assert ".traffic-context-strip" in css_source
    assert ".analyze-ai-feedback" in css_source
    assert "@keyframes traffic-flow" in css_source
    assert "@media (max-width: 980px)" in css_source
