import { useEffect, useState } from "react";

type BootstrapSummary = {
  loadState: "idle" | "loading" | "loaded" | "error";
  surfaceName: string;
  seed: number | null;
  simulatedTimeS: number | null;
  vehicleCount: number | null;
  blockedEdgeCount: number | null;
  traceEventCount: number | null;
  selectedVehicleCount: number | null;
  recentCommandCount: number | null;
  suggestionCount: number | null;
  anomalyCount: number | null;
  routePreviewCount: number | null;
  message: string;
  commandCenter: CommandCenterPayload;
  summary: BundleSummaryPayload | null;
};

type BundleSummaryPayload = {
  completed_job_count?: number;
  completed_task_count?: number;
  trace_event_count?: number;
} | null;

type CommandCenterPayload = {
  selected_vehicle_ids?: number[];
  recent_commands?: string[];
  route_previews?: RoutePreviewPayload[];
  vehicle_inspections?: VehicleInspectionPayload[];
  ai_assist?: AIAssistPayload;
};

type RoutePreviewPayload = {
  vehicle_id?: number;
  destination_node_id?: number;
  is_actionable?: boolean;
  reason?: string | null;
  total_distance?: number;
  node_ids?: number[];
};

type VehicleInspectionPayload = {
  vehicle_id?: number;
  operational_state?: string;
  current_node_id?: number;
  current_job_id?: string | null;
  wait_reason?: string | null;
  eta_s?: number | null;
  diagnostics?: DiagnosticPayload[];
};

type DiagnosticPayload = {
  code?: string;
  severity?: string;
  message?: string;
};

type AIAssistPayload = {
  explanations?: ExplanationPayload[];
  suggestions?: SuggestionPayload[];
  anomalies?: AnomalyPayload[];
};

type ExplanationPayload = {
  vehicle_id?: number;
  summary?: string;
};

type SuggestionPayload = {
  suggestion_id?: string;
  kind?: string;
  priority?: string;
  summary?: string;
  target_vehicle_id?: number | null;
  target_edge_id?: number | null;
};

type AnomalyPayload = {
  anomaly_id?: string;
  severity?: string;
  summary?: string;
  vehicle_id?: number | null;
};

type BundlePayload = {
  metadata?: { surface_name?: string };
  seed?: number;
  simulated_time_s?: number;
  trace_events?: unknown[];
  summary?: BundleSummaryPayload;
  command_center?: CommandCenterPayload;
  snapshot?: {
    simulated_time_s?: number;
    blocked_edge_ids?: unknown[];
    vehicles?: unknown[];
  };
};

const architecture = {
  primaryStack: "React + TypeScript + Vite",
  authority: "Python simulator remains authoritative",
  launchMode: "Live session bootstrap through versioned bundle surfaces",
};

const sessionActions = [
  "Launch Live Run",
  "Reconnect Bundle",
  "Focus Selected Vehicle",
  "Open Timeline",
];

function App(): JSX.Element {
  const [bootstrap, setBootstrap] = useState<BootstrapSummary>({
    loadState: "idle",
    surfaceName: "unbound",
    seed: null,
    simulatedTimeS: null,
    vehicleCount: null,
    blockedEdgeCount: null,
    traceEventCount: null,
    selectedVehicleCount: null,
    recentCommandCount: null,
    suggestionCount: null,
    anomalyCount: null,
    routePreviewCount: null,
    message: "No live bundle is connected yet.",
    commandCenter: {},
    summary: null,
  });

  useEffect(() => {
    const bundlePath = new URLSearchParams(window.location.search).get("bundle");
    if (!bundlePath) {
      return;
    }

    let cancelled = false;
    setBootstrap((current) => ({
      ...current,
      loadState: "loading",
      message: `Loading live bundle from ${bundlePath}`,
    }));

    void fetch(bundlePath)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Bundle request failed with ${response.status}`);
        }
        return response.json() as Promise<BundlePayload>;
      })
      .then((bundle) => {
        if (cancelled) {
          return;
        }
        const snapshot = bundle.snapshot ?? {};
        const commandCenter = bundle.command_center ?? {};
        const aiAssist = commandCenter.ai_assist ?? {};
        const summary = bundle.summary ?? null;

        setBootstrap({
          loadState: "loaded",
          surfaceName: bundle.metadata?.surface_name ?? "unknown_surface",
          seed: bundle.seed ?? null,
          simulatedTimeS: bundle.simulated_time_s ?? snapshot.simulated_time_s ?? null,
          vehicleCount: Array.isArray(snapshot.vehicles) ? snapshot.vehicles.length : null,
          blockedEdgeCount: Array.isArray(snapshot.blocked_edge_ids)
            ? snapshot.blocked_edge_ids.length
            : null,
          traceEventCount: Array.isArray(bundle.trace_events)
            ? bundle.trace_events.length
            : summary?.trace_event_count ?? null,
          selectedVehicleCount: Array.isArray(commandCenter.selected_vehicle_ids)
            ? commandCenter.selected_vehicle_ids.length
            : null,
          recentCommandCount: Array.isArray(commandCenter.recent_commands)
            ? commandCenter.recent_commands.length
            : null,
          suggestionCount: Array.isArray(aiAssist.suggestions)
            ? aiAssist.suggestions.length
            : null,
          anomalyCount: Array.isArray(aiAssist.anomalies)
            ? aiAssist.anomalies.length
            : null,
          routePreviewCount: Array.isArray(commandCenter.route_previews)
            ? commandCenter.route_previews.length
            : null,
          message: "Live bundle bootstrap connected.",
          commandCenter,
          summary,
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message = error instanceof Error ? error.message : "Unknown bootstrap error";
        setBootstrap({
          loadState: "error",
          surfaceName: "bootstrap_failed",
          seed: null,
          simulatedTimeS: null,
          vehicleCount: null,
          blockedEdgeCount: null,
          traceEventCount: null,
          selectedVehicleCount: null,
          recentCommandCount: null,
          suggestionCount: null,
          anomalyCount: null,
          routePreviewCount: null,
          message,
          commandCenter: {},
          summary: null,
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const routePreviews = bootstrap.commandCenter.route_previews ?? [];
  const inspections = bootstrap.commandCenter.vehicle_inspections ?? [];
  const recentCommands = bootstrap.commandCenter.recent_commands ?? [];
  const suggestions = bootstrap.commandCenter.ai_assist?.suggestions ?? [];
  const anomalies = bootstrap.commandCenter.ai_assist?.anomalies ?? [];
  const explanations = bootstrap.commandCenter.ai_assist?.explanations ?? [];

  return (
    <div className="shell">
      <header className="masthead panel">
        <div className="masthead-copy">
          <p className="eyebrow">Step 43 Operator Shell</p>
          <h1>Autonomous Ops Command Deck</h1>
          <p className="lede">
            The serious frontend now has a real operator-facing frame with live
            metadata, command-center regions, inspection space, alerts, and a
            timeline dock, while scene interaction stays reserved for the next step.
          </p>
        </div>
        <div className="masthead-meta">
          <div className="badge-row" aria-label="Architecture decisions">
            <span className="badge">Primary: {architecture.primaryStack}</span>
            <span className="badge">Authority: Python simulator</span>
            <span className="badge accent-2">{architecture.launchMode}</span>
          </div>
          <div className="toolbar-strip" aria-label="Top toolbar">
            {sessionActions.map((action) => (
              <button key={action} className="toolbar-button" type="button">
                {action}
              </button>
            ))}
          </div>
        </div>
      </header>

      <section className="session-bar panel" aria-label="Session metadata">
        <div className="metric-pill">
          <span className="metric-label">Bundle</span>
          <strong>{bootstrap.surfaceName}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Seed</span>
          <strong>{formatMaybeNumber(bootstrap.seed)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Simulated Time</span>
          <strong>{formatSeconds(bootstrap.simulatedTimeS)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Vehicles</span>
          <strong>{formatMaybeNumber(bootstrap.vehicleCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Blocked Edges</span>
          <strong>{formatMaybeNumber(bootstrap.blockedEdgeCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Trace Events</span>
          <strong>{formatMaybeNumber(bootstrap.traceEventCount)}</strong>
        </div>
        <div className={`health-pill health-pill-${bootstrap.loadState}`}>
          {bootstrap.loadState.toUpperCase()}
        </div>
      </section>

      <main className="workspace">
        <section className="main-column">
          <section className="stage panel" aria-labelledby="scene-title">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Scene Region</p>
                <h2 id="scene-title">Operations Viewport</h2>
              </div>
              <div className="status-stack">
                <span className="status-pill">SVG scene baseline</span>
                <span className="status-pill secondary">Minimap placeholder ready</span>
              </div>
            </div>
            <div className="stage-grid">
              <div className="stage-canvas" role="img" aria-label="Placeholder scene">
                <div className="grid-overlay" />
                <div className="scene-routes">
                  <span className="route-chip route-chip-primary">Haul corridor</span>
                  <span className="route-chip route-chip-secondary">Loading loop</span>
                  <span className="route-chip route-chip-alert">Blocked edge watch</span>
                </div>
                <div className="focus-card">
                  <strong>Viewport reserved for Step 44 camera controls</strong>
                  <p>
                    This region already sits inside the real shell layout, with room
                    for scene graph layers, fit-to-scene, and direct selection next.
                  </p>
                </div>
              </div>
              <aside className="overview-panel">
                <div className="overview-card">
                  <p className="eyebrow">Overview</p>
                  <h3>Minimap / Scene Summary</h3>
                  <p>
                    Mining scene overview placeholder with reserved space for map
                    extent, camera box, and quick navigation.
                  </p>
                </div>
                <div className="overview-card">
                  <p className="eyebrow">Session Status</p>
                  <ul className="mini-list">
                    <li>{bootstrap.message}</li>
                    <li>{inspections.length} inspection record(s) available</li>
                    <li>{routePreviews.length} route preview(s) available</li>
                  </ul>
                </div>
              </aside>
            </div>
          </section>

          <section className="timeline-region panel" aria-labelledby="timeline-title">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Timeline Region</p>
                <h2 id="timeline-title">Playback and Session Timeline</h2>
              </div>
              <span className="status-pill secondary">Docked placeholder</span>
            </div>
            <div className="timeline-body">
              <div className="timeline-track">
                <div className="timeline-fill" />
              </div>
              <div className="timeline-metrics">
                <div className="timeline-card">
                  <span className="metric-label">Completed Jobs</span>
                  <strong>
                    {formatMaybeNumber(bootstrap.summary?.completed_job_count ?? null)}
                  </strong>
                </div>
                <div className="timeline-card">
                  <span className="metric-label">Completed Tasks</span>
                  <strong>
                    {formatMaybeNumber(bootstrap.summary?.completed_task_count ?? null)}
                  </strong>
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
        </section>

        <aside className="sidebar">
          <section className="panel info-panel" aria-labelledby="command-center-title">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Command-Center Region</p>
                <h2 id="command-center-title">Fleet Actions</h2>
              </div>
              <span className="status-pill secondary">
                {formatMaybeNumber(bootstrap.selectedVehicleCount)} selected
              </span>
            </div>
            <div className="section-stack">
              <div className="subsection">
                <h3>Recent Commands</h3>
                <ul className="data-list">
                  {recentCommands.length > 0 ? (
                    recentCommands.slice(0, 4).map((command, index) => (
                      <li key={`${command}-${index}`}>{command}</li>
                    ))
                  ) : (
                    <li>No command history is available yet.</li>
                  )}
                </ul>
              </div>
              <div className="subsection">
                <h3>Route Previews</h3>
                <ul className="data-list">
                  {routePreviews.length > 0 ? (
                    routePreviews.slice(0, 3).map((preview, index) => (
                      <li key={`${preview.vehicle_id ?? "vehicle"}-${index}`}>
                        Vehicle {formatMaybeNumber(preview.vehicle_id ?? null)} to node{" "}
                        {formatMaybeNumber(preview.destination_node_id ?? null)}
                        {" · "}
                        {preview.reason ?? (preview.is_actionable ? "actionable" : "queued")}
                      </li>
                    ))
                  ) : (
                    <li>No route previews are currently attached.</li>
                  )}
                </ul>
              </div>
            </div>
          </section>

          <section className="panel info-panel" aria-labelledby="inspector-title">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Inspector Region</p>
                <h2 id="inspector-title">Vehicle Inspection</h2>
              </div>
              <span className="status-pill secondary">{inspections.length} records</span>
            </div>
            <div className="section-stack">
              {inspections.length > 0 ? (
                inspections.slice(0, 2).map((inspection, index) => (
                  <article
                    key={`${inspection.vehicle_id ?? "inspection"}-${index}`}
                    className="inspection-card"
                  >
                    <div className="inspection-header">
                      <strong>Vehicle {formatMaybeNumber(inspection.vehicle_id ?? null)}</strong>
                      <span>{inspection.operational_state ?? "unknown_state"}</span>
                    </div>
                    <ul className="mini-list">
                      <li>Node: {formatMaybeNumber(inspection.current_node_id ?? null)}</li>
                      <li>ETA: {formatSeconds(inspection.eta_s ?? null)}</li>
                      <li>Job: {inspection.current_job_id ?? "none"}</li>
                      <li>Wait: {inspection.wait_reason ?? "none"}</li>
                    </ul>
                    <div className="diagnostic-row">
                      {(inspection.diagnostics ?? []).slice(0, 2).map((diagnostic, diagIndex) => (
                        <span
                          key={`${diagnostic.code ?? "diag"}-${diagIndex}`}
                          className="diagnostic-pill"
                        >
                          {(diagnostic.severity ?? "info").toUpperCase()}:{" "}
                          {diagnostic.code ?? "diagnostic"}
                        </span>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty-state">
                  Inspection surfaces will populate here once a live session carries
                  selected vehicles and runtime diagnostics.
                </div>
              )}
            </div>
          </section>

          <section className="panel info-panel" aria-labelledby="alerts-title">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Alerts Region</p>
                <h2 id="alerts-title">AI and Operational Alerts</h2>
              </div>
              <span className="status-pill secondary">
                {formatMaybeNumber(bootstrap.anomalyCount)} anomalies
              </span>
            </div>
            <div className="section-stack">
              <div className="subsection">
                <h3>Suggestions</h3>
                <ul className="data-list">
                  {suggestions.length > 0 ? (
                    suggestions.slice(0, 3).map((suggestion) => (
                      <li key={suggestion.suggestion_id ?? suggestion.summary ?? "suggestion"}>
                        {suggestion.kind ?? "suggestion"} · {suggestion.summary ?? "No summary"}
                      </li>
                    ))
                  ) : (
                    <li>No actionable suggestions are currently attached.</li>
                  )}
                </ul>
              </div>
              <div className="subsection">
                <h3>Anomalies</h3>
                <ul className="data-list">
                  {anomalies.length > 0 ? (
                    anomalies.slice(0, 3).map((anomaly) => (
                      <li key={anomaly.anomaly_id ?? anomaly.summary ?? "anomaly"}>
                        {(anomaly.severity ?? "info").toUpperCase()} ·{" "}
                        {anomaly.summary ?? "No anomaly summary"}
                      </li>
                    ))
                  ) : (
                    <li>No anomalies are currently attached.</li>
                  )}
                </ul>
              </div>
              <div className="subsection">
                <h3>Explanations</h3>
                <ul className="data-list">
                  {explanations.length > 0 ? (
                    explanations.slice(0, 2).map((explanation, index) => (
                      <li key={`${explanation.vehicle_id ?? "explanation"}-${index}`}>
                        Vehicle {formatMaybeNumber(explanation.vehicle_id ?? null)} ·{" "}
                        {explanation.summary ?? "No explanation summary"}
                      </li>
                    ))
                  ) : (
                    <li>No AI explanations are currently attached.</li>
                  )}
                </ul>
              </div>
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}

function formatMaybeNumber(value: number | null): string {
  return value === null ? "pending" : String(value);
}

function formatSeconds(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(1)}s`;
}

export default App;
