import { useEffect, useRef, useState, type MouseEvent } from "react";

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
  bundle: BundlePayload | null;
};

type ViewportState = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type LayerState = {
  areas: boolean;
  roads: boolean;
  intersections: boolean;
  vehicles: boolean;
  routes: boolean;
  reservations: boolean;
  hazards: boolean;
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
  edge_ids?: number[];
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

type Position3 = [number, number, number];

type RenderGeometryPayload = {
  roads?: RoadPayload[];
  intersections?: IntersectionPayload[];
  areas?: AreaPayload[];
};

type RoadPayload = {
  road_id?: string;
  edge_ids?: number[];
  centerline?: Position3[];
  road_class?: string;
  directionality?: string;
  lane_count?: number;
  width_m?: number;
};

type IntersectionPayload = {
  intersection_id?: string;
  node_id?: number;
  polygon?: Position3[];
  intersection_type?: string;
};

type AreaPayload = {
  area_id?: string;
  kind?: string;
  polygon?: Position3[];
  label?: string | null;
};

type MapSurfacePayload = {
  nodes?: NodePayload[];
  edges?: EdgePayload[];
};

type NodePayload = {
  node_id?: number;
  position?: Position3;
  node_type?: string;
};

type EdgePayload = {
  edge_id?: number;
  start_node_id?: number;
  end_node_id?: number;
  distance?: number;
  speed_limit?: number;
};

type VehicleSnapshotPayload = {
  vehicle_id?: number;
  node_id?: number;
  position?: Position3;
  operational_state?: string;
};

type TrafficBaselinePayload = {
  control_points?: Array<{ edge_id?: number; state?: string }>;
  queue_records?: Array<{ edge_id?: number; vehicle_ids?: number[] }>;
};

type BundlePayload = {
  metadata?: { surface_name?: string };
  seed?: number;
  simulated_time_s?: number;
  trace_events?: unknown[];
  summary?: BundleSummaryPayload;
  command_center?: CommandCenterPayload;
  map_surface?: MapSurfacePayload;
  render_geometry?: RenderGeometryPayload;
  traffic_baseline?: TrafficBaselinePayload;
  snapshot?: {
    simulated_time_s?: number;
    blocked_edge_ids?: number[];
    vehicles?: VehicleSnapshotPayload[];
  };
};

type Bounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

type SelectedTarget =
  | { kind: "vehicle"; vehicleId: number }
  | { kind: "road"; roadId: string }
  | { kind: "queue"; edgeId: number }
  | { kind: "hazard"; edgeId: number };

type HoverTarget = {
  label: string;
  detail: string;
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

const defaultLayers: LayerState = {
  areas: true,
  roads: true,
  intersections: true,
  vehicles: true,
  routes: true,
  reservations: true,
  hazards: true,
};

function App(): JSX.Element {
  const minimapRef = useRef<SVGSVGElement | null>(null);
  const [layers, setLayers] = useState<LayerState>(defaultLayers);
  const [selectedTarget, setSelectedTarget] = useState<SelectedTarget | null>(null);
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
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
    bundle: null,
  });
  const [viewport, setViewport] = useState<ViewportState>({
    x: -20,
    y: -12,
    width: 40,
    height: 24,
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
        const fittedViewport = fitViewportToBundle(bundle);

        setViewport(fittedViewport);
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
          bundle,
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
          bundle: null,
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const bundle = bootstrap.bundle;
  const bounds = computeSceneBounds(bundle);
  const routePreviews = bootstrap.commandCenter.route_previews ?? [];
  const inspections = bootstrap.commandCenter.vehicle_inspections ?? [];
  const recentCommands = bootstrap.commandCenter.recent_commands ?? [];
  const suggestions = bootstrap.commandCenter.ai_assist?.suggestions ?? [];
  const anomalies = bootstrap.commandCenter.ai_assist?.anomalies ?? [];
  const explanations = bootstrap.commandCenter.ai_assist?.explanations ?? [];
  const defaultVehicleId =
    bootstrap.commandCenter.selected_vehicle_ids?.[0] ?? inspections[0]?.vehicle_id ?? null;
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle" ? selectedTarget.vehicleId : defaultVehicleId;
  const selectedVehicle = findVehicleById(bundle, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? inspections.find((inspection) => inspection.vehicle_id === selectedVehicleId) ?? null
    : null;
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedQueueRecord =
    selectedTarget?.kind === "queue"
      ? (bundle?.traffic_baseline?.queue_records ?? []).find(
          (record) => record.edge_id === selectedTarget.edgeId,
        ) ?? null
      : null;
  const selectedHazardEdge =
    selectedTarget?.kind === "hazard"
      ? findEdgeById(bundle?.map_surface?.edges ?? [], selectedTarget.edgeId)
      : null;

  function panView(deltaX: number, deltaY: number): void {
    setViewport((current) => ({
      ...current,
      x: current.x + deltaX * current.width,
      y: current.y + deltaY * current.height,
    }));
  }

  function zoomView(factor: number): void {
    setViewport((current) => {
      const nextWidth = current.width * factor;
      const nextHeight = current.height * factor;
      return {
        x: current.x + (current.width - nextWidth) / 2,
        y: current.y + (current.height - nextHeight) / 2,
        width: nextWidth,
        height: nextHeight,
      };
    });
  }

  function fitScene(): void {
    setViewport(fitViewportToBundle(bundle));
  }

  function focusSelectedVehicle(): void {
    if (!selectedVehicle?.position) {
      return;
    }
    const [x, y] = selectedVehicle.position;
    const nextWidth = Math.max(bounds.width * 0.32, 8);
    const nextHeight = Math.max(bounds.height * 0.32, 6);
    setViewport({
      x: x - nextWidth / 2,
      y: y - nextHeight / 2,
      width: nextWidth,
      height: nextHeight,
    });
  }

  function handleMinimapClick(event: MouseEvent<SVGSVGElement>): void {
    if (!minimapRef.current) {
      return;
    }
    const rect = minimapRef.current.getBoundingClientRect();
    const clickX = (event.clientX - rect.left) / rect.width;
    const clickY = (event.clientY - rect.top) / rect.height;
    const targetX = bounds.minX + clickX * bounds.width;
    const targetY = bounds.minY + clickY * bounds.height;
    setViewport((current) => ({
      ...current,
      x: targetX - current.width / 2,
      y: targetY - current.height / 2,
    }));
  }

  function toggleLayer(layer: keyof LayerState): void {
    setLayers((current) => ({
      ...current,
      [layer]: !current[layer],
    }));
  }

  function selectVehicle(vehicleId: number | undefined): void {
    if (vehicleId === undefined) {
      return;
    }
    setSelectedTarget({ kind: "vehicle", vehicleId });
  }

  function selectRoad(roadId: string | undefined): void {
    if (!roadId) {
      return;
    }
    setSelectedTarget({ kind: "road", roadId });
  }

  function selectQueue(edgeId: number | undefined): void {
    if (edgeId === undefined) {
      return;
    }
    setSelectedTarget({ kind: "queue", edgeId });
  }

  function selectHazard(edgeId: number | undefined): void {
    if (edgeId === undefined) {
      return;
    }
    setSelectedTarget({ kind: "hazard", edgeId });
  }

  const minimapRect = {
    x: ((viewport.x - bounds.minX) / bounds.width) * 100,
    y: ((viewport.y - bounds.minY) / bounds.height) * 100,
    width: (viewport.width / bounds.width) * 100,
    height: (viewport.height / bounds.height) * 100,
  };

  return (
    <div className="shell">
      <div className="shell-accent shell-accent-left" aria-hidden="true" />
      <div className="shell-accent shell-accent-right" aria-hidden="true" />
      <header className="masthead panel">
        <div className="masthead-copy">
          <p className="eyebrow">Step 46 Visual Polish Pass</p>
          <h1>Autonomous Ops Command Deck</h1>
          <p className="lede">
            The serious frontend now carries a presentation-grade operator shell:
            sharper visual hierarchy, cleaner overlays, richer scene atmosphere, and
            clearer inspection surfaces on top of the live interaction baseline.
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
                <span className="status-pill">Camera controls active</span>
                <span className="status-pill secondary">Hover and selection active</span>
                <span className="status-pill accent">Presentation polish active</span>
              </div>
            </div>

            <div className="scene-toolbar" aria-label="Scene toolbar">
              <div className="tool-group">
                <button className="scene-button" type="button" onClick={() => panView(0, -0.18)}>
                  Pan Up
                </button>
                <button className="scene-button" type="button" onClick={() => panView(-0.18, 0)}>
                  Pan Left
                </button>
                <button className="scene-button" type="button" onClick={() => panView(0.18, 0)}>
                  Pan Right
                </button>
                <button className="scene-button" type="button" onClick={() => panView(0, 0.18)}>
                  Pan Down
                </button>
              </div>
              <div className="tool-group">
                <button className="scene-button" type="button" onClick={() => zoomView(0.82)}>
                  Zoom In
                </button>
                <button className="scene-button" type="button" onClick={() => zoomView(1.2)}>
                  Zoom Out
                </button>
                <button className="scene-button" type="button" onClick={fitScene}>
                  Fit Scene
                </button>
                <button
                  className="scene-button"
                  type="button"
                  onClick={focusSelectedVehicle}
                  disabled={selectedVehicle === null}
                >
                  Focus Selected
                </button>
              </div>
            </div>

            <div className="layer-toolbar" aria-label="Layer toggles">
              {Object.entries(layers).map(([layer, enabled]) => (
                <button
                  key={layer}
                  className={`layer-chip ${enabled ? "layer-chip-active" : ""}`}
                  type="button"
                  onClick={() => toggleLayer(layer as keyof LayerState)}
                >
                  {layer}
                </button>
              ))}
            </div>

            <div className="stage-grid">
              <div className="stage-canvas-frame">
                <div className="scene-rim scene-rim-top" aria-hidden="true" />
                <div className="scene-rim scene-rim-bottom" aria-hidden="true" />
                <svg
                  className="stage-canvas"
                  viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
                  aria-label="Simulation scene graph"
                  onMouseLeave={() => setHoverTarget(null)}
                >
                  <rect
                    x={bounds.minX}
                    y={bounds.minY}
                    width={bounds.width}
                    height={bounds.height}
                    className="scene-backdrop"
                  />

                  {layers.areas &&
                    (bundle?.render_geometry?.areas ?? []).map((area, index) => (
                      <polygon
                        key={area.area_id ?? `area-${index}`}
                        points={toPointString(area.polygon)}
                        className={`scene-area scene-area-${area.kind ?? "generic"}`}
                      />
                    ))}

                  {layers.roads &&
                    (bundle?.render_geometry?.roads ?? []).map((road, index) => (
                      <polyline
                        key={road.road_id ?? `road-${index}`}
                        points={toPointString(road.centerline)}
                        className={`scene-road scene-road-${road.road_class ?? "connector"} ${
                          selectedTarget?.kind === "road" &&
                          selectedTarget.roadId === road.road_id
                            ? "selected"
                            : ""
                        }`}
                        strokeWidth={Math.max(road.width_m ?? 1.4, 0.9)}
                        onClick={() => selectRoad(road.road_id)}
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: road.road_id ?? "road",
                            detail: `${road.directionality ?? "unknown"} · ${road.lane_count ?? 0} lane(s)`,
                          })
                        }
                      />
                    ))}

                  {layers.intersections &&
                    (bundle?.render_geometry?.intersections ?? []).map((intersection, index) => (
                      <polygon
                        key={intersection.intersection_id ?? `intersection-${index}`}
                        points={toPointString(intersection.polygon)}
                        className="scene-intersection"
                      />
                    ))}

                  {layers.routes &&
                    routePreviews.map((preview, previewIndex) => {
                      const routePoints = buildRoutePreviewPoints(
                        preview,
                        bundle?.map_surface?.nodes ?? [],
                      );
                      if (routePoints.length < 2) {
                        return null;
                      }
                      return (
                        <polyline
                          key={`route-preview-${previewIndex}`}
                          points={toPointString(routePoints)}
                          className="scene-route-preview"
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Route preview V${preview.vehicle_id ?? "?"}`,
                              detail: preview.reason ?? "actionable preview",
                            })
                          }
                        />
                      );
                    })}

                  {layers.reservations &&
                    (bundle?.traffic_baseline?.queue_records ?? []).map((record, queueIndex) => {
                      const edge = findEdgeById(
                        bundle?.map_surface?.edges ?? [],
                        record.edge_id ?? null,
                      );
                      const start = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                        : null;
                      const end = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                        : null;
                      if (!start || !end) {
                        return null;
                      }
                      return (
                        <line
                          key={`reservation-${queueIndex}`}
                          x1={start[0]}
                          y1={start[1]}
                          x2={end[0]}
                          y2={end[1]}
                          className={`scene-reservation ${
                            selectedTarget?.kind === "queue" &&
                            selectedTarget.edgeId === record.edge_id
                              ? "selected"
                              : ""
                          }`}
                          onClick={() => selectQueue(record.edge_id)}
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Queue edge ${record.edge_id ?? "?"}`,
                              detail: `${record.vehicle_ids?.length ?? 0} vehicle(s) queued`,
                            })
                          }
                        />
                      );
                    })}

                  {layers.hazards &&
                    (bundle?.snapshot?.blocked_edge_ids ?? []).map((edgeId, blockedIndex) => {
                      const edge = findEdgeById(bundle?.map_surface?.edges ?? [], edgeId);
                      const start = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                        : null;
                      const end = edge
                        ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                        : null;
                      if (!start || !end) {
                        return null;
                      }
                      return (
                        <line
                          key={`hazard-${blockedIndex}`}
                          x1={start[0]}
                          y1={start[1]}
                          x2={end[0]}
                          y2={end[1]}
                          className={`scene-hazard ${
                            selectedTarget?.kind === "hazard" &&
                            selectedTarget.edgeId === edgeId
                              ? "selected"
                              : ""
                          }`}
                          onClick={() => selectHazard(edgeId)}
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Blocked edge ${edgeId}`,
                              detail: "Conflict / hazard overlay",
                            })
                          }
                        />
                      );
                    })}

                  {layers.vehicles &&
                    (bundle?.snapshot?.vehicles ?? []).map((vehicle, vehicleIndex) => {
                      const position = vehicle.position ?? [0, 0, 0];
                      const isSelected = vehicle.vehicle_id === selectedVehicleId;
                      return (
                        <g
                          key={vehicle.vehicle_id ?? `vehicle-${vehicleIndex}`}
                          className={isSelected ? "scene-vehicle selected" : "scene-vehicle"}
                          onClick={() => selectVehicle(vehicle.vehicle_id)}
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Vehicle ${vehicle.vehicle_id ?? vehicleIndex}`,
                              detail: vehicle.operational_state ?? "unknown_state",
                            })
                          }
                        >
                          <circle cx={position[0]} cy={position[1]} r={0.55} />
                          <text x={position[0]} y={position[1] - 0.85}>
                            V{vehicle.vehicle_id ?? vehicleIndex}
                          </text>
                        </g>
                      );
                    })}
                </svg>

                <div className="focus-card">
                  <strong>Visual polish pass is now live</strong>
                  <p>
                    This pass sharpens the command deck without changing simulator
                    authority: better scene depth, cleaner panels, clearer overlays, and
                    a more presentation-ready mining control aesthetic.
                  </p>
                </div>
                <div className="scene-legend">
                  <span className="legend-item">
                    <span className="legend-swatch road" />
                    Roads
                  </span>
                  <span className="legend-item">
                    <span className="legend-swatch vehicle" />
                    Vehicles
                  </span>
                  <span className="legend-item">
                    <span className="legend-swatch hazard" />
                    Hazards
                  </span>
                </div>
                {hoverTarget ? (
                  <div className="hover-card" aria-live="polite">
                    <strong>{hoverTarget.label}</strong>
                    <p>{hoverTarget.detail}</p>
                  </div>
                ) : null}
              </div>

              <aside className="overview-panel">
                <div className="overview-card">
                  <p className="eyebrow">Overview</p>
                  <h3>Minimap Navigation</h3>
                  <svg
                    ref={minimapRef}
                    className="minimap"
                    viewBox={`0 0 100 100`}
                    aria-label="Scene minimap"
                    onClick={handleMinimapClick}
                  >
                    <rect x={0} y={0} width={100} height={100} className="minimap-bg" />
                    {(bundle?.render_geometry?.roads ?? []).map((road, index) => (
                      <polyline
                        key={road.road_id ?? `minimap-road-${index}`}
                        points={toScaledPointString(road.centerline, bounds)}
                        className="minimap-road"
                      />
                    ))}
                    {(bundle?.snapshot?.vehicles ?? []).map((vehicle, index) => (
                      <circle
                        key={vehicle.vehicle_id ?? `minimap-vehicle-${index}`}
                        cx={scaleX(vehicle.position?.[0] ?? 0, bounds)}
                        cy={scaleY(vehicle.position?.[1] ?? 0, bounds)}
                        r={1.7}
                        className="minimap-vehicle"
                      />
                    ))}
                    <rect
                      x={minimapRect.x}
                      y={minimapRect.y}
                      width={minimapRect.width}
                      height={minimapRect.height}
                      className="minimap-viewport"
                    />
                  </svg>
                  <p>Click anywhere on the minimap to recenter the current viewport.</p>
                </div>

                <div className="overview-card">
                  <p className="eyebrow">Layer Summary</p>
                  <ul className="mini-list">
                    <li>
                      Roads: {layers.roads ? "visible" : "hidden"} · Areas:{" "}
                      {layers.areas ? "visible" : "hidden"}
                    </li>
                    <li>
                      Intersections: {layers.intersections ? "visible" : "hidden"} ·
                      Vehicles: {layers.vehicles ? "visible" : "hidden"}
                    </li>
                    <li>
                      Routes: {layers.routes ? "visible" : "hidden"} · Reservations:{" "}
                      {layers.reservations ? "visible" : "hidden"}
                    </li>
                    <li>Hazards: {layers.hazards ? "visible" : "hidden"}</li>
                    <li>
                      Selection: {describeSelectedTarget(selectedTarget, selectedVehicleId)}
                    </li>
                  </ul>
                </div>

                <div className="overview-card">
                  <p className="eyebrow">Visual Readout</p>
                  <ul className="mini-list">
                    <li>Overlay palette tuned for road, route, queue, and hazard contrast</li>
                    <li>Panels elevated for quicker operator scanning on laptop displays</li>
                    <li>Scene framing reserved for more cinematic polish in later passes</li>
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
              <span className="status-pill secondary">
                {selectedTarget ? describeSelectedBadge(selectedTarget) : `${inspections.length} records`}
              </span>
            </div>
            <div className="section-stack">
              {selectedTarget?.kind === "road" && selectedRoad ? (
                <article className="inspection-card">
                  <div className="inspection-header">
                    <strong>{selectedRoad.road_id ?? "road"}</strong>
                    <span>{selectedRoad.road_class ?? "connector"}</span>
                  </div>
                  <ul className="mini-list">
                    <li>Directionality: {selectedRoad.directionality ?? "unknown"}</li>
                    <li>Lanes: {formatMaybeNumber(selectedRoad.lane_count ?? null)}</li>
                    <li>Width: {selectedRoad.width_m ?? "pending"}m</li>
                    <li>Edges: {(selectedRoad.edge_ids ?? []).join(", ") || "none"}</li>
                  </ul>
                </article>
              ) : null}

              {selectedTarget?.kind === "queue" && selectedQueueRecord ? (
                <article className="inspection-card">
                  <div className="inspection-header">
                    <strong>Queue Edge {selectedQueueRecord.edge_id ?? "?"}</strong>
                    <span>reservation queue</span>
                  </div>
                  <ul className="mini-list">
                    <li>Queued vehicles: {selectedQueueRecord.vehicle_ids?.join(", ") || "none"}</li>
                    <li>Queue length: {selectedQueueRecord.vehicle_ids?.length ?? 0}</li>
                  </ul>
                </article>
              ) : null}

              {selectedTarget?.kind === "hazard" && selectedHazardEdge ? (
                <article className="inspection-card">
                  <div className="inspection-header">
                    <strong>Blocked Edge {selectedHazardEdge.edge_id ?? "?"}</strong>
                    <span>conflict area</span>
                  </div>
                  <ul className="mini-list">
                    <li>Start node: {formatMaybeNumber(selectedHazardEdge.start_node_id ?? null)}</li>
                    <li>End node: {formatMaybeNumber(selectedHazardEdge.end_node_id ?? null)}</li>
                    <li>Distance: {selectedHazardEdge.distance ?? "pending"}</li>
                    <li>Speed limit: {selectedHazardEdge.speed_limit ?? "pending"}</li>
                  </ul>
                </article>
              ) : null}

              {selectedInspection ? (
                <article className="inspection-card">
                  <div className="inspection-header">
                    <strong>Vehicle {formatMaybeNumber(selectedInspection.vehicle_id ?? null)}</strong>
                    <span>{selectedInspection.operational_state ?? "unknown_state"}</span>
                  </div>
                  <ul className="mini-list">
                    <li>Node: {formatMaybeNumber(selectedInspection.current_node_id ?? null)}</li>
                    <li>ETA: {formatSeconds(selectedInspection.eta_s ?? null)}</li>
                    <li>Job: {selectedInspection.current_job_id ?? "none"}</li>
                    <li>Wait: {selectedInspection.wait_reason ?? "none"}</li>
                  </ul>
                  <div className="diagnostic-row">
                    {(selectedInspection.diagnostics ?? []).slice(0, 3).map((diagnostic, diagIndex) => (
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
              ) : null}

              {!selectedTarget && inspections.length > 0 ? (
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
              ) : null}

              {!selectedTarget && inspections.length === 0 ? (
                <div className="empty-state">
                  Inspection surfaces will populate here once a live session carries
                  selected vehicles and runtime diagnostics.
                </div>
              ) : null}
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

function fitViewportToBundle(bundle: BundlePayload | null): ViewportState {
  const bounds = computeSceneBounds(bundle);
  const paddingX = Math.max(bounds.width * 0.08, 2);
  const paddingY = Math.max(bounds.height * 0.1, 2);
  return {
    x: bounds.minX - paddingX,
    y: bounds.minY - paddingY,
    width: bounds.width + paddingX * 2,
    height: bounds.height + paddingY * 2,
  };
}

function computeSceneBounds(bundle: BundlePayload | null): Bounds {
  const points: Position3[] = [];

  for (const road of bundle?.render_geometry?.roads ?? []) {
    points.push(...(road.centerline ?? []));
  }
  for (const area of bundle?.render_geometry?.areas ?? []) {
    points.push(...(area.polygon ?? []));
  }
  for (const intersection of bundle?.render_geometry?.intersections ?? []) {
    points.push(...(intersection.polygon ?? []));
  }
  for (const node of bundle?.map_surface?.nodes ?? []) {
    if (node.position) {
      points.push(node.position);
    }
  }
  for (const vehicle of bundle?.snapshot?.vehicles ?? []) {
    if (vehicle.position) {
      points.push(vehicle.position);
    }
  }

  if (points.length === 0) {
    return {
      minX: -10,
      minY: -6,
      maxX: 10,
      maxY: 6,
      width: 20,
      height: 12,
    };
  }

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

function toPointString(points: Position3[] | undefined): string {
  return (points ?? []).map(([x, y]) => `${x},${y}`).join(" ");
}

function toScaledPointString(points: Position3[] | undefined, bounds: Bounds): string {
  return (points ?? [])
    .map(([x, y]) => `${scaleX(x, bounds)},${scaleY(y, bounds)}`)
    .join(" ");
}

function scaleX(x: number, bounds: Bounds): number {
  return ((x - bounds.minX) / bounds.width) * 100;
}

function scaleY(y: number, bounds: Bounds): number {
  return ((y - bounds.minY) / bounds.height) * 100;
}

function buildRoutePreviewPoints(
  preview: RoutePreviewPayload,
  nodes: NodePayload[],
): Position3[] {
  const routePoints: Position3[] = [];
  for (const nodeId of preview.node_ids ?? []) {
    const point = findNodePosition(nodes, nodeId);
    if (point) {
      routePoints.push(point);
    }
  }
  return routePoints;
}

function findVehicleById(
  bundle: BundlePayload | null,
  vehicleId: number | null,
): VehicleSnapshotPayload | null {
  if (vehicleId === null) {
    return null;
  }
  return (
    (bundle?.snapshot?.vehicles ?? []).find((vehicle) => vehicle.vehicle_id === vehicleId) ??
    null
  );
}

function findEdgeById(edges: EdgePayload[], edgeId: number | null): EdgePayload | null {
  if (edgeId === null) {
    return null;
  }
  return edges.find((edge) => edge.edge_id === edgeId) ?? null;
}

function findNodePosition(nodes: NodePayload[], nodeId: number | undefined): Position3 | null {
  if (nodeId === undefined) {
    return null;
  }
  return nodes.find((node) => node.node_id === nodeId)?.position ?? null;
}

function describeSelectedTarget(
  selectedTarget: SelectedTarget | null,
  selectedVehicleId: number | null,
): string {
  if (selectedTarget?.kind === "road") {
    return `road ${selectedTarget.roadId}`;
  }
  if (selectedTarget?.kind === "queue") {
    return `queue edge ${selectedTarget.edgeId}`;
  }
  if (selectedTarget?.kind === "hazard") {
    return `blocked edge ${selectedTarget.edgeId}`;
  }
  if (selectedVehicleId !== null) {
    return `vehicle ${selectedVehicleId}`;
  }
  return "none";
}

function describeSelectedBadge(selectedTarget: SelectedTarget): string {
  if (selectedTarget.kind === "vehicle") {
    return `vehicle ${selectedTarget.vehicleId}`;
  }
  if (selectedTarget.kind === "road") {
    return "road";
  }
  if (selectedTarget.kind === "queue") {
    return "queue";
  }
  return "hazard";
}

function formatMaybeNumber(value: number | null): string {
  return value === null ? "pending" : String(value);
}

function formatSeconds(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(1)}s`;
}

export default App;
