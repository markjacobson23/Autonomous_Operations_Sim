import { useEffect, useState } from "react";

import { frontendOwnedState, frontendV2Home, repoLayoutDecision, simulatorOwnedTruth } from "./architecture";
import "./app-shell.css";

type JsonRecord = Record<string, unknown>;
type ModeId = "operate" | "traffic" | "fleet" | "editor" | "analyze";
type LoadState = "loading" | "ready" | "error";
type Point2 = readonly [number, number];

const modeDetails: Array<{ id: ModeId; label: string; summary: string }> = [
  { id: "operate", label: "Operate", summary: "Live watch and intervention surface" },
  { id: "traffic", label: "Traffic", summary: "Congestion and blockage context" },
  { id: "fleet", label: "Fleet", summary: "Vehicle-focused overview" },
  { id: "editor", label: "Editor", summary: "Authoring entry point" },
  { id: "analyze", label: "Analyze", summary: "Diagnostics and explanation" },
];

function App(): JSX.Element {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [bundle, setBundle] = useState<JsonRecord | null>(null);
  const [loadMessage, setLoadMessage] = useState("Connecting to live session bundle...");
  const [activeMode, setActiveMode] = useState<ModeId>("operate");

  useEffect(() => {
    const controller = new AbortController();
    const bundlePath = new URLSearchParams(window.location.search).get("bundle") ?? "/live_session_bundle.json";
    const resolvedBundleUrl = new URL(bundlePath, window.location.href).toString();

    async function loadBundle() {
      setLoadState("loading");
      setLoadMessage(`Connecting to ${bundlePath}...`);
      try {
        const response = await fetch(resolvedBundleUrl, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }

        const payload: unknown = await response.json();
        if (!isRecord(payload)) {
          throw new Error("Live bundle did not decode to an object");
        }

        setBundle(payload);
        setLoadState("ready");
        setLoadMessage("Live session connected");
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setBundle(null);
        setLoadState("error");
        setLoadMessage(error instanceof Error ? error.message : "Unable to load live bundle");
      }
    }

    void loadBundle();
    return () => controller.abort();
  }, []);

  const metadata = readRecord(bundle, "metadata");
  const authoring = readRecord(bundle, "authoring");
  const sessionControl = readRecord(bundle, "session_control");
  const commandCenter = readRecord(bundle, "command_center");
  const snapshot = readRecord(bundle, "snapshot");
  const renderGeometry = readRecord(bundle, "render_geometry");
  const trafficBaseline = readRecord(bundle, "traffic_baseline");
  const aiAssist = readRecord(commandCenter, "ai_assist");

  const roads = readArray(renderGeometry, "roads").flatMap((road) => {
    const roadRecord = isRecord(road) ? road : null;
    return roadRecord !== null ? [roadRecord] : [];
  });
  const vehicles = readArray(snapshot, "vehicles").flatMap((vehicle) => {
    const vehicleRecord = isRecord(vehicle) ? vehicle : null;
    return vehicleRecord !== null ? [vehicleRecord] : [];
  });
  const blockedEdgeIds = readNumberArray(snapshot, "blocked_edge_ids");
  const trafficRoadStates = readArray(trafficBaseline, "road_states").flatMap((entry) => {
    const roadState = isRecord(entry) ? entry : null;
    return roadState !== null ? [roadState] : [];
  });
  const anomalies = readArray(aiAssist, "anomalies").flatMap((entry) => {
    const anomaly = isRecord(entry) ? entry : null;
    return anomaly !== null ? [anomaly] : [];
  });
  const alerts = [
    ...(blockedEdgeIds.length > 0 ? [`${blockedEdgeIds.length} blocked edge(s)`] : []),
    ...(trafficRoadStates.some((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2)
      ? [`${trafficRoadStates.filter((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2).length} congested road(s)`]
      : []),
    ...(anomalies.length > 0 ? [`${anomalies.length} anomaly signal(s)`] : []),
  ];

  const points = collectScenePoints(bundle);
  const bounds = padBounds(computeBounds(points), 2.0);
  const scenarioPath = readString(authoring, "source_scenario_path", "unknown scenario");
  const scenarioName = scenarioPath.split("/").pop()?.replace(/\.json$/u, "") ?? "live session";
  const surfaceName = readString(metadata, "surface_name", "live_session_bundle");
  const seedValue = readNumber(bundle, "seed", Number.NaN);
  const simulatedTimeS = readNumber(bundle, "simulated_time_s", Number.NaN);
  const apiVersion = readNumber(metadata, "api_version", Number.NaN);
  const playState = readString(sessionControl, "play_state", "paused");
  const stepSeconds = readNumber(sessionControl, "step_seconds", Number.NaN);
  const bundleUrl = new URLSearchParams(window.location.search).get("bundle") ?? "/live_session_bundle.json";

  return (
    <div className="app-shell">
      <header className="shell-header">
        <div className="shell-title-block">
          <p className="eyebrow">Frontend v2 live shell</p>
          <h1>Autonomous Ops</h1>
          <p className="shell-subtitle">
            Live mining session surface driven by authoritative simulator bundles.
          </p>
        </div>

        <div className="shell-status-cluster">
          <div className="status-badge status-badge-emphasis">{connectionLabel(loadState)}</div>
          <div className="status-badge">Bundle: {surfaceName}</div>
          <div className="status-badge">Scenario: {scenarioName}</div>
          <div className="status-badge">Mode: {activeMode}</div>
        </div>

        <div className="mode-switcher" role="tablist" aria-label="Frontend modes">
          {modeDetails.map((mode) => (
            <button
              key={mode.id}
              type="button"
              className={`mode-button ${activeMode === mode.id ? "mode-button-active" : ""}`}
              onClick={() => setActiveMode(mode.id)}
              aria-pressed={activeMode === mode.id}
            >
              <strong>{mode.label}</strong>
              <span>{mode.summary}</span>
            </button>
          ))}
        </div>
      </header>

      <section className={`global-alert ${loadState === "error" ? "global-alert-error" : ""}`} aria-live="polite">
        <strong>{loadState === "error" ? "Connection problem" : "Live status"}</strong>
        <span>{loadMessage}</span>
        <span>{alerts.length > 0 ? alerts.join(" · ") : "No active alerts"}</span>
      </section>

      <main className="shell-grid">
        <section className="map-panel panel">
          <div className="panel-topline">
            <div>
              <p className="panel-kicker">Main map</p>
              <h2>Live scene</h2>
            </div>
            <div className="panel-metrics">
              <span>{roads.length} roads</span>
              <span>{vehicles.length} vehicles</span>
              <span>{formatNumber(seedValue, "seed pending")}</span>
            </div>
          </div>

          <div className="map-stage" aria-label="Live map region">
            {loadState === "ready" && bundle !== null ? (
              <svg
                className="map-canvas"
                viewBox={`${bounds.minX} ${bounds.minY} ${bounds.width} ${bounds.height}`}
                role="img"
                aria-label="Authoritative live map view"
                preserveAspectRatio="xMidYMid meet"
              >
                <defs>
                  <pattern id="grid" width="12" height="12" patternUnits="userSpaceOnUse">
                    <path d="M 12 0 L 0 0 0 12" fill="none" stroke="rgba(39, 52, 58, 0.08)" strokeWidth="0.5" />
                  </pattern>
                </defs>
                <rect x={bounds.minX} y={bounds.minY} width={bounds.width} height={bounds.height} fill="url(#grid)" />
                {roads.map((road, index) => {
                  const roadId = readString(road, "road_id", `road-${index}`);
                  const centerline = readPositionList(readArray(road, "centerline"));
                  if (centerline.length < 2) {
                    return null;
                  }
                  const blocked = readNumberArray(road, "edge_ids").some((edgeId) => blockedEdgeIds.includes(edgeId));
                  return (
                    <g key={roadId}>
                      <path
                        d={pointsToPath(centerline)}
                        className={blocked ? "road-path road-path-blocked" : "road-path"}
                      />
                      <path d={pointsToPath(centerline)} className="road-path road-path-glow" />
                    </g>
                  );
                })}
                {vehicles.map((vehicle, index) => {
                  const position = readPoint(readArray(vehicle, "position"));
                  if (position === null) {
                    return null;
                  }
                  const vehicleId = readNumber(vehicle, "vehicle_id", index + 1);
                  const state = readString(vehicle, "operational_state", "idle");
                  return (
                    <g key={vehicleId} transform={`translate(${position[0]} ${position[1]})`}>
                      <circle className={`vehicle-core vehicle-core-${vehicleStateClass(state)}`} r="0.55" />
                      <circle className="vehicle-halo" r="0.95" />
                      <text className="vehicle-label" y="-1.1" textAnchor="middle">
                        {vehicleLabel(vehicleId, state)}
                      </text>
                    </g>
                  );
                })}
              </svg>
            ) : (
              <div className="map-loading">
                <strong>{loadState === "error" ? "Map unavailable" : "Loading live map..."}</strong>
                <span>{loadState === "error" ? loadMessage : "Waiting for the authoritative bundle."}</span>
              </div>
            )}
          </div>

          <div className="map-legend">
            <span>Visual contract: roads, vehicles, and environment form only.</span>
            <span>Selection workflows arrive in the next step.</span>
          </div>
        </section>

        <aside className="shell-rail">
          <section className="panel">
            <h2>Session identity</h2>
            <dl className="info-grid">
              <div>
                <dt>Scenario</dt>
                <dd>{scenarioPath}</dd>
              </div>
              <div>
                <dt>Surface</dt>
                <dd>{surfaceName}</dd>
              </div>
              <div>
                <dt>API version</dt>
                <dd>{Number.isNaN(apiVersion) ? "unknown" : String(apiVersion)}</dd>
              </div>
              <div>
                <dt>Play state</dt>
                <dd>{playState}</dd>
              </div>
              <div>
                <dt>Step size</dt>
                <dd>{Number.isNaN(stepSeconds) ? "unknown" : `${stepSeconds.toFixed(1)}s`}</dd>
              </div>
              <div>
                <dt>Sim time</dt>
                <dd>{Number.isNaN(simulatedTimeS) ? "pending" : `${simulatedTimeS.toFixed(1)}s`}</dd>
              </div>
            </dl>
          </section>

          <section className="panel">
            <h2>Connection state</h2>
            <div className="stack-copy">
              <p className="status-line">
                <strong>{connectionLabel(loadState)}</strong>
                <span>{bundleUrl}</span>
              </p>
              <p>{loadMessage}</p>
            </div>
          </section>

          <section className="panel">
            <h2>Global alerts</h2>
            <ul className="list-copy">
              {alerts.length > 0 ? (
                alerts.map((alert) => <li key={alert}>{alert}</li>)
              ) : (
                <li>No active alerts.</li>
              )}
            </ul>
          </section>

          <section className="panel">
            <h2>Inspector</h2>
            <p className="stack-copy">
              Reserved for selection-scoped inspection. Step 42 only exposes the shell and
              authoritative session identity.
            </p>
            <ul className="list-copy">
              <li>Current mode: {activeMode}</li>
              <li>Vehicles visible: {vehicles.length}</li>
              <li>Blocked edges: {blockedEdgeIds.length}</li>
            </ul>
          </section>

          <section className="panel">
            <h2>Command surface</h2>
            <p className="stack-copy">
              Reserved for typed preview and commit workflows. The live transport already exists
              in the backend; the UI interaction model comes next.
            </p>
            <ul className="list-copy">
              <li>Session control endpoint: <code>{stringOrUnknown(sessionControl, "session_control_endpoint")}</code></li>
              <li>Command endpoint: <code>{stringOrUnknown(sessionControl, "command_endpoint")}</code></li>
              <li>Preview endpoint: <code>{stringOrUnknown(sessionControl, "route_preview_endpoint")}</code></li>
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

function connectionLabel(loadState: LoadState): string {
  if (loadState === "ready") {
    return "Connected";
  }
  if (loadState === "error") {
    return "Connection error";
  }
  return "Connecting";
}

function vehicleStateClass(state: string): string {
  const normalized = state.toLowerCase();
  if (normalized.includes("wait") || normalized.includes("queue")) {
    return "waiting";
  }
  if (normalized.includes("move")) {
    return "moving";
  }
  return "idle";
}

function vehicleLabel(vehicleId: number, state: string): string {
  return `${vehicleId} · ${state}`;
}

function formatNumber(value: number, fallback: string): string {
  return Number.isNaN(value) ? fallback : String(value);
}

function stringOrUnknown(record: JsonRecord | null, key: string): string {
  return readString(record, key, "unknown");
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readRecord(value: JsonRecord | null, key: string): JsonRecord | null {
  if (value === null) {
    return null;
  }
  const nested = value[key];
  return isRecord(nested) ? nested : null;
}

function readArray(value: JsonRecord | null, key: string): unknown[] {
  if (value === null) {
    return [];
  }
  const nested = value[key];
  return Array.isArray(nested) ? nested : [];
}

function readString(value: JsonRecord | null | undefined, key: string, fallback: string): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  const nested = value[key];
  return typeof nested === "string" && nested.trim().length > 0 ? nested : fallback;
}

function readNumber(value: JsonRecord | null | undefined, key: string, fallback: number): number {
  if (value === null || value === undefined) {
    return fallback;
  }
  const nested = value[key];
  return typeof nested === "number" && Number.isFinite(nested) ? nested : fallback;
}

function readNumberArray(value: JsonRecord | null, key: string): number[] {
  return readArray(value, key).flatMap((entry) => (typeof entry === "number" && Number.isFinite(entry) ? [entry] : []));
}

function readPoint(value: unknown): Point2 | null {
  if (!Array.isArray(value) || value.length < 2) {
    return null;
  }
  const [x, y] = value;
  if (typeof x !== "number" || typeof y !== "number") {
    return null;
  }
  return [x, y];
}

function readPositionList(points: unknown[]): Point2[] {
  return points.flatMap((point) => {
    const resolved = readPoint(point);
    return resolved === null ? [] : [resolved];
  });
}

function collectScenePoints(bundle: JsonRecord | null): Point2[] {
  const points: Point2[] = [];
  const renderGeometry = readRecord(bundle, "render_geometry");
  const snapshot = readRecord(bundle, "snapshot");

  for (const road of readArray(renderGeometry, "roads")) {
    if (!isRecord(road)) {
      continue;
    }
    points.push(...readPositionList(readArray(road, "centerline")));
  }

  for (const vehicle of readArray(snapshot, "vehicles")) {
    if (!isRecord(vehicle)) {
      continue;
    }
    const position = readPoint(vehicle.position);
    if (position !== null) {
      points.push(position);
    }
  }

  if (points.length === 0) {
    return [
      [-10, -6],
      [10, 6],
    ];
  }

  return points;
}

function computeBounds(points: Point2[]): { minX: number; minY: number; maxX: number; maxY: number; width: number; height: number } {
  let minX = points[0][0];
  let minY = points[0][1];
  let maxX = points[0][0];
  let maxY = points[0][1];

  for (const [x, y] of points) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: Math.max(maxX - minX, 1),
    height: Math.max(maxY - minY, 1),
  };
}

function padBounds(
  bounds: { minX: number; minY: number; maxX: number; maxY: number; width: number; height: number },
  padding: number,
): { minX: number; minY: number; maxX: number; maxY: number; width: number; height: number } {
  return {
    minX: bounds.minX - padding,
    minY: bounds.minY - padding,
    maxX: bounds.maxX + padding,
    maxY: bounds.maxY + padding,
    width: bounds.width + padding * 2,
    height: bounds.height + padding * 2,
  };
}

function pointsToPath(points: Point2[]): string {
  if (points.length < 2) {
    return "";
  }
  const [first, ...rest] = points;
  const commands = [`M ${first[0]} ${first[1]}`];
  for (const point of rest) {
    commands.push(`L ${point[0]} ${point[1]}`);
  }
  return commands.join(" ");
}

export default App;
