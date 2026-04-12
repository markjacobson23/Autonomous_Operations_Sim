import type { Dispatch, MouseEvent, RefObject, SetStateAction } from "react";

import { SceneViewport } from "../SceneViewport";
import { PanelHeader } from "../shared/PanelHeader";
import { SectionCard } from "../shared/SectionCard";
import {
  describeRoutePreviewDestination,
  describeSelectedTarget,
  describeVehicleName,
  findVehicleById,
  formatMaybeNumber,
  formatSeconds,
} from "../../viewModel";
import type {
  BootstrapSummary,
  BundlePayload,
  HoverTarget,
  LayerState,
  LiveCommandDraft,
  RoutePlanDestination,
  RoutePlanEntry,
  RoutePreviewPayload,
  SceneViewMode,
  SelectedTarget,
  ViewportState,
} from "../../types";

type OperateTabProps = {
  bundle: BundlePayload | null;
  bootstrap: BootstrapSummary;
  motionClockS: number;
  viewport: ViewportState;
  boundsLabel: string;
  layers: LayerState;
  selectedTarget: SelectedTarget | null;
  selectedVehicleIds: number[];
  selectedRouteDestination: RoutePlanDestination | null;
  routePlans: RoutePlanEntry[];
  activeRoutePlanId: string | null;
  activeRoutePreview: RoutePreviewPayload | null;
  isRoutePreviewing: boolean;
  liveCommandDraft: LiveCommandDraft;
  setLiveCommandDraft: Dispatch<SetStateAction<LiveCommandDraft>>;
  liveCommandMessage: string;
  sessionControl: BundlePayload["session_control"] | null;
  editorEnabled: boolean;
  hoverTarget: HoverTarget | null;
  setHoverTarget: Dispatch<SetStateAction<HoverTarget | null>>;
  sceneRef: RefObject<SVGSVGElement | null>;
  minimapRef: RefObject<SVGSVGElement | null>;
  onPan: (deltaX: number, deltaY: number) => void;
  onZoom: (factor: number) => void;
  onFit: () => void;
  onFocusSelected: () => void;
  onToggleLayer: (layer: keyof LayerState) => void;
  onSelectVehicle: (vehicleId: number | undefined, options?: { additive?: boolean }) => void;
  onSelectRoad: (roadId: string | undefined) => void;
  onSelectArea: (areaId: string | undefined) => void;
  onSelectQueue: (roadId: string | undefined) => void;
  onSelectHazard: (edgeId: number | undefined) => void;
  onSelectRouteDestination: (destination: RoutePlanDestination) => void;
  onMinimapClick: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseMove: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseUp: () => void;
  onSceneMouseLeave: () => void;
  onBeginNodeDrag: (event: MouseEvent<SVGCircleElement>, node: { node_id?: number; position?: [number, number, number] }) => void;
  onBeginRoadPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    roadId: string,
    pointIndex: number,
    z: number,
  ) => void;
  onBeginAreaPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    areaId: string,
    pointIndex: number,
    z: number,
  ) => void;
  sceneViewMode: SceneViewMode;
  onSceneViewModeChange: (mode: SceneViewMode) => void;
  onControlLiveSession: (action: "play" | "pause" | "step") => void;
  onCreateRoutePlan: () => void;
  onActivateRoutePlan: (planId: string) => void;
  onCommitRoutePlan: (planId: string) => void;
  onPreviewRouteFromDraft: () => void;
  onAssignDestinationFromDraft: () => void;
  onRepositionVehicleFromDraft: () => void;
};

export function OperateTab({
  bundle,
  bootstrap,
  motionClockS,
  viewport,
  boundsLabel,
  layers,
  selectedTarget,
  selectedVehicleIds,
  selectedRouteDestination,
  routePlans,
  activeRoutePlanId,
  activeRoutePreview,
  isRoutePreviewing,
  liveCommandDraft,
  setLiveCommandDraft,
  liveCommandMessage,
  sessionControl,
  editorEnabled,
  hoverTarget,
  setHoverTarget,
  sceneRef,
  minimapRef,
  onPan,
  onZoom,
  onFit,
  onFocusSelected,
  onToggleLayer,
  onSelectVehicle,
  onSelectRoad,
  onSelectArea,
  onSelectQueue,
  onSelectHazard,
  onSelectRouteDestination,
  onMinimapClick,
  onSceneMouseMove,
  onSceneMouseUp,
  onSceneMouseLeave,
  onBeginNodeDrag,
  onBeginRoadPointDrag,
  onBeginAreaPointDrag,
  sceneViewMode,
  onSceneViewModeChange,
  onControlLiveSession,
  onCreateRoutePlan,
  onActivateRoutePlan,
  onCommitRoutePlan,
  onPreviewRouteFromDraft,
  onAssignDestinationFromDraft,
  onRepositionVehicleFromDraft,
}: OperateTabProps): JSX.Element {
  const completedJobCount = formatMaybeNumber(bootstrap.summary?.completed_job_count ?? null);
  const completedTaskCount = formatMaybeNumber(bootstrap.summary?.completed_task_count ?? null);
  const traceEventCount = formatMaybeNumber(bootstrap.summary?.trace_event_count ?? null);
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle"
      ? selectedTarget.vehicleId
      : selectedVehicleIds[0] ?? bundle?.command_center?.vehicle_inspections?.[0]?.vehicle_id ?? null;
  const selectedPlanningVehicle = findVehicleById(bundle, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? (bundle?.command_center?.vehicle_inspections ?? []).find(
        (inspection) => inspection.vehicle_id === selectedVehicleId,
      ) ?? null
    : null;
  const activeRoutePlan =
    routePlans.find((entry) => entry.id === activeRoutePlanId) ?? routePlans[0] ?? null;
  const selectedRoutePreview =
    activeRoutePreview ??
    activeRoutePlan?.preview ??
    routePlans.find((entry) => entry.vehicleId === selectedVehicleId)?.preview ??
    bundle?.command_center?.route_previews?.find((preview) => preview.vehicle_id === selectedVehicleId) ??
    null;
  const selectedVehicleTitle = selectedPlanningVehicle
    ? describeVehicleName(selectedPlanningVehicle)
    : selectedVehicleId !== null
      ? `Vehicle ${selectedVehicleId}`
      : "No vehicle selected";
  const selectedVehicleSummary =
    selectedVehicleId !== null
      ? `${selectedVehicleTitle} · ${selectedInspection?.operational_state ?? "staged"}`
      : "Select a vehicle on the map to start planning.";
  const destinationSummary =
    selectedRouteDestination !== null
      ? `${selectedRouteDestination.label} · node ${selectedRouteDestination.nodeId}`
      : "Select a road or area on the map to choose a destination.";
  const routePreviewSummary =
    selectedRoutePreview !== null
      ? describeRoutePreviewDestination(bundle, selectedRoutePreview, { includeNodeId: true })
      : "Preview appears after a plan is created.";
  const routePreviewDetail =
    selectedRoutePreview !== null
      ? `${selectedRoutePreview.is_actionable ? "Actionable" : "Pending"}${
          selectedRoutePreview.reason ? ` · ${selectedRoutePreview.reason}` : ""
        }`
      : "Create a plan to preview the route on the map.";
  const operateSessionStateSummary = `Mode ${sessionControl?.play_state ?? "paused"} · step ${formatSeconds(sessionControl?.step_seconds ?? null)} · ${
    sessionControl?.session_control_endpoint ?? "unbound"
  }`;
  const operateSelectionSummary =
    selectedTarget !== null
      ? describeSelectedTarget(selectedTarget, selectedVehicleId)
      : selectedVehicleIds.length > 0
        ? `Fleet selection active · ${selectedVehicleIds.length} vehicle(s)`
        : "No selection yet";
  const canCreatePlan = selectedVehicleId !== null && selectedRouteDestination !== null;

  return (
    <section className="main-column operate-pane">
      <SceneViewport
        bundle={bundle}
        motionClockS={motionClockS}
        viewport={viewport}
        layers={layers}
        selectedTarget={selectedTarget}
        selectedVehicleIds={selectedVehicleIds}
        selectedRouteDestination={selectedRouteDestination}
        onSelectRouteDestination={onSelectRouteDestination}
        activeRoutePreview={selectedRoutePreview}
        editorEnabled={editorEnabled}
        hoverTarget={hoverTarget}
        setHoverTarget={setHoverTarget}
        sceneRef={sceneRef}
        minimapRef={minimapRef}
        onPan={onPan}
        onZoom={onZoom}
        onFit={onFit}
        onFocusSelected={onFocusSelected}
        onToggleLayer={onToggleLayer}
        onSelectVehicle={onSelectVehicle}
        onSelectRoad={onSelectRoad}
        onSelectArea={onSelectArea}
        onSelectQueue={onSelectQueue}
        onSelectHazard={onSelectHazard}
        onMinimapClick={onMinimapClick}
        onSceneMouseMove={onSceneMouseMove}
        onSceneMouseUp={onSceneMouseUp}
        onSceneMouseLeave={onSceneMouseLeave}
        onBeginNodeDrag={onBeginNodeDrag}
        onBeginRoadPointDrag={onBeginRoadPointDrag}
        onBeginAreaPointDrag={onBeginAreaPointDrag}
        sceneViewMode={sceneViewMode}
        onSceneViewModeChange={onSceneViewModeChange}
      />

      <div className="operate-dock-grid">
        <SectionCard
          eyebrow="Operate Dock"
          title="Session Controls"
          titleId="session-control-title"
          lede="Playback stays close at hand while the map remains the focus."
          className="panel info-panel operate-session-controls"
          meta={<span className="status-pill secondary">{operateSessionStateSummary}</span>}
        >
          <div className="operate-dock-actions">
            <div className="action-row operate-session-actions">
              <button
                className="scene-button scene-button-primary"
                type="button"
                onClick={() => onControlLiveSession("play")}
                disabled={!sessionControl?.session_control_endpoint}
              >
                Play
              </button>
              <button
                className="scene-button"
                type="button"
                onClick={() => onControlLiveSession("pause")}
                disabled={!sessionControl?.session_control_endpoint}
              >
                Pause
              </button>
              <button
                className="scene-button"
                type="button"
                onClick={() => onControlLiveSession("step")}
                disabled={!sessionControl?.session_control_endpoint}
              >
                Single-Step
              </button>
            </div>
            <div className="selection-strip operate-status-strip">
              <span className="selection-pill">Mode: {sessionControl?.play_state ?? "paused"}</span>
              <span className="selection-pill">
                Step: {formatSeconds(sessionControl?.step_seconds ?? null)}
              </span>
              <span className="selection-pill">
                Channel: {sessionControl?.session_control_endpoint ?? "unbound"}
              </span>
            </div>
            <div className="selection-strip operate-timeline-strip">
              <span className="selection-pill">Jobs: {completedJobCount}</span>
              <span className="selection-pill">Tasks: {completedTaskCount}</span>
              <span className="selection-pill">Trace: {traceEventCount}</span>
              <span className="selection-pill">Routes: {formatMaybeNumber(bootstrap.routePreviewCount)}</span>
            </div>
            <p className="status-copy">{liveCommandMessage}</p>
          </div>
        </SectionCard>

        <section className="panel info-panel operate-route-planning" aria-label="route-planning">
          <PanelHeader
            eyebrow="Operate Dock"
            title="Plan Inspector"
            lede="Select a vehicle on the map, choose a road or area destination, and turn that pairing into a plan entry."
            className="compact"
            meta={
              <div className="status-stack">
                <span className="status-pill secondary">Fleet: {selectedVehicleIds.length} vehicle(s)</span>
                <span className="status-pill secondary">Plans: {routePlans.length}</span>
                <span className="status-pill secondary">Map span: {boundsLabel}</span>
              </div>
            }
          />
          <div className="operate-context-grid operate-plan-inspector-grid">
            <section className="operate-context-card operate-context-card-compact">
              <p className="operate-card-label">Vehicle</p>
              <strong>{selectedVehicleTitle}</strong>
              <p>{selectedVehicleSummary}</p>
              <p className="operate-card-note">
                Primary target: {operateSelectionSummary}
              </p>
            </section>
            <section className="operate-context-card operate-context-card-compact">
              <p className="operate-card-label">Destination</p>
              <strong>{selectedRouteDestination?.label ?? "No place selected"}</strong>
              <p>{destinationSummary}</p>
              <p className="operate-card-note">
                Selecting a road or area on the map populates the plan draft destination.
              </p>
            </section>
            <section className="operate-context-card operate-context-card-compact">
              <p className="operate-card-label">Preview</p>
              <strong>{routePreviewSummary}</strong>
              <p>{routePreviewDetail}</p>
              <p className="operate-card-note">
                Preview source: {activeRoutePlan?.id ? `plan ${activeRoutePlan.id}` : "live bundle"}
              </p>
            </section>
          </div>
          <div className="route-primary-actions action-row">
            <button
              className="scene-button scene-button-primary"
              type="button"
              onClick={onCreateRoutePlan}
              disabled={!canCreatePlan || isRoutePreviewing}
            >
              Create Plan
            </button>
            <span className="selection-pill">
              {canCreatePlan
                ? "Ready to add a plan entry"
                : "Choose a vehicle and destination from the map"}
            </span>
          </div>
        </section>

        <section className="panel info-panel operate-plan-stack" aria-label="plan-stack">
          <PanelHeader
            eyebrow="Operate Dock"
            title="Plan Stack"
            lede="Each plan stays visible, can be previewed again by clicking it, and commits through the existing command path."
            className="compact"
            meta={
              <div className="status-stack">
                <span className="status-pill secondary">Preview: {routePreviewSummary}</span>
                <span className="status-pill secondary">Entries: {routePlans.length}</span>
              </div>
            }
          />
          {routePlans.length > 0 ? (
            <div className="operate-plan-list">
              {routePlans.map((plan, index) => {
                const isActive = plan.id === activeRoutePlanId;
                const planPreviewSummary =
                  plan.preview !== null
                    ? describeRoutePreviewDestination(bundle, plan.preview, { includeNodeId: true })
                    : `${plan.destination.label} · node ${plan.destination.nodeId}`;
                const planStateLabel = plan.committed
                  ? "Committed"
                  : plan.preview?.is_actionable
                    ? "Ready"
                    : "Pending";
                const planDetail = plan.preview?.reason ?? "Preview requested from the Python session.";
                return (
                  <article
                    key={plan.id}
                    className={`operate-plan-card ${isActive ? "selected" : ""} ${plan.committed ? "committed" : ""}`}
                  >
                    <button
                      className="operate-plan-card-main"
                      type="button"
                      onClick={() => onActivateRoutePlan(plan.id)}
                      aria-pressed={isActive}
                    >
                      <div className="operate-plan-card-head">
                        <span className="operate-plan-card-index">Plan {index + 1}</span>
                        <span className="operate-plan-card-state">{planStateLabel}</span>
                      </div>
                      <strong>
                        {describeVehicleName(findVehicleById(bundle, plan.vehicleId))} → {plan.destination.label}
                      </strong>
                      <p>{planPreviewSummary}</p>
                      <p className="operate-plan-card-detail">{planDetail}</p>
                    </button>
                    <div className="operate-plan-card-actions">
                      <span className="selection-pill">
                        {plan.committed ? "Committed on live bundle" : isActive ? "Previewing on map" : "Click to preview"}
                      </span>
                      <button
                        className="scene-button scene-button-primary"
                        type="button"
                        onClick={() => onCommitRoutePlan(plan.id)}
                        disabled={plan.preview === null || plan.committed || !sessionControl?.command_endpoint}
                      >
                        Commit
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="operate-empty-plan-list">
              <strong>No plans yet.</strong>
              <p>
                Select a vehicle and a destination place on the map, then create the first plan
                entry here.
              </p>
            </div>
          )}
        </section>

        <details className="operate-advanced">
          <summary>Advanced / debug commands</summary>
          <div className="operate-advanced-body">
            <p className="operate-route-hint">
              Raw numeric controls stay available here for debugging, but the primary workflow is
              now map-first.
            </p>
            <div className="operate-command-grid">
              <label className="form-field">
                <span>Vehicle ID</span>
                <input
                  type="number"
                  value={liveCommandDraft.vehicleId}
                  onChange={(event) =>
                    setLiveCommandDraft((current) => ({
                      ...current,
                      vehicleId: event.target.value,
                    }))
                  }
                  placeholder={selectedVehicleId !== null ? String(selectedVehicleId) : "77"}
                />
              </label>
              <label className="form-field">
                <span>Destination Node</span>
                <input
                  type="number"
                  value={liveCommandDraft.destinationNodeId}
                  onChange={(event) =>
                    setLiveCommandDraft((current) => ({
                      ...current,
                      destinationNodeId: event.target.value,
                    }))
                  }
                  placeholder={
                    selectedRoutePreview?.destination_node_id !== undefined
                      ? String(selectedRoutePreview.destination_node_id)
                      : "3"
                  }
                />
              </label>
              <label className="form-field">
                <span>Reposition Node</span>
                <input
                  type="number"
                  value={liveCommandDraft.nodeId}
                  onChange={(event) =>
                    setLiveCommandDraft((current) => ({
                      ...current,
                      nodeId: event.target.value,
                    }))
                  }
                  placeholder={
                    selectedInspection?.current_node_id !== undefined
                      ? String(selectedInspection.current_node_id)
                      : "1"
                  }
                />
              </label>
            </div>
            <div className="route-primary-actions action-row">
              <button
                className="scene-button"
                type="button"
                onClick={onPreviewRouteFromDraft}
                disabled={!sessionControl?.route_preview_endpoint}
              >
                Preview Route
              </button>
              <button
                className="scene-button"
                type="button"
                onClick={onAssignDestinationFromDraft}
                disabled={!sessionControl?.command_endpoint}
              >
                Assign Destination
              </button>
              <button
                className="scene-button"
                type="button"
                onClick={onRepositionVehicleFromDraft}
                disabled={!sessionControl?.command_endpoint}
              >
                Reposition Vehicle
              </button>
            </div>
          </div>
        </details>
      </div>
    </section>
  );
}
