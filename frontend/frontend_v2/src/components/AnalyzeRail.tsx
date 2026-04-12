import type { LiveBundleViewModel, LiveRoutePreviewViewModel } from "../adapters/liveBundle";
import { buildSelectionPresentation, resolveSelectionVehicleIds } from "../adapters/selectionModel";
import type { FrontendUiState } from "../state/frontendUiState";

type AnalyzeRailProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  activeRoutePreview: LiveRoutePreviewViewModel | null;
};

type SeverityBucket = "info" | "warn" | "error";

export function AnalyzeRail({ bundle, uiState, activeRoutePreview }: AnalyzeRailProps): JSX.Element {
  const selectedVehicleIds = resolveSelectionVehicleIds(bundle, uiState);
  const selectedVehicleId = selectedVehicleIds[0] ?? null;
  const selectionPresentation = buildSelectionPresentation(bundle, uiState);
  const selectedInspection =
    selectedVehicleId !== null
      ? bundle.commandCenter.vehicleInspections.find((inspection) => inspection.vehicleId === selectedVehicleId) ?? null
      : null;
  const selectedBundlePreview =
    selectedVehicleId !== null
      ? bundle.commandCenter.routePreviews.find((preview) => preview.vehicleId === selectedVehicleId) ?? null
      : null;
  const comparisonPreview = activeRoutePreview ?? selectedBundlePreview;
  const previewDiagnostics = comparisonPreview?.renderDiagnostics ?? [];
  const diagnostics = bundle.commandCenter.vehicleInspections.flatMap((inspection) =>
    inspection.diagnostics.map((diagnostic) => ({
      ...diagnostic,
      vehicleId: inspection.vehicleId,
    })),
  );
  const diagnosticsBySeverity = summarizeSeverityCounts(diagnostics);
  const selectedDiagnostics = selectedInspection?.diagnostics ?? [];
  const anomalySignals = bundle.analysis.anomalySignals;
  const explainedAlerts = bundle.alerts.length > 0 ? bundle.alerts.slice(0, 4) : [];
  const routeComparison = comparisonPreview !== null ? compareRouteContext(comparisonPreview, selectedInspection) : null;
  const routeMatchLabel =
    routeComparison === null
      ? "No route preview available"
      : routeComparison.matching ? "Route context aligns" : "Route context differs";

  return (
    <section className="panel analyze-rail">
      <div className="panel-topline">
        <div>
          <p className="panel-kicker">Analyze</p>
          <h2>Analyze mode baseline</h2>
        </div>
        <div className="panel-metrics">
          <span>{anomalySignals.length} anomaly signal(s)</span>
          <span>{diagnostics.length} diagnostic item(s)</span>
          <span>{selectedVehicleIds.length} selected vehicle(s)</span>
        </div>
      </div>

      <p className="stack-copy">
        Analyze mode is the explanation home for later diagnostics work. It stays grounded in simulator truth, summarizes what the bundle already
        knows, and keeps the map primary instead of pretending to generate new intelligence.
      </p>

      <section className="analyze-overview-card">
        <div className="analyze-section-head">
          <div>
            <p className="panel-kicker">Explanation surface</p>
            <h3>{selectionPresentation?.title ?? "Current bundle view"}</h3>
          </div>
          <span className="selection-popup-badge">{routeMatchLabel}</span>
        </div>
        <p className="stack-copy">
          {selectionPresentation?.summary ??
            "No selection is active. The analyzer is summarizing bundle-level signals, diagnostics, and route context instead."}
        </p>
        <p className="analyze-explanation-copy">
          {selectionPresentation?.context ?? "Bundle-level signals remain authoritative; the rail only explains what is already present."}
        </p>
      </section>

      <section className="analyze-section">
        <div className="analyze-section-head">
          <div>
            <h3>Anomaly surfacing</h3>
            <p>Simulator anomaly signals are surfaced as a compact baseline, separate from human-operated commands.</p>
          </div>
          <span className="selection-popup-badge">{anomalySignals.length} signal(s)</span>
        </div>
        <div className="analyze-signal-list">
          {anomalySignals.length > 0 ? (
            anomalySignals.slice(0, 6).map((signal) => (
              <article key={`${signal.code}-${signal.message}`} className={`analyze-signal-card analyze-signal-${severityToken(signal.severity)}`}>
                <div className="analyze-signal-head">
                  <strong>{signal.code}</strong>
                  <span>{signal.severity}</span>
                </div>
                <p>{signal.message}</p>
                <span className="analyze-signal-meta">
                  {signal.vehicleId !== null ? `Vehicle ${signal.vehicleId}` : "Bundle-level signal"}
                </span>
              </article>
            ))
          ) : (
            <div className="analyze-empty-state">No simulator anomaly signals are exposed in the current bundle.</div>
          )}
        </div>
      </section>

      {previewDiagnostics.length > 0 ? (
        <section className="analyze-section">
          <div className="analyze-section-head">
            <div>
              <h3>Preview geometry diagnostics</h3>
              <p>The active route preview exists, but some node references could not be resolved against the canonical node map.</p>
            </div>
            <span className="selection-popup-badge">{previewDiagnostics.length} issue(s)</span>
          </div>
          <ul className="list-copy">
            {previewDiagnostics.slice(0, 3).map((diagnostic) => (
              <li key={diagnostic}>{diagnostic}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="analyze-section">
        <div className="analyze-section-head">
          <div>
            <h3>Route comparison context</h3>
            <p>Compare the selected vehicle’s route truth with the current route preview when one is available.</p>
          </div>
          <span className="selection-popup-badge">{comparisonPreview !== null ? `Vehicle ${comparisonPreview.vehicleId}` : "No preview"}</span>
        </div>
        {routeComparison !== null && comparisonPreview !== null ? (
          <div className="analyze-comparison-card">
            <div className="analyze-comparison-grid">
              <div>
                <span>Preview destination</span>
                <strong>Node {comparisonPreview.destinationNodeId}</strong>
              </div>
              <div>
                <span>Preview route length</span>
                <strong>{comparisonPreview.nodeIds.length} node(s)</strong>
              </div>
              <div>
                <span>Inspection route ahead</span>
                <strong>{selectedInspection !== null ? `${selectedInspection.routeAheadNodeIds.length} node(s)` : "Unknown"}</strong>
              </div>
              <div>
                <span>Comparison result</span>
                <strong>{routeComparison.matching ? "Aligned" : "Not aligned"}</strong>
              </div>
            </div>
            <p className="analyze-comparison-copy">{routeComparison.explanation}</p>
          </div>
        ) : (
          <div className="analyze-empty-state">
            Select a vehicle or load a route preview to see comparison context here.
          </div>
        )}
      </section>

      <section className="analyze-section">
        <div className="analyze-section-head">
          <div>
            <h3>Diagnostics aggregation</h3>
            <p>Diagnostics are grouped from authoritative vehicle inspections so the rail can explain the bundle without inventing new state.</p>
          </div>
          <span className="selection-popup-badge">{diagnostics.length} total</span>
        </div>
        <div className="analyze-diagnostic-summary">
          {Object.entries(diagnosticsBySeverity).map(([severity, count]) => (
            <span key={severity} className="selection-pill">
              {severity}: {count}
            </span>
          ))}
        </div>
        {selectedDiagnostics.length > 0 ? (
          <div className="analyze-diagnostic-list">
            {selectedDiagnostics.map((diagnostic) => (
              <article key={`${diagnostic.code}-${diagnostic.message}`} className={`analyze-diagnostic-card analyze-diagnostic-${severityToken(diagnostic.severity)}`}>
                <div className="analyze-signal-head">
                  <strong>{diagnostic.code}</strong>
                  <span>{diagnostic.severity}</span>
                </div>
                <p>{diagnostic.message}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="analyze-empty-state">
            {selectedVehicleId !== null
              ? `Vehicle ${selectedVehicleId} has no diagnostics attached in the current bundle.`
              : "Select a vehicle to inspect its diagnostics in detail."}
          </div>
        )}
      </section>

      <section className="analyze-section">
        <div className="analyze-section-head">
          <div>
            <h3>Bundle explanation notes</h3>
            <p>These summaries help the operator understand what is already visible in the simulator truth.</p>
          </div>
        </div>
        <div className="analyze-notes-grid">
          <article className="analyze-note-card">
            <strong>Alerts</strong>
            <p>{explainedAlerts.length > 0 ? explainedAlerts.join(" · ") : "No active alerts were reported by the bundle."}</p>
          </article>
          <article className="analyze-note-card">
            <strong>Selection focus</strong>
            <p>
              {selectedVehicleIds.length > 0
                ? `${selectedVehicleIds.length} selected vehicle(s) are available for explanation context.`
                : "No current vehicle selection is shaping the analysis view."}
            </p>
          </article>
          <article className="analyze-note-card">
            <strong>Route truth</strong>
            <p>
              {comparisonPreview !== null
                ? `Route preview data is bundle-backed for vehicle ${comparisonPreview.vehicleId}.`
                : "No route preview is active, so only bundle alerts and diagnostics are shown."}
            </p>
          </article>
        </div>
      </section>
    </section>
  );
}

function compareRouteContext(
  preview: LiveRoutePreviewViewModel,
  inspection: LiveBundleViewModel["commandCenter"]["vehicleInspections"][number] | null,
): { matching: boolean; explanation: string } {
  if (inspection === null) {
    return {
      matching: false,
      explanation: `Preview points to node ${preview.destinationNodeId}, but no inspection is available to compare against.`,
    };
  }

  const destinationAligned =
    inspection.routeAheadNodeIds.length > 0 ? inspection.routeAheadNodeIds[inspection.routeAheadNodeIds.length - 1] === preview.destinationNodeId : false;
  const previewNodeCount = preview.nodeIds.length;
  const inspectionNodeCount = inspection.routeAheadNodeIds.length;
  const matching = destinationAligned && previewNodeCount > 0;

  return {
    matching,
    explanation: matching
      ? `Preview destination node ${preview.destinationNodeId} aligns with the inspection route-ahead tail, based on ${previewNodeCount} preview node(s) and ${inspectionNodeCount} inspection node(s).`
      : `Preview destination node ${preview.destinationNodeId} does not line up with the current inspection route-ahead tail; preview has ${previewNodeCount} node(s) and inspection has ${inspectionNodeCount} node(s).`,
  };
}

function summarizeSeverityCounts(diagnostics: Array<{ severity: string }>): Record<SeverityBucket, number> {
  const counts: Record<SeverityBucket, number> = {
    info: 0,
    warn: 0,
    error: 0,
  };

  for (const diagnostic of diagnostics) {
    const severity = severityToken(diagnostic.severity);
    counts[severity] += 1;
  }

  return counts;
}

function severityToken(value: string): SeverityBucket {
  const normalized = value.trim().toLowerCase();
  if (normalized.includes("error") || normalized.includes("critical") || normalized.includes("fail")) {
    return "error";
  }
  if (normalized.includes("warn") || normalized.includes("caution") || normalized.includes("advis")) {
    return "warn";
  }
  return "info";
}
