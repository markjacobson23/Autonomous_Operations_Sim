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
  recent_commands?: RecentCommandPayload[];
  route_previews?: RoutePreviewPayload[];
  vehicle_inspections?: VehicleInspectionPayload[];
  ai_assist?: AIAssistPayload;
  session_control?: SessionControlPayload;
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
  traffic_control_state?: string | null;
  traffic_control_detail?: string | null;
  route_ahead_node_ids?: number[];
  route_ahead_edge_ids?: number[];
  diagnostics?: DiagnosticPayload[];
};

type RecentCommandPayload = {
  command_type?: string;
  edge_id?: number;
  vehicle_id?: number;
  node_id?: number;
  destination_node_id?: number;
  hazard_label?: string;
  vehicle_type?: string;
  payload?: number;
  velocity?: number;
  max_payload?: number;
  max_speed?: number;
  job?: {
    id?: string;
    tasks?: Array<Record<string, unknown>>;
  };
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
  vehicle_type?: string;
  presentation_key?: string;
  display_name?: string;
  role_label?: string;
  body_length_m?: number;
  body_width_m?: number;
  spacing_envelope_m?: number;
  primary_color?: string;
  accent_color?: string;
  road_id?: string | null;
  lane_id?: string | null;
  lane_index?: number | null;
  lane_role?: string | null;
  lane_directionality?: string | null;
  lane_selection_reason?: string | null;
};

type MotionSegmentPayload = {
  vehicle_id?: number;
  segment_index?: number;
  edge_id?: number;
  road_id?: string | null;
  start_node_id?: number;
  end_node_id?: number;
  start_time_s?: number;
  end_time_s?: number;
  duration_s?: number;
  distance?: number;
  start_position?: Position3;
  end_position?: Position3;
  path_points?: Position3[];
  body_length_m?: number;
  body_width_m?: number;
  spacing_envelope_m?: number;
  heading_rad?: number;
  nominal_speed?: number;
  peak_speed?: number;
  acceleration_mps2?: number;
  deceleration_mps2?: number;
  profile_kind?: string;
  lane_id?: string | null;
  lane_index?: number | null;
  lane_role?: string | null;
  lane_directionality?: string | null;
  lane_selection_reason?: string | null;
};

type TrafficBaselinePayload = {
  control_points?: TrafficControlPointPayload[];
  queue_records?: Array<{
    vehicle_id?: number;
    vehicle_ids?: number[];
    node_id?: number;
    road_id?: string | null;
    queue_start_s?: number;
    queue_end_s?: number;
    reason?: string;
  }>;
};

type TrafficControlPointPayload = {
  control_id?: string;
  node_id?: number;
  control_type?: string;
  controlled_road_ids?: string[];
  stop_line_ids?: string[];
  protected_conflict_zone_ids?: string[];
  signal_ready?: boolean;
};

type TrafficRoadStatePayload = {
  road_id?: string;
  active_vehicle_ids?: number[];
  queued_vehicle_ids?: number[];
  occupancy_count?: number;
  min_spacing_m?: number | null;
  congestion_intensity?: number;
  congestion_level?: string;
  control_state?: string;
  stop_line_ids?: string[];
  protected_conflict_zone_ids?: string[];
};

type TrafficSnapshotPayload = {
  timestamp_s?: number;
  road_states?: TrafficRoadStatePayload[];
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

type SessionControlPayload = {
  play_state?: "paused" | "playing" | string;
  step_seconds?: number;
  route_preview_endpoint?: string;
  command_endpoint?: string;
  session_control_endpoint?: string;
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
  traffic_snapshot?: TrafficSnapshotPayload;
  authoring?: AuthoringPayload;
  session_control?: SessionControlPayload;
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
  | { kind: "queue"; roadId: string }
  | { kind: "hazard"; edgeId: number };

type RouteDestinationMarker = {
  destinationNodeId: number;
  position: Position3;
  selected: boolean;
  previewVehicleId?: number;
};

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

type LiveCommandDraft = {
  vehicleId: string;
  destinationNodeId: string;
  edgeId: string;
  nodeId: string;
  hazardLabel: string;
  spawnVehicleType: string;
  spawnPayload: string;
  spawnVelocity: string;
  spawnMaxPayload: string;
  spawnMaxSpeed: string;
  jobId: string;
  jobTaskNodeId: string;
  jobTaskDestinationNodeId: string;
  stepSeconds: string;
};

type DragState =
  | { kind: "node"; nodeId: number; z: number }
  | { kind: "road-point"; roadId: string; pointIndex: number; z: number }
  | { kind: "area-point"; areaId: string; pointIndex: number; z: number };

type WorkspaceTab = "operate" | "traffic" | "fleet" | "editor" | "analyze";

const architecture = {
  primaryStack: "React + TypeScript + Vite",
  authority: "Python simulator remains authoritative",
  launchMode: "Live session + live authoring through versioned bundle surfaces",
};

const workspaceTabs: Array<{
  id: WorkspaceTab;
  label: string;
  summary: string;
}> = [
  { id: "operate", label: "Operate", summary: "Primary map and route workflow" },
  { id: "traffic", label: "Traffic", summary: "Congestion, queues, and hazards" },
  { id: "fleet", label: "Fleet", summary: "Selection and runtime admin" },
  { id: "editor", label: "Editor", summary: "Scenario authoring" },
  { id: "analyze", label: "Analyze", summary: "Diagnostics and AI review" },
];

const sessionActions = [
  "Launch Live Run",
  "Reconnect Bundle",
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
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("operate");
  const [selectedTarget, setSelectedTarget] = useState<SelectedTarget | null>(null);
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [editorEnabled, setEditorEnabled] = useState(false);
  const [draftTransaction, setDraftTransaction] = useState<EditTransaction>(emptyTransaction);
  const [validationMessages, setValidationMessages] = useState<ValidationMessage[]>([]);
  const [editorMessage, setEditorMessage] = useState("Authoring surface is standing by.");
  const [liveCommandMessage, setLiveCommandMessage] = useState(
    "Live command controls are standing by.",
  );
  const [bundlePath, setBundlePath] = useState<string | null>(null);
  const [liveCommandDraft, setLiveCommandDraft] = useState<LiveCommandDraft>({
    vehicleId: "",
    destinationNodeId: "",
    edgeId: "",
    nodeId: "",
    hazardLabel: "temporary closure",
    spawnVehicleType: "GENERIC",
    spawnPayload: "0",
    spawnVelocity: "0",
    spawnMaxPayload: "120",
    spawnMaxSpeed: "12",
    jobId: "live-injection",
    jobTaskNodeId: "",
    jobTaskDestinationNodeId: "",
    stepSeconds: "0.5",
  });
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<number[] | null>(null);
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

    setBundlePath(bundlePath);

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
    const sessionControl = bootstrap.bundle?.session_control;
    if (sessionControl?.play_state !== "playing" || !bundlePath) {
      return;
    }

    let cancelled = false;
    const refresh = () => {
      void fetch(bundlePath)
        .then(async (response) => {
          if (!response.ok) {
            throw new Error(`Bundle request failed with ${response.status}`);
          }
          return response.json() as Promise<BundlePayload>;
        })
        .then((bundle) => {
          if (!cancelled) {
            setBootstrap((current) => buildBootstrapSummary(bundle, current.message));
          }
        })
        .catch(() => {
          if (!cancelled) {
            setLiveCommandMessage("Live bundle refresh failed.");
          }
        });
    };

    const intervalId = window.setInterval(refresh, 2000);
    refresh();
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [bundlePath, bootstrap.bundle?.session_control?.play_state]);

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
  const minDisplayedSpacingM = computeMinDisplayedSpacing(displayedVehicles);
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const trafficRoadById = new Map(
    trafficRoadStates
      .filter((state) => state.road_id)
      .map((state) => [state.road_id as string, state]),
  );
  const trafficRoadStatesRanked = [...trafficRoadStates].sort(
    (left, right) =>
      trafficRoadPressureScore(right) - trafficRoadPressureScore(left) ||
      (left.road_id ?? "").localeCompare(right.road_id ?? ""),
  );
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + (roadState.queued_vehicle_ids?.length ?? 0),
    0,
  );
  const congestedRoadCount = trafficRoadStates.filter(
    (roadState) => (roadState.congestion_intensity ?? 0) > 0.2,
  ).length;
  const peakTrafficIntensity = trafficRoadStates.reduce(
    (peak, roadState) => Math.max(peak, roadState.congestion_intensity ?? 0),
    0,
  );
  const bounds = computeSceneBounds(bundle);
  const routePreviews = bootstrap.commandCenter.route_previews ?? [];
  const inspections = bootstrap.commandCenter.vehicle_inspections ?? [];
  const recentCommands = bootstrap.commandCenter.recent_commands ?? [];
  const suggestions = bootstrap.commandCenter.ai_assist?.suggestions ?? [];
  const anomalies = bootstrap.commandCenter.ai_assist?.anomalies ?? [];
  const explanations = bootstrap.commandCenter.ai_assist?.explanations ?? [];
  const commandCenterSelectedVehicleIds = bootstrap.commandCenter.selected_vehicle_ids ?? [];
  const effectiveSelectedVehicleIds =
    selectedVehicleIds ?? commandCenterSelectedVehicleIds;
  const primaryVehicleId =
    effectiveSelectedVehicleIds[0] ??
    inspections[0]?.vehicle_id ??
    null;
  const selectedRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === primaryVehicleId) ??
    routePreviews[0] ??
    null;
  const routeDestinationMarkers = [...routePreviews.reduce((markers, preview) => {
    const destinationNodeId = preview.destination_node_id;
    if (destinationNodeId === undefined) {
      return markers;
    }
    const position = findNodePosition(bundle?.map_surface?.nodes ?? [], destinationNodeId);
    if (!position) {
      return markers;
    }
    const selected = selectedRoutePreview?.vehicle_id !== undefined
      ? selectedRoutePreview.vehicle_id === preview.vehicle_id
      : false;
    const existingMarker = markers.get(destinationNodeId);
    if (!existingMarker || (!existingMarker.selected && selected)) {
      markers.set(destinationNodeId, {
        destinationNodeId,
        position,
        selected,
        previewVehicleId: preview.vehicle_id,
      });
    }
    return markers;
  }, new Map<number, RouteDestinationMarker>()).values()];
  const selectedRoutePreviewRoadIds = new Set(
    (bundle?.render_geometry?.roads ?? [])
      .filter((road) =>
        routePreviews.some(
          (preview) =>
            effectiveSelectedVehicleIds.includes(preview.vehicle_id ?? -1) &&
            (preview.edge_ids ?? []).some((edgeId) => (road.edge_ids ?? []).includes(edgeId)),
        ),
      )
      .map((road) => road.road_id)
      .filter((roadId): roadId is string => Boolean(roadId)),
  );
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle" ? selectedTarget.vehicleId : primaryVehicleId;
  const selectedVehicle = findVehicleById(bundle, selectedVehicleId);
  const displayedSelectedVehicle =
    selectedVehicleId !== null
      ? displayedVehicles.find((vehicle) => vehicle.vehicle_id === selectedVehicleId) ?? null
      : null;
  const selectedInspection = selectedVehicleId
    ? inspections.find((inspection) => inspection.vehicle_id === selectedVehicleId) ?? null
    : null;
  const selectedVehicleInspections = inspections.filter((inspection) =>
    effectiveSelectedVehicleIds.includes(inspection.vehicle_id ?? -1),
  );
  const selectedFleetVehicles = effectiveSelectedVehicleIds
    .map(
      (vehicleId) =>
        displayedVehicles.find((vehicle) => vehicle.vehicle_id === vehicleId) ??
        findVehicleById(bundle, vehicleId),
    )
    .filter(
      (
        vehicle,
      ): vehicle is VehicleSnapshotPayload & {
        heading_rad?: number;
        speed?: number;
      } => vehicle !== null,
    );
  const selectedFleetPrimaryVehicle =
    selectedFleetVehicles[0] ?? displayedSelectedVehicle ?? selectedVehicle ?? null;
  const selectedFleetPrimaryVehicleId = selectedFleetPrimaryVehicle?.vehicle_id ?? null;
  const selectedFleetPrimaryInspection =
    selectedFleetPrimaryVehicleId !== null
      ? selectedVehicleInspections.find(
          (inspection) => inspection.vehicle_id === selectedFleetPrimaryVehicleId,
        ) ?? selectedInspection
      : selectedInspection;
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
      ? selectedFleetStateEntries
          .slice(0, 3)
          .map(([state, count]) => `${count} ${state}`)
          .join(" · ")
      : "No selected vehicles";
  const selectedFleetRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === selectedFleetPrimaryVehicleId) ??
    routePreviews.find((preview) => effectiveSelectedVehicleIds.includes(preview.vehicle_id ?? -1)) ??
    null;
  const selectedFleetRouteSummary = selectedFleetRoutePreview
    ? `Node ${formatMaybeNumber(selectedFleetRoutePreview.destination_node_id ?? null)}${
        selectedFleetRoutePreview.total_distance !== undefined
          ? ` · ${formatMeters(selectedFleetRoutePreview.total_distance)}`
          : ""
      }`
    : "No route preview attached";
  const selectedFleetRouteDetail = selectedFleetRoutePreview
    ? `${selectedFleetRoutePreview.is_actionable ? "Actionable" : "Held"}${
        selectedFleetRoutePreview.reason ? ` · ${selectedFleetRoutePreview.reason}` : ""
      }`
    : selectedFleetPrimaryInspection?.route_ahead_node_ids?.length
      ? `Inspection sees ${selectedFleetPrimaryInspection.route_ahead_node_ids.length} upcoming node(s)`
      : "No route preview context available";
  const reviewAnomalies = [...anomalies].sort(
    (left, right) =>
      reviewSeverityRank(left.severity) - reviewSeverityRank(right.severity) ||
      (left.summary ?? "").localeCompare(right.summary ?? "") ||
      (left.anomaly_id ?? "").localeCompare(right.anomaly_id ?? ""),
  );
  const reviewSuggestions = [...suggestions].sort(
    (left, right) =>
      reviewPriorityRank(left.priority) - reviewPriorityRank(right.priority) ||
      (left.kind ?? "").localeCompare(right.kind ?? "") ||
      (left.summary ?? "").localeCompare(right.summary ?? "") ||
      (left.suggestion_id ?? "").localeCompare(right.suggestion_id ?? ""),
  );
  const reviewExplanations = [...explanations].sort(
    (left, right) =>
      Number((left.vehicle_id ?? Number.MAX_SAFE_INTEGER) === selectedVehicleId) -
        Number((right.vehicle_id ?? Number.MAX_SAFE_INTEGER) === selectedVehicleId) ||
      (left.vehicle_id ?? Number.MAX_SAFE_INTEGER) - (right.vehicle_id ?? Number.MAX_SAFE_INTEGER) ||
      (left.summary ?? "").localeCompare(right.summary ?? ""),
  );
  const reviewRecentCommands = recentCommands.slice(0, 4);
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedRoadTraffic =
    selectedRoad?.road_id !== undefined
      ? trafficRoadById.get(selectedRoad.road_id) ?? null
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
          (record) => record.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedQueueTraffic =
    typeof selectedQueueRecord?.road_id === "string"
      ? trafficRoadById.get(selectedQueueRecord.road_id) ?? null
      : null;
  const selectedHazardEdge =
    selectedTarget?.kind === "hazard"
      ? findEdgeById(bundle?.map_surface?.edges ?? [], selectedTarget.edgeId)
      : null;
  const blockedEdgeIds = [...(bootstrap.bundle?.snapshot?.blocked_edge_ids ?? [])].sort(
    (left, right) => left - right,
  );
  const trafficFocusRoadState =
    selectedRoadTraffic ?? trafficRoadStatesRanked[0] ?? null;
  const trafficFocusRoad =
    trafficFocusRoadState?.road_id !== undefined
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === trafficFocusRoadState.road_id,
        ) ?? selectedRoad
      : selectedRoad;
  const trafficMonitoringRoadStates = (() => {
    const states: TrafficRoadStatePayload[] = [];
    const seenRoadIds = new Set<string>();
    if (trafficFocusRoadState?.road_id) {
      states.push(trafficFocusRoadState);
      seenRoadIds.add(trafficFocusRoadState.road_id);
    }
    for (const roadState of trafficRoadStatesRanked) {
      if (!roadState.road_id || seenRoadIds.has(roadState.road_id)) {
        continue;
      }
      states.push(roadState);
      seenRoadIds.add(roadState.road_id);
      if (states.length >= 5) {
        break;
      }
    }
    return states;
  })();
  const trafficQueueRecords = [...(bundle?.traffic_baseline?.queue_records ?? [])].sort(
    (left, right) => {
      const leftRoadState =
        typeof left.road_id === "string" ? trafficRoadById.get(left.road_id) ?? null : null;
      const rightRoadState =
        typeof right.road_id === "string" ? trafficRoadById.get(right.road_id) ?? null : null;
      const leftVehicleCount =
        left.vehicle_ids?.length ?? (left.vehicle_id !== undefined ? 1 : 0);
      const rightVehicleCount =
        right.vehicle_ids?.length ?? (right.vehicle_id !== undefined ? 1 : 0);
      return (
        trafficRoadPressureScore(rightRoadState) +
        rightVehicleCount * 10 -
        (trafficRoadPressureScore(leftRoadState) + leftVehicleCount * 10) ||
        (left.road_id ?? "").localeCompare(right.road_id ?? "") ||
        (left.node_id ?? 0) - (right.node_id ?? 0)
      );
    },
  );
  const authoring = bootstrap.bundle?.authoring;
  const sessionControl = bootstrap.bundle?.session_control ?? null;
  const liveSessionPlaying = sessionControl?.play_state === "playing";
  const editCount = draftTransaction.operations.length;
  const hasDraftEdits = editCount > 0;
  const validationBlocked = validationMessages.length > 0;
  const editorModeLabel = editorEnabled ? "Edit mode on" : "Edit mode off";
  const draftStatusLabel = hasDraftEdits
    ? `${editCount} staged edit${editCount === 1 ? "" : "s"}`
    : "No draft edits";
  const validationStatusLabel = validationBlocked ? "Validation blocked" : "Validation clean";
  const workingScenarioPath = authoring?.working_scenario_path ?? "unavailable";
  const sourceScenarioPath = authoring?.source_scenario_path ?? "unavailable";
  const authoringModeLabel = authoring?.mode ?? "authoring";

  function applyLoadedBundle(
    bundlePayload: BundlePayload,
    message: string,
    options: {
      refitViewport?: boolean;
      resetDraft?: boolean;
      resetValidation?: boolean;
      resetDrag?: boolean;
    } = {},
  ): void {
    if (options.refitViewport ?? true) {
      setViewport(fitViewportToBundle(bundlePayload));
    }
    if (options.resetDraft ?? true) {
      setDraftTransaction(emptyTransaction);
    }
    if (options.resetValidation ?? true) {
      setValidationMessages([]);
    }
    if (options.resetDrag ?? true) {
      setDragState(null);
    }
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

  function selectVehicle(
    vehicleId: number | undefined,
    options: { additive?: boolean } = {},
  ): void {
    if (vehicleId !== undefined) {
      setSelectedTarget({ kind: "vehicle", vehicleId });
      setSelectedVehicleIds((current) => {
        const currentSelection = current ?? [];
        if (options.additive) {
          if (currentSelection.includes(vehicleId)) {
            return currentSelection.filter((existingVehicleId) => existingVehicleId !== vehicleId);
          }
          return [...currentSelection, vehicleId];
        }
        return [vehicleId];
      });
    }
  }

  function selectAllVisibleVehicles(): void {
    const visibleVehicleIds = displayedVehicles
      .map((vehicle) => vehicle.vehicle_id)
      .filter((vehicleId): vehicleId is number => vehicleId !== undefined);
    if (visibleVehicleIds.length === 0) {
      return;
    }
    setSelectedVehicleIds(visibleVehicleIds);
    setSelectedTarget({ kind: "vehicle", vehicleId: visibleVehicleIds[0] });
  }

  function clearVehicleSelection(): void {
    setSelectedVehicleIds([]);
    if (selectedTarget?.kind === "vehicle") {
      setSelectedTarget(null);
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

  function selectQueue(roadId: string | undefined): void {
    if (roadId) {
      setSelectedTarget({ kind: "queue", roadId });
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

  useEffect(() => {
    setLiveCommandDraft((current) => ({
      ...current,
      vehicleId:
        current.vehicleId ||
        (effectiveSelectedVehicleIds[0] !== undefined
          ? String(effectiveSelectedVehicleIds[0])
          : current.vehicleId),
      destinationNodeId:
        current.destinationNodeId ||
        (routePreviews[0]?.destination_node_id !== undefined
          ? String(routePreviews[0].destination_node_id)
          : current.destinationNodeId),
      edgeId:
        current.edgeId ||
        (selectedTarget?.kind === "hazard"
          ? String(selectedTarget.edgeId)
          : selectedRoad?.edge_ids?.[0] !== undefined
            ? String(selectedRoad.edge_ids[0])
            : current.edgeId),
      nodeId:
        current.nodeId ||
        (selectedInspection?.current_node_id !== undefined
          ? String(selectedInspection.current_node_id)
          : current.nodeId),
      jobTaskNodeId:
        current.jobTaskNodeId ||
        (selectedInspection?.current_node_id !== undefined
          ? String(selectedInspection.current_node_id)
          : current.jobTaskNodeId),
      jobTaskDestinationNodeId:
        current.jobTaskDestinationNodeId ||
        (routePreviews[0]?.destination_node_id !== undefined
          ? String(routePreviews[0].destination_node_id)
          : current.jobTaskDestinationNodeId),
      stepSeconds:
        current.stepSeconds || String(sessionControl?.step_seconds ?? 0.5),
    }));
  }, [
    routePreviews,
    selectedInspection?.current_node_id,
    selectedRoad?.edge_ids,
    selectedTarget?.kind,
    selectedTarget?.kind === "hazard" ? selectedTarget.edgeId : undefined,
    effectiveSelectedVehicleIds,
    sessionControl?.step_seconds,
  ]);

  function parseDraftInteger(value: string): number | null {
    if (!value.trim()) {
      return null;
    }
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function parseDraftFloat(value: string): number | null {
    if (!value.trim()) {
      return null;
    }
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function resolveCommandVehicleIds(fallbackVehicleId: number | null = null): number[] {
    if (selectedVehicleIds !== null) {
      return selectedVehicleIds.length > 0 ? selectedVehicleIds : fallbackVehicleId !== null ? [fallbackVehicleId] : [];
    }
    if (selectedTarget?.kind === "vehicle") {
      return [selectedTarget.vehicleId];
    }
    if (fallbackVehicleId !== null) {
      return [fallbackVehicleId];
    }
    return commandCenterSelectedVehicleIds;
  }

  function submitLiveCommand(commandPayload: Record<string, unknown>): void {
    const endpoint = sessionControl?.command_endpoint ?? "/api/live/command";
    setLiveCommandMessage("Sending live command to the Python session...");
    const targetVehicleIds =
      commandPayload.vehicle_ids !== undefined
        ? commandPayload.vehicle_ids
        : effectiveSelectedVehicleIds;
    void fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...commandPayload,
        selected_vehicle_ids: targetVehicleIds,
      }),
    })
      .then(async (response) => {
        const payload = (await response.json()) as {
          ok?: boolean;
          command_result?: { message?: string | null };
          bundle?: BundlePayload;
          message?: string;
        };
        if (!response.ok) {
          throw new Error(payload.message ?? `Command request failed with ${response.status}`);
        }
        return payload;
      })
      .then((payload) => {
        if (payload.bundle) {
          refreshLiveBundle(
            payload.bundle,
            payload.ok ? "Live command applied." : "Live command response returned.",
          );
        }
        setLiveCommandMessage(
          payload.command_result?.message ?? (payload.ok ? "Command accepted." : "Command rejected."),
        );
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Command request failed";
        setLiveCommandMessage(message);
      });
  }

  function submitRoutePreview(previewPayload: Record<string, unknown>): void {
    const endpoint = sessionControl?.route_preview_endpoint ?? "/api/live/preview";
    setLiveCommandMessage("Requesting a route preview from the Python session...");
    const targetVehicleIds =
      previewPayload.vehicle_ids !== undefined
        ? previewPayload.vehicle_ids
        : effectiveSelectedVehicleIds;
    void fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...previewPayload,
        selected_vehicle_ids: targetVehicleIds,
      }),
    })
      .then(async (response) => {
        const payload = (await response.json()) as {
          ok?: boolean;
          bundle?: BundlePayload;
          message?: string;
        };
        if (!response.ok) {
          throw new Error(payload.message ?? `Preview request failed with ${response.status}`);
        }
        return payload;
      })
      .then((payload) => {
        if (payload.bundle) {
          refreshLiveBundle(payload.bundle, "Route preview refreshed.");
        }
        setLiveCommandMessage(payload.ok ? "Route preview loaded." : "Route preview response returned.");
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Route preview request failed";
        setLiveCommandMessage(message);
      });
  }

  function controlLiveSession(action: "play" | "pause" | "step"): void {
    const endpoint = sessionControl?.session_control_endpoint ?? "/api/live/session/control";
    const stepSeconds = parseDraftFloat(liveCommandDraft.stepSeconds) ?? sessionControl?.step_seconds ?? 0.5;
    setLiveCommandMessage(
      action === "step"
        ? "Advancing the live session by one explicit step..."
        : action === "play"
          ? "Setting live session refresh to play mode..."
          : "Pausing live session refresh...",
    );
    void fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        delta_s: stepSeconds,
        selected_vehicle_ids: effectiveSelectedVehicleIds,
      }),
    })
      .then(async (response) => {
        const payload = (await response.json()) as {
          ok?: boolean;
          bundle?: BundlePayload;
          message?: string;
        };
        if (!response.ok) {
          throw new Error(payload.message ?? `Session control failed with ${response.status}`);
        }
        return payload;
      })
      .then((payload) => {
        if (payload.bundle) {
          refreshLiveBundle(
            payload.bundle,
            action === "step" ? "Live session advanced by one step." : "Session control updated.",
          );
        }
        setLiveCommandMessage(
          action === "step"
            ? "Single-step completed."
            : action === "play"
              ? "Session refresh set to play mode."
              : "Session refresh paused.",
        );
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : "Session control failed";
        setLiveCommandMessage(message);
      });
  }

  function assignDestinationFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.destinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      setLiveCommandMessage("Enter a valid vehicle id and destination node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitLiveCommand({
      command_type: "assign_vehicle_destination",
      vehicle_id: vehicleId,
      destination_node_id: destinationNodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function previewRouteFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.destinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      setLiveCommandMessage("Enter a valid vehicle id and destination node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitRoutePreview({
      vehicle_id: vehicleId,
      destination_node_id: destinationNodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function repositionVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const nodeId = parseDraftInteger(liveCommandDraft.nodeId);
    if (vehicleId === null || nodeId === null) {
      setLiveCommandMessage("Enter a valid vehicle id and node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitLiveCommand({
      command_type: "reposition_vehicle",
      vehicle_id: vehicleId,
      node_id: nodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function blockRoadFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "block_edge",
      edge_id: edgeId,
    });
  }

  function unblockRoadFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "unblock_edge",
      edge_id: edgeId,
    });
  }

  function spawnVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const nodeId = parseDraftInteger(liveCommandDraft.nodeId);
    const maxSpeed = parseDraftFloat(liveCommandDraft.spawnMaxSpeed);
    const maxPayload = parseDraftFloat(liveCommandDraft.spawnMaxPayload);
    const payload = parseDraftFloat(liveCommandDraft.spawnPayload) ?? 0;
    const velocity = parseDraftFloat(liveCommandDraft.spawnVelocity) ?? 0;
    if (vehicleId === null || nodeId === null || maxSpeed === null || maxPayload === null) {
      setLiveCommandMessage("Enter valid spawn vehicle, node, max speed, and payload values first.");
      return;
    }
    submitLiveCommand({
      command_type: "spawn_vehicle",
      vehicle_id: vehicleId,
      node_id: nodeId,
      max_speed: maxSpeed,
      max_payload: maxPayload,
      vehicle_type: liveCommandDraft.spawnVehicleType || "GENERIC",
      payload,
      velocity,
    });
  }

  function removeVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    if (vehicleId === null) {
      setLiveCommandMessage("Enter a valid vehicle id first.");
      return;
    }
    submitLiveCommand({
      command_type: "remove_vehicle",
      vehicle_id: vehicleId,
    });
  }

  function injectJobFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.jobTaskDestinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      setLiveCommandMessage("Enter a valid vehicle id and job destination node id first.");
      return;
    }
    submitLiveCommand({
      command_type: "inject_job",
      vehicle_id: vehicleId,
      job: {
        id: liveCommandDraft.jobId || `live-job-${vehicleId}-${destinationNodeId}`,
        tasks: [
          {
            kind: "move",
            destination_node_id: destinationNodeId,
          },
        ],
      },
    });
  }

  function declareTemporaryHazardFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "declare_temporary_hazard",
      edge_id: edgeId,
      hazard_label: liveCommandDraft.hazardLabel || "temporary closure",
    });
  }

  function clearTemporaryHazardFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "clear_temporary_hazard",
      edge_id: edgeId,
    });
  }

  function refreshLiveBundle(bundlePayload: BundlePayload, message: string): void {
    applyLoadedBundle(bundlePayload, message, {
      refitViewport: false,
      resetDraft: false,
      resetValidation: false,
      resetDrag: false,
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
    <div className={`shell shell-tab-${activeTab} ${activeTab === "editor" ? "shell-editor-focused" : ""}`}>
      <div className="shell-accent shell-accent-left" aria-hidden="true" />
      <div className="shell-accent shell-accent-right" aria-hidden="true" />
      <header className="masthead panel">
        <div className="masthead-copy">
          <p className="eyebrow">Step 64 Task/resource realism expansion</p>
          <h1>Autonomous Ops Command Deck</h1>
          <p className="lede">
            Stop lines, yield controls, and protected conflict areas are now
            visible in the serious UI, so controlled junctions show why vehicles
            are pausing instead of flattening traffic into a single static line.
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
          <span className="metric-label">Selected Fleet</span>
          <strong>{formatMaybeNumber(effectiveSelectedVehicleIds.length)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Min Spacing</span>
          <strong>{formatMeters(minDisplayedSpacingM)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Queued Vehicles</span>
          <strong>{formatMaybeNumber(queuedVehicleCount)}</strong>
        </div>
        <div className="metric-pill">
          <span className="metric-label">Congested Roads</span>
          <strong>{formatMaybeNumber(congestedRoadCount)}</strong>
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

      <nav className="workspace-tabs panel" aria-label="Workspace tabs">
        {workspaceTabs.map((tab) => (
          <button
            key={tab.id}
            className={`workspace-tab workspace-tab-${tab.id} ${activeTab === tab.id ? "workspace-tab-active" : ""}`}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            aria-pressed={activeTab === tab.id}
          >
            <strong>{tab.label}</strong>
            <span>{tab.summary}</span>
          </button>
        ))}
      </nav>

      <main className="workspace">
        <section className="main-column operate-pane">
          <section className="stage panel" aria-labelledby="scene-title">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Scene Region</p>
                <h2 id="scene-title">Operations Viewport</h2>
              </div>
              <div className="status-stack">
                <span className="status-pill">Camera controls active</span>
                <span className="status-pill secondary">Selection active</span>
                <span className="status-pill accent">Layer toggles active</span>
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
                    (bundle?.render_geometry?.roads ?? []).map((road, index) => {
                      const roadPath = toSmoothPathString(road.centerline);
                      if (!roadPath) {
                        return null;
                      }
                      const roadWidth = Math.min(
                        Math.max((road.width_m ?? 1.4) * 0.34, 0.4),
                        1.72,
                      );
                      const roadTraffic = trafficRoadById.get(road.road_id ?? "");
                      return (
                        <g key={road.road_id ?? `road-${index}`}>
                          <path
                            d={roadPath}
                            className={`scene-road-heatmap scene-road-heatmap-${
                              roadTraffic?.congestion_level ?? "free"
                            }`}
                            strokeWidth={roadWidth + 0.34}
                            style={{
                              opacity: Math.max(
                                0.05,
                                (roadTraffic?.congestion_intensity ?? 0) * 0.38,
                              ),
                            }}
                            aria-hidden="true"
                          />
                          <path
                            d={roadPath}
                            className={`scene-road scene-road-${road.road_class ?? "connector"} ${
                              selectedTarget?.kind === "road" &&
                              selectedTarget.roadId === road.road_id
                                ? "selected"
                                : ""
                            }`}
                            strokeWidth={roadWidth}
                            onClick={() => selectRoad(road.road_id)}
                            onMouseEnter={() => {
                              setHoverTarget({
                                label: road.road_id ?? "road",
                                detail: roadTraffic
                                  ? `${road.directionality ?? "unknown"} · ${
                                      road.lane_count ?? 0
                                    } lane(s) · ${roadTraffic.congestion_level} · ${
                                      roadTraffic.queued_vehicle_ids?.length ?? 0
                                    } queued`
                                  : `${road.directionality ?? "unknown"} · ${
                                      road.lane_count ?? 0
                                    } lane(s)`,
                              });
                            }}
                          />
                        </g>
                      );
                    })}

                  {layers.intersections &&
                    (bundle?.render_geometry?.intersections ?? []).map((intersection, index) => {
                      const controlPoint = (bundle?.traffic_baseline?.control_points ?? []).find(
                        (point) => point.node_id === intersection.node_id,
                      );
                      const intersectionPath = toSmoothPathString(intersection.polygon, true);
                      if (!intersectionPath) {
                        return null;
                      }
                      return (
                        <path
                          key={intersection.intersection_id ?? `intersection-${index}`}
                          d={intersectionPath}
                          className="scene-intersection"
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: intersection.intersection_id ?? "intersection",
                              detail: controlPoint
                                ? `${controlPoint.control_type} · ${
                                    controlPoint.controlled_road_ids?.length ?? 0
                                  } road(s) · ${
                                    controlPoint.stop_line_ids?.length ?? 0
                                  } stop line(s)`
                                : intersection.intersection_type ?? "intersection",
                            })
                          }
                        />
                      );
                    })}

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

                  {layers.reservations &&
                    (bundle?.traffic_baseline?.queue_records ?? []).map((record, queueIndex) => {
                      const road = (bundle?.render_geometry?.roads ?? []).find(
                        (entry) => entry.road_id === record.road_id,
                      );
                      const roadTraffic =
                        typeof record.road_id === "string"
                          ? trafficRoadById.get(record.road_id) ?? null
                          : null;
                      const roadPath = toSmoothPathString(road?.centerline);
                      if (!roadPath) {
                        return null;
                      }
                      const roadWidth = Math.min(
                        Math.max((road?.width_m ?? 1.4) * 0.34, 0.4),
                        1.72,
                      );
                      return (
                        <path
                          key={`reservation-${queueIndex}`}
                          d={roadPath}
                          className={`scene-reservation scene-queue-overlay ${
                            selectedTarget?.kind === "queue" &&
                            selectedTarget.roadId === record.road_id
                              ? "selected"
                              : selectedRoutePreviewRoadIds.has(record.road_id ?? "")
                                ? "selected preview"
                              : ""
                          }`}
                          strokeWidth={roadWidth + 0.42}
                          onClick={() => selectQueue(record.road_id ?? undefined)}
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Queue ${record.road_id ?? "road"}`,
                              detail: `${roadTraffic?.queued_vehicle_ids?.length ?? 0} vehicle(s) queued`,
                            })
                          }
                        />
                      );
                    })}

                  {layers.vehicles &&
                    displayedVehicles.map((vehicle, vehicleIndex) => {
                      const position = vehicle.position ?? [0, 0, 0];
                      const isSelected = effectiveSelectedVehicleIds.includes(
                        vehicle.vehicle_id ?? -1,
                      );
                      const vehicleLabel = `${vehiclePresentationBadge(vehicle)} ${vehicle.vehicle_id ?? vehicleIndex}`;
                      const labelWidth = Math.max(1.12, vehicleLabel.length * 0.22 + 0.34);
                      const labelY = position[1] - Math.max((vehicle.body_length_m ?? 1.12) * 0.66, 1);
                      const selectionEnvelopeLength = Math.max(
                        vehicle.spacing_envelope_m ?? spacingEnvelopeFromVehicle(vehicle),
                        0.9,
                      );
                      const selectionEnvelopeWidth = Math.max((vehicle.body_width_m ?? 0.62) * 1.9, 1);
                      return (
                        <g
                          key={vehicle.vehicle_id ?? `vehicle-${vehicleIndex}`}
                          className={isSelected ? "scene-vehicle selected" : "scene-vehicle"}
                          onClick={(event) =>
                            selectVehicle(vehicle.vehicle_id, {
                              additive: event.shiftKey || event.metaKey || event.ctrlKey,
                            })
                          }
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Vehicle ${vehicle.vehicle_id ?? vehicleIndex}`,
                              detail: `${vehicle.operational_state ?? "unknown_state"} · ${
                                vehicle.lane_id ?? "lane-unassigned"
                              } · ${formatMeters(vehicle.spacing_envelope_m ?? null)} envelope`,
                            })
                          }
                        >
                          {isSelected ? (
                            <rect
                              x={position[0] - selectionEnvelopeLength * 0.56}
                              y={position[1] - selectionEnvelopeWidth * 0.5}
                              width={selectionEnvelopeLength * 1.12}
                              height={selectionEnvelopeWidth}
                              rx={0.28}
                              className="vehicle-selection-ring"
                            />
                          ) : null}
                          <g transform={`translate(${position[0]} ${position[1]}) rotate(${radiansToDegrees(
                            vehicle.heading_rad ?? 0,
                          )})`}>
                            {renderVehicleEnvelope(vehicle)}
                            {renderVehicleGlyph(vehicle)}
                          </g>
                          <g className="vehicle-label">
                            <rect
                              x={position[0] - labelWidth * 0.5}
                              y={labelY - 0.24}
                              width={labelWidth}
                              height={0.46}
                              rx={0.16}
                              className="vehicle-label-bg"
                            />
                            <text x={position[0]} y={labelY} className="vehicle-label-text">
                              {vehicleLabel}
                            </text>
                          </g>
                        </g>
                      );
                    })}

                  {layers.routes &&
                    routeDestinationMarkers.map((marker) => (
                      <g
                        key={`route-destination-${marker.destinationNodeId}`}
                        className={`scene-destination scene-route-endpoint ${
                          marker.selected ? "selected" : ""
                        }`}
                        transform={`translate(${marker.position[0]} ${marker.position[1]})`}
                      >
                        <circle
                          r={marker.selected ? 1.08 : 0.86}
                          className="scene-destination-threshold"
                        />
                        <circle
                          r={marker.selected ? 0.38 : 0.3}
                          className="scene-destination-core"
                        />
                      </g>
                    ))}

                  {layers.routes &&
                    routePreviews.map((preview, previewIndex) => {
                      const routePoints = buildRoutePreviewPoints(
                        preview,
                        bundle?.map_surface?.nodes ?? [],
                      );
                      const routePath = toSmoothPathString(routePoints);
                      if (!routePath) {
                        return null;
                      }
                      return (
                        <path
                          key={`route-preview-${previewIndex}`}
                          d={routePath}
                          className={`scene-route-preview ${
                            preview.vehicle_id === selectedVehicleId ? "selected" : ""
                          }`}
                          onMouseEnter={() =>
                            setHoverTarget({
                              label: `Route preview V${preview.vehicle_id ?? "?"}`,
                              detail: preview.reason ?? "actionable preview",
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
                </svg>

                <div className="focus-card">
                  <strong>Stop lines and yield controls are now live</strong>
                  <p>
                    Traffic snapshots now carry control-state overlays and
                    inspection reasons, so dense corridors stay legible while
                    still revealing where vehicles are waiting.
                  </p>
                </div>
                <div className="scene-legend">
                  <span className="legend-item">
                    <span className="legend-swatch road" />
                    Roads
                  </span>
                  <span className="legend-item">
                    <span className="legend-swatch traffic" />
                    Traffic heatmap
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
                <div className="overview-card operate-route-planning">
                  <p className="eyebrow">Route Planning</p>
                  <h3>Primary Operator Workflow</h3>
                  <div className="selection-strip">
                    <span className="selection-pill">
                      Fleet selection: {effectiveSelectedVehicleIds.length} vehicle(s)
                    </span>
                    <span className="selection-pill">
                      Selected preview:{" "}
                      {selectedRoutePreview?.vehicle_id !== undefined
                        ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id)}`
                        : "none"}
                    </span>
                    <span className="selection-pill">
                      Destination node:{" "}
                      {formatMaybeNumber(selectedRoutePreview?.destination_node_id ?? null)}
                    </span>
                  </div>
                  <div className="route-planning-grid">
                    <label className="form-field">
                      <span>Vehicle ID</span>
                      <input
                        type="number"
                        value={liveCommandDraft.vehicleId}
                        onChange={(event) =>
                          setLiveCommandDraft((current) => ({
                            ...current,
                            vehicleId: event.target.value,
                          }))
                        }
                        placeholder={selectedVehicleId !== null ? String(selectedVehicleId) : "77"}
                      />
                    </label>
                    <label className="form-field">
                      <span>Destination Node</span>
                      <input
                        type="number"
                        value={liveCommandDraft.destinationNodeId}
                        onChange={(event) =>
                          setLiveCommandDraft((current) => ({
                            ...current,
                            destinationNodeId: event.target.value,
                          }))
                        }
                        placeholder={
                          routePreviews[0]?.destination_node_id !== undefined
                            ? String(routePreviews[0].destination_node_id)
                            : "3"
                        }
                      />
                    </label>
                    <label className="form-field">
                      <span>Reposition Node</span>
                      <input
                        type="number"
                        value={liveCommandDraft.nodeId}
                        onChange={(event) =>
                          setLiveCommandDraft((current) => ({
                            ...current,
                            nodeId: event.target.value,
                          }))
                        }
                        placeholder={
                          selectedInspection?.current_node_id !== undefined
                            ? String(selectedInspection.current_node_id)
                            : "1"
                        }
                      />
                    </label>
                    <label className="form-field">
                      <span>Step Seconds</span>
                      <input
                        type="number"
                        step="0.1"
                        value={liveCommandDraft.stepSeconds}
                        onChange={(event) =>
                          setLiveCommandDraft((current) => ({
                            ...current,
                            stepSeconds: event.target.value,
                          }))
                        }
                        placeholder={String(sessionControl?.step_seconds ?? 0.5)}
                      />
                    </label>
                  </div>
                  <div className="route-primary-actions action-row">
                    <button
                      className="scene-button scene-button-primary"
                      type="button"
                      onClick={previewRouteFromDraft}
                      disabled={!sessionControl?.route_preview_endpoint}
                    >
                      Preview Route
                    </button>
                    <button
                      className="scene-button scene-button-primary"
                      type="button"
                      onClick={assignDestinationFromDraft}
                      disabled={!sessionControl?.command_endpoint}
                    >
                      Assign Destination
                    </button>
                    <button
                      className="scene-button"
                      type="button"
                      onClick={repositionVehicleFromDraft}
                      disabled={!sessionControl?.command_endpoint}
                    >
                      Reposition Vehicle
                    </button>
                  </div>
                  <div className="route-preview-summary">
                    <div className="preview-badge">
                      <span className="preview-label">Selected Preview</span>
                      <strong>
                        V{formatMaybeNumber(selectedRoutePreview?.vehicle_id ?? null)} · Node{" "}
                        {formatMaybeNumber(selectedRoutePreview?.destination_node_id ?? null)}
                      </strong>
                    </div>
                    <ul className="mini-list">
                      <li>Actionable: {selectedRoutePreview?.is_actionable ? "yes" : "no"}</li>
                      <li>Reason: {selectedRoutePreview?.reason ?? "none"}</li>
                      <li>
                        Distance: {formatMeters(selectedRoutePreview?.total_distance ?? null)}
                      </li>
                      <li>Edges: {(selectedRoutePreview?.edge_ids ?? []).join(", ") || "none"}</li>
                      <li>Nodes: {(selectedRoutePreview?.node_ids ?? []).join(" → ") || "none"}</li>
                    </ul>
                  </div>
                </div>
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
                    {routeDestinationMarkers.map((marker) => (
                      <g
                        key={`minimap-route-destination-${marker.destinationNodeId}`}
                        className={`minimap-destination ${marker.selected ? "selected" : ""}`}
                      >
                        <circle
                          cx={scaleX(marker.position[0], bounds)}
                          cy={scaleY(marker.position[1], bounds)}
                          r={marker.selected ? 2.0 : 1.55}
                          className="minimap-destination-threshold"
                        />
                        <circle
                          cx={scaleX(marker.position[0], bounds)}
                          cy={scaleY(marker.position[1], bounds)}
                          r={marker.selected ? 0.85 : 0.62}
                          className="minimap-destination-core"
                        />
                      </g>
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

              </aside>
            </div>
            <section className="panel info-panel operate-session-controls" aria-labelledby="session-control-title">
              <div className="panel-header compact">
                <div>
                  <p className="eyebrow">Operate Region</p>
                  <h2 id="session-control-title">Compact Session Status</h2>
                </div>
                <span className="status-pill secondary">
                  {liveSessionPlaying ? "playing" : "paused"} · step{" "}
                  {formatSeconds(sessionControl?.step_seconds ?? null)}
                </span>
              </div>
              <div className="section-stack">
                <div className="subsection">
                  <div className="action-row">
                    <button
                      className="scene-button scene-button-primary"
                      type="button"
                      onClick={() => controlLiveSession("play")}
                      disabled={!sessionControl?.session_control_endpoint}
                    >
                      Play
                    </button>
                    <button
                      className="scene-button"
                      type="button"
                      onClick={() => controlLiveSession("pause")}
                      disabled={!sessionControl?.session_control_endpoint}
                    >
                      Pause
                    </button>
                    <button
                      className="scene-button"
                      type="button"
                      onClick={() => controlLiveSession("step")}
                      disabled={!sessionControl?.session_control_endpoint}
                    >
                      Single-Step
                    </button>
                  </div>
                  <ul className="mini-list">
                    <li>Mode: {sessionControl?.play_state ?? "paused"}</li>
                    <li>Step size: {formatSeconds(sessionControl?.step_seconds ?? null)}</li>
                    <li>Session channel: {sessionControl?.session_control_endpoint ?? "unbound"}</li>
                  </ul>
                  <p className="status-copy">{liveCommandMessage}</p>
                </div>
              </div>
            </section>
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
          <section className="panel info-panel editor-pane" aria-labelledby="editor-title">
            <div className="panel-header compact editor-panel-header">
              <div>
                <p className="eyebrow">Authoring Region</p>
                <h2 id="editor-title">Scenario Authoring</h2>
                <p className="status-copy">
                  Dedicated controls for the working scenario, staged geometry, and validation
                  live here.
                </p>
              </div>
              <div className="editor-header-stack" aria-label="Editor mode summary">
                <span className={`status-pill ${editorEnabled ? "accent" : "secondary"}`}>
                  {editorModeLabel}
                </span>
                <span className={`status-pill ${hasDraftEdits ? "accent" : "secondary"}`}>
                  {draftStatusLabel}
                </span>
                <span className={`status-pill ${validationBlocked ? "secondary" : "accent"}`}>
                  {validationStatusLabel}
                </span>
              </div>
            </div>
            <div className="section-stack">
              <div className="editor-mode-banner">
                <div className="editor-mode-copy">
                  <p className="eyebrow">Working Scenario</p>
                  <strong>{workingScenarioPath}</strong>
                  <p>
                    Source: {sourceScenarioPath} · Mode: {authoringModeLabel} · Save endpoint{" "}
                    {authoring?.save_endpoint ? "ready" : "unavailable"}
                  </p>
                </div>
                <div className="editor-status-grid">
                  <div className="editor-status-card">
                    <span>Edit mode</span>
                    <strong>{editorModeLabel}</strong>
                    <p>
                      {editorEnabled
                        ? "Handles are active and geometry moves will stage into the draft."
                        : "Turn edit mode on to stage geometry changes and reveal the authoring handles."}
                    </p>
                  </div>
                  <div className="editor-status-card">
                    <span>Draft edits</span>
                    <strong>{draftStatusLabel}</strong>
                    <p>
                      {hasDraftEdits
                        ? "Save to persist the staged geometry or reload to discard it."
                        : "No staged geometry edits are present yet."}
                    </p>
                  </div>
                  <div className="editor-status-card">
                    <span>Validation</span>
                    <strong>{validationStatusLabel}</strong>
                    <p>
                      {validationBlocked
                        ? "Resolve the messages below before saving."
                        : "Draft validation is clean and the working scenario is ready."}
                    </p>
                  </div>
                </div>
              </div>

              <div className="subsection editor-controls">
                <div className="subsection-header">
                  <h3>Authoring Controls</h3>
                  <span className={`status-pill ${editorEnabled ? "accent" : "secondary"}`}>
                    {editorEnabled ? "Ready to author" : "Edit mode paused"}
                  </span>
                </div>
                <div className="action-row editor-action-row">
                  <button className="scene-button scene-button-primary" type="button" onClick={toggleEditMode}>
                    {editorEnabled ? "Pause Edit Mode" : "Edit Scene"}
                  </button>
                  <button
                    className="scene-button scene-button-primary"
                    type="button"
                    onClick={saveScenario}
                    disabled={!authoring?.save_endpoint || !hasDraftEdits}
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

              <div className="editor-detail-grid">
                <div className="overview-card editor-state-card">
                  <div className="subsection-header">
                    <p className="eyebrow">Authoring State</p>
                    <span className={`status-pill ${validationBlocked ? "secondary" : "accent"}`}>
                      {validationStatusLabel}
                    </span>
                  </div>
                  <ul className="mini-list editor-state-list">
                    <li>{editorEnabled ? "Edit mode is active" : "Edit mode is paused"}</li>
                    <li>Working copy: {workingScenarioPath}</li>
                    <li>Source scenario: {sourceScenarioPath}</li>
                    <li>
                      Geometry: {formatMaybeNumber(authoring?.editable_node_count ?? null)} nodes ·{" "}
                      {formatMaybeNumber(authoring?.editable_road_count ?? null)} roads ·{" "}
                      {formatMaybeNumber(authoring?.editable_area_count ?? null)} zones
                    </li>
                  </ul>
                </div>

                <div className="subsection editor-validation-card">
                  <div className="subsection-header">
                    <h3>Validation Messages</h3>
                    <span className={`status-pill ${validationBlocked ? "secondary" : "accent"}`}>
                      {validationStatusLabel}
                    </span>
                  </div>
                  <ul className="editor-message-list">
                    {validationMessages.length > 0 ? (
                      validationMessages.map((message, index) => {
                        const severity = (message.severity ?? "info").toLowerCase();
                        return (
                          <li
                            key={`${message.code ?? "validation"}-${index}`}
                            className={`editor-validation-item editor-validation-item-${severity}`}
                          >
                            <div className="editor-item-heading">
                              <strong>{message.code ?? severity.toUpperCase()}</strong>
                              <span className="editor-item-chip">
                                {message.target_kind ?? "global"}
                                {message.target_id !== undefined && message.target_id !== null
                                  ? ` · ${message.target_id}`
                                  : ""}
                              </span>
                            </div>
                            <p>{message.message ?? "No validation message"}</p>
                          </li>
                        );
                      })
                    ) : (
                      <li className="editor-empty-state">No validation issues are currently blocking the draft.</li>
                    )}
                  </ul>
                </div>

                <div className="subsection editor-draft-card">
                  <div className="subsection-header">
                    <h3>Draft Operations</h3>
                    <span className={`status-pill ${hasDraftEdits ? "accent" : "secondary"}`}>
                      {draftStatusLabel}
                    </span>
                  </div>
                  <ul className="editor-operation-list">
                    {draftTransaction.operations.length > 0 ? (
                      draftTransaction.operations.map((operation, index) => (
                        <li
                          key={`${operation.kind}-${operation.target_id}-${index}`}
                          className="editor-draft-item"
                        >
                          <div className="editor-item-heading">
                            <strong>{operation.kind.split("_").join(" ")}</strong>
                            <span className="editor-item-chip">
                              {operation.kind === "move_node"
                                ? `node ${operation.target_id}`
                                : operation.kind === "set_road_centerline"
                                  ? `road ${operation.target_id}`
                                  : `zone ${operation.target_id}`}
                            </span>
                          </div>
                          <p>{describeOperation(operation)}</p>
                        </li>
                      ))
                    ) : (
                      <li className="editor-empty-state">No geometry edits are staged yet.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section className="panel info-panel fleet-pane" aria-labelledby="command-center-title">
            <div className="panel-header compact fleet-panel-header">
              <div>
                <p className="eyebrow">Command-Center Region</p>
                <h2 id="command-center-title">Fleet Control</h2>
                <p className="fleet-panel-lede">
                  Dedicated fleet selection, batch actions, runtime admin changes, and inspection
                  context stay grouped here so the control surface reads like an operations desk.
                </p>
              </div>
              <div className="fleet-panel-meta">
                <span className="status-pill secondary">
                  {formatMaybeNumber(effectiveSelectedVehicleIds.length)} selected
                </span>
                <span className="status-pill accent">
                  Lead {selectedFleetPrimaryVehicleId !== null ? `V${selectedFleetPrimaryVehicleId}` : "none"}
                </span>
              </div>
            </div>

            <div className="fleet-control-grid">
              <article className="subsection fleet-card fleet-summary-card">
                <div className="subsection-header fleet-card-header">
                  <div>
                    <h3>Current Controlled Fleet</h3>
                    <p className="fleet-card-lede">
                      The selected fleet stays on top so the operator can scan lead vehicle,
                      state mix, and destination context before making a move.
                    </p>
                  </div>
                  <span className="fleet-card-badge">
                    {formatMaybeNumber(effectiveSelectedVehicleIds.length)} selected
                  </span>
                </div>
                <div className="fleet-summary-grid">
                  <div className="fleet-summary-metric">
                    <span>Lead vehicle</span>
                    <strong>
                      {selectedFleetPrimaryVehicleId !== null
                        ? `V${selectedFleetPrimaryVehicleId}`
                        : "none"}
                    </strong>
                    <p>
                      {selectedFleetPrimaryVehicle?.display_name ??
                        selectedFleetPrimaryVehicle?.role_label ??
                        "No primary selection"}
                    </p>
                  </div>
                  <div className="fleet-summary-metric">
                    <span>Selection scope</span>
                    <strong>{formatMaybeNumber(displayedVehicles.length)} visible</strong>
                    <p>
                      {effectiveSelectedVehicleIds.length > 1
                        ? `Batch-ready control is active for ${effectiveSelectedVehicleIds.length} vehicles.`
                        : "Single vehicle focus is active."}
                    </p>
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
                    <span className="fleet-empty-state">No fleet state is currently selected.</span>
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
                          onClick={() => selectVehicle(vehicle.vehicle_id)}
                          aria-pressed={vehicleId === selectedFleetPrimaryVehicleId}
                          aria-label={`Focus vehicle ${formatMaybeNumber(vehicleId)}`}
                        >
                          <span className="fleet-vehicle-pill-id">
                            V{formatMaybeNumber(vehicleId)}
                          </span>
                          <span className="fleet-vehicle-pill-state">
                            {vehicle.operational_state ?? "unknown"}
                          </span>
                          <span className="fleet-vehicle-pill-detail">
                            {vehicle.display_name ?? vehicle.role_label ?? vehicle.vehicle_type ?? "Vehicle"}
                          </span>
                          <span className="fleet-vehicle-pill-route">
                            {vehicleRoutePreview?.destination_node_id !== undefined
                              ? `→ node ${formatMaybeNumber(vehicleRoutePreview.destination_node_id)}`
                              : vehicle.lane_id !== undefined && vehicle.lane_id !== null
                                ? `${vehicle.lane_id}`
                                : "No route preview"}
                          </span>
                        </button>
                      );
                    })
                  ) : (
                    <div className="fleet-empty-state">
                      No vehicles are selected yet. Use the batch tools to build a controlled fleet.
                    </div>
                  )}
                </div>
              </article>

              <article className="subsection fleet-card fleet-batch-card">
                <div className="subsection-header fleet-card-header">
                  <div>
                    <h3>Batch Selection</h3>
                    <p className="fleet-card-lede">
                      Use the viewport to shape a deliberate batch before applying fleet-scoped
                      actions.
                    </p>
                  </div>
                  <span className="fleet-card-badge">Viewport batch</span>
                </div>
                <div className="fleet-batch-summary">
                  <span className="fleet-batch-chip">Selected {effectiveSelectedVehicleIds.length}</span>
                  <span className="fleet-batch-chip">Visible {displayedVehicles.length}</span>
                  <span className="fleet-batch-chip">
                    Lead{" "}
                    {selectedFleetPrimaryVehicleId !== null
                      ? `V${selectedFleetPrimaryVehicleId}`
                      : "none"}
                  </span>
                </div>
                <div className="selection-strip fleet-selection-actions">
                  <button
                    className="scene-button scene-button-primary"
                    type="button"
                    onClick={selectAllVisibleVehicles}
                    disabled={displayedVehicles.length === 0}
                  >
                    Select Visible
                  </button>
                  <button
                    className="scene-button"
                    type="button"
                    onClick={clearVehicleSelection}
                    disabled={effectiveSelectedVehicleIds.length === 0}
                  >
                    Clear Selection
                  </button>
                </div>
                <p className="status-copy">
                  Batch mode is active when more than one vehicle is selected, and fleet-scoped
                  commands apply to every vehicle in that controlled set.
                </p>
              </article>

              <article className="subsection fleet-card fleet-admin-card">
                <div className="subsection-header fleet-card-header">
                  <div>
                    <h3>Runtime Admin Actions</h3>
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
                        <input
                          type="number"
                          value={liveCommandDraft.nodeId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              nodeId: event.target.value,
                            }))
                          }
                          placeholder={
                            selectedFleetPrimaryInspection?.current_node_id !== undefined
                              ? String(selectedFleetPrimaryInspection.current_node_id)
                              : selectedFleetRoutePreview?.destination_node_id !== undefined
                                ? String(selectedFleetRoutePreview.destination_node_id)
                                : "1"
                          }
                        />
                      </label>
                      <label className="form-field">
                        <span>Vehicle ID</span>
                        <input
                          type="number"
                          value={liveCommandDraft.vehicleId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              vehicleId: event.target.value,
                            }))
                          }
                          placeholder={
                            selectedFleetPrimaryVehicleId !== null
                              ? String(selectedFleetPrimaryVehicleId)
                              : "77"
                          }
                        />
                      </label>
                      <label className="form-field">
                        <span>Spawn Type</span>
                        <input
                          type="text"
                          value={liveCommandDraft.spawnVehicleType}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              spawnVehicleType: event.target.value,
                            }))
                          }
                          placeholder="GENERIC"
                        />
                      </label>
                      <label className="form-field">
                        <span>Spawn Max Speed</span>
                        <input
                          type="number"
                          step="0.1"
                          value={liveCommandDraft.spawnMaxSpeed}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              spawnMaxSpeed: event.target.value,
                            }))
                          }
                          placeholder="12"
                        />
                      </label>
                      <label className="form-field">
                        <span>Spawn Max Payload</span>
                        <input
                          type="number"
                          step="0.1"
                          value={liveCommandDraft.spawnMaxPayload}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              spawnMaxPayload: event.target.value,
                            }))
                          }
                          placeholder="120"
                        />
                      </label>
                      <label className="form-field">
                        <span>Spawn Payload</span>
                        <input
                          type="number"
                          step="0.1"
                          value={liveCommandDraft.spawnPayload}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              spawnPayload: event.target.value,
                            }))
                          }
                          placeholder="0"
                        />
                      </label>
                      <label className="form-field">
                        <span>Spawn Velocity</span>
                        <input
                          type="number"
                          step="0.1"
                          value={liveCommandDraft.spawnVelocity}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              spawnVelocity: event.target.value,
                            }))
                          }
                          placeholder="0"
                        />
                      </label>
                    </div>
                    <div className="action-row fleet-action-row">
                      <button
                        className="scene-button scene-button-primary"
                        type="button"
                        onClick={spawnVehicleFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
                        Spawn Vehicle
                      </button>
                      <button
                        className="scene-button"
                        type="button"
                        onClick={removeVehicleFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
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
                        <input
                          type="text"
                          value={liveCommandDraft.jobId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              jobId: event.target.value,
                            }))
                          }
                          placeholder="live-job-77"
                        />
                      </label>
                      <label className="form-field">
                        <span>Job Node</span>
                        <input
                          type="number"
                          value={liveCommandDraft.jobTaskNodeId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              jobTaskNodeId: event.target.value,
                            }))
                          }
                          placeholder={
                            selectedFleetPrimaryInspection?.current_node_id !== undefined
                              ? String(selectedFleetPrimaryInspection.current_node_id)
                              : "1"
                          }
                        />
                      </label>
                      <label className="form-field">
                        <span>Job Destination</span>
                        <input
                          type="number"
                          value={liveCommandDraft.jobTaskDestinationNodeId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              jobTaskDestinationNodeId: event.target.value,
                            }))
                          }
                          placeholder={
                            selectedFleetRoutePreview?.destination_node_id !== undefined
                              ? String(selectedFleetRoutePreview.destination_node_id)
                              : "3"
                          }
                        />
                      </label>
                    </div>
                    <div className="action-row fleet-action-row">
                      <button
                        className="scene-button"
                        type="button"
                        onClick={injectJobFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
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
                        <input
                          type="number"
                          value={liveCommandDraft.edgeId}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              edgeId: event.target.value,
                            }))
                          }
                          placeholder={
                            selectedTarget?.kind === "hazard"
                              ? String(selectedTarget.edgeId)
                              : selectedRoad?.edge_ids?.[0] !== undefined
                                ? String(selectedRoad.edge_ids[0])
                                : "2"
                          }
                        />
                      </label>
                      <label className="form-field">
                        <span>Hazard Label</span>
                        <input
                          type="text"
                          value={liveCommandDraft.hazardLabel}
                          onChange={(event) =>
                            setLiveCommandDraft((current) => ({
                              ...current,
                              hazardLabel: event.target.value,
                            }))
                          }
                          placeholder="temporary closure"
                        />
                      </label>
                    </div>
                    <div className="action-row fleet-action-row">
                      <button
                        className="scene-button"
                        type="button"
                        onClick={declareTemporaryHazardFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
                        Declare Hazard
                      </button>
                      <button
                        className="scene-button"
                        type="button"
                        onClick={clearTemporaryHazardFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
                        Clear Hazard
                      </button>
                      <button
                        className="scene-button"
                        type="button"
                        onClick={blockRoadFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
                        Block Road
                      </button>
                      <button
                        className="scene-button"
                        type="button"
                        onClick={unblockRoadFromDraft}
                        disabled={!sessionControl?.command_endpoint}
                      >
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
                    <h3>Inspection and Support Context</h3>
                    <p className="fleet-card-lede">
                      The selected vehicle stays visible alongside recent commands so the operator
                      can confirm what changed and what still needs attention.
                    </p>
                  </div>
                  <span className="fleet-card-badge">Inspection context</span>
                </div>

                {selectedFleetPrimaryInspection ? (
                  <div className="fleet-inspection-spotlight">
                    <div className="fleet-inspection-spotlight-header">
                      <div>
                        <strong>
                          {selectedFleetPrimaryVehicle?.display_name ??
                            selectedFleetPrimaryVehicle?.role_label ??
                            "Vehicle"}{" "}
                          {formatMaybeNumber(selectedFleetPrimaryInspection.vehicle_id ?? null)}
                        </strong>
                        <p>
                          {selectedFleetPrimaryVehicle?.operational_state ??
                            selectedFleetPrimaryInspection.operational_state ??
                            "unknown_state"}
                        </p>
                      </div>
                      <span className="fleet-inspection-chip">Current target</span>
                    </div>
                    <div className="fleet-inspection-metric-grid" aria-label="Fleet inspection metrics">
                      <div className="fleet-inspection-metric">
                        <span>Node</span>
                        <strong>
                          {formatMaybeNumber(selectedFleetPrimaryInspection.current_node_id ?? null)}
                        </strong>
                      </div>
                      <div className="fleet-inspection-metric">
                        <span>ETA</span>
                        <strong>{formatSeconds(selectedFleetPrimaryInspection.eta_s ?? null)}</strong>
                      </div>
                      <div className="fleet-inspection-metric">
                        <span>Job</span>
                        <strong>{selectedFleetPrimaryInspection.current_job_id ?? "none"}</strong>
                      </div>
                      <div className="fleet-inspection-metric">
                        <span>Wait</span>
                        <strong>{selectedFleetPrimaryInspection.wait_reason ?? "none"}</strong>
                      </div>
                      <div className="fleet-inspection-metric">
                        <span>Control</span>
                        <strong>{selectedFleetPrimaryInspection.traffic_control_state ?? "none"}</strong>
                      </div>
                      <div className="fleet-inspection-metric">
                        <span>Route</span>
                        <strong>{selectedFleetRouteSummary}</strong>
                      </div>
                    </div>
                    <ul className="fleet-inspection-context-list">
                      <li>
                        Lane:{" "}
                        {selectedFleetPrimaryVehicle?.lane_id
                          ? `${selectedFleetPrimaryVehicle.lane_id} · ${
                              selectedFleetPrimaryVehicle.lane_role ?? "travel"
                            }`
                          : "unassigned"}
                      </li>
                      <li>
                        Lane direction: {selectedFleetPrimaryVehicle?.lane_directionality ?? "unknown"}
                      </li>
                      <li>
                        Lane note: {selectedFleetPrimaryVehicle?.lane_selection_reason ?? "none"}
                      </li>
                      <li>
                        Spacing: {formatMeters(selectedFleetPrimaryVehicle?.spacing_envelope_m ?? null)}
                      </li>
                      <li>
                        Heading: {formatHeadingDegrees(selectedFleetPrimaryVehicle?.heading_rad ?? null)}
                      </li>
                      <li>{selectedFleetRouteDetail}</li>
                    </ul>
                    <div className="fleet-inspection-diagnostic-strip">
                      {(selectedFleetPrimaryInspection.diagnostics ?? []).length > 0 ? (
                        (selectedFleetPrimaryInspection.diagnostics ?? []).map((diagnostic, diagIndex) => {
                          const diagnosticSeverity = normalizeReviewLevel(diagnostic.severity, "info");
                          return (
                            <span
                              key={`${diagnostic.code ?? "diag"}-${diagIndex}`}
                              className={`diagnostic-pill review-diagnostic-pill review-diagnostic-pill-${diagnosticSeverity}`}
                            >
                              <strong>{diagnosticSeverity.toUpperCase()}</strong>
                              <span>{diagnostic.code ?? "diagnostic"}</span>
                            </span>
                          );
                        })
                      ) : (
                        <span className="fleet-empty-state">No diagnostics are currently attached.</span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="fleet-empty-state">
                    Select a vehicle to reveal per-vehicle inspection context and live command trace.
                  </div>
                )}

                <div className="fleet-inspection-grid">
                  <div className="fleet-inspection-panel">
                    <div className="fleet-inspection-panel-header">
                      <h4>Selected Vehicle Roster</h4>
                      <span>
                        {effectiveSelectedVehicleIds.length > 1
                          ? `${effectiveSelectedVehicleIds.length} vehicles`
                          : "single target"}
                      </span>
                    </div>
                    <ul className="fleet-inspection-list">
                      {selectedVehicleInspections.length > 0 ? (
                        selectedVehicleInspections.map((inspection) => {
                          const inspectionVehicle =
                            selectedFleetVehicles.find(
                              (vehicle) => vehicle.vehicle_id === inspection.vehicle_id,
                            ) ??
                            displayedVehicles.find(
                              (vehicle) => vehicle.vehicle_id === inspection.vehicle_id,
                            ) ??
                            null;
                          return (
                            <li key={`fleet-inspection-${inspection.vehicle_id ?? "vehicle"}`}>
                              <div className="fleet-inspection-row-header">
                                <strong>V{formatMaybeNumber(inspection.vehicle_id ?? null)}</strong>
                                <span>
                                  {inspectionVehicle?.operational_state ??
                                    inspection.operational_state ??
                                    "unknown_state"}
                                </span>
                              </div>
                              <p>
                                Node {formatMaybeNumber(inspection.current_node_id ?? null)} · ETA{" "}
                                {formatSeconds(inspection.eta_s ?? null)} ·{" "}
                                {inspection.traffic_control_detail ??
                                  inspection.wait_reason ??
                                  "No detailed inspection note"}
                              </p>
                            </li>
                          );
                        })
                      ) : (
                        <li className="fleet-empty-state">
                          No selected vehicle inspections are available yet.
                        </li>
                      )}
                    </ul>
                  </div>

                  <div className="fleet-inspection-panel">
                    <div className="fleet-inspection-panel-header">
                      <h4>Recent Command Trace</h4>
                      <span>{recentCommands.length} total</span>
                    </div>
                    <ul className="data-list fleet-command-list">
                      {recentCommands.length > 0 ? (
                        recentCommands.slice(0, 4).map((command, index) => (
                          <li key={`${command.command_type ?? "command"}-${index}`}>
                            {describeRecentCommand(command)}
                          </li>
                        ))
                      ) : (
                        <li>No command history is available yet.</li>
                      )}
                    </ul>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <section className="panel info-panel traffic-pane" aria-labelledby="traffic-title">
            <div className="panel-header compact traffic-panel-header">
              <div>
                <p className="eyebrow">Traffic Control Room</p>
                <h2 id="traffic-title">Traffic Control</h2>
                <p className="traffic-panel-lede">
                  Urgent congestion, blocked edges, queue reservations, and road-state cards are
                  ranked so the highest-pressure issues stay at the top.
                </p>
              </div>
              <span className="status-pill secondary traffic-panel-status">
                {formatMaybeNumber(blockedEdgeIds.length)} blocked edges
              </span>
            </div>

            <div className="section-stack traffic-monitor-stack">
              <div className="subsection traffic-monitor-board">
                <div className="traffic-summary-row traffic-summary-row-monitor">
                  <span className="traffic-summary-chip critical">
                    {formatMaybeNumber(queuedVehicleCount)} queued
                  </span>
                  <span className="traffic-summary-chip">
                    {formatMaybeNumber(congestedRoadCount)} congested roads
                  </span>
                  <span className="traffic-summary-chip accent">
                    Peak {Math.round(peakTrafficIntensity * 100)}%
                  </span>
                  <span className="traffic-summary-chip critical">
                    {formatMaybeNumber(blockedEdgeIds.length)} blocked edges
                  </span>
                </div>
                <div className="traffic-alert-grid">
                  <article className="traffic-alert-card traffic-alert-card-congestion">
                    <div className="traffic-alert-card-header">
                      <div>
                        <p className="traffic-alert-kicker">Urgent traffic issues</p>
                        <h3>Congestion Overview</h3>
                        <p className="traffic-card-lede">
                          Roads with the highest pressure appear first, followed by the rest of the
                          monitored road set.
                        </p>
                      </div>
                      <span className="traffic-alert-badge">
                        {formatMaybeNumber(congestedRoadCount)} active
                      </span>
                    </div>
                    <ul className="traffic-alert-list">
                      {trafficMonitoringRoadStates.filter(
                        (roadState) => trafficRoadPressureScore(roadState) > 0,
                      ).length > 0 ? (
                        trafficMonitoringRoadStates
                          .filter((roadState) => trafficRoadPressureScore(roadState) > 0)
                          .slice(0, 3)
                          .map((roadState) => (
                            <li
                              key={`traffic-urgent-${roadState.road_id ?? "road"}`}
                              className="traffic-alert-row"
                            >
                              <div className="traffic-alert-row-header">
                                <div>
                                  <strong>Road {roadState.road_id ?? "unknown"}</strong>
                                  <span>
                                    {roadState.congestion_level ?? "active"} · {roadState.control_state ?? "free_flow"}
                                  </span>
                                </div>
                                <span className="traffic-alert-row-score">
                                  {Math.round((roadState.congestion_intensity ?? 0) * 100)}%
                                </span>
                              </div>
                              <div className="traffic-alert-bar" aria-hidden="true">
                                <span
                                  style={{
                                    width: `${Math.round(
                                      (roadState.congestion_intensity ?? 0) * 100,
                                    )}%`,
                                  }}
                                />
                              </div>
                              <div className="traffic-alert-row-meta">
                                <span>Queued {formatMaybeNumber(roadState.queued_vehicle_ids?.length ?? 0)}</span>
                                <span>Occupancy {formatMaybeNumber(roadState.occupancy_count ?? null)}</span>
                                <span>Min spacing {formatMeters(roadState.min_spacing_m ?? null)}</span>
                              </div>
                            </li>
                          ))
                      ) : (
                        <li className="traffic-alert-row traffic-alert-row-calm">
                          <div className="traffic-alert-row-header">
                            <div>
                              <strong>All monitored roads</strong>
                              <span>No congestion at the current sample</span>
                            </div>
                            <span className="traffic-alert-row-score">0%</span>
                          </div>
                          <div className="traffic-alert-bar" aria-hidden="true">
                            <span style={{ width: "0%" }} />
                          </div>
                        </li>
                      )}
                    </ul>
                  </article>

                  <article className="traffic-alert-card traffic-alert-card-hazard">
                    <div className="traffic-alert-card-header">
                      <div>
                        <p className="traffic-alert-kicker">Hazard watch</p>
                        <h3>Blocked Edge Watch</h3>
                        <p className="traffic-card-lede">
                          Blocked edges are surfaced before neutral traffic data so closures and
                          hazards stay obvious.
                        </p>
                      </div>
                      <span className="traffic-alert-badge traffic-alert-badge-critical">
                        {formatMaybeNumber(blockedEdgeIds.length)} blocked
                      </span>
                    </div>
                    {selectedTarget?.kind === "hazard" && selectedHazardEdge ? (
                      <div className="traffic-hazard-focus">
                        <div className="traffic-hazard-focus-header">
                          <strong>Selected blocked edge {selectedHazardEdge.edge_id ?? "?"}</strong>
                          <span>{selectedHazardEdge.distance ?? "pending"} distance</span>
                        </div>
                        <div className="traffic-hazard-focus-meta">
                          <span>Start node {formatMaybeNumber(selectedHazardEdge.start_node_id ?? null)}</span>
                          <span>End node {formatMaybeNumber(selectedHazardEdge.end_node_id ?? null)}</span>
                          <span>Speed limit {selectedHazardEdge.speed_limit ?? "pending"}</span>
                        </div>
                      </div>
                    ) : blockedEdgeIds.length > 0 ? (
                      <ul className="traffic-hazard-list">
                        {blockedEdgeIds.slice(0, 5).map((edgeId) => (
                          <li key={`blocked-${edgeId}`} className="traffic-hazard-card">
                            <strong>Edge {edgeId}</strong>
                            <span>Blocked edge under active monitoring</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="traffic-hazard-empty">
                        <strong>No blocked edges</strong>
                        <span>Hazard watch is clear at the current sample.</span>
                      </div>
                    )}
                  </article>
                </div>
              </div>

              <div className="subsection traffic-road-state-pane">
                <div className="traffic-section-heading">
                  <div>
                    <h3>Active Road Conditions</h3>
                    <p className="traffic-section-lede">
                      Road-state cards surface congestion intensity, occupancy, queued vehicles,
                      and control state in a scan-friendly order.
                    </p>
                  </div>
                  <span className="traffic-section-badge">
                    {formatMaybeNumber(trafficRoadStatesRanked.length)} roads sampled
                  </span>
                </div>
                {trafficFocusRoadState ? (
                  <article
                    className={`traffic-road-card traffic-road-card-spotlight ${
                      trafficFocusRoadState.road_id &&
                      selectedRoadTraffic?.road_id === trafficFocusRoadState.road_id
                        ? "selected"
                        : ""
                    }`}
                  >
                    <div className="traffic-road-card-header">
                      <div>
                        <p className="traffic-road-card-kicker">Road focus</p>
                        <h4>Road {trafficFocusRoadState.road_id ?? "unknown"}</h4>
                        <p className="traffic-road-card-summary">
                          {trafficFocusRoad?.road_class ?? "connector"} ·{" "}
                          {trafficFocusRoad?.directionality ?? "unknown"} ·{" "}
                          {formatMaybeNumber(trafficFocusRoad?.lane_count ?? null)} lanes ·{" "}
                          {trafficFocusRoad?.width_m ?? "pending"}m width
                        </p>
                      </div>
                      <span className="traffic-road-card-pill">
                        {trafficFocusRoadState.congestion_level ?? "free"} ·{" "}
                        {trafficFocusRoadState.control_state ?? "free_flow"}
                      </span>
                    </div>
                    <div className="traffic-road-card-metrics">
                      <span>
                        Intensity <strong>{Math.round((trafficFocusRoadState.congestion_intensity ?? 0) * 100)}%</strong>
                      </span>
                      <span>
                        Occupancy <strong>{formatMaybeNumber(trafficFocusRoadState.occupancy_count ?? null)}</strong>
                      </span>
                      <span>
                        Queued <strong>{formatMaybeNumber(trafficFocusRoadState.queued_vehicle_ids?.length ?? 0)}</strong>
                      </span>
                      <span>
                        Control <strong>{trafficFocusRoadState.control_state ?? "free_flow"}</strong>
                      </span>
                      <span>
                        Min spacing <strong>{formatMeters(trafficFocusRoadState.min_spacing_m ?? null)}</strong>
                      </span>
                    </div>
                    <div className="traffic-road-card-bar" aria-hidden="true">
                      <span
                        style={{
                          width: `${Math.round((trafficFocusRoadState.congestion_intensity ?? 0) * 100)}%`,
                        }}
                      />
                    </div>
                    <div className="traffic-road-card-footnote">
                      <span>
                        Stop lines {trafficFocusRoadState.stop_line_ids?.join(", ") || "none"}
                      </span>
                      <span>
                        Protected zones{" "}
                        {trafficFocusRoadState.protected_conflict_zone_ids?.join(", ") || "none"}
                      </span>
                    </div>
                  </article>
                ) : null}
                <div className="traffic-road-card-grid">
                  {trafficMonitoringRoadStates.slice(trafficFocusRoadState ? 1 : 0).map((roadState) => (
                    <article
                      key={`road-state-${roadState.road_id ?? "road"}`}
                      className={`traffic-road-card ${
                        (roadState.congestion_intensity ?? 0) > 0.65
                          ? "traffic-road-card-hot"
                          : (roadState.queued_vehicle_ids?.length ?? 0) > 0
                            ? "traffic-road-card-queued"
                            : "traffic-road-card-calm"
                      }`}
                    >
                      <div className="traffic-road-card-header">
                        <div>
                          <p className="traffic-road-card-kicker">
                            Road {roadState.road_id ?? "unknown"}
                          </p>
                          <h4>{roadState.congestion_level ?? "free"} traffic</h4>
                        </div>
                        <span className="traffic-road-card-pill">
                          {roadState.control_state ?? "free_flow"}
                        </span>
                      </div>
                      <div className="traffic-road-card-metrics">
                        <span>
                          Intensity <strong>{Math.round((roadState.congestion_intensity ?? 0) * 100)}%</strong>
                        </span>
                        <span>
                          Occupancy <strong>{formatMaybeNumber(roadState.occupancy_count ?? null)}</strong>
                        </span>
                        <span>
                          Queued <strong>{formatMaybeNumber(roadState.queued_vehicle_ids?.length ?? 0)}</strong>
                        </span>
                        <span>
                          Control <strong>{roadState.control_state ?? "free_flow"}</strong>
                        </span>
                      </div>
                      <div className="traffic-road-card-bar" aria-hidden="true">
                        <span
                          style={{
                            width: `${Math.round((roadState.congestion_intensity ?? 0) * 100)}%`,
                          }}
                        />
                      </div>
                      <div className="traffic-road-card-footnote">
                        <span>
                          Active {formatMaybeNumber(roadState.active_vehicle_ids?.length ?? 0)}
                        </span>
                        <span>Min spacing {formatMeters(roadState.min_spacing_m ?? null)}</span>
                      </div>
                    </article>
                  ))}
                  {trafficMonitoringRoadStates.length === 0 ? (
                    <div className="traffic-road-empty">
                      No traffic road-state samples are currently attached.
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="subsection traffic-reservation-inspection">
                <div className="traffic-section-heading">
                  <div>
                    <h3>Queue & Reservation Detail</h3>
                    <p className="traffic-section-lede">
                      Queue records are linked to the road they affect so reservation pressure is
                      easy to follow.
                    </p>
                  </div>
                  <span className="traffic-section-badge">
                    {formatMaybeNumber(trafficQueueRecords.length)} reservations
                  </span>
                </div>
                {selectedQueueRecord ? (
                  <article className="traffic-reservation-card traffic-reservation-card-spotlight">
                    <div className="traffic-reservation-card-header">
                      <div>
                        <p className="traffic-reservation-card-kicker">Selected queue</p>
                        <h4>Road {selectedQueueRecord.road_id ?? "unknown"}</h4>
                        <p className="traffic-reservation-card-summary">
                          Node {formatMaybeNumber(selectedQueueRecord.node_id ?? null)} ·{" "}
                          {selectedQueueRecord.reason ?? "queued"}
                        </p>
                      </div>
                      <span className="traffic-reservation-badge">
                        {selectedQueueRecord.vehicle_ids?.length ??
                          (selectedQueueRecord.vehicle_id !== undefined ? 1 : 0)}{" "}
                        vehicle(s)
                      </span>
                    </div>
                    <div className="traffic-reservation-meta">
                      <span>
                        Control {selectedQueueTraffic?.control_state ?? "yield"}
                      </span>
                      <span>
                        Congestion {selectedQueueTraffic?.congestion_level ?? "free"}
                      </span>
                      <span>
                        Queued {selectedQueueTraffic?.queued_vehicle_ids?.length ?? 0}
                      </span>
                      <span>
                        Occupancy {formatMaybeNumber(selectedQueueTraffic?.occupancy_count ?? null)}
                      </span>
                    </div>
                  </article>
                ) : null}
                <div className="traffic-reservation-grid">
                  {trafficQueueRecords.length > 0 ? (
                    trafficQueueRecords
                      .filter((record) => record !== selectedQueueRecord)
                      .slice(0, 4)
                      .map((record, index) => {
                        const roadTraffic =
                          typeof record.road_id === "string"
                            ? trafficRoadById.get(record.road_id) ?? null
                            : null;
                        const queuedVehicleCount =
                          record.vehicle_ids?.length ?? (record.vehicle_id !== undefined ? 1 : 0);
                        return (
                          <article
                            key={`${record.road_id ?? "queue"}-${index}`}
                            className="traffic-reservation-card"
                          >
                            <div className="traffic-reservation-card-header">
                              <div>
                                <p className="traffic-reservation-card-kicker">
                                  Road {record.road_id ?? "unknown"}
                                </p>
                                <h4>{record.reason ?? "Queued reservation"}</h4>
                              </div>
                              <span className="traffic-reservation-badge">
                                {queuedVehicleCount} vehicle(s)
                              </span>
                            </div>
                            <div className="traffic-reservation-meta">
                              <span>
                                Control {roadTraffic?.control_state ?? "yield"}
                              </span>
                              <span>
                                Congestion {roadTraffic?.congestion_level ?? "free"}
                              </span>
                              <span>
                                Occupancy {formatMaybeNumber(roadTraffic?.occupancy_count ?? null)}
                              </span>
                              <span>
                                Node {formatMaybeNumber(record.node_id ?? null)}
                              </span>
                            </div>
                          </article>
                        );
                      })
                  ) : (
                    <div className="traffic-reservation-empty">No queue reservations are currently active.</div>
                  )}
                </div>
                <div className="traffic-context-strip">
                  <span>Selected route conflicts {selectedRoutePreview?.reason ?? "none"}</span>
                  <span>
                    Route preview roads{" "}
                    {selectedRoutePreviewRoadIds.size > 0
                      ? Array.from(selectedRoutePreviewRoadIds).join(", ")
                      : "none"}
                  </span>
                  <span>
                    Blocked edges{" "}
                    {blockedEdgeIds.length > 0 ? blockedEdgeIds.join(", ") : "none"}
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section className="panel info-panel analyze-pane" aria-labelledby="inspector-title">
            <div className="panel-header compact analyze-panel-header">
              <div className="analyze-panel-copy">
                <p className="eyebrow">Inspector Region</p>
                <h2 id="inspector-title">Diagnostics and AI Review</h2>
                <p className="analyze-panel-lede">
                  Urgent issues first, recommended actions second, and supporting context last.
                </p>
              </div>
              <div className="analyze-panel-meta">
                <span className="status-pill secondary">
                  {selectedTarget ? describeSelectedBadge(selectedTarget) : `${inspections.length} records`}
                </span>
                <div className="analyze-summary-strip" aria-label="Analyze summary">
                  <span className="analysis-chip analysis-chip-alert">
                    {reviewAnomalies.length} urgent issue{reviewAnomalies.length === 1 ? "" : "s"}
                  </span>
                  <span className="analysis-chip analysis-chip-action">
                    {reviewSuggestions.length} action{reviewSuggestions.length === 1 ? "" : "s"}
                  </span>
                  <span className="analysis-chip analysis-chip-context">
                    {reviewExplanations.length} explanation{reviewExplanations.length === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            </div>

            <div className="analyze-review-stack">
              <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-urgent">
                <div className="analyze-section-header">
                  <div>
                    <h3>Urgent issues</h3>
                    <p>Escalations and anomalies are surfaced first for immediate review.</p>
                  </div>
                  <span className="analysis-section-chip">
                    {reviewAnomalies.length > 0 ? "highest severity" : "no active anomalies"}
                  </span>
                </div>
                <div className="analyze-card-stack">
                  {reviewAnomalies.length > 0 ? (
                    reviewAnomalies.map((anomaly) => {
                      const anomalyVehicle = findDisplayedVehicleById(
                        displayedVehicles,
                        anomaly.vehicle_id ?? null,
                      );
                      const anomalyTargetLabel =
                        anomaly.vehicle_id !== undefined
                          ? `Vehicle ${formatMaybeNumber(anomaly.vehicle_id)}${
                              anomalyVehicle?.display_name ? ` · ${anomalyVehicle.display_name}` : ""
                            }`
                          : null;
                      const severityLabel = normalizeReviewLevel(anomaly.severity, "info");
                      return (
                        <article
                          key={anomaly.anomaly_id ?? anomaly.summary ?? "anomaly"}
                          className={`review-card review-card-urgent review-card-${severityLabel}`}
                        >
                          <div className="review-card-header">
                            <div className="review-card-title">
                              <strong>{anomaly.summary ?? "No anomaly summary"}</strong>
                              <span>Anomaly review item</span>
                            </div>
                            <div className="review-card-meta">
                              <span className={`review-level-chip review-level-chip-${severityLabel}`}>
                                {severityLabel.toUpperCase()}
                              </span>
                              {anomalyTargetLabel ? (
                                <span className="review-target-chip">{anomalyTargetLabel}</span>
                              ) : null}
                            </div>
                          </div>
                          <div className="review-card-body">
                            {anomaly.vehicle_id !== undefined
                              ? "This anomaly is tied to a specific vehicle and should be reviewed before the next action."
                              : "This anomaly is not tied to a vehicle target."}
                          </div>
                        </article>
                      );
                    })
                  ) : (
                    <div className="review-empty-state">No anomalies are currently attached.</div>
                  )}
                </div>
              </section>

              <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-actions">
                <div className="analyze-section-header">
                  <div>
                    <h3>Suggestions</h3>
                    <p>Recommended actions are ordered by priority and linked to their target when possible.</p>
                  </div>
                  <span className="analysis-section-chip">
                    {reviewSuggestions.length > 0 ? "actionable review" : "no recommendations"}
                  </span>
                </div>
                <div className="analyze-card-stack">
                  {reviewSuggestions.length > 0 ? (
                    reviewSuggestions.map((suggestion) => {
                      const suggestionVehicle = findDisplayedVehicleById(
                        displayedVehicles,
                        suggestion.target_vehicle_id ?? null,
                      );
                      const suggestionTargetLabel =
                        suggestion.target_vehicle_id !== undefined && suggestion.target_vehicle_id !== null
                          ? `Vehicle ${formatMaybeNumber(suggestion.target_vehicle_id)}${
                              suggestionVehicle?.display_name ? ` · ${suggestionVehicle.display_name}` : ""
                            }`
                          : suggestion.target_edge_id !== undefined
                            ? describeEdgeTargetLabel(
                                suggestion.target_edge_id ?? undefined,
                                bundle?.render_geometry?.roads ?? [],
                              )
                            : null;
                      const priorityLabel = normalizeReviewLevel(suggestion.priority, "medium");
                      return (
                        <article
                          key={suggestion.suggestion_id ?? suggestion.summary ?? "suggestion"}
                          className={`review-card review-card-action review-card-${priorityLabel}`}
                        >
                          <div className="review-card-header">
                            <div className="review-card-title">
                              <strong>{suggestion.summary ?? "No summary"}</strong>
                              <span>{suggestion.kind ?? "suggestion"}</span>
                            </div>
                            <div className="review-card-meta">
                              <span className={`review-level-chip review-level-chip-${priorityLabel}`}>
                                {priorityLabel.toUpperCase()}
                              </span>
                              {suggestionTargetLabel ? (
                                <span className="review-target-chip">{suggestionTargetLabel}</span>
                              ) : null}
                            </div>
                          </div>
                          <div className="review-card-body">
                            {suggestion.target_vehicle_id !== undefined ||
                            suggestion.target_edge_id !== undefined
                              ? "This action is tied to a concrete target and can be executed or inspected directly."
                              : "This action is general guidance without a specific target."}
                          </div>
                        </article>
                      );
                    })
                  ) : (
                    <div className="review-empty-state">No actionable suggestions are currently attached.</div>
                  )}
                </div>
              </section>

              <section className="subsection analyze-ai-feedback analyze-review-section analyze-review-section-context">
                <div className="analyze-section-header">
                  <div>
                    <h3>Explanations</h3>
                    <p>Supporting context stays compact so the key review items remain easy to scan.</p>
                  </div>
                  <span className="analysis-section-chip">
                    {reviewRecentCommands.length > 0 ? `${reviewRecentCommands.length} recent commands` : "context only"}
                  </span>
                </div>

                {selectedInspection ? (
                  <article className="review-card review-card-context analyze-context-card">
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>
                          {displayedSelectedVehicle?.display_name ?? "Vehicle"}{" "}
                          {formatMaybeNumber(selectedInspection.vehicle_id ?? null)}
                        </strong>
                        <span>
                          {displayedSelectedVehicle?.role_label ??
                            selectedInspection.operational_state ??
                            "unknown_state"}
                        </span>
                      </div>
                      <span className="review-level-chip review-level-chip-info">Current target</span>
                    </div>
                    <div className="review-metric-grid" aria-label="Inspection metrics">
                      <div className="review-metric">
                        <span>Node</span>
                        <strong>{formatMaybeNumber(selectedInspection.current_node_id ?? null)}</strong>
                      </div>
                      <div className="review-metric">
                        <span>ETA</span>
                        <strong>{formatSeconds(selectedInspection.eta_s ?? null)}</strong>
                      </div>
                      <div className="review-metric">
                        <span>Job</span>
                        <strong>{selectedInspection.current_job_id ?? "none"}</strong>
                      </div>
                      <div className="review-metric">
                        <span>Wait</span>
                        <strong>{selectedInspection.wait_reason ?? "none"}</strong>
                      </div>
                      <div className="review-metric">
                        <span>Type</span>
                        <strong>{displayedSelectedVehicle?.vehicle_type ?? "GENERIC"}</strong>
                      </div>
                      <div className="review-metric">
                        <span>Control</span>
                        <strong>{selectedInspection.traffic_control_state ?? "none"}</strong>
                      </div>
                    </div>
                    <ul className="review-context-list">
                      <li>
                        Lane:{" "}
                        {displayedSelectedVehicle?.lane_id
                          ? `${displayedSelectedVehicle.lane_id} · ${
                              displayedSelectedVehicle.lane_role ?? "travel"
                            }`
                          : "unassigned"}
                      </li>
                      <li>
                        Lane direction: {displayedSelectedVehicle?.lane_directionality ?? "unknown"}
                      </li>
                      <li>
                        Lane note: {displayedSelectedVehicle?.lane_selection_reason ?? "none"}
                      </li>
                      <li>
                        Spacing: {formatMeters(displayedSelectedVehicle?.spacing_envelope_m ?? null)}
                      </li>
                      <li>Heading: {formatHeadingDegrees(displayedSelectedVehicle?.heading_rad ?? null)}</li>
                      <li>{selectedInspection.traffic_control_detail ?? "No control detail"}</li>
                    </ul>
                    <div className="review-diagnostic-strip">
                      {(selectedInspection.diagnostics ?? []).length > 0 ? (
                        (selectedInspection.diagnostics ?? []).map((diagnostic, diagIndex) => {
                          const diagnosticSeverity = normalizeReviewLevel(diagnostic.severity, "info");
                          return (
                            <span
                              key={`${diagnostic.code ?? "diag"}-${diagIndex}`}
                              className={`diagnostic-pill review-diagnostic-pill review-diagnostic-pill-${diagnosticSeverity}`}
                            >
                              <strong>{diagnosticSeverity.toUpperCase()}</strong>
                              <span>{diagnostic.code ?? "diagnostic"}</span>
                            </span>
                          );
                        })
                      ) : (
                        <span className="review-empty-state">No diagnostics are currently attached.</span>
                      )}
                    </div>
                  </article>
                ) : null}

                {effectiveSelectedVehicleIds.length > 1 ? (
                  <article className="review-card review-card-context">
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>Fleet Selection</strong>
                        <span>multi-select</span>
                      </div>
                      <span className="review-level-chip review-level-chip-info">
                        {effectiveSelectedVehicleIds.length} vehicles
                      </span>
                    </div>
                    <ul className="review-context-list">
                      <li>Vehicles: {effectiveSelectedVehicleIds.join(", ")}</li>
                      <li>Selected records: {selectedVehicleInspections.length}</li>
                      <li>
                        Route previews:{" "}
                        {
                          routePreviews.filter((preview) =>
                            effectiveSelectedVehicleIds.includes(preview.vehicle_id ?? -1),
                          ).length
                        }
                      </li>
                      <li>Batch commands: assign and reposition apply to every selected vehicle.</li>
                    </ul>
                  </article>
                ) : null}

                {selectedTarget?.kind === "area" && selectedArea ? (
                  <article className="review-card review-card-context">
                    <div className="review-card-header">
                      <div className="review-card-title">
                        <strong>{selectedArea.label ?? selectedArea.area_id ?? "zone"}</strong>
                        <span>{selectedArea.kind ?? "area"}</span>
                      </div>
                      <span className="review-level-chip review-level-chip-info">Geometry target</span>
                    </div>
                    <ul className="review-context-list">
                      <li>Polygon vertices: {selectedArea.polygon?.length ?? 0}</li>
                      <li>Area id: {selectedArea.area_id ?? "unknown"}</li>
                      <li>Editing target: zone polygon</li>
                    </ul>
                  </article>
                ) : null}

                <article className="review-card review-card-context analyze-command-card">
                  <div className="review-card-header">
                    <div className="review-card-title">
                      <strong>Recent command trace</strong>
                      <span>Latest operator actions</span>
                    </div>
                    <span className="review-level-chip review-level-chip-info">
                      {reviewRecentCommands.length} shown
                    </span>
                  </div>
                  <div className="review-command-list">
                    {reviewRecentCommands.length > 0 ? (
                      reviewRecentCommands.map((command, commandIndex) => (
                        <div key={`${command.command_type ?? "command"}-${commandIndex}`} className="review-command-item">
                          <span className="review-command-kind">{command.command_type ?? "command"}</span>
                          <span className="review-command-summary">{describeRecentCommand(command)}</span>
                        </div>
                      ))
                    ) : (
                      <div className="review-empty-state">No recent commands are currently attached.</div>
                    )}
                  </div>
                </article>

                <div className="analyze-explanation-grid">
                  {reviewExplanations.length > 0 ? (
                    reviewExplanations.slice(0, 3).map((explanation, index) => {
                      const explanationVehicle = findDisplayedVehicleById(
                        displayedVehicles,
                        explanation.vehicle_id ?? null,
                      );
                      return (
                        <article
                          key={`${explanation.vehicle_id ?? "explanation"}-${index}`}
                          className="review-card review-card-context review-explanation-card"
                        >
                          <div className="review-card-header">
                            <div className="review-card-title">
                              <strong>
                                Vehicle {formatMaybeNumber(explanation.vehicle_id ?? null)}
                              </strong>
                              <span>
                                {explanationVehicle?.display_name ??
                                  explanationVehicle?.role_label ??
                                  "explanation"}
                              </span>
                            </div>
                            <span className="review-level-chip review-level-chip-info">Explanation</span>
                          </div>
                          <div className="review-card-body review-explanation-body">
                            {explanation.summary ?? "No explanation summary"}
                          </div>
                        </article>
                      );
                    })
                  ) : (
                    <div className="review-empty-state">No AI explanations are currently attached.</div>
                  )}
                </div>
              </section>
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

function toSmoothPathString(points: Position3[] | undefined, closed = false): string {
  const pathPoints = (points ?? []).map(([x, y]) => [x, y] as const);
  if (pathPoints.length < 2) {
    return "";
  }
  if (pathPoints.length === 2) {
    const [[x1, y1], [x2, y2]] = pathPoints;
    return `M ${x1} ${y1} L ${x2} ${y2}`;
  }

  const smoothFactor = closed ? 0.14 : 0.16;
  const commands: string[] = [`M ${pathPoints[0][0]} ${pathPoints[0][1]}`];

  for (let index = 0; index < pathPoints.length - 1; index += 1) {
    const current = pathPoints[index];
    const next = pathPoints[index + 1];
    const previous = closed
      ? pathPoints[(index - 1 + pathPoints.length) % pathPoints.length]
      : pathPoints[Math.max(index - 1, 0)];
    const following = closed
      ? pathPoints[(index + 2) % pathPoints.length]
      : pathPoints[Math.min(index + 2, pathPoints.length - 1)];

    const c1x = current[0] + (next[0] - previous[0]) * smoothFactor;
    const c1y = current[1] + (next[1] - previous[1]) * smoothFactor;
    const c2x = next[0] - (following[0] - current[0]) * smoothFactor;
    const c2y = next[1] - (following[1] - current[1]) * smoothFactor;
    commands.push(`C ${c1x} ${c1y} ${c2x} ${c2y} ${next[0]} ${next[1]}`);
  }

  if (closed) {
    commands.push("Z");
  }
  return commands.join(" ");
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
  const baseVehicles = new Map<number, VehicleSnapshotPayload & { heading_rad?: number; speed?: number }>();
  for (const vehicle of bundle?.snapshot?.vehicles ?? []) {
    if (vehicle.vehicle_id === undefined) {
      continue;
    }
    baseVehicles.set(vehicle.vehicle_id, {
      ...vehicle,
      heading_rad: 0,
      speed: 0,
      spacing_envelope_m: vehicle.spacing_envelope_m ?? spacingEnvelopeFromVehicle(vehicle),
    });
  }
  if (!bundle?.motion_segments?.length) {
    return [...baseVehicles.values()];
  }

  const sampledVehicles = new Map<number, VehicleSnapshotPayload & { heading_rad?: number; speed?: number }>();
  for (const vehicle of baseVehicles.values()) {
    if (vehicle.vehicle_id !== undefined) {
      sampledVehicles.set(vehicle.vehicle_id, vehicle);
    }
  }

  const motionSegments = [...bundle.motion_segments].sort(
    (left, right) =>
      (left.start_time_s ?? 0) - (right.start_time_s ?? 0) ||
      (left.segment_index ?? 0) - (right.segment_index ?? 0),
  );

  type MotionSpacingEntry = {
    vehicleId: number;
    edgeId: number;
    pathPoints: Position3[];
    distanceAlongPath: number;
    headingRad: number;
    speed: number;
    spacingEnvelopeM: number;
    roadId?: string | null;
    laneId?: string | null;
    laneIndex?: number | null;
    laneRole?: string | null;
    laneDirectionality?: string | null;
    laneSelectionReason?: string | null;
    segment: MotionSegmentPayload;
  };
  const activeEntries: MotionSpacingEntry[] = [];

  for (const segment of motionSegments) {
    const vehicleId = segment.vehicle_id;
    if (
      vehicleId === undefined ||
      segment.start_time_s === undefined ||
      segment.end_time_s === undefined
    ) {
      continue;
    }
    let existing = sampledVehicles.get(vehicleId);
    if (!existing) {
      sampledVehicles.set(vehicleId, {
        vehicle_id: vehicleId,
        node_id: segment.start_node_id,
        position: segment.start_position,
        operational_state: "moving",
        vehicle_type: "GENERIC",
        presentation_key: "generic",
        display_name: "Generic Vehicle",
        role_label: "General operations",
        body_length_m: 1.12,
        body_width_m: 0.62,
        spacing_envelope_m: spacingEnvelopeFromVehicle({
          body_length_m: 1.12,
          body_width_m: 0.62,
        }),
        primary_color: "rgba(95, 109, 121, 0.96)",
        accent_color: "rgba(255, 255, 255, 0.92)",
        heading_rad: segment.heading_rad ?? 0,
        speed: 0,
      });
      existing = sampledVehicles.get(vehicleId);
    }
    if (!existing) {
      continue;
    }
    if (existing.position === undefined && segment.start_position) {
      existing.position = segment.start_position;
    }
    if (motionClockS < segment.start_time_s) {
      continue;
    }
    const pathPoints = resolvePathPoints(segment);
    const pathLength = polylineLength(pathPoints);
    const sampled = sampleMotionSegmentPayload(segment, motionClockS);
    const progress = sampled.progress;
    const distanceAlongPath = pathLength * progress;
    activeEntries.push({
      vehicleId,
      edgeId: segment.edge_id ?? -1,
      pathPoints,
      distanceAlongPath,
      headingRad: sampled.headingRad,
      speed: sampled.speed,
      spacingEnvelopeM: segment.spacing_envelope_m ?? spacingEnvelopeFromVehicle(segment),
      roadId: segment.road_id ?? null,
      laneId: segment.lane_id ?? null,
      laneIndex: segment.lane_index ?? null,
      laneRole: segment.lane_role ?? null,
      laneDirectionality: segment.lane_directionality ?? null,
      laneSelectionReason: segment.lane_selection_reason ?? null,
      segment,
    });
    if (motionClockS > segment.end_time_s) {
      const settled = sampledVehicles.get(vehicleId);
      if (settled) {
        settled.position = segment.end_position ?? settled.position;
        settled.node_id = segment.end_node_id ?? settled.node_id;
        settled.heading_rad = segment.heading_rad ?? settled.heading_rad;
        settled.speed = 0;
      }
      continue;
    }
  }

  const adjustedEntries = applyFollowingSpacing(activeEntries);
  for (const entry of adjustedEntries) {
    const vehicle = sampledVehicles.get(entry.vehicleId);
    if (!vehicle) {
      continue;
    }
    vehicle.position = entry.position;
    vehicle.node_id = entry.segment.start_node_id ?? vehicle.node_id;
    vehicle.operational_state = entry.operationalState;
    vehicle.heading_rad = entry.headingRad;
    vehicle.speed = entry.speed;
    vehicle.spacing_envelope_m = entry.spacingEnvelopeM;
    vehicle.body_length_m = entry.segment.body_length_m ?? vehicle.body_length_m;
    vehicle.body_width_m = entry.segment.body_width_m ?? vehicle.body_width_m;
    vehicle.presentation_key = vehicle.presentation_key ?? "generic";
    vehicle.road_id = entry.roadId ?? vehicle.road_id;
    vehicle.lane_id = entry.laneId ?? vehicle.lane_id;
    vehicle.lane_index = entry.laneIndex ?? vehicle.lane_index;
    vehicle.lane_role = entry.laneRole ?? vehicle.lane_role;
    vehicle.lane_directionality = entry.laneDirectionality ?? vehicle.lane_directionality;
    vehicle.lane_selection_reason = entry.laneSelectionReason ?? vehicle.lane_selection_reason;
  }

  return [...sampledVehicles.values()].sort(
    (left, right) => (left.vehicle_id ?? 0) - (right.vehicle_id ?? 0),
  );
}

function computeMinDisplayedSpacing(
  vehicles: Array<VehicleSnapshotPayload & { heading_rad?: number; speed?: number }>,
): number | null {
  let minimum: number | null = null;
  for (let index = 0; index < vehicles.length; index += 1) {
    const left = vehicles[index];
    if (!left.position) {
      continue;
    }
    for (let inner = index + 1; inner < vehicles.length; inner += 1) {
      const right = vehicles[inner];
      if (!right.position) {
        continue;
      }
      const distance = pointDistance(left.position, right.position);
      if (minimum === null || distance < minimum) {
        minimum = distance;
      }
    }
  }
  return minimum;
}

function sampleTrafficSnapshot(
  bundle: BundlePayload | null,
  motionClockS: number,
): TrafficSnapshotPayload {
  const roads = bundle?.render_geometry?.roads ?? [];
  const motionSegments = [...(bundle?.motion_segments ?? [])].sort(
    (left, right) =>
      (left.start_time_s ?? 0) - (right.start_time_s ?? 0) ||
      (left.segment_index ?? 0) - (right.segment_index ?? 0),
  );
  const roadStates: TrafficRoadStatePayload[] = roads.map((road) => {
    const activeSegments = motionSegments.filter(
      (segment) =>
        segment.edge_id !== undefined &&
        (road.edge_ids ?? []).includes(segment.edge_id) &&
        (segment.start_time_s ?? 0) < motionClockS &&
        motionClockS < (segment.end_time_s ?? 0),
    );
    const activePositions = activeSegments.map(
      (segment) => sampleMotionSegmentPayload(segment, motionClockS).position,
    );
    const queuedVehicleIds = (bundle?.traffic_baseline?.queue_records ?? [])
      .filter(
        (record) =>
          record.road_id === road.road_id &&
          (record.queue_start_s ?? 0) <= motionClockS &&
          motionClockS < (record.queue_end_s ?? 0),
      )
      .map((record) => record.vehicle_id)
      .filter((vehicleId): vehicleId is number => vehicleId !== undefined)
      .sort((left, right) => left - right);
    const activeVehicleIds = activeSegments
      .map((segment) => segment.vehicle_id)
      .filter((vehicleId): vehicleId is number => vehicleId !== undefined)
      .sort((left, right) => left - right);
    const occupancyCount = activeVehicleIds.length;
    const minSpacingM = computeMinPointSpacing(activePositions);
    const congestionLevel = trafficCongestionLevel(
      occupancyCount,
      queuedVehicleIds.length,
      minSpacingM,
    );
    const congestionIntensity = trafficCongestionIntensity(
      occupancyCount,
      queuedVehicleIds.length,
      minSpacingM,
    );
    return {
      road_id: road.road_id,
      active_vehicle_ids: activeVehicleIds,
      queued_vehicle_ids: queuedVehicleIds,
      occupancy_count: occupancyCount,
      min_spacing_m: minSpacingM,
      congestion_intensity: congestionIntensity,
      congestion_level: congestionLevel,
    };
  });
  return {
    timestamp_s: motionClockS,
    road_states: roadStates,
  };
}

function computeMinPointSpacing(points: Position3[]): number | null {
  if (points.length < 2) {
    return null;
  }
  let minimum: number | null = null;
  for (let index = 0; index < points.length; index += 1) {
    const left = points[index];
    for (let inner = index + 1; inner < points.length; inner += 1) {
      const right = points[inner];
      const distance = pointDistance(left, right);
      if (minimum === null || distance < minimum) {
        minimum = distance;
      }
    }
  }
  return minimum;
}

function sampleMotionSegmentPayload(
  segment: MotionSegmentPayload,
  timestampS: number,
): { position: Position3; headingRad: number; speed: number; progress: number } {
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
    progress,
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

function trafficCongestionLevel(
  occupancyCount: number,
  queueCount: number,
  minSpacingM: number | null,
): string {
  if (queueCount > 0) {
    return "queued";
  }
  if (occupancyCount >= 2 && minSpacingM !== null && minSpacingM <= 1.5) {
    return "congested";
  }
  if (occupancyCount >= 1) {
    return "active";
  }
  return "free";
}

function trafficCongestionIntensity(
  occupancyCount: number,
  queueCount: number,
  minSpacingM: number | null,
): number {
  if (occupancyCount <= 0 && queueCount <= 0) {
    return 0;
  }
  const spacingPressure =
    minSpacingM === null ? 0 : Math.max(0, Math.min(1, (1.8 - minSpacingM) / 1.8));
  const vehiclePressure = Math.min(1, occupancyCount / 4);
  const queuePressure = Math.min(1, queueCount / 3);
  if (queueCount > 0) {
    return Math.min(
      1,
      0.55 + queuePressure * 0.35 + vehiclePressure * 0.1 + spacingPressure * 0.2,
    );
  }
  return Math.min(1, vehiclePressure * 0.55 + spacingPressure * 0.45);
}

function trafficRoadPressureScore(roadState: TrafficRoadStatePayload | null): number {
  if (!roadState) {
    return 0;
  }
  const intensity = roadState.congestion_intensity ?? 0;
  const queuedVehicleCount = roadState.queued_vehicle_ids?.length ?? 0;
  const occupancyCount = roadState.occupancy_count ?? 0;
  const controlState = roadState.control_state ?? "";
  let score = intensity * 100;
  score += queuedVehicleCount * 16;
  score += occupancyCount * 6;
  if (controlState !== "free_flow") {
    score += 8;
  }
  if (controlState === "blocked" || controlState === "stop" || controlState === "yield") {
    score += 8;
  }
  return score;
}

function spacingEnvelopeFromVehicle(
  vehicle: Pick<VehicleSnapshotPayload, "body_length_m" | "body_width_m">,
): number {
  const length = vehicle.body_length_m ?? 1.12;
  const width = vehicle.body_width_m ?? 0.62;
  return Math.max(length * 1.35, width * 2.2, 0.9);
}

function resolvePathPoints(segment: MotionSegmentPayload): Position3[] {
  return (segment.path_points?.length ?? 0) >= 2
    ? (segment.path_points as Position3[])
    : ([segment.start_position ?? [0, 0, 0], segment.end_position ?? [0, 0, 0]] as Position3[]);
}

function applyFollowingSpacing(
  entries: Array<{
    vehicleId: number;
    edgeId: number;
    pathPoints: Position3[];
    distanceAlongPath: number;
    headingRad: number;
    speed: number;
    spacingEnvelopeM: number;
    roadId?: string | null;
    laneId?: string | null;
    laneIndex?: number | null;
    laneRole?: string | null;
    laneDirectionality?: string | null;
    laneSelectionReason?: string | null;
    segment: MotionSegmentPayload;
  }>,
): Array<{
  vehicleId: number;
  position: Position3;
  headingRad: number;
  speed: number;
  operationalState: string;
  spacingEnvelopeM: number;
  roadId?: string | null;
  laneId?: string | null;
  laneIndex?: number | null;
  laneRole?: string | null;
  laneDirectionality?: string | null;
  laneSelectionReason?: string | null;
  segment: MotionSegmentPayload;
}> {
  const adjusted: Array<{
    vehicleId: number;
    position: Position3;
    headingRad: number;
    speed: number;
    operationalState: string;
    spacingEnvelopeM: number;
    roadId?: string | null;
    laneId?: string | null;
    laneIndex?: number | null;
    laneRole?: string | null;
    laneDirectionality?: string | null;
    laneSelectionReason?: string | null;
    segment: MotionSegmentPayload;
  }> = [];
  const grouped = new Map<number, typeof entries>();
  for (const entry of entries) {
    const current = grouped.get(entry.edgeId) ?? [];
    current.push(entry);
    grouped.set(entry.edgeId, current);
  }
  for (const [edgeId, edgeEntries] of [...grouped.entries()].sort((left, right) => left[0] - right[0])) {
    const sorted = [...edgeEntries].sort(
      (left, right) =>
        right.distanceAlongPath - left.distanceAlongPath ||
        left.vehicleId - right.vehicleId,
    );
    let leaderDistance: number | null = null;
    let leaderEnvelope = 0;
    for (const entry of sorted) {
      let finalDistance = entry.distanceAlongPath;
      let finalSpeed = entry.speed;
      let finalState = "moving";
      if (leaderDistance !== null) {
        const safeDistance = Math.max(leaderEnvelope, entry.spacingEnvelopeM);
        const allowedDistance = Math.max(0, leaderDistance - safeDistance);
        if (finalDistance > allowedDistance) {
          finalDistance = allowedDistance;
          finalSpeed = 0;
          finalState = "waiting";
        }
      }
      adjusted.push({
        vehicleId: entry.vehicleId,
        position: samplePathPosition(entry.pathPoints, finalDistance),
        headingRad: headingAlongPath(entry.pathPoints, finalDistance),
        speed: finalSpeed,
        operationalState: finalState,
        spacingEnvelopeM: entry.spacingEnvelopeM,
        segment: entry.segment,
      });
      leaderDistance = finalDistance;
      leaderEnvelope = entry.spacingEnvelopeM;
    }
  }
  return adjusted;
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

function vehiclePresentationBadge(vehicle: VehicleSnapshotPayload): string {
  if (vehicle.presentation_key === "haul_truck") {
    return "HT";
  }
  if (vehicle.presentation_key === "forklift") {
    return "FL";
  }
  if (vehicle.presentation_key === "car") {
    return "CV";
  }
  return "GV";
}

function renderVehicleEnvelope(
  vehicle: VehicleSnapshotPayload & { heading_rad?: number; speed?: number },
): JSX.Element {
  const length = Math.max(vehicle.spacing_envelope_m ?? spacingEnvelopeFromVehicle(vehicle), 0.9);
  const width = Math.max((vehicle.body_width_m ?? 0.62) * 1.7, 0.8);
  return (
    <rect
      x={-length * 0.5}
      y={-width * 0.5}
      width={length}
      height={width}
      rx={0.24}
      className="vehicle-envelope"
    />
  );
}

function renderVehicleHeading(length: number, width: number): JSX.Element {
  return (
    <g className="vehicle-heading-group">
      <line
        x1={-length * 0.12}
        y1={0}
        x2={length * 0.3}
        y2={0}
        className="vehicle-heading"
      />
      <path
        d={`M ${length * 0.24} ${-width * 0.16} L ${length * 0.52} 0 L ${length * 0.24} ${width * 0.16} Z`}
        className="vehicle-heading"
      />
    </g>
  );
}

function renderWheelPair(
  frontX: number,
  rearX: number,
  y: number,
  radius: number,
): JSX.Element[] {
  return [
    <circle key={`rear-${rearX}`} cx={rearX} cy={y} r={radius} className="vehicle-wheel" />,
    <circle key={`front-${frontX}`} cx={frontX} cy={y} r={radius} className="vehicle-wheel" />,
  ];
}

function renderVehicleGlyph(
  vehicle: VehicleSnapshotPayload & { heading_rad?: number; speed?: number },
): JSX.Element {
  const length = vehicle.body_length_m ?? 1.12;
  const width = vehicle.body_width_m ?? 0.62;
  if (vehicle.presentation_key === "haul_truck") {
    return (
      <>
        <rect
          x={-length * 0.5}
          y={-width * 0.34}
          width={length * 0.76}
          height={width * 0.68}
          rx={0.11}
          className="vehicle-body vehicle-body-haul"
        />
        <rect
          x={-length * 0.18}
          y={-width * 0.45}
          width={length * 0.16}
          height={width * 0.14}
          rx={0.05}
          className="vehicle-cab vehicle-cab-haul"
        />
        <polygon
          points={`${length * 0.18},${-width * 0.29} ${length * 0.52},0 ${length * 0.18},${width * 0.29}`}
          className="vehicle-cab vehicle-cab-haul"
        />
        <rect
          x={-length * 0.38}
          y={-width * 0.5}
          width={length * 0.18}
          height={width * 0.16}
          rx={0.05}
          className="vehicle-cab vehicle-cab-haul"
        />
        {renderWheelPair(length * 0.14, -length * 0.28, width * 0.33, width * 0.08)}
        {renderVehicleHeading(length, width)}
      </>
    );
  }
  if (vehicle.presentation_key === "forklift") {
    return (
      <>
        <rect
          x={-length * 0.45}
          y={-width * 0.28}
          width={length * 0.66}
          height={width * 0.56}
          rx={0.09}
          className="vehicle-body vehicle-body-forklift"
        />
        <rect
          x={-length * 0.04}
          y={-width * 0.24}
          width={length * 0.14}
          height={width * 0.48}
          rx={0.05}
          className="vehicle-cab vehicle-cab-forklift"
        />
        <rect
          x={-length * 0.14}
          y={-width * 0.42}
          width={length * 0.28}
          height={width * 0.1}
          rx={0.04}
          className="vehicle-cab vehicle-cab-forklift"
        />
        <line
          x1={length * 0.2}
          y1={-width * 0.38}
          x2={length * 0.2}
          y2={width * 0.34}
          className="vehicle-fork"
        />
        <line
          x1={length * 0.2}
          y1={-width * 0.18}
          x2={length * 0.58}
          y2={-width * 0.18}
          className="vehicle-fork"
        />
        <line
          x1={length * 0.2}
          y1={width * 0.18}
          x2={length * 0.58}
          y2={width * 0.18}
          className="vehicle-fork"
        />
        {renderWheelPair(length * 0.1, -length * 0.22, width * 0.34, width * 0.075)}
        {renderVehicleHeading(length, width)}
      </>
    );
  }
  if (vehicle.presentation_key === "car") {
    return (
      <>
        <path
          d={`M ${-length * 0.48} ${width * 0.16}
              L ${-length * 0.36} ${-width * 0.22}
              Q ${-length * 0.14} ${-width * 0.42} ${length * 0.12} ${-width * 0.42}
              L ${length * 0.3} ${-width * 0.28}
              Q ${length * 0.44} ${-width * 0.18} ${length * 0.48} 0
              Q ${length * 0.44} ${width * 0.18} ${length * 0.3} ${width * 0.28}
              L ${-length * 0.14} ${width * 0.28}
              Q ${-length * 0.34} ${width * 0.28} ${-length * 0.48} ${width * 0.16}
              Z`}
          className="vehicle-body vehicle-body-car"
        />
        <path
          d={`M ${-length * 0.18} ${-width * 0.18}
              Q ${-length * 0.08} ${-width * 0.34} ${length * 0.08} ${-width * 0.34}
              L ${length * 0.2} ${-width * 0.12}
              Q ${length * 0.12} ${0} ${-length * 0.08} ${0}
              Z`}
          className="vehicle-cab vehicle-cab-car"
        />
        {renderWheelPair(length * 0.26, -length * 0.24, width * 0.32, width * 0.078)}
        {renderVehicleHeading(length, width)}
      </>
    );
  }
  return (
    <>
      <rect
        x={-length * 0.42}
        y={-width * 0.26}
        width={length * 0.78}
        height={width * 0.52}
        rx={0.12}
        className="vehicle-body vehicle-body-generic"
      />
      <rect
        x={-length * 0.14}
        y={-width * 0.4}
        width={length * 0.24}
        height={width * 0.11}
        rx={0.04}
        className="vehicle-cab vehicle-cab-generic"
      />
      {renderWheelPair(length * 0.2, -length * 0.22, width * 0.3, width * 0.074)}
      {renderVehicleHeading(length, width)}
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
    return `queue ${selectedTarget.roadId}`;
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

function normalizeReviewLevel(value: string | undefined, fallback = "info"): string {
  return (value ?? fallback).trim().toLowerCase().replace(/\s+/g, "-");
}

function reviewSeverityRank(value: string | undefined): number {
  switch (normalizeReviewLevel(value)) {
    case "critical":
    case "error":
      return 0;
    case "high":
      return 1;
    case "warning":
      return 2;
    case "medium":
      return 3;
    case "low":
      return 4;
    default:
      return 5;
  }
}

function reviewPriorityRank(value: string | undefined): number {
  switch (normalizeReviewLevel(value, "medium")) {
    case "critical":
    case "urgent":
      return 0;
    case "high":
      return 1;
    case "medium":
      return 2;
    case "normal":
    case "low":
      return 3;
    default:
      return 4;
  }
}

function describeEdgeTargetLabel(edgeId: number | undefined, roads: RoadPayload[]): string | null {
  if (edgeId === undefined) {
    return null;
  }
  const road = roads.find((entry) => (entry.edge_ids ?? []).includes(edgeId));
  if (road?.road_id) {
    return `Edge ${edgeId} · Road ${road.road_id}`;
  }
  return `Edge ${edgeId}`;
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

function describeRecentCommand(command: RecentCommandPayload): string {
  const commandType = command.command_type ?? "command";
  if (commandType === "assign_vehicle_destination") {
    return `assign_vehicle_destination · vehicle ${formatMaybeNumber(command.vehicle_id ?? null)} → node ${formatMaybeNumber(command.destination_node_id ?? null)}`;
  }
  if (commandType === "reposition_vehicle") {
    return `reposition_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id ?? null)} → node ${formatMaybeNumber(command.node_id ?? null)}`;
  }
  if (commandType === "block_edge" || commandType === "unblock_edge") {
    return `${commandType} · edge ${formatMaybeNumber(command.edge_id ?? null)}`;
  }
  if (commandType === "spawn_vehicle") {
    return `spawn_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id ?? null)} at node ${formatMaybeNumber(command.node_id ?? null)} type ${command.vehicle_type ?? "GENERIC"}`;
  }
  if (commandType === "remove_vehicle") {
    return `remove_vehicle · vehicle ${formatMaybeNumber(command.vehicle_id ?? null)}`;
  }
  if (commandType === "inject_job") {
    return `inject_job · vehicle ${formatMaybeNumber(command.vehicle_id ?? null)} job ${command.job?.id ?? "job"}`;
  }
  if (commandType === "declare_temporary_hazard" || commandType === "clear_temporary_hazard") {
    return `${commandType} · edge ${formatMaybeNumber(command.edge_id ?? null)}${command.hazard_label ? ` (${command.hazard_label})` : ""}`;
  }
  return commandType;
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

function formatMeters(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(2)}m`;
}

export default App;
