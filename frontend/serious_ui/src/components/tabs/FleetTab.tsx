import type { Dispatch, SetStateAction } from "react";

import { PanelHeader } from "../shared/PanelHeader";
import {
  describeRecentCommand,
  describeVehicleName,
  describeVehicleOperationalSummary,
  formatMaybeNumber,
  formatMeters,
  formatSeconds,
  humanizeIdentifier,
  sampleDisplayedVehicles,
  type DisplayedVehicle,
} from "../../viewModel";
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
  onSelectVehicle: (vehicleId: number | undefined, options?: { additive?: boolean }) => void;
  onSpawnVehicleFromDraft: () => void;
  onRemoveVehicleFromDraft: () => void;
  onInjectJobFromDraft: () => void;
  onDeclareTemporaryHazardFromDraft: () => void;
  onClearTemporaryHazardFromDraft: () => void;
  onBlockRoadFromDraft: () => void;
  onUnblockRoadFromDraft: () => void;
};

type FleetStateGroup = {
  stateLabel: string;
  vehicles: DisplayedVehicle[];
};

function toFleetStateLabel(state: string | null | undefined): string {
  return humanizeIdentifier(state ?? "unknown").toLowerCase();
}

function groupVehiclesByState(vehicles: DisplayedVehicle[]): FleetStateGroup[] {
  const grouped = vehicles.reduce<Record<string, DisplayedVehicle[]>>((accumulator, vehicle) => {
    const stateLabel = toFleetStateLabel(vehicle.operational_state);
    (accumulator[stateLabel] ??= []).push(vehicle);
    return accumulator;
  }, {});

  return Object.entries(grouped)
    .map(([stateLabel, groupedVehicles]) => ({
      stateLabel,
      vehicles: groupedVehicles.sort((left, right) => {
        const leftId = left.vehicle_id ?? Number.MAX_SAFE_INTEGER;
        const rightId = right.vehicle_id ?? Number.MAX_SAFE_INTEGER;
        return leftId - rightId;
      }),
    }))
    .sort((left, right) => right.vehicles.length - left.vehicles.length || left.stateLabel.localeCompare(right.stateLabel));
}

function formatVehicleSummary(bundle: BundlePayload | null, vehicle: DisplayedVehicle): string {
  const inspection = bundle?.command_center?.vehicle_inspections?.find(
    (entry) => entry.vehicle_id === vehicle.vehicle_id,
  ) ?? null;
  const routePreview = bundle?.command_center?.route_previews?.find(
    (entry) => entry.vehicle_id === vehicle.vehicle_id,
  ) ?? null;
  return describeVehicleOperationalSummary(bundle, vehicle, inspection, routePreview);
}

export function FleetTab({
  bundle,
  motionClockS,
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
  const visibleVehicleCount = displayedVehicles.length;
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
  const selectedFleetPrimaryRoutePreview =
    selectedFleetPrimaryVehicleId !== null
      ? routePreviews.find((preview) => preview.vehicle_id === selectedFleetPrimaryVehicleId) ?? null
      : null;
  const selectedFleetGroups = groupVehiclesByState(selectedFleetVehicles);
  const selectedFleetStateSummary =
    selectedFleetGroups.length > 0
      ? selectedFleetGroups
          .slice(0, 3)
          .map((group) => `${group.vehicles.length} ${group.stateLabel}`)
          .join(" · ")
      : "No vehicles selected yet";
  const selectedFleetIdSummary =
    selectedFleetVehicles.length > 0
      ? selectedFleetVehicles.map((vehicle) => `V${formatMaybeNumber(vehicle.vehicle_id ?? null)}`).join(", ")
      : "none";
  const selectedFleetRouteSummary = selectedFleetPrimaryRoutePreview
    ? `Node ${formatMaybeNumber(selectedFleetPrimaryRoutePreview.destination_node_id ?? null)}${
        selectedFleetPrimaryRoutePreview.total_distance !== undefined
          ? ` · ${formatMeters(selectedFleetPrimaryRoutePreview.total_distance)}`
          : ""
      }`
    : "No route preview for the lead vehicle";
  const selectedFleetRouteDetail = selectedFleetPrimaryRoutePreview
    ? `${selectedFleetPrimaryRoutePreview.is_actionable ? "Actionable" : "Pending"}${
        selectedFleetPrimaryRoutePreview.reason ? ` · ${selectedFleetPrimaryRoutePreview.reason}` : ""
      }`
    : selectedFleetPrimaryInspection?.route_ahead_node_ids?.length
      ? `Inspection sees ${selectedFleetPrimaryInspection.route_ahead_node_ids.length} upcoming node(s)`
      : "Select a vehicle to reveal route and inspection context.";
  const selectionModeCopy =
    selectedVehicleIds.length > 1
      ? "Batch select is active"
      : selectedVehicleIds.length === 1
        ? "Single-select is active"
        : "No selection yet";
  const batchHookCopy =
    selectedVehicleIds.length > 1
      ? "This selection set is ready to become the target for future batch commands."
      : "Select more than one vehicle to stage a batch target.";

  return (
    <section className="panel info-panel fleet-pane" aria-labelledby="fleet-mode-title">
      <PanelHeader
        eyebrow="Fleet Region"
        title="Fleet Mode"
        titleId="fleet-mode-title"
        lede="Fleet mode is the place to understand multiple vehicles at once: who is selected, how the set is grouped, and what the next batch target could be."
        className="compact fleet-panel-header"
        meta={
          <div className="fleet-panel-meta">
            <span className="status-pill secondary">{formatMaybeNumber(selectedVehicleIds.length)} selected</span>
            <span className="status-pill accent">Visible {formatMaybeNumber(visibleVehicleCount)}</span>
            <span className="status-pill">{selectionModeCopy}</span>
          </div>
        }
      />

      <div className="fleet-mode-grid">
        <article className="subsection fleet-card fleet-summary-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Selection Summary</h3>
              <p className="fleet-card-lede">
                The selected fleet stays readable as a set, so the operator can see the primary vehicle,
                the state mix, and the live route context without opening the inspector.
              </p>
            </div>
            <span className="fleet-card-badge">
              {selectedVehicleIds.length > 1 ? "Batch-ready" : "Selection focus"}
            </span>
          </div>

          <div className="fleet-summary-grid">
            <div className="fleet-summary-metric">
              <span>Lead vehicle</span>
              <strong>{selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}</strong>
              <p>{selectedFleetPrimaryVehicle ? describeVehicleName(selectedFleetPrimaryVehicle) : "No primary selection"}</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Selection scope</span>
              <strong>{selectedVehicleIds.length > 1 ? "Multi-select" : "Single-select"}</strong>
              <p>{selectedVehicleIds.length} selected of {visibleVehicleCount} visible vehicles.</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Fleet groups</span>
              <strong>{formatMaybeNumber(selectedFleetGroups.length)} buckets</strong>
              <p>{selectedFleetStateSummary}</p>
            </div>
            <div className="fleet-summary-metric">
              <span>Route context</span>
              <strong>{selectedFleetRouteSummary}</strong>
              <p>{selectedFleetRouteDetail}</p>
            </div>
          </div>

          <div className="fleet-selection-strip">
            <div className="fleet-batch-summary">
              <span className="fleet-batch-chip">Selected: {selectedFleetIdSummary}</span>
              <span className="fleet-batch-chip">Lead: {selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}</span>
              <span className="fleet-batch-chip">Route previews: {formatMaybeNumber(routePreviews.length)}</span>
            </div>
          </div>
        </article>

        <article className="subsection fleet-card fleet-roster-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Fleet Roster</h3>
              <p className="fleet-card-lede">
                Each visible vehicle can be focused individually or added to the current batch. The roster
                makes single-select and multi-select explicit.
              </p>
            </div>
            <span className="fleet-card-badge">Visible {formatMaybeNumber(visibleVehicleCount)}</span>
          </div>

          <ul className="fleet-roster-list" aria-label="Fleet roster">
            {displayedVehicles.length > 0 ? (
              displayedVehicles.map((vehicle, index) => {
                const vehicleId = vehicle.vehicle_id ?? null;
                const isSelected = vehicleId !== null && selectedVehicleIds.includes(vehicleId);
                const inspection = inspections.find((entry) => entry.vehicle_id === vehicleId) ?? null;
                const routePreview = routePreviews.find((entry) => entry.vehicle_id === vehicleId) ?? null;
                const vehicleSummary = formatVehicleSummary(bundle, vehicle);
                const vehicleLabel = describeVehicleName(vehicle);
                return (
                  <li
                    key={vehicleId ?? `fleet-vehicle-${index}`}
                    className={`fleet-roster-item ${isSelected ? "fleet-roster-item-selected" : ""}`}
                  >
                    <div className="fleet-roster-item-top">
                      <div>
                        <p className="fleet-roster-item-id">V{formatMaybeNumber(vehicleId)}</p>
                        <strong>{vehicleLabel}</strong>
                      </div>
                      <span className="fleet-roster-item-state">{humanizeIdentifier(vehicle.operational_state ?? "unknown")}</span>
                    </div>
                    <p className="fleet-roster-item-summary">{vehicleSummary}</p>
                    <div className="fleet-roster-item-details">
                      <span>Node {formatMaybeNumber(inspection?.current_node_id ?? vehicle.node_id ?? null)}</span>
                      <span>ETA {formatSeconds(inspection?.eta_s ?? null)}</span>
                      <span>
                        {routePreview?.destination_node_id !== undefined
                          ? `→ node ${formatMaybeNumber(routePreview.destination_node_id)}`
                          : vehicle.lane_id !== undefined && vehicle.lane_id !== null
                            ? `${vehicle.lane_id} · ${vehicle.lane_role ?? "travel"}`
                            : "preview pending"}
                      </span>
                    </div>
                    <div className="fleet-roster-item-actions">
                      <button
                        className="scene-button scene-button-primary"
                        type="button"
                        onClick={() => onSelectVehicle(vehicleId ?? undefined)}
                      >
                        Select only
                      </button>
                      <button
                        className="scene-button"
                        type="button"
                        onClick={() => onSelectVehicle(vehicleId ?? undefined, { additive: true })}
                        aria-label={`${isSelected ? "Remove" : "Add"} V${formatMaybeNumber(vehicleId)} ${isSelected ? "from batch" : "to batch"}`}
                      >
                        {isSelected ? "Remove from batch" : "Add to batch"}
                      </button>
                    </div>
                  </li>
                );
              })
            ) : (
              <li className="fleet-empty-state">No visible vehicles were found in the current snapshot.</li>
            )}
          </ul>
        </article>

        <article className="subsection fleet-card fleet-group-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Grouped Vehicle Context</h3>
              <p className="fleet-card-lede">
                Selected vehicles are grouped by operational state so a batch can be understood before it
                is acted on.
              </p>
            </div>
            <span className="fleet-card-badge">{selectedVehicleIds.length > 1 ? "Grouped batch" : "Grouped detail"}</span>
          </div>

          {selectedFleetGroups.length > 0 ? (
            <div className="fleet-group-grid">
              {selectedFleetGroups.map((group) => (
                <section key={group.stateLabel} className="fleet-group">
                  <div className="fleet-group-header">
                    <div>
                      <h4>{group.stateLabel}</h4>
                      <span>{group.vehicles.length} vehicle(s)</span>
                    </div>
                  </div>
                  <ul className="fleet-group-list">
                    {group.vehicles.map((vehicle) => {
                      const vehicleId = vehicle.vehicle_id ?? null;
                      const routePreview = routePreviews.find((entry) => entry.vehicle_id === vehicleId) ?? null;
                      const inspection = inspections.find((entry) => entry.vehicle_id === vehicleId) ?? null;
                      return (
                        <li key={vehicleId ?? `${group.stateLabel}-unknown`}>
                          <div className="fleet-group-list-header">
                            <strong>{describeVehicleName(vehicle)}</strong>
                            <span>V{formatMaybeNumber(vehicleId)}</span>
                          </div>
                          <p>
                            Node {formatMaybeNumber(inspection?.current_node_id ?? vehicle.node_id ?? null)} ·
                            {routePreview?.destination_node_id !== undefined
                              ? ` route to node ${formatMaybeNumber(routePreview.destination_node_id)}`
                              : ` ${vehicle.lane_id !== undefined && vehicle.lane_id !== null ? `${vehicle.lane_id} · ${vehicle.lane_role ?? "travel"}` : "no route preview"}`}
                          </p>
                        </li>
                      );
                    })}
                  </ul>
                </section>
              ))}
            </div>
          ) : (
            <div className="fleet-empty-state">
              Select one or more vehicles in the roster to reveal grouped fleet context here.
            </div>
          )}
        </article>

        <article className="subsection fleet-card fleet-batch-card">
          <div className="subsection-header fleet-card-header">
            <div>
              <h3>Batch Action Hooks</h3>
              <p className="fleet-card-lede">
                These controls keep the selection set bounded and give later batch commands a clear home
                without pretending the deeper fleet workflows already exist.
              </p>
            </div>
            <span className="fleet-card-badge">Selection-ready</span>
          </div>

          <div className="fleet-batch-summary">
            <span className="fleet-batch-chip">Mode: {selectionModeCopy}</span>
            <span className="fleet-batch-chip">Batch scope: {selectedVehicleIds.length} vehicle(s)</span>
            <span className="fleet-batch-chip">Live command: {sessionControl?.command_endpoint ? "connected" : "offline"}</span>
          </div>

          <div className="fleet-selection-actions">
            <button
              className="scene-button scene-button-primary"
              type="button"
              onClick={onSelectVisible}
              disabled={displayedVehicles.length === 0}
            >
              Select visible
            </button>
            <button
              className="scene-button"
              type="button"
              onClick={onClearSelection}
              disabled={selectedVehicleIds.length === 0}
            >
              Clear selection
            </button>
            <button
              className="scene-button"
              type="button"
              onClick={() => onSelectVehicle(selectedFleetPrimaryVehicleId ?? undefined)}
              disabled={selectedFleetPrimaryVehicleId === null}
            >
              Focus lead
            </button>
            <button
              className="scene-button"
              type="button"
              disabled
              title="Reserved for the first true batch command once later fleet operations land."
            >
              Preview batch command
            </button>
          </div>

          <p className="status-copy">
            {batchHookCopy} The selection set is visible, manipulable, and ready for later bounded batch
            actions.
          </p>

          {recentCommands.length > 0 ? (
            <div className="fleet-recent-strip">
              <span className="fleet-card-badge">Recent live activity</span>
              <ul className="data-list fleet-command-list">
                {recentCommands.slice(0, 4).map((command, index) => (
                  <li key={`${command.command_type ?? "command"}-${index}`}>{describeRecentCommand(command)}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </article>
      </div>

      <p className="fleet-status-copy">{liveCommandMessage}</p>
    </section>
  );
}
