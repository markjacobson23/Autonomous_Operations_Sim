from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_step_45_app_shell_source_includes_required_operator_regions() -> None:
    app_source = (
        REPO_ROOT / "frontend" / "serious_ui" / "src" / "App.tsx"
    ).read_text(encoding="utf-8")

    assert "Step 64 Task/resource realism expansion" in app_source
    assert "Operate" in app_source
    assert "Traffic" in app_source
    assert "Fleet" in app_source
    assert "Editor" in app_source
    assert "Analyze" in app_source
    assert "Primary Operator Workflow" in app_source
    assert "Compact Session Status" in app_source
    assert "Traffic Control Room" in app_source
    assert "Fleet Control" in app_source
    assert "Current Controlled Fleet" in app_source
    assert "Batch Selection" in app_source
    assert "Runtime Admin Actions" in app_source
    assert "Inspection and Support Context" in app_source
    assert "Selected Vehicle Roster" in app_source
    assert "Recent Command Trace" in app_source
    assert "Scenario Authoring" in app_source
    assert "Dedicated controls for the working scenario" in app_source
    assert "Authoring Controls" in app_source
    assert "Working Scenario" in app_source
    assert "Validation clean" in app_source
    assert "Validation blocked" in app_source
    assert "Diagnostics and AI Review" in app_source
    assert "Urgent issues" in app_source
    assert "Recommended actions" in app_source
    assert "Supporting context" in app_source
    assert "Recent command trace" in app_source
    assert "Current target" in app_source
    assert "Route Planning" in app_source
    assert "Selected Preview" in app_source
    assert "Preview Route" in app_source
    assert "Assign Destination" in app_source
    assert "Reposition Vehicle" in app_source
    assert "Select Visible" in app_source
    assert "Clear Selection" in app_source
    assert "Spawn Vehicle" in app_source
    assert "Remove Vehicle" in app_source
    assert "Inject Job" in app_source
    assert "Declare Hazard" in app_source
    assert "Clear Hazard" in app_source
    assert "Edit Scene" in app_source
    assert "Save Scenario" in app_source
    assert "Reload Scenario" in app_source
    assert "Single-Step" in app_source
    assert "Batch mode is active" in app_source
    assert "Traffic Control Room" in app_source
    assert "Traffic Control" in app_source
    assert "Congestion Overview" in app_source
    assert "Active Road Conditions" in app_source
    assert "Queue & Reservation Detail" in app_source
    assert "Blocked Edge Watch" in app_source
    assert "Suggestions" in app_source
    assert "Anomalies" in app_source
    assert "Explanations" in app_source
    assert "analysis-chip-alert" in app_source
    assert "analyze-review-section-urgent" in app_source
    assert "review-card-urgent" in app_source
    assert "review-command-item" in app_source
    assert "review-diagnostic-pill" in app_source
    assert "operate-session-controls" in app_source
    assert "operate-route-planning" in app_source
    assert "fleet-pane" in app_source
    assert "editor-pane" in app_source
    assert "traffic-pane" in app_source
    assert "traffic-monitor-board" in app_source
    assert "traffic-alert-grid" in app_source
    assert "traffic-alert-card-congestion" in app_source
    assert "traffic-alert-card-hazard" in app_source
    assert "traffic-road-state-pane" in app_source
    assert "traffic-road-card-grid" in app_source
    assert "traffic-road-card-spotlight" in app_source
    assert "traffic-reservation-grid" in app_source
    assert "traffic-reservation-card-spotlight" in app_source
    assert "traffic-hazard-focus" in app_source
    assert "traffic-context-strip" in app_source
    assert "analyze-pane" in app_source
    assert "analyze-ai-feedback" in app_source
    assert "workspace-tabs" in app_source
    assert "workspace-tab-active" in app_source
    assert "shell-editor-focused" in app_source
    assert "editor-mode-banner" in app_source
    assert "editor-status-grid" in app_source
    assert "editor-detail-grid" in app_source
    assert "fleet-control-grid" in app_source
    assert "fleet-summary-card" in app_source
    assert "fleet-batch-card" in app_source
    assert "fleet-admin-card" in app_source
    assert "fleet-inspection-card" in app_source
    assert "fleet-vehicle-pill" in app_source
    assert "fleet-inspection-spotlight" in app_source
    assert "fleet-inspection-grid" in app_source
    assert "fleet-empty-state" in app_source
    assert "scene-road-heatmap" in app_source
    assert "scene-route-endpoint" in app_source
    assert "scene-destination-threshold" in app_source
    assert "toSmoothPathString" in app_source
    assert "vehiclePresentationBadge" in app_source
    assert "vehicle-selection-ring" in app_source
    assert "vehicle-label-text" in app_source
    assert "traffic-summary-chip" in app_source
    assert "scene-legend" in app_source
    assert "scene-button-primary" in app_source
    assert "route-planning-grid" in app_source
    assert "route-preview-summary" in app_source
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
    assert ".minimap" in css_source
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
    assert ".vehicle-label-bg" in css_source
    assert ".vehicle-label-text" in css_source
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
