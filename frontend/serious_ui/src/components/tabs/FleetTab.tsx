import { PanelHeader } from "../shared/PanelHeader";
import {
  describeRecentCommand,
  formatMeters,
  formatMaybeNumber,
  formatSeconds,
  sampleDisplayedVehicles,
  type DisplayedVehicle,
} from "../../viewModel";
import type { Dispatch, SetStateAction } from "react";
import type { BundlePayload, LiveCommandDraft, SelectedTarget } from "../../types";

type FleetTabProps = {
  bundle: BundlePayload | null;
  motionClockS: number;
  selectedTarget: SelectedTarget | null;
  selectedVehicleIds: number[];
  liveCommandDraft: LiveCommandDraft;
  setLiveCommandDraft: Dispatch<SetStateAction<LiveCommandDraft>>;
  liveCommandMessage: string;
  sessionControl: BundlePayload["session_control"] | null;
  onSelectVisible: () => void;
  onClearSelection: () => void;
  onSelectVehicle: (vehicleId: number | undefined) => void;
  onSpawnVehicleFromDraft: () => void;
  onRemoveVehicleFromDraft: () => void;
  onInjectJobFromDraft: () => void;
  onDeclareTemporaryHazardFromDraft: () => void;
  onClearTemporaryHazardFromDraft: () => void;
  onBlockRoadFromDraft: () => void;
  onUnblockRoadFromDraft: () => void;
};

export function FleetTab({
  bundle,
  motionClockS,
  selectedTarget,
  selectedVehicleIds,
  liveCommandDraft,
  setLiveCommandDraft,
  liveCommandMessage,
  sessionControl,
  onSelectVisible,
  onClearSelection,
  onSelectVehicle,
  onSpawnVehicleFromDraft,
  onRemoveVehicleFromDraft,
  onInjectJobFromDraft,
  onDeclareTemporaryHazardFromDraft,
  onClearTemporaryHazardFromDraft,
  onBlockRoadFromDraft,
  onUnblockRoadFromDraft,
}: FleetTabProps): JSX.Element {
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const routePreviews = bundle?.command_center?.route_previews ?? [];
  const inspections = bundle?.command_center?.vehicle_inspections ?? [];
  const recentCommands = bundle?.command_center?.recent_commands ?? [];
  const selectedFleetVehicles = selectedVehicleIds
    .map(
      (vehicleId) =>
        displayedVehicles.find((vehicle) => vehicle.vehicle_id === vehicleId) ??
        (bundle?.snapshot?.vehicles ?? []).find((vehicle) => vehicle.vehicle_id === vehicleId),
    )
    .filter((vehicle): vehicle is DisplayedVehicle => vehicle !== null);
  const selectedFleetPrimaryVehicle = selectedFleetVehicles[0] ?? null;
  const selectedFleetPrimaryVehicleId = selectedFleetPrimaryVehicle?.vehicle_id ?? null;
  const selectedFleetPrimaryInspection =
    selectedFleetPrimaryVehicleId !== null
      ? inspections.find((inspection) => inspection.vehicle_id === selectedFleetPrimaryVehicleId) ?? null
      : null;
  const selectedFleetRoutePreview =
    selectedFleetPrimaryVehicleId !== null
      ? routePreviews.find((preview) => preview.vehicle_id === selectedFleetPrimaryVehicleId) ?? null
      : null;
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
  const selectedFleetStateCounts = selectedFleetVehicles.reduce<Record<string, number>>(
    (counts, vehicle) => {
      const operationalState = (vehicle.operational_state ?? "unknown").split("_").join(" ");
      counts[operationalState] = (counts[operationalState] ?? 0) + 1;
      return counts;
    },
    {},
  );
  const selectedFleetStateEntries = Object.entries(selectedFleetStateCounts).sort(
    (left, right) => right[1] - left[1] || left[0].localeCompare(right[0]),
  );
  const selectedFleetStateSummary =
    selectedFleetStateEntries.length > 0
      ? selectedFleetStateEntries.slice(0, 3).map(([state, count]) => `${count} ${state}`).join(" · ")
      : "No vehicles selected yet";

  return (
    <section className="panel info-panel fleet-pane" aria-labelledby="command-center-title">
      <PanelHeader
        eyebrow="Fleet Region"
        title="Fleet Control"
        titleId="command-center-title"
        lede="Fleet selection, batch actions, runtime admin controls, and inspection context live together here."
        className="compact fleet-panel-header"
        meta={
          <div className="fleet-panel-meta">
            <span className="status-pill secondary">{formatMaybeNumber(selectedVehicleIds.length)} selected</span>
            <span className="status-pill accent">
              Lead {selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}
            </span>
          </div>
        }
      />

      <div className="fleet-control-grid">
        <article className="subsection fleet-card fleet-summary-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Selected Fleet</h3>
              <p className="fleet-card-lede">
                The selected fleet stays in view so the operator can scan lead vehicle, state mix,
                and destination context before making a move.
              </p>
            </div>
            <span className="fleet-card-badge">{formatMaybeNumber(selectedVehicleIds.length)} selected</span>
          </div>
          <div className="fleet-summary-grid">
            <div className="fleet-summary-metric">
              <span>Lead vehicle</span>
              <strong>{selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}</strong>
              <p>{selectedFleetPrimaryVehicle?.display_name ?? selectedFleetPrimaryVehicle?.role_label ?? "No primary selection"}</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Selection scope</span>
              <strong>{formatMaybeNumber(displayedVehicles.length)} visible</strong>
              <p>{selectedVehicleIds.length > 1 ? `Batch-ready control is active for ${selectedVehicleIds.length} vehicles.` : "Single vehicle focus is active."}</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Operational states</span>
              <strong>{formatMaybeNumber(selectedFleetStateEntries.length)} state buckets</strong>
              <p>{selectedFleetStateSummary}</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Route context</span>
              <strong>{selectedFleetRouteSummary}</strong>
              <p>{selectedFleetRouteDetail}</p>
            </div>
          </div>
          <div className="fleet-state-strip">
            {selectedFleetStateEntries.length > 0 ? (
              selectedFleetStateEntries.slice(0, 4).map(([state, count]) => (
                <span key={state} className="fleet-state-pill">
                  {count} {state}
                </span>
              ))
            ) : (
              <span className="fleet-empty-state">
                No fleet selection is active yet. Select a vehicle or use Select Visible to populate
                the state mix.
              </span>
            )}
          </div>
          <div className="fleet-selection-strip fleet-vehicle-strip">
            {selectedFleetVehicles.length > 0 ? (
              selectedFleetVehicles.map((vehicle, index) => {
                const vehicleId = vehicle.vehicle_id ?? null;
                const vehicleRoutePreview =
                  vehicleId !== null
                    ? routePreviews.find((preview) => preview.vehicle_id === vehicleId) ?? null
                    : null;
                return (
                  <button
                    key={vehicleId ?? `fleet-vehicle-${index}`}
                    className={`fleet-vehicle-pill ${
                      vehicleId === selectedFleetPrimaryVehicleId ? "fleet-vehicle-pill-primary" : ""
                    }`}
                    type="button"
                    onClick={() => onSelectVehicle(vehicle.vehicle_id)}
                    aria-pressed={vehicleId === selectedFleetPrimaryVehicleId}
                    aria-label={`Focus vehicle ${formatMaybeNumber(vehicleId)}`}
                  >
                    <span className="fleet-vehicle-pill-id">V{formatMaybeNumber(vehicleId)}</span>
                    <span className="fleet-vehicle-pill-state">{vehicle.operational_state ?? "unknown"}</span>
                    <span className="fleet-vehicle-pill-detail">
                      {vehicle.display_name ?? vehicle.role_label ?? vehicle.vehicle_type ?? "Vehicle"}
                    </span>
                    <span className="fleet-vehicle-pill-route">
                      {vehicleRoutePreview?.destination_node_id !== undefined
                        ? `→ node ${formatMaybeNumber(vehicleRoutePreview.destination_node_id)}`
                        : vehicle.lane_id !== undefined && vehicle.lane_id !== null
                          ? `${vehicle.lane_id}`
                          : "Preview pending"}
                    </span>
                  </button>
                );
              })
            ) : (
              <div className="fleet-empty-state">
                No vehicles are selected yet. Use the scene or Select Visible to build a controlled
                fleet before applying batch actions.
              </div>
            )}
          </div>
        </article>

        <article className="subsection fleet-card fleet-batch-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Batch Actions</h3>
              <p className="fleet-card-lede">Use the viewport to shape a deliberate batch before applying batch actions.</p>
            </div>
            <span className="fleet-card-badge">Viewport batch</span>
          </div>
          <div className="fleet-batch-summary">
            <span className="fleet-batch-chip">Selected {selectedVehicleIds.length}</span>
            <span className="fleet-batch-chip">Visible {displayedVehicles.length}</span>
            <span className="fleet-batch-chip">Lead {selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}</span>
          </div>
          <div className="selection-strip fleet-selection-actions">
            <button className="scene-button scene-button-primary" type="button" onClick={onSelectVisible} disabled={displayedVehicles.length === 0}>
              Select Visible
            </button>
            <button className="scene-button" type="button" onClick={onClearSelection} disabled={selectedVehicleIds.length === 0}>
              Clear Selection
            </button>
          </div>
          <p className="status-copy">
            Batch mode activates when more than one vehicle is selected, and batch commands apply
            to every vehicle in that controlled set.
          </p>
        </article>

        <article className="subsection fleet-card fleet-admin-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Runtime Controls</h3>
              <p className="fleet-card-lede">
                Live mutations stay grouped by task so spawn, inject, and hazard changes feel
                deliberate instead of bolted on.
              </p>
            </div>
            <span className="fleet-card-badge">Live mutation</span>
          </div>
          <div className="fleet-admin-grid">
            <section className="fleet-admin-group fleet-admin-group-vehicle">
              <div className="fleet-admin-group-header">
                <div>
                  <h4>Vehicle Mutations</h4>
                  <span>Spawn or retire equipment</span>
                </div>
              </div>
              <div className="command-grid fleet-command-grid fleet-command-grid-vehicle">
                <label className="form-field">
                  <span>Spawn Node</span>
                  <input type="number" value={liveCommandDraft.nodeId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, nodeId: event.target.value }))} placeholder="1" />
                </label>
                <label className="form-field">
                  <span>Vehicle ID</span>
                  <input type="number" value={liveCommandDraft.vehicleId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, vehicleId: event.target.value }))} placeholder="77" />
                </label>
                <label className="form-field">
                  <span>Spawn Type</span>
                  <input type="text" value={liveCommandDraft.spawnVehicleType} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, spawnVehicleType: event.target.value }))} placeholder="GENERIC" />
                </label>
                <label className="form-field">
                  <span>Spawn Max Speed</span>
                  <input type="number" step="0.1" value={liveCommandDraft.spawnMaxSpeed} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, spawnMaxSpeed: event.target.value }))} placeholder="12" />
                </label>
                <label className="form-field">
                  <span>Spawn Max Payload</span>
                  <input type="number" step="0.1" value={liveCommandDraft.spawnMaxPayload} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, spawnMaxPayload: event.target.value }))} placeholder="120" />
                </label>
                <label className="form-field">
                  <span>Spawn Payload</span>
                  <input type="number" step="0.1" value={liveCommandDraft.spawnPayload} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, spawnPayload: event.target.value }))} placeholder="0" />
                </label>
                <label className="form-field">
                  <span>Spawn Velocity</span>
                  <input type="number" step="0.1" value={liveCommandDraft.spawnVelocity} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, spawnVelocity: event.target.value }))} placeholder="0" />
                </label>
              </div>
              <div className="action-row fleet-action-row">
                <button className="scene-button scene-button-primary" type="button" onClick={onSpawnVehicleFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Spawn Vehicle
                </button>
                <button className="scene-button" type="button" onClick={onRemoveVehicleFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Remove Vehicle
                </button>
              </div>
            </section>
            <section className="fleet-admin-group fleet-admin-group-job">
              <div className="fleet-admin-group-header">
                <div>
                  <h4>Job Injection</h4>
                  <span>Assign work to the live fleet</span>
                </div>
              </div>
              <div className="command-grid fleet-command-grid fleet-command-grid-job">
                <label className="form-field">
                  <span>Job ID</span>
                  <input type="text" value={liveCommandDraft.jobId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, jobId: event.target.value }))} placeholder="live-job-77" />
                </label>
                <label className="form-field">
                  <span>Job Node</span>
                  <input type="number" value={liveCommandDraft.jobTaskNodeId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, jobTaskNodeId: event.target.value }))} placeholder="1" />
                </label>
                <label className="form-field">
                  <span>Job Destination</span>
                  <input type="number" value={liveCommandDraft.jobTaskDestinationNodeId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, jobTaskDestinationNodeId: event.target.value }))} placeholder="3" />
                </label>
              </div>
              <div className="action-row fleet-action-row">
                <button className="scene-button" type="button" onClick={onInjectJobFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Inject Job
                </button>
              </div>
            </section>
            <section className="fleet-admin-group fleet-admin-group-hazard">
              <div className="fleet-admin-group-header">
                <div>
                  <h4>Hazard and Road Controls</h4>
                  <span>Declare or clear live constraints</span>
                </div>
              </div>
              <div className="command-grid fleet-command-grid fleet-command-grid-hazard">
                <label className="form-field">
                  <span>Edge ID</span>
                  <input type="number" value={liveCommandDraft.edgeId} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, edgeId: event.target.value }))} placeholder="2" />
                </label>
                <label className="form-field">
                  <span>Hazard Label</span>
                  <input type="text" value={liveCommandDraft.hazardLabel} onChange={(event) => setLiveCommandDraft((current) => ({ ...current, hazardLabel: event.target.value }))} placeholder="temporary closure" />
                </label>
              </div>
              <div className="action-row fleet-action-row">
                <button className="scene-button" type="button" onClick={onDeclareTemporaryHazardFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Declare Hazard
                </button>
                <button className="scene-button" type="button" onClick={onClearTemporaryHazardFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Clear Hazard
                </button>
                <button className="scene-button" type="button" onClick={onBlockRoadFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Block Road
                </button>
                <button className="scene-button" type="button" onClick={onUnblockRoadFromDraft} disabled={!sessionControl?.command_endpoint}>
                  Unblock Road
                </button>
              </div>
            </section>
          </div>
          <p className="status-copy">{liveCommandMessage}</p>
        </article>

        <article className="subsection fleet-card fleet-inspection-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Inspection Context</h3>
              <p className="fleet-card-lede">
                The selected vehicle stays visible alongside recent commands so the operator can
                confirm what changed and what still needs attention.
              </p>
            </div>
            <span className="fleet-card-badge">Inspection context</span>
          </div>
          {selectedFleetPrimaryInspection ? (
            <div className="fleet-inspection-spotlight">
              <div className="fleet-inspection-spotlight-header">
                <div>
                  <strong>{selectedFleetPrimaryVehicle?.display_name ?? selectedFleetPrimaryVehicle?.role_label ?? "Vehicle"} {formatMaybeNumber(selectedFleetPrimaryInspection.vehicle_id ?? null)}</strong>
                  <p>{selectedFleetPrimaryVehicle?.operational_state ?? selectedFleetPrimaryInspection.operational_state ?? "unknown_state"}</p>
                </div>
                <span className="fleet-inspection-chip">Current target</span>
              </div>
              <div className="fleet-inspection-metric-grid" aria-label="Fleet inspection metrics">
                <div className="fleet-inspection-metric"><span>Node</span><strong>{formatMaybeNumber(selectedFleetPrimaryInspection.current_node_id ?? null)}</strong></div>
                <div className="fleet-inspection-metric"><span>ETA</span><strong>{formatSeconds(selectedFleetPrimaryInspection.eta_s ?? null)}</strong></div>
                <div className="fleet-inspection-metric"><span>Job</span><strong>{selectedFleetPrimaryInspection.current_job_id ?? "none"}</strong></div>
                <div className="fleet-inspection-metric"><span>Wait</span><strong>{selectedFleetPrimaryInspection.wait_reason ?? "none"}</strong></div>
                <div className="fleet-inspection-metric"><span>Control</span><strong>{selectedFleetPrimaryInspection.traffic_control_state ?? "none"}</strong></div>
                <div className="fleet-inspection-metric"><span>Route</span><strong>{selectedFleetRouteSummary}</strong></div>
              </div>
              <ul className="fleet-inspection-context-list">
                <li>Lane: {selectedFleetPrimaryVehicle?.lane_id ? `${selectedFleetPrimaryVehicle.lane_id} · ${selectedFleetPrimaryVehicle.lane_role ?? "travel"}` : "unassigned"}</li>
                <li>Lane direction: {selectedFleetPrimaryVehicle?.lane_directionality ?? "unknown"}</li>
                <li>Lane note: {selectedFleetPrimaryVehicle?.lane_selection_reason ?? "none"}</li>
                <li>Spacing: {formatMeters(selectedFleetPrimaryVehicle?.spacing_envelope_m ?? null)}</li>
                <li>Heading: {selectedFleetPrimaryVehicle ? formatMaybeNumber(Math.round((selectedFleetPrimaryVehicle.heading_rad ?? 0) * 180 / Math.PI)) : "unknown"}</li>
                <li>{selectedFleetRouteDetail}</li>
              </ul>
            </div>
          ) : (
            <div className="fleet-empty-state">
              Select a vehicle to reveal per-vehicle inspection context, live command trace, and
              route detail.
            </div>
          )}
          <div className="fleet-inspection-grid">
            <div className="fleet-inspection-panel">
              <div className="fleet-inspection-panel-header">
                <h4>Selected Vehicles</h4>
                <span>{selectedVehicleIds.length > 1 ? `${selectedVehicleIds.length} vehicles` : "single target"}</span>
              </div>
              <ul className="fleet-inspection-list">
                {selectedFleetPrimaryInspection ? (
                  <li>
                    <div className="fleet-inspection-row-header">
                      <strong>V{formatMaybeNumber(selectedFleetPrimaryInspection.vehicle_id ?? null)}</strong>
                      <span>{selectedFleetPrimaryVehicle?.operational_state ?? selectedFleetPrimaryInspection.operational_state ?? "unknown_state"}</span>
                    </div>
                    <p>Node {formatMaybeNumber(selectedFleetPrimaryInspection.current_node_id ?? null)} · ETA {formatSeconds(selectedFleetPrimaryInspection.eta_s ?? null)} · {selectedFleetPrimaryInspection.traffic_control_detail ?? selectedFleetPrimaryInspection.wait_reason ?? "No detailed inspection note"}</p>
                  </li>
                ) : (
                  <li className="fleet-empty-state">No selected vehicle inspections are available yet.</li>
                )}
              </ul>
            </div>
            <div className="fleet-inspection-panel">
              <div className="fleet-inspection-panel-header">
                <h4>Recent Commands</h4>
                <span>{recentCommands.length} total</span>
              </div>
              <ul className="data-list fleet-command-list">
                {recentCommands.length > 0 ? (
                  recentCommands.slice(0, 4).map((command, index) => <li key={`${command.command_type ?? "command"}-${index}`}>{describeRecentCommand(command)}</li>)
                ) : (
                  <li>No command history is available yet. The trace will populate after the first operator action.</li>
                )}
              </ul>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
