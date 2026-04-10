import { useEffect, useRef, useState, type MouseEvent } from "react";

type Position3 = [number, number, number];

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

type LanePayload = {
  lane_id?: string;
  road_id?: string;
  lane_index?: number;
  directionality?: string;
  lane_role?: string;
  centerline?: Position3[];
  width_m?: number;
};

type TurnConnectorPayload = {
  connector_id?: string;
  from_lane_id?: string;
  to_lane_id?: string;
  connector_type?: string;
  centerline?: Position3[];
};

type StopLinePayload = {
  stop_line_id?: string;
  lane_id?: string;
  control_kind?: string;
  segment?: Position3[];
};

type MergeZonePayload = {
  merge_zone_id?: string;
  lane_ids?: string[];
  kind?: string;
  polygon?: Position3[];
};

type RenderGeometryPayload = {
  roads?: RoadPayload[];
  intersections?: IntersectionPayload[];
  areas?: AreaPayload[];
  lanes?: LanePayload[];
  turn_connectors?: TurnConnectorPayload[];
  stop_lines?: StopLinePayload[];
  merge_zones?: MergeZonePayload[];
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

type MapSurfacePayload = {
  nodes?: NodePayload[];
  edges?: EdgePayload[];
};

type VehicleSnapshotPayload = {
  vehicle_id?: number;
  node_id?: number;
  position?: Position3;
  operational_state?: string;
};

type MotionSegmentPayload = {
  vehicle_id?: number;
  segment_index?: number;
  edge_id?: number;
  start_node_id?: number;
  end_node_id?: number;
  start_time_s?: number;
  end_time_s?: number;
  duration_s?: number;
  distance?: number;
  start_position?: Position3;
  end_position?: Position3;
  path_points?: Position3[];
  heading_rad?: number;
  nominal_speed?: number;
  peak_speed?: number;
  acceleration_mps2?: number;
  deceleration_mps2?: number;
  profile_kind?: string;
};

type TrafficBaselinePayload = {
  control_points?: Array<{ edge_id?: number; state?: string }>;
  queue_records?: Array<{ edge_id?: number; vehicle_ids?: number[] }>;
};

type AuthoringPayload = {
  mode?: string;
  save_endpoint?: string;
  reload_endpoint?: string;
  validate_endpoint?: string;
  source_scenario_path?: string;
  working_scenario_path?: string;
  editable_node_count?: number;
  editable_road_count?: number;
  editable_area_count?: number;
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
  motion_segments?: MotionSegmentPayload[];
  traffic_baseline?: TrafficBaselinePayload;
  authoring?: AuthoringPayload;
  snapshot?: {
    simulated_time_s?: number;
    blocked_edge_ids?: number[];
    vehicles?: VehicleSnapshotPayload[];
  };
};

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

type SelectedTarget =
  | { kind: "vehicle"; vehicleId: number }
  | { kind: "road"; roadId: string }
  | { kind: "area"; areaId: string }
  | { kind: "queue"; edgeId: number }
  | { kind: "hazard"; edgeId: number };

type HoverTarget = {
  label: string;
  detail: string;
};

type Bounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

type ValidationMessage = {
  severity?: string;
  code?: string;
  message?: string;
  target_kind?: string | null;
  target_id?: string | number | null;
};

type MoveNodeEditOperation = {
  kind: "move_node";
  target_id: number;
  position: Position3;
};

type RoadEditOperation = {
  kind: "set_road_centerline";
  target_id: string;
  points: Position3[];
};

type AreaEditOperation = {
  kind: "set_area_polygon";
  target_id: string;
  points: Position3[];
};

type EditOperation = MoveNodeEditOperation | RoadEditOperation | AreaEditOperation;

type EditTransaction = {
  label: string;
  operations: EditOperation[];
};

type DragState =
  | { kind: "node"; nodeId: number; z: number }
  | { kind: "road-point"; roadId: string; pointIndex: number; z: number }
  | { kind: "area-point"; areaId: string; pointIndex: number; z: number };

const architecture = {
  primaryStack: "React + TypeScript + Vite",
  authority: "Python simulator remains authoritative",
  launchMode: "Live session + live authoring through versioned bundle surfaces",
};

const sessionActions = [
  "Launch Live Run",
  "Reconnect Bundle",
  "Edit Scene",
  "Save Scenario",
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

const emptyTransaction: EditTransaction = {
  label: "live_geometry_edit",
  operations: [],
};

function App(): JSX.Element {
  const minimapRef = useRef<SVGSVGElement | null>(null);
  const sceneRef = useRef<SVGSVGElement | null>(null);
  const [layers, setLayers] = useState<LayerState>(defaultLayers);
  const [selectedTarget, setSelectedTarget] = useState<SelectedTarget | null>(null);
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [editorEnabled, setEditorEnabled] = useState(false);
  const [draftTransaction, setDraftTransaction] = useState<EditTransaction>(emptyTransaction);
  const [validationMessages, setValidationMessages] = useState<ValidationMessage[]>([]);
  const [editorMessage, setEditorMessage] = useState("Authoring surface is standing by.");
  const [dragState, setDragState] = useState<DragState | null>(null);
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
  const [motionClockS, setMotionClockS] = useState(0);

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
        applyLoadedBundle(bundle, "Live bundle bootstrap connected.");
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

  useEffect(() => {
    const motionEndTimeS = maxMotionTime(bootstrap.bundle);
    if (motionEndTimeS <= 0.0) {
      setMotionClockS(0);
      return;
    }

    let frameId = 0;
    let lastTimestampMs: number | null = null;
    const tick = (timestampMs: number) => {
      if (lastTimestampMs === null) {
        lastTimestampMs = timestampMs;
      }
      const deltaS = (timestampMs - lastTimestampMs) / 1000;
      lastTimestampMs = timestampMs;
      setMotionClockS((current) => {
        const next = current + deltaS;
        return next > motionEndTimeS ? next % motionEndTimeS : next;
      });
      frameId = window.requestAnimationFrame(tick);
    };

    frameId = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frameId);
  }, [bootstrap.bundle]);

  useEffect(() => {
    const authoring = bootstrap.bundle?.authoring;
    if (!authoring?.validate_endpoint || draftTransaction.operations.length === 0) {
      setValidationMessages([]);
      return;
    }

    let cancelled = false;
    void fetch(authoring.validate_endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(draftTransaction),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Validation request failed with ${response.status}`);
        }
        return response.json() as Promise<{
          ok?: boolean;
          validation_messages?: ValidationMessage[];
        }>;
      })
      .then((payload) => {
        if (!cancelled) {
          setValidationMessages(payload.validation_messages ?? []);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Validation request failed";
          setValidationMessages([
            {
              severity: "error",
              code: "validation_request_failed",
              message,
            },
          ]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [bootstrap.bundle, draftTransaction]);

  const bundle = applyTransactionToBundle(bootstrap.bundle, draftTransaction);
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
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
  const displayedSelectedVehicle =
    selectedVehicleId !== null
      ? displayedVehicles.find((vehicle) => vehicle.vehicle_id === selectedVehicleId) ?? null
      : null;
  const selectedInspection = selectedVehicleId
    ? inspections.find((inspection) => inspection.vehicle_id === selectedVehicleId) ?? null
    : null;
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedArea =
    selectedTarget?.kind === "area"
      ? (bundle?.render_geometry?.areas ?? []).find(
          (area) => area.area_id === selectedTarget.areaId,
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
  const authoring = bootstrap.bundle?.authoring;
  const editCount = draftTransaction.operations.length;

  function applyLoadedBundle(bundlePayload: BundlePayload, message: string): void {
    const nextViewport = fitViewportToBundle(bundlePayload);
    setViewport(nextViewport);
    setDraftTransaction(emptyTransaction);
    setValidationMessages([]);
    setDragState(null);
    setBootstrap(buildBootstrapSummary(bundlePayload, message));
  }

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
    if (!displayedSelectedVehicle?.position) {
      return;
    }
    const [x, y] = displayedSelectedVehicle.position;
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
    if (vehicleId !== undefined) {
      setSelectedTarget({ kind: "vehicle", vehicleId });
    }
  }

  function selectRoad(roadId: string | undefined): void {
    if (roadId) {
      setSelectedTarget({ kind: "road", roadId });
    }
  }

  function selectArea(areaId: string | undefined): void {
    if (areaId) {
      setSelectedTarget({ kind: "area", areaId });
    }
  }

  function selectQueue(edgeId: number | undefined): void {
    if (edgeId !== undefined) {
      setSelectedTarget({ kind: "queue", edgeId });
    }
  }

  function selectHazard(edgeId: number | undefined): void {
    if (edgeId !== undefined) {
      setSelectedTarget({ kind: "hazard", edgeId });
    }
  }

  function toggleEditMode(): void {
    setEditorEnabled((current) => !current);
    setEditorMessage(
      !editorEnabled
        ? "Edit mode enabled. Drag node, road, or zone handles to stage geometry mutations."
        : "Edit mode paused. Draft mutations are preserved until you save or reload.",
    );
  }

  function saveScenario(): void {
    if (!authoring?.save_endpoint || editCount === 0) {
      return;
    }
    setEditorMessage("Saving live geometry edits into the working scenario...");
    void fetch(authoring.save_endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(draftTransaction),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Save request failed with ${response.status}`);
        }
        return response.json() as Promise<{
          ok?: boolean;
          bundle?: BundlePayload;
          validation_messages?: ValidationMessage[];
        }>;
      })
      .then((payload) => {
        setValidationMessages(payload.validation_messages ?? []);
        if (!payload.ok || !payload.bundle) {
          setEditorMessage("Save rejected. Resolve validation issues and try again.");
          return;
        }
        applyLoadedBundle(payload.bundle, "Live authoring save completed.");
        setEditorMessage("Scenario changes saved and live bundle reloaded.");
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Save request failed";
        setEditorMessage(message);
      });
  }

  function reloadScenario(): void {
    if (!authoring?.reload_endpoint) {
      return;
    }
    setEditorMessage("Reloading working scenario from the Python authoring surface...");
    void fetch(authoring.reload_endpoint)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Reload request failed with ${response.status}`);
        }
        return response.json() as Promise<{ ok?: boolean; bundle?: BundlePayload }>;
      })
      .then((payload) => {
        if (!payload.ok || !payload.bundle) {
          throw new Error("Reload response did not include a bundle.");
        }
        applyLoadedBundle(payload.bundle, "Working scenario reloaded.");
        setEditorMessage("Working scenario reloaded and draft edits cleared.");
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Reload request failed";
        setEditorMessage(message);
      });
  }

  function upsertOperation(nextOperation: EditOperation): void {
    setDraftTransaction((current) => {
      const nextOperations = current.operations.filter(
        (operation) =>
          !(
            operation.kind === nextOperation.kind &&
            operation.target_id === nextOperation.target_id
          ),
      );
      nextOperations.push(nextOperation);
      return {
        ...current,
        operations: nextOperations,
      };
    });
  }

  function beginNodeDrag(event: MouseEvent<SVGCircleElement>, node: NodePayload): void {
    if (!editorEnabled || node.node_id === undefined) {
      return;
    }
    event.stopPropagation();
    const z = node.position?.[2] ?? 0;
    setSelectedTarget(null);
    setDragState({
      kind: "node",
      nodeId: node.node_id,
      z,
    });
  }

  function beginRoadPointDrag(
    event: MouseEvent<SVGCircleElement>,
    roadId: string,
    pointIndex: number,
    z: number,
  ): void {
    if (!editorEnabled) {
      return;
    }
    event.stopPropagation();
    setDragState({
      kind: "road-point",
      roadId,
      pointIndex,
      z,
    });
  }

  function beginAreaPointDrag(
    event: MouseEvent<SVGCircleElement>,
    areaId: string,
    pointIndex: number,
    z: number,
  ): void {
    if (!editorEnabled) {
      return;
    }
    event.stopPropagation();
    setDragState({
      kind: "area-point",
      areaId,
      pointIndex,
      z,
    });
  }

  function handleSceneMouseMove(event: MouseEvent<SVGSVGElement>): void {
    if (!dragState || !bundle) {
      return;
    }
    const scenePoint = clientPointToScene(event, sceneRef.current, viewport, dragState.z);
    if (!scenePoint) {
      return;
    }

    if (dragState.kind === "node") {
      upsertOperation({
        kind: "move_node",
        target_id: dragState.nodeId,
        position: scenePoint,
      });
      return;
    }

    if (dragState.kind === "road-point") {
      const road = (bundle.render_geometry?.roads ?? []).find(
        (entry) => entry.road_id === dragState.roadId,
      );
      if (!road?.centerline) {
        return;
      }
      const nextPoints = road.centerline.map((point) => [...point] as Position3);
      nextPoints[dragState.pointIndex] = scenePoint;
      upsertOperation({
        kind: "set_road_centerline",
        target_id: dragState.roadId,
        points: nextPoints,
      });
      return;
    }

    const area = (bundle.render_geometry?.areas ?? []).find(
      (entry) => entry.area_id === dragState.areaId,
    );
    if (!area?.polygon) {
      return;
    }
    const nextPoints = area.polygon.map((point) => [...point] as Position3);
    nextPoints[dragState.pointIndex] = scenePoint;
    upsertOperation({
      kind: "set_area_polygon",
      target_id: dragState.areaId,
      points: nextPoints,
    });
  }

  function stopDragging(): void {
    if (dragState) {
      setEditorMessage("Draft geometry edit staged. Save the scenario to persist it.");
    }
    setDragState(null);
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
          <p className="eyebrow">Step 53 Curve-Following and Turn Arcs</p>
          <h1>Autonomous Ops Command Deck</h1>
          <p className="lede">
            The serious frontend now plays vehicles along curved path geometry
            with heading-aware directional marks, so turns read naturally
            through roads, connectors, and shaped intersections.
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
          <span className="metric-label">Pending Edits</span>
          <strong>{formatMaybeNumber(editCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Validation</span>
          <strong>{validationMessages.length === 0 ? "clean" : `${validationMessages.length} issue(s)`}</strong>
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
                <span className="status-pill secondary">Selection active</span>
                <span className="status-pill accent">
                  {editorEnabled ? "Edit handles active" : "Edit handles armed"}
                </span>
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
              <div className="tool-group">
                <button className="scene-button" type="button" onClick={toggleEditMode}>
                  {editorEnabled ? "Pause Edit Mode" : "Edit Scene"}
                </button>
                <button
                  className="scene-button"
                  type="button"
                  onClick={saveScenario}
                  disabled={!authoring?.save_endpoint || editCount === 0}
                >
                  Save Scenario
                </button>
                <button
                  className="scene-button"
                  type="button"
                  onClick={reloadScenario}
                  disabled={!authoring?.reload_endpoint}
                >
                  Reload Scenario
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
                  ref={sceneRef}
                  className="stage-canvas"
                  viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
                  aria-label="Simulation scene graph"
                  onMouseLeave={() => {
                    setHoverTarget(null);
                    stopDragging();
                  }}
                  onMouseMove={handleSceneMouseMove}
                  onMouseUp={stopDragging}
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
                        className={`scene-area scene-area-${area.kind ?? "generic"} ${
                          selectedTarget?.kind === "area" && selectedTarget.areaId === area.area_id
                            ? "selected"
                            : ""
                        }`}
                        onClick={() => selectArea(area.area_id)}
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: area.label ?? area.area_id ?? "zone",
                            detail: area.kind ?? "zone",
                          })
                        }
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

                  {layers.roads &&
                    (bundle?.render_geometry?.lanes ?? []).map((lane, index) => (
                      <polyline
                        key={lane.lane_id ?? `lane-${index}`}
                        points={toPointString(lane.centerline)}
                        className={`scene-lane scene-lane-${lane.directionality ?? "forward"}`}
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: lane.lane_id ?? "lane",
                            detail: `${lane.lane_role ?? "travel"} · ${lane.directionality ?? "forward"}`,
                          })
                        }
                      />
                    ))}

                  {layers.roads &&
                    (bundle?.render_geometry?.turn_connectors ?? []).map((connector, index) => (
                      <polyline
                        key={connector.connector_id ?? `connector-${index}`}
                        points={toPointString(connector.centerline)}
                        className="scene-turn-connector"
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: connector.connector_id ?? "connector",
                            detail: connector.connector_type ?? "turn connector",
                          })
                        }
                      />
                    ))}

                  {layers.roads &&
                    (bundle?.render_geometry?.stop_lines ?? []).map((stopLine, index) => (
                      <line
                        key={stopLine.stop_line_id ?? `stop-line-${index}`}
                        x1={stopLine.segment?.[0]?.[0] ?? 0}
                        y1={stopLine.segment?.[0]?.[1] ?? 0}
                        x2={stopLine.segment?.[1]?.[0] ?? 0}
                        y2={stopLine.segment?.[1]?.[1] ?? 0}
                        className="scene-stop-line"
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: stopLine.stop_line_id ?? "stop line",
                            detail: stopLine.control_kind ?? "stop control",
                          })
                        }
                      />
                    ))}

                  {layers.roads &&
                    (bundle?.render_geometry?.merge_zones ?? []).map((zone, index) => (
                      <polygon
                        key={zone.merge_zone_id ?? `merge-zone-${index}`}
                        points={toPointString(zone.polygon)}
                        className="scene-merge-zone"
                        onMouseEnter={() =>
                          setHoverTarget({
                            label: zone.merge_zone_id ?? "merge zone",
                            detail: `${zone.kind ?? "merge"} · ${(zone.lane_ids ?? []).length} lane(s)`,
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

                  {editorEnabled &&
                    (bundle?.map_surface?.nodes ?? []).map((node, index) => {
                      if (node.node_id === undefined || !node.position) {
                        return null;
                      }
                      return (
                        <circle
                          key={node.node_id ?? `node-handle-${index}`}
                          cx={node.position[0]}
                          cy={node.position[1]}
                          r={0.32}
                          className="scene-edit-handle node"
                          onMouseDown={(event) => beginNodeDrag(event, node)}
                        />
                      );
                    })}

                  {editorEnabled &&
                    selectedRoad?.centerline?.map((point, index) => (
                      <circle
                        key={`${selectedRoad.road_id ?? "road"}-point-${index}`}
                        cx={point[0]}
                        cy={point[1]}
                        r={0.3}
                        className="scene-edit-handle road"
                        onMouseDown={(event) =>
                          beginRoadPointDrag(
                            event,
                            selectedRoad.road_id ?? "road",
                            index,
                            point[2] ?? 0,
                          )
                        }
                      />
                    ))}

                  {editorEnabled &&
                    selectedArea?.polygon?.map((point, index) => (
                      <circle
                        key={`${selectedArea.area_id ?? "area"}-point-${index}`}
                        cx={point[0]}
                        cy={point[1]}
                        r={0.3}
                        className="scene-edit-handle area"
                        onMouseDown={(event) =>
                          beginAreaPointDrag(
                            event,
                            selectedArea.area_id ?? "area",
                            index,
                            point[2] ?? 0,
                          )
                        }
                      />
                    ))}

                  {layers.vehicles &&
                    displayedVehicles.map((vehicle, vehicleIndex) => {
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
                          <g
                            transform={`translate(${position[0]} ${position[1]}) rotate(${radiansToDegrees(
                              vehicle.heading_rad ?? 0,
                            )})`}
                          >
                            {renderVehicleMarker()}
                          </g>
                          <text x={position[0]} y={position[1] - 0.84}>
                            V{vehicle.vehicle_id ?? vehicleIndex}
                          </text>
                        </g>
                      );
                    })}
                </svg>

                <div className="focus-card">
                  <strong>Curved motion and heading-aware playback are now live</strong>
                  <p>
                    Motion playback now follows authored path geometry instead of
                    only straight edge interpolation, and vehicle heading updates
                    continuously through turns and connectors.
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
                  <span className="legend-item">
                    <span className="legend-swatch handle" />
                    Edit handles
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
                    {displayedVehicles.map((vehicle, index) => (
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
                  <p className="eyebrow">Authoring State</p>
                  <ul className="mini-list">
                    <li>{editorEnabled ? "Edit mode is active" : "Edit mode is paused"}</li>
                    <li>Working copy: {authoring?.working_scenario_path ?? "unavailable"}</li>
                    <li>Nodes: {formatMaybeNumber(authoring?.editable_node_count ?? null)}</li>
                    <li>Roads: {formatMaybeNumber(authoring?.editable_road_count ?? null)}</li>
                    <li>Zones: {formatMaybeNumber(authoring?.editable_area_count ?? null)}</li>
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
          <section className="panel info-panel" aria-labelledby="editor-title">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Authoring Region</p>
                <h2 id="editor-title">Live Geometry Editing</h2>
              </div>
              <span className="status-pill secondary">{editCount} staged</span>
            </div>
            <div className="section-stack">
              <div className="subsection">
                <h3>Authoring Controls</h3>
                <div className="action-row">
                  <button className="scene-button" type="button" onClick={toggleEditMode}>
                    {editorEnabled ? "Pause Edit Mode" : "Edit Scene"}
                  </button>
                  <button
                    className="scene-button"
                    type="button"
                    onClick={saveScenario}
                    disabled={!authoring?.save_endpoint || editCount === 0}
                  >
                    Save Scenario
                  </button>
                  <button
                    className="scene-button"
                    type="button"
                    onClick={reloadScenario}
                    disabled={!authoring?.reload_endpoint}
                  >
                    Reload Scenario
                  </button>
                </div>
                <p className="status-copy">{editorMessage}</p>
              </div>

              <div className="subsection">
                <h3>Validation Messages</h3>
                <ul className="data-list">
                  {validationMessages.length > 0 ? (
                    validationMessages.map((message, index) => (
                      <li key={`${message.code ?? "validation"}-${index}`}>
                        {(message.severity ?? "info").toUpperCase()} ·{" "}
                        {message.message ?? "No validation message"}
                      </li>
                    ))
                  ) : (
                    <li>No validation issues are currently blocking the draft.</li>
                  )}
                </ul>
              </div>

              <div className="subsection">
                <h3>Draft Operations</h3>
                <ul className="data-list">
                  {draftTransaction.operations.length > 0 ? (
                    draftTransaction.operations.map((operation, index) => (
                      <li key={`${operation.kind}-${operation.target_id}-${index}`}>
                        {describeOperation(operation)}
                      </li>
                    ))
                  ) : (
                    <li>No geometry edits are staged yet.</li>
                  )}
                </ul>
              </div>
            </div>
          </section>

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

              {selectedTarget?.kind === "area" && selectedArea ? (
                <article className="inspection-card">
                  <div className="inspection-header">
                    <strong>{selectedArea.label ?? selectedArea.area_id ?? "zone"}</strong>
                    <span>{selectedArea.kind ?? "area"}</span>
                  </div>
                  <ul className="mini-list">
                    <li>Polygon vertices: {selectedArea.polygon?.length ?? 0}</li>
                    <li>Area id: {selectedArea.area_id ?? "unknown"}</li>
                    <li>Editing target: zone polygon</li>
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
                    <strong>
                      Vehicle {formatMaybeNumber(selectedInspection.vehicle_id ?? null)}
                    </strong>
                    <span>{selectedInspection.operational_state ?? "unknown_state"}</span>
                  </div>
                  <ul className="mini-list">
                    <li>Node: {formatMaybeNumber(selectedInspection.current_node_id ?? null)}</li>
                    <li>ETA: {formatSeconds(selectedInspection.eta_s ?? null)}</li>
                    <li>Job: {selectedInspection.current_job_id ?? "none"}</li>
                    <li>Wait: {selectedInspection.wait_reason ?? "none"}</li>
                    <li>Heading: {formatHeadingDegrees(displayedSelectedVehicle?.heading_rad ?? null)}</li>
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
                      <li>
                        Heading: {formatHeadingDegrees(findDisplayedVehicleById(displayedVehicles, inspection.vehicle_id ?? null)?.heading_rad ?? null)}
                      </li>
                    </ul>
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

function buildBootstrapSummary(
  bundle: BundlePayload,
  message: string,
): BootstrapSummary {
  const snapshot = bundle.snapshot ?? {};
  const commandCenter = bundle.command_center ?? {};
  const aiAssist = commandCenter.ai_assist ?? {};
  const summary = bundle.summary ?? null;
  return {
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
    message,
    commandCenter,
    summary,
    bundle,
  };
}

function applyTransactionToBundle(
  bundle: BundlePayload | null,
  transaction: EditTransaction,
): BundlePayload | null {
  if (!bundle || transaction.operations.length === 0) {
    return bundle;
  }
  const draft = deepClone(bundle);
  for (const operation of transaction.operations) {
    if (operation.kind === "move_node") {
      applyMoveNodeOperation(draft, operation);
    } else if (operation.kind === "set_road_centerline") {
      const road = (draft.render_geometry?.roads ?? []).find(
        (entry) => entry.road_id === operation.target_id,
      );
      if (road) {
        road.centerline = operation.points.map((point) => [...point] as Position3);
      }
    } else if (operation.kind === "set_area_polygon") {
      const area = (draft.render_geometry?.areas ?? []).find(
        (entry) => entry.area_id === operation.target_id,
      );
      if (area) {
        area.polygon = operation.points.map((point) => [...point] as Position3);
      }
    }
  }
  return draft;
}

function applyMoveNodeOperation(
  bundle: BundlePayload,
  operation: MoveNodeEditOperation,
): void {
  const node = (bundle.map_surface?.nodes ?? []).find(
    (entry) => entry.node_id === operation.target_id,
  );
  if (!node?.position) {
    return;
  }
  const oldPosition = [...node.position] as Position3;
  node.position = [...operation.position] as Position3;

  for (const road of bundle.render_geometry?.roads ?? []) {
    const edgeIds = new Set(road.edge_ids ?? []);
    const connected = (bundle.map_surface?.edges ?? []).some(
      (edge) =>
        edge.edge_id !== undefined &&
        edgeIds.has(edge.edge_id) &&
        (edge.start_node_id === operation.target_id || edge.end_node_id === operation.target_id),
    );
    if (!connected || !road.centerline) {
      continue;
    }
    if (pointsEqual(road.centerline[0], oldPosition)) {
      road.centerline[0] = [...operation.position] as Position3;
    }
    if (pointsEqual(road.centerline[road.centerline.length - 1], oldPosition)) {
      road.centerline[road.centerline.length - 1] = [...operation.position] as Position3;
    }
  }

  for (const intersection of bundle.render_geometry?.intersections ?? []) {
    if (intersection.node_id !== operation.target_id || !intersection.polygon) {
      continue;
    }
    const deltaX = operation.position[0] - oldPosition[0];
    const deltaY = operation.position[1] - oldPosition[1];
    const deltaZ = operation.position[2] - oldPosition[2];
    intersection.polygon = intersection.polygon.map(([x, y, z]) => [
      x + deltaX,
      y + deltaY,
      z + deltaZ,
    ]);
  }
}

function clientPointToScene(
  event: MouseEvent<SVGSVGElement>,
  svg: SVGSVGElement | null,
  viewport: ViewportState,
  z: number,
): Position3 | null {
  if (!svg) {
    return null;
  }
  const rect = svg.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    return null;
  }
  const x = viewport.x + ((event.clientX - rect.left) / rect.width) * viewport.width;
  const y = viewport.y + ((event.clientY - rect.top) / rect.height) * viewport.height;
  return [roundPointValue(x), roundPointValue(y), z];
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

function sampleDisplayedVehicles(
  bundle: BundlePayload | null,
  motionClockS: number,
): Array<VehicleSnapshotPayload & { heading_rad?: number; speed?: number }> {
  const baseVehicles = (bundle?.snapshot?.vehicles ?? []).map((vehicle) => ({
    ...vehicle,
    heading_rad: 0,
    speed: 0,
  }));
  if (!bundle?.motion_segments?.length) {
    return baseVehicles;
  }

  const vehiclesById = new Map<number, VehicleSnapshotPayload & { heading_rad?: number; speed?: number }>();
  for (const vehicle of baseVehicles) {
    if (vehicle.vehicle_id !== undefined) {
      vehiclesById.set(vehicle.vehicle_id, vehicle);
    }
  }

  const motionSegments = [...bundle.motion_segments].sort(
    (left, right) =>
      (left.start_time_s ?? 0) - (right.start_time_s ?? 0) ||
      (left.segment_index ?? 0) - (right.segment_index ?? 0),
  );

  for (const segment of motionSegments) {
    const vehicleId = segment.vehicle_id;
    if (
      vehicleId === undefined ||
      segment.start_time_s === undefined ||
      segment.end_time_s === undefined
    ) {
      continue;
    }
    const existing = vehiclesById.get(vehicleId);
    if (!existing) {
      vehiclesById.set(vehicleId, {
        vehicle_id: vehicleId,
        node_id: segment.start_node_id,
        position: segment.start_position,
        operational_state: "moving",
        heading_rad: segment.heading_rad ?? 0,
        speed: 0,
      });
    } else if (existing.position === undefined && segment.start_position) {
      existing.position = segment.start_position;
    }
    if (motionClockS < segment.start_time_s) {
      continue;
    }
    if (motionClockS > segment.end_time_s) {
      const settled = vehiclesById.get(vehicleId);
      if (settled) {
        settled.position = segment.end_position ?? settled.position;
        settled.node_id = segment.end_node_id ?? settled.node_id;
        settled.heading_rad = segment.heading_rad ?? settled.heading_rad;
        settled.speed = 0;
      }
      continue;
    }
    const sampled = sampleMotionSegmentPayload(segment, motionClockS);
    const active = vehiclesById.get(vehicleId);
    if (active) {
      active.position = sampled.position;
      active.node_id = segment.start_node_id ?? active.node_id;
      active.operational_state = "moving";
      active.heading_rad = sampled.headingRad;
      active.speed = sampled.speed;
    }
  }

  return [...vehiclesById.values()].sort(
    (left, right) => (left.vehicle_id ?? 0) - (right.vehicle_id ?? 0),
  );
}

function sampleMotionSegmentPayload(
  segment: MotionSegmentPayload,
  timestampS: number,
): { position: Position3; headingRad: number; speed: number } {
  const startTimeS = segment.start_time_s ?? 0;
  const endTimeS = segment.end_time_s ?? startTimeS;
  const durationS = Math.max((segment.duration_s ?? endTimeS - startTimeS), 0.0001);
  const boundedTimestampS = Math.min(Math.max(timestampS, startTimeS), endTimeS);
  const progress = Math.min(
    1,
    Math.max(0, (boundedTimestampS - startTimeS) / durationS),
  );
  const pathPoints = (segment.path_points?.length ?? 0) >= 2
    ? (segment.path_points as Position3[])
    : ([segment.start_position ?? [0, 0, 0], segment.end_position ?? [0, 0, 0]] as Position3[]);
  const pathLength = polylineLength(pathPoints);
  const distanceAlongPath = pathLength * progress;
  return {
    position: samplePathPosition(pathPoints, distanceAlongPath),
    headingRad: headingAlongPath(pathPoints, distanceAlongPath),
    speed: sampleSegmentSpeed(segment, progress),
  };
}

function sampleSegmentSpeed(segment: MotionSegmentPayload, progress: number): number {
  const peakSpeed = segment.peak_speed ?? segment.nominal_speed ?? 0;
  if ((segment.profile_kind ?? "").startsWith("triangle")) {
    return progress <= 0.5 ? peakSpeed * (progress / 0.5) : peakSpeed * ((1 - progress) / 0.5);
  }
  return peakSpeed;
}

function polylineLength(points: Position3[]): number {
  let total = 0;
  for (let index = 1; index < points.length; index += 1) {
    total += pointDistance(points[index - 1], points[index]);
  }
  return total;
}

function samplePathPosition(points: Position3[], distanceAlongPath: number): Position3 {
  if (points.length === 0) {
    return [0, 0, 0];
  }
  if (points.length === 1) {
    return points[0];
  }
  let remaining = Math.min(Math.max(distanceAlongPath, 0), polylineLength(points));
  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const segmentLength = pointDistance(start, end);
    if (segmentLength <= 0) {
      continue;
    }
    if (remaining <= segmentLength) {
      const progress = remaining / segmentLength;
      return [
        start[0] + (end[0] - start[0]) * progress,
        start[1] + (end[1] - start[1]) * progress,
        start[2] + (end[2] - start[2]) * progress,
      ];
    }
    remaining -= segmentLength;
  }
  return points[points.length - 1];
}

function headingAlongPath(points: Position3[], distanceAlongPath: number): number {
  if (points.length < 2) {
    return 0;
  }
  let remaining = Math.min(Math.max(distanceAlongPath, 0), polylineLength(points));
  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const segmentLength = pointDistance(start, end);
    if (segmentLength <= 0) {
      continue;
    }
    if (remaining <= segmentLength) {
      return Math.atan2(end[1] - start[1], end[0] - start[0]);
    }
    remaining -= segmentLength;
  }
  const start = points[points.length - 2];
  const end = points[points.length - 1];
  return Math.atan2(end[1] - start[1], end[0] - start[0]);
}

function pointDistance(start: Position3, end: Position3): number {
  return Math.hypot(end[0] - start[0], end[1] - start[1], end[2] - start[2]);
}

function maxMotionTime(bundle: BundlePayload | null): number {
  return Math.max(
    0,
    ...((bundle?.motion_segments ?? []).map((segment) => segment.end_time_s ?? 0)),
  );
}

function radiansToDegrees(value: number): number {
  return (value * 180) / Math.PI;
}

function renderVehicleMarker(): JSX.Element {
  return (
    <>
      <circle r={0.34} className="vehicle-body" />
      <path d="M 0.08 -0.16 L 0.58 0 L 0.08 0.16 Z" className="vehicle-heading" />
    </>
  );
}

function findDisplayedVehicleById(
  vehicles: Array<VehicleSnapshotPayload & { heading_rad?: number; speed?: number }>,
  vehicleId: number | null,
): (VehicleSnapshotPayload & { heading_rad?: number; speed?: number }) | null {
  if (vehicleId === null) {
    return null;
  }
  return vehicles.find((vehicle) => vehicle.vehicle_id === vehicleId) ?? null;
}

function formatHeadingDegrees(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "unknown";
  }
  const normalized = ((radiansToDegrees(value) % 360) + 360) % 360;
  return `${Math.round(normalized)} deg`;
}

function describeSelectedTarget(
  selectedTarget: SelectedTarget | null,
  selectedVehicleId: number | null,
): string {
  if (selectedTarget?.kind === "road") {
    return `road ${selectedTarget.roadId}`;
  }
  if (selectedTarget?.kind === "area") {
    return `zone ${selectedTarget.areaId}`;
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
  if (selectedTarget.kind === "area") {
    return "zone";
  }
  if (selectedTarget.kind === "queue") {
    return "queue";
  }
  return "hazard";
}

function describeOperation(operation: EditOperation): string {
  if (operation.kind === "move_node") {
    return `move node ${operation.target_id} to ${operation.position.join(", ")}`;
  }
  if (operation.kind === "set_road_centerline") {
    return `edit road ${operation.target_id} with ${operation.points.length} centerline point(s)`;
  }
  return `edit zone ${operation.target_id} with ${operation.points.length} polygon vertex/vertices`;
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function pointsEqual(left: Position3 | undefined, right: Position3): boolean {
  return (
    Array.isArray(left) &&
    left[0] === right[0] &&
    left[1] === right[1] &&
    left[2] === right[2]
  );
}

function roundPointValue(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function formatMaybeNumber(value: number | null): string {
  return value === null ? "pending" : String(value);
}

function formatSeconds(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(1)}s`;
}

export default App;
