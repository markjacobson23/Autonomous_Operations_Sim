import { frontendOwnedState, frontendV2Home, repoLayoutDecision, simulatorOwnedTruth } from "../architecture";
import type { LiveBundleViewModel } from "../adapters/liveBundle";
import type { FrontendModeId, FrontendUiActions, FrontendUiState } from "../state/frontendUiState";
import { MapShell } from "./MapShell";

type FrontendShellProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  actions: FrontendUiActions;
};

const modeDetails: Array<{ id: FrontendModeId; label: string; summary: string }> = [
  { id: "operate", label: "Operate", summary: "Live watch and intervention surface" },
  { id: "traffic", label: "Traffic", summary: "Congestion and blockage context" },
  { id: "fleet", label: "Fleet", summary: "Vehicle-focused overview" },
  { id: "editor", label: "Editor", summary: "Authoring entry point" },
  { id: "analyze", label: "Analyze", summary: "Diagnostics and explanation" },
];

export function FrontendShell({ bundle, uiState, actions }: FrontendShellProps): JSX.Element {

  return (
    <div className="app-shell">
      <header className="shell-header">
        <div className="shell-title-block">
          <p className="eyebrow">Frontend v2 live shell</p>
          <h1>Autonomous Ops</h1>
          <p className="shell-subtitle">Live mining session surface driven by authoritative simulator bundles.</p>
        </div>

        <div className="shell-status-cluster">
          <div className="status-badge status-badge-emphasis">{connectionLabel(bundle.loadState)}</div>
          <div className="status-badge">Bundle: {bundle.sessionIdentity.surfaceName}</div>
          <div className="status-badge">Scenario: {bundle.sessionIdentity.scenarioName}</div>
          <div className="status-badge">Mode: {uiState.modePanel.activeMode}</div>
        </div>

        <div className="mode-switcher" role="tablist" aria-label="Frontend modes">
          {modeDetails.map((mode) => (
            <button
              key={mode.id}
              type="button"
              className={`mode-button ${uiState.modePanel.activeMode === mode.id ? "mode-button-active" : ""}`}
              onClick={() => actions.setMode(mode.id)}
              aria-pressed={uiState.modePanel.activeMode === mode.id}
            >
              <strong>{mode.label}</strong>
              <span>{mode.summary}</span>
            </button>
          ))}
        </div>
      </header>

      <section className={`global-alert ${bundle.loadState === "error" ? "global-alert-error" : ""}`} aria-live="polite">
        <strong>{bundle.loadState === "error" ? "Connection problem" : "Live status"}</strong>
        <span>{bundle.loadMessage}</span>
        <span>{bundle.alerts.length > 0 ? bundle.alerts.join(" · ") : "No active alerts"}</span>
      </section>

      <main className="shell-grid">
        <MapShell bundle={bundle} uiState={uiState} actions={actions} />

        <aside className="shell-rail">
          <section className="panel">
            <h2>Session identity</h2>
            <dl className="info-grid">
              <div>
                <dt>Scenario</dt>
                <dd>{bundle.sessionIdentity.scenarioPath}</dd>
              </div>
              <div>
                <dt>Surface</dt>
                <dd>{bundle.sessionIdentity.surfaceName}</dd>
              </div>
              <div>
                <dt>API version</dt>
                <dd>{bundle.sessionIdentity.apiVersion}</dd>
              </div>
              <div>
                <dt>Play state</dt>
                <dd>{bundle.sessionIdentity.playState}</dd>
              </div>
              <div>
                <dt>Step size</dt>
                <dd>{bundle.sessionIdentity.stepSeconds}</dd>
              </div>
              <div>
                <dt>Sim time</dt>
                <dd>{bundle.sessionIdentity.simulatedTime}</dd>
              </div>
            </dl>
          </section>

          <section className="panel">
            <h2>Connection state</h2>
            <div className="stack-copy">
              <p className="status-line">
                <strong>{connectionLabel(bundle.loadState)}</strong>
                <span>{bundle.bundleUrl}</span>
              </p>
              <p>{bundle.loadMessage}</p>
            </div>
          </section>

          <section className="panel">
            <h2>Global alerts</h2>
            <ul className="list-copy">
              {bundle.alerts.length > 0 ? (
                bundle.alerts.map((alert) => <li key={alert}>{alert}</li>)
              ) : (
                <li>No active alerts.</li>
              )}
            </ul>
          </section>

          <section className="panel">
            <h2>Inspector</h2>
            <p className="stack-copy">
              Reserved for selection-scoped inspection. Step 43 keeps the shell visible while the interaction model remains out of scope.
            </p>
            <ul className="list-copy">
              <li>Current mode: {uiState.modePanel.activeMode}</li>
              <li>Vehicles visible: {bundle.map.vehicles.length}</li>
              <li>Blocked edges: {bundle.map.blockedEdgeIds.length}</li>
              <li>Viewport: {describeViewport(uiState)}</li>
            </ul>
          </section>

          <section className="panel">
            <h2>Command surface</h2>
            <p className="stack-copy">
              Reserved for typed preview and commit workflows. The live transport already exists in the backend; the UI interaction model comes next.
            </p>
            <ul className="list-copy">
              <li>
                Session control endpoint: <code>{bundle.commandSurface.sessionControlEndpoint}</code>
              </li>
              <li>
                Command endpoint: <code>{bundle.commandSurface.commandEndpoint}</code>
              </li>
              <li>
                Preview endpoint: <code>{bundle.commandSurface.previewEndpoint}</code>
              </li>
            </ul>
          </section>

          <section className="panel">
            <h2>Utility surfaces</h2>
            <ul className="list-copy">
              <li>Mode switching is local-only in this step.</li>
              <li>Frontend-owned state: {frontendOwnedState.join(", ")}.</li>
              <li>Simulator-owned truth: {simulatorOwnedTruth.join(", ")}.</li>
              <li>Repo home: <code>{frontendV2Home}</code></li>
            </ul>
            <div className="mini-summary">
              {repoLayoutDecision.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}

function connectionLabel(loadState: LiveBundleViewModel["loadState"]): string {
  if (loadState === "ready") {
    return "Connected";
  }
  if (loadState === "error") {
    return "Connection error";
  }
  return "Connecting";
}

function describeViewport(uiState: FrontendUiState): string {
  const { x, y, zoom, sceneViewMode } = uiState.camera;
  return `${sceneViewMode} @ ${x.toFixed(1)}, ${y.toFixed(1)} · ${zoom.toFixed(2)}x`;
}
