import { useMemo, useState } from "react";

import type { LiveBundleViewModel } from "../adapters/liveBundle";
import {
  buildSelectionPresentation,
  resolveSelectionVehicleIds,
} from "../adapters/selectionModel";
import type { FrontendUiState } from "../state/frontendUiState";

type OperateRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  refreshBundle: () => void;
};

export function OperateRail({ bundle, uiState, refreshBundle }: OperateRailProps): JSX.Element {
  const [destinationNodeId, setDestinationNodeId] = useState("");
  const initialStepSeconds = Number.parseFloat(bundle.sessionIdentity.stepSeconds);
  const [sessionStepSeconds, setSessionStepSeconds] = useState(
    Number.isFinite(initialStepSeconds) ? String(initialStepSeconds) : "",
  );
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const selectionPresentation = buildSelectionPresentation(bundle, uiState);
  const selectedVehicleIds = useMemo(() => resolveSelectionVehicleIds(bundle, uiState), [bundle, uiState]);
  const selectedVehicles = selectedVehicleIds.flatMap((vehicleId) => {
    const inspection = bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === vehicleId) ?? null;
    const liveVehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId) ?? null;
    if (inspection === null && liveVehicle === null) {
      return [];
    }
    return [
      {
        vehicleId,
        state: inspection?.operationalState ?? liveVehicle?.state ?? "unknown",
        waitReason: inspection?.waitReason ?? null,
        summary:
          inspection !== null && inspection.currentTaskType !== null
            ? inspection.currentTaskType
            : inspection?.trafficControlDetail ?? liveVehicle?.state ?? "unknown",
      },
    ];
  });
  const selectedVehicleCount = selectedVehicleIds.length;
  const hasVehicleSelection = selectedVehicleCount > 0;
  const queueCount = selectedVehicles.filter((vehicle) => vehicle.waitReason !== null).length;
  const blockedEdges = bundle.map.blockedEdgeIds.length;
  const hazardSignals = bundle.alerts.filter((alert) => alert.toLowerCase().includes("anomaly"));
  const congestionSignals = bundle.alerts.filter((alert) => alert.toLowerCase().includes("congested"));

  async function handlePreviewRoute() {
    if (!hasVehicleSelection) {
      setStatusMessage("Select a vehicle first to preview a route.");
      return;
    }
    const destinationNode = Number(destinationNodeId);
    if (!Number.isFinite(destinationNode)) {
      setStatusMessage("Enter a valid destination node.");
      return;
    }

    setStatusMessage("Previewing route...");
    const response = await fetch(new URL(bundle.commandSurface.previewEndpoint, window.location.origin), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        selected_vehicle_ids: selectedVehicleIds,
        vehicle_ids: selectedVehicleIds,
        destination_node_id: destinationNode,
      }),
    });
    if (!response.ok) {
      setStatusMessage(`Route preview failed: ${response.status}`);
      return;
    }

    refreshBundle();
    setStatusMessage(`Previewed ${selectedVehicleCount} vehicle(s) to node ${destinationNode}.`);
  }

  async function handleAssignDestination() {
    if (!hasVehicleSelection) {
      setStatusMessage("Select a vehicle first to issue a command.");
      return;
    }
    const destinationNode = Number(destinationNodeId);
    if (!Number.isFinite(destinationNode)) {
      setStatusMessage("Enter a valid destination node.");
      return;
    }

    setStatusMessage("Sending command...");
    const response = await fetch(new URL(bundle.commandSurface.commandEndpoint, window.location.origin), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        command_type: "assign_vehicle_destination",
        selected_vehicle_ids: selectedVehicleIds,
        destination_node_id: destinationNode,
      }),
    });
    if (!response.ok) {
      setStatusMessage(`Command failed: ${response.status}`);
      return;
    }

    refreshBundle();
    setStatusMessage(`Command sent for ${selectedVehicleCount} vehicle(s).`);
  }

  async function handleSessionAction(action: "play" | "pause" | "step") {
    setStatusMessage(`${action === "step" ? "Stepping" : action === "play" ? "Starting" : "Pausing"} live session...`);
    const payload: Record<string, unknown> = { action };
    if (action === "step") {
      payload.delta_s = Number.parseFloat(sessionStepSeconds) || Number.parseFloat(bundle.sessionIdentity.stepSeconds) || 0.5;
    }

    const response = await fetch(new URL(bundle.commandSurface.sessionControlEndpoint, window.location.origin), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setStatusMessage(`Session control failed: ${response.status}`);
      return;
    }

    refreshBundle();
    setStatusMessage(
      action === "step" ? "Advanced the live session." : action === "play" ? "Session started." : "Session paused.",
    );
  }

  return (
    <>
      <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Operate</p>
            <h2>Live watch and control</h2>
          </div>
          <div className="panel-metrics">
            <span>{selectedVehicleCount} selected</span>
            <span>{queueCount} queued</span>
            <span>{blockedEdges} blocked edges</span>
          </div>
        </div>
        <p className="stack-copy">
          Map-first operate mode keeps the scene primary while compact controls support preview, commit, and live watch.
        </p>
        <div className="operate-chip-row">
          {selectedVehicles.length > 0 ? (
            selectedVehicles.map((vehicle) => (
              <span key={vehicle.vehicleId} className="operate-chip">
                Vehicle {vehicle.vehicleId} · {vehicle.state}
              </span>
            ))
          ) : (
            <span className="operate-chip operate-chip-muted">Select vehicles on the map to start previewing commands.</span>
          )}
        </div>
        <div className="minimap-context-strip">
          {bundle.alerts.length > 0 ? <span>{bundle.alerts[0]}</span> : <span>No active alerts.</span>}
          {congestionSignals.length > 0 ? <span>{congestionSignals[0]}</span> : null}
          {hazardSignals.length > 0 ? <span>{hazardSignals[0]}</span> : null}
          {selectionPresentation !== null ? <span>Selection ready for inspection.</span> : null}
        </div>
        {statusMessage !== null ? <p className="operate-status">{statusMessage}</p> : null}
      </section>

      <section className="panel">
        <h2>Inspector</h2>
        {selectionPresentation === null ? (
          <p className="stack-copy">
            Click a vehicle, road, or area to inspect it. Route preview and commands unlock when a vehicle is selected.
          </p>
        ) : (
          <>
            <div className="selection-inspector-head">
              <div>
                <p className="panel-kicker">Selected</p>
                <h3>{selectionPresentation.title}</h3>
              </div>
              <span className="selection-popup-badge">{selectionPresentation.badge}</span>
            </div>
            <p className="stack-copy">{selectionPresentation.summary}</p>
            <p className="selection-inspector-context">{selectionPresentation.context}</p>
            <dl className="selection-inspector-details">
              {selectionPresentation.details.map((detail) => (
                <div key={detail.label}>
                  <dt>{detail.label}</dt>
                  <dd>{detail.value}</dd>
                </div>
              ))}
            </dl>
            {selectionPresentation.notes.length > 0 ? (
              <ul className="list-copy">
                {selectionPresentation.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : null}
          </>
        )}
      </section>

      <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Preview</p>
            <h2>Route and command entry</h2>
          </div>
          <span className="status-badge">{selectedVehicleCount > 0 ? "Ready" : "Select a vehicle"}</span>
        </div>
        <p className="stack-copy">
          Preview a route first, then issue the same destination as a live command. The bundle stays authoritative and refreshes after each submission.
        </p>
        <label className="operate-field">
          <span>Destination node</span>
          <input
            type="number"
            min="0"
            inputMode="numeric"
            value={destinationNodeId}
            onChange={(event) => setDestinationNodeId(event.currentTarget.value)}
            placeholder="Enter node id"
          />
        </label>
        <div className="map-shell-toolbar-group">
          <button type="button" className="scene-button-primary" onClick={() => void handlePreviewRoute()} disabled={!hasVehicleSelection}>
            Preview selected
          </button>
          <button type="button" className="scene-button-primary" onClick={() => void handleAssignDestination()} disabled={!hasVehicleSelection}>
            Assign destination
          </button>
        </div>
      </section>

      <section className="panel">
        <div className="panel-topline">
          <div>
            <p className="panel-kicker">Session</p>
            <h2>Compact live controls</h2>
          </div>
          <span className="status-badge">{bundle.sessionIdentity.playState}</span>
        </div>
        <p className="stack-copy">
          Live session controls stay compact: play, pause, step, and refresh. The map remains the main surface.
        </p>
        <label className="operate-field operate-field-inline">
          <span>Step seconds</span>
          <input
            type="number"
            min="0.1"
            step="0.1"
            inputMode="decimal"
            value={sessionStepSeconds}
            onChange={(event) => setSessionStepSeconds(event.currentTarget.value)}
          />
        </label>
        <div className="map-shell-toolbar-group">
          <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("play")}>
            Play
          </button>
          <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("pause")}>
            Pause
          </button>
          <button type="button" className="scene-button-primary" onClick={() => void handleSessionAction("step")}>
            Step
          </button>
          <button type="button" className="scene-button-primary" onClick={refreshBundle}>
            Refresh
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Live context</h2>
        <ul className="list-copy">
          <li>Environment: {bundle.map.environment.displayName}</li>
          <li>Fleet awareness: {selectedVehicleCount > 1 ? "multi-vehicle" : selectedVehicleCount === 1 ? "single vehicle" : "no selected vehicle"}</li>
          <li>Queue awareness: {queueCount > 0 ? `${queueCount} selected vehicle(s) waiting` : "no selected queue pressure"}</li>
          <li>Hazard awareness: {hazardSignals.length > 0 ? hazardSignals.join(" · ") : "no active hazard signal"}</li>
        </ul>
      </section>
    </>
  );
}
