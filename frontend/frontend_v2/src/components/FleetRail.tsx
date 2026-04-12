import type { LiveBundleViewModel } from "../adapters/liveBundle";
import { buildFleetRosterSummary, buildSelectionPresentation } from "../adapters/selectionModel";
import type { FrontendUiActions, FrontendUiState } from "../state/frontendUiState";

type FleetRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  actions: FrontendUiActions;
};

export function FleetRail({ bundle, uiState, actions }: FleetRailProps): JSX.Element {
  const fleetSummary = buildFleetRosterSummary(bundle, uiState);
  const selectedPoints = fleetSummary.selectedVehicleIds.flatMap((vehicleId) => {
    const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId);
    return vehicle === undefined ? [] : [vehicle.position];
  });
  const canFocusSelected = selectedPoints.length > 0;
  const visibleVehicleIds = bundle.map.vehicles.map((vehicle) => vehicle.vehicleId);

  function commitFleetSelection(vehicleIds: number[]) {
    if (vehicleIds.length === 0) {
      actions.setSelection(null, [], null);
      actions.setPopup(false, null);
      actions.setInspector(false, "summary");
      return;
    }

    const leadVehicleId = vehicleIds[0];
    const target = { kind: "vehicle" as const, vehicleId: leadVehicleId };
    const nextUiState = {
      ...uiState,
      selection: {
        ...uiState.selection,
        target,
        vehicleIds,
        hoveredTarget: null,
      },
    };
    const presentation = buildSelectionPresentation(bundle, nextUiState);
    actions.setSelection(target, vehicleIds, null);
    actions.setPopup(true, presentation?.title ?? null);
    actions.setInspector(false, "summary");
  }

  function handleSelectAllVisible() {
    commitFleetSelection(visibleVehicleIds);
  }

  function handleClearSelection() {
    commitFleetSelection([]);
  }

  function handleFocusSelected() {
    actions.focusPoints(selectedPoints, bundle.map.bounds);
  }

  return (
    <section className="panel fleet-rail">
      <div className="panel-topline">
        <div>
          <p className="panel-kicker">Fleet</p>
          <h2>Fleet mode baseline</h2>
        </div>
        <div className="panel-metrics">
          <span>{fleetSummary.selectedVehicleCount} selected</span>
          <span>{fleetSummary.totalVehicleCount} visible</span>
          <span>{fleetSummary.selectionSource} source</span>
        </div>
      </div>

      <p className="stack-copy">
        Use Fleet mode to understand several vehicles at once. The map stays primary, but this rail makes selection, grouping, and future batch
        actions easier to read than in Operate mode.
      </p>

      <div className="fleet-summary-strip">
        <span className="selection-pill">{fleetSummary.summary}</span>
        <span className="selection-pill">{fleetSummary.groups.length > 0 ? `${fleetSummary.groups.length} grouped context(s)` : "No group context yet"}</span>
        <span className="selection-pill">{fleetSummary.selectionSource === "local" ? "Frontend-owned selection" : fleetSummary.selectionSource === "bundle" ? "Bundle-driven selection" : "No active selection"}</span>
      </div>

      <section className="fleet-section fleet-selection-card">
        <div className="fleet-section-head">
          <div>
            <p className="panel-kicker">Selection state</p>
            <h3>{fleetSummary.selectedVehicleCount > 0 ? "Multi-select is active" : "Select one or more vehicles"}</h3>
          </div>
          <span className="selection-popup-badge">{fleetSummary.leadVehicleId !== null ? `Lead ${fleetSummary.leadVehicleId}` : "No lead vehicle"}</span>
        </div>
        <p className="stack-copy">{fleetSummary.context}</p>
        <div className="fleet-selection-chips">
          {fleetSummary.selectedVehicleIds.length > 0 ? (
            fleetSummary.selectedVehicleIds.map((vehicleId) => (
              <button
                key={vehicleId}
                type="button"
                className="fleet-selection-chip"
                onClick={() => commitFleetSelection([vehicleId])}
              >
                Vehicle {vehicleId}
              </button>
            ))
          ) : (
            <span className="fleet-selection-chip fleet-selection-chip-muted">No fleet vehicles selected</span>
          )}
        </div>
        <div className="fleet-selection-actions">
          <button type="button" className="scene-button-primary" onClick={handleSelectAllVisible} disabled={visibleVehicleIds.length === 0}>
            Select all visible
          </button>
          <button type="button" className="scene-button-primary" onClick={handleClearSelection} disabled={fleetSummary.selectedVehicleCount === 0}>
            Clear selection
          </button>
          <button type="button" className="scene-button-primary" onClick={handleFocusSelected} disabled={!canFocusSelected}>
            Focus selected
          </button>
        </div>
      </section>

      <section className="fleet-section">
        <div className="fleet-section-head">
          <div>
            <h3>Fleet roster</h3>
            <p>Visible vehicles are sorted by fleet state and kept compact so the map can stay primary.</p>
          </div>
          <span className="selection-popup-badge">{visibleVehicleIds.length} total</span>
        </div>
        <div className="fleet-roster-list">
          {fleetSummary.visibleVehicles.map((vehicle) => (
            <button
              key={vehicle.vehicleId}
              type="button"
              className={`fleet-roster-row ${vehicle.selected ? "fleet-roster-row-selected" : ""}`}
              onClick={() => commitFleetSelection([vehicle.vehicleId])}
            >
              <div className="fleet-roster-row-head">
                <strong>Vehicle {vehicle.vehicleId}</strong>
                <span className="selection-popup-badge">{vehicle.selected ? "Selected" : vehicle.stateClass}</span>
              </div>
              <p>{vehicle.summary}</p>
              <span className="fleet-roster-row-detail">{vehicle.context}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="fleet-section">
        <div className="fleet-section-head">
          <div>
            <h3>Grouped vehicle context</h3>
            <p>Selected and visible vehicles are grouped by live state so batch work has a stable home later.</p>
          </div>
          <span className="selection-popup-badge">{fleetSummary.groups.length} group(s)</span>
        </div>
        <div className="fleet-group-grid">
          {fleetSummary.groups.map((group) => (
            <article key={group.key} className="fleet-group-card">
              <div className="fleet-group-card-head">
                <div>
                  <p className="fleet-group-card-kicker">{group.label}</p>
                  <h4>{group.summary}</h4>
                </div>
                <span className="selection-popup-badge">{group.count}</span>
              </div>
              <div className="fleet-group-chips">
                {group.vehicleSummaries.map((summary) => (
                  <span key={summary} className="fleet-group-chip">
                    {summary}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="fleet-section fleet-batch-hub">
        <div className="fleet-section-head">
          <div>
            <h3>Batch action hooks</h3>
            <p>These affordances reserve a bounded lane for later fleet operations without inventing shadow state now.</p>
          </div>
          <span className="selection-popup-badge">Future step hook</span>
        </div>
        <div className="fleet-batch-actions">
          <button type="button" className="scene-button-primary" disabled>
            Preview batch action
          </button>
          <button type="button" className="scene-button-primary" disabled>
            Commit batch action
          </button>
          <button type="button" className="scene-button-primary" disabled>
            Bulk reposition
          </button>
        </div>
        <p className="fleet-batch-note">
          Later fleet operations can land here without changing the selection model or the map-first interaction pattern.
        </p>
      </section>

      <section className="fleet-section">
        <div className="fleet-section-head">
          <div>
            <h3>Fleet state notes</h3>
            <p>Useful reminders that keep the surface grounded in bundle truth.</p>
          </div>
        </div>
        <ul className="list-copy">
          {fleetSummary.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}
