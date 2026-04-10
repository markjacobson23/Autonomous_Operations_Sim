import type { Dispatch, MouseEvent, RefObject, SetStateAction } from "react";

import { SceneViewport } from "../SceneViewport";
import { PanelHeader } from "../shared/PanelHeader";
import { SectionCard } from "../shared/SectionCard";
import {
  describeSelectedTarget,
  findVehicleById,
  formatMeters,
  formatMaybeNumber,
  formatSeconds,
  sampleDisplayedVehicles,
  sampleTrafficSnapshot,
  trafficRoadPressureScore,
  type DisplayedVehicle,
} from "../../viewModel";
import type {
  BootstrapSummary,
  BundlePayload,
  HoverTarget,
  LayerState,
  LiveCommandDraft,
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
  onControlLiveSession: (action: "play" | "pause" | "step") => void;
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
  onMinimapClick,
  onSceneMouseMove,
  onSceneMouseUp,
  onSceneMouseLeave,
  onBeginNodeDrag,
  onBeginRoadPointDrag,
  onBeginAreaPointDrag,
  onControlLiveSession,
  onPreviewRouteFromDraft,
  onAssignDestinationFromDraft,
  onRepositionVehicleFromDraft,
}: OperateTabProps): JSX.Element {
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + (roadState.queued_vehicle_ids?.length ?? 0),
    0,
  );
  const congestedRoadCount = trafficRoadStates.filter(
    (roadState) => (roadState.congestion_intensity ?? 0) > 0.2,
  ).length;
  const minDisplayedSpacing = displayedVehicles.length > 1 ? "computed" : "pending";
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle"
      ? selectedTarget.vehicleId
      : selectedVehicleIds[0] ?? bundle?.command_center?.vehicle_inspections?.[0]?.vehicle_id ?? null;
  const selectedVehicle = findVehicleById(bundle, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? (bundle?.command_center?.vehicle_inspections ?? []).find(
        (inspection) => inspection.vehicle_id === selectedVehicleId,
      ) ?? null
    : null;
  const routePreviews = bundle?.command_center?.route_previews ?? [];
  const selectedRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === selectedVehicleId) ??
    routePreviews[0] ??
    null;
  const operateSelectedTargetSummary = describeSelectedTarget(selectedTarget, selectedVehicleId);
  const operateSelectedVehicleSummary =
    selectedVehicle !== null
      ? `${selectedVehicle.display_name ?? selectedVehicle.role_label ?? "Vehicle"} · ${
          selectedInspection?.operational_state ??
          selectedVehicle.operational_state ??
          "state unknown"
        }`
      : selectedVehicleIds.length > 0
        ? `Fleet selection active · ${selectedVehicleIds.length} vehicle(s)`
        : "No vehicle selected yet";
  const operateSelectedContextSummary =
    selectedInspection !== null
      ? `Node ${formatMaybeNumber(selectedInspection.current_node_id ?? null)} · ETA ${formatSeconds(selectedInspection.eta_s ?? null)} · ${selectedInspection.current_job_id ?? "no job"}`
      : "Select a vehicle on the map or from the roster to open inspection details.";
  const operateRoutePreviewSummary =
    selectedRoutePreview !== null
      ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id ?? null)} · Node ${formatMaybeNumber(selectedRoutePreview.destination_node_id ?? null)} · ${
          selectedRoutePreview.is_actionable ? "actionable" : "pending"
        }`
      : "Waiting for route preview";
  const operateRoutePreviewDetail =
    selectedRoutePreview !== null
      ? `${selectedRoutePreview.reason ?? "No reason provided"}${
          selectedRoutePreview.total_distance !== undefined
            ? ` · ${formatMeters(selectedRoutePreview.total_distance)}`
            : ""
        }`
      : "Choose a vehicle and destination, then preview the route to populate node, edge, and distance details.";
  const operatePrimaryActionLabel = selectedRoutePreview?.is_actionable ? "Assign Destination" : "Preview Route";
  const operatePrimaryActionDetail = selectedRoutePreview
    ? selectedRoutePreview.is_actionable
      ? "The preview is actionable. Assign the destination to keep the route attached to the selected vehicle."
      : "Preview the route first to verify the selected vehicle and destination before assigning it."
    : "Pick a vehicle on the map or from the roster, then preview the route before assigning it.";
  const operateSessionStateSummary = `Mode ${sessionControl?.play_state ?? "paused"} · step ${formatSeconds(sessionControl?.step_seconds ?? null)} · ${
    sessionControl?.session_control_endpoint ?? "unbound"
  }`;

  const selectedFleetPrimaryInspection = selectedInspection;
  const selectedFleetPrimaryVehicle = selectedVehicle;
  const selectedFleetPrimaryVehicleId = selectedVehicleId;
  const selectedFleetRoutePreview = selectedRoutePreview;
  const selectedFleetRouteSummary = selectedFleetRoutePreview
    ? `Node ${formatMaybeNumber(selectedFleetRoutePreview.destination_node_id ?? null)}${
        selectedFleetRoutePreview.total_distance !== undefined
          ? ` · ${formatMeters(selectedFleetRoutePreview.total_distance)}`
          : ""
      }`
    : "Waiting for route preview";
  const selectedFleetRouteDetail = selectedFleetRoutePreview
    ? `${selectedFleetRoutePreview.is_actionable ? "Actionable" : "Pending"}${
        selectedFleetRoutePreview.reason ? ` · ${selectedFleetRoutePreview.reason}` : ""
      }`
    : selectedFleetPrimaryInspection?.route_ahead_node_ids?.length
      ? `Inspection sees ${selectedFleetPrimaryInspection.route_ahead_node_ids.length} upcoming node(s)`
      : "Select a vehicle first to surface route and inspection context.";

  return (
    <section className="main-column operate-pane">
      <SceneViewport
        bundle={bundle}
        motionClockS={motionClockS}
        viewport={viewport}
        layers={layers}
        selectedTarget={selectedTarget}
        selectedVehicleIds={selectedVehicleIds}
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
      />

      <SectionCard
        eyebrow="Operate Region"
        title="Session Status"
        titleId="session-control-title"
        lede="Live session controls stay grouped so play-state changes remain easy to scan."
        className="panel info-panel operate-session-controls"
        meta={<span className="status-pill secondary">{operateSessionStateSummary}</span>}
      >
        <div className="section-stack">
          <div className="subsection">
            <div className="action-row">
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
            <div className="selection-strip operate-session-strip">
              <span className="selection-pill">Mode: {sessionControl?.play_state ?? "paused"}</span>
              <span className="selection-pill">
                Step: {formatSeconds(sessionControl?.step_seconds ?? null)}
              </span>
              <span className="selection-pill">
                Channel: {sessionControl?.session_control_endpoint ?? "unbound"}
              </span>
            </div>
            <p className="status-copy">{liveCommandMessage}</p>
          </div>
        </div>
      </SectionCard>

      <section className="timeline-region panel" aria-labelledby="timeline-title">
        <PanelHeader
          eyebrow="Timeline Region"
          title="Playback and Session Timeline"
          titleId="timeline-title"
          lede="Playback, trace, and command surfaces stay visually docked even when the timeline is only a placeholder."
          meta={<span className="status-pill secondary">Docked placeholder</span>}
        />
        <div className="timeline-body">
          <div className="timeline-track">
            <div className="timeline-fill" />
          </div>
          <div className="timeline-metrics">
            <div className="timeline-card">
              <span className="metric-label">Completed Jobs</span>
              <strong>{formatMaybeNumber(bootstrap.summary?.completed_job_count ?? null)}</strong>
            </div>
            <div className="timeline-card">
              <span className="metric-label">Completed Tasks</span>
              <strong>{formatMaybeNumber(bootstrap.summary?.completed_task_count ?? null)}</strong>
            </div>
            <div className="timeline-card">
              <span className="metric-label">Recent Commands</span>
              <strong>{formatMaybeNumber(bootstrap.recentCommandCount)}</strong>
            </div>
            <div className="timeline-card">
              <span className="metric-label">Preview Routes</span>
              <strong>{formatMaybeNumber(bootstrap.routePreviewCount)}</strong>
            </div>
          </div>
        </div>
      </section>

      <aside className="sidebar">
        <section className="panel info-panel operate-route-planning" aria-label="route-planning">
          <PanelHeader
            eyebrow="Route Planning"
            title="Primary Operator Workflow"
            lede="Select a vehicle in the scene, confirm the route preview, then use the primary action to commit or refine the destination without leaving the map."
            className="compact"
            meta={
              <div className="status-stack">
                <span className="status-pill secondary">Fleet selection: {selectedVehicleIds.length} vehicle(s)</span>
                <span className="status-pill secondary">
                  Route preview:{" "}
                  {selectedRoutePreview?.vehicle_id !== undefined
                    ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id)}`
                    : "waiting for preview"}
                </span>
              </div>
            }
          />
          <div className="selection-strip">
            <span className="selection-pill">
              Destination node:{" "}
              {selectedRoutePreview?.destination_node_id !== undefined
                ? formatMaybeNumber(selectedRoutePreview.destination_node_id)
                : "not set yet"}
            </span>
            <span className="selection-pill">Current target: {operateSelectedTargetSummary}</span>
          </div>
          <p className="operate-route-hint">
            Select a vehicle in the scene, confirm the route preview, then use the primary action to
            commit or refine the destination without leaving the map.
          </p>
          <div className="operate-context-grid">
            <section className="operate-context-card">
              <p className="operate-card-label">Selected Context</p>
              <strong>{operateSelectedVehicleSummary}</strong>
              <p>{operateSelectedContextSummary}</p>
              <ul className="mini-list">
                <li>Current target: {operateSelectedTargetSummary}</li>
                <li>
                  Selection source:{" "}
                  {selectedVehicleIds.length > 1 ? `${selectedVehicleIds.length} vehicles` : "single vehicle focus"}
                </li>
              </ul>
            </section>
            <div className="route-preview-summary operate-context-card">
              <div className="preview-badge">
                <span className="preview-label">Route Preview</span>
                <strong>{operateRoutePreviewSummary}</strong>
              </div>
              <p className="operate-route-preview-detail">{operateRoutePreviewDetail}</p>
              <ul className="mini-list">
                <li>Actionable: {selectedRoutePreview?.is_actionable ? "yes" : "no"}</li>
                <li>Reason: {selectedRoutePreview?.reason ?? "none"}</li>
                <li>Distance: {formatMeters(selectedRoutePreview?.total_distance ?? null)}</li>
                <li>Edges: {(selectedRoutePreview?.edge_ids ?? []).join(", ") || "none"}</li>
                <li>Nodes: {(selectedRoutePreview?.node_ids ?? []).join(" → ") || "none"}</li>
              </ul>
            </div>
          </div>
          <div className="operate-workflow-actions">
            <div className="operate-next-action">
              <span className="operate-card-label">Primary next action</span>
              <strong>{operatePrimaryActionLabel}</strong>
              <p>{operatePrimaryActionDetail}</p>
            </div>
            <div className="route-planning-grid">
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
                    routePreviews[0]?.destination_node_id !== undefined
                      ? String(routePreviews[0].destination_node_id)
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
              <label className="form-field">
                <span>Step Seconds</span>
                <input
                  type="number"
                  step="0.1"
                  value={liveCommandDraft.stepSeconds}
                  onChange={(event) =>
                    setLiveCommandDraft((current) => ({
                      ...current,
                      stepSeconds: event.target.value,
                    }))
                  }
                  placeholder={String(sessionControl?.step_seconds ?? 0.5)}
                />
              </label>
            </div>
            <div className="route-primary-actions action-row">
              <button
                className="scene-button scene-button-primary"
                type="button"
                onClick={onPreviewRouteFromDraft}
                disabled={!sessionControl?.route_preview_endpoint}
              >
                Preview Route
              </button>
              <button
                className="scene-button scene-button-primary"
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
        </section>
      </aside>
    </section>
  );
}
