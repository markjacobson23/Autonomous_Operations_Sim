export type JsonRecord = Record<string, unknown>;

export type LoadState = "loading" | "ready" | "error";

export type Point2 = readonly [number, number];

export type LiveBundleResource = {
  bundleUrl: string;
  loadState: LoadState;
  loadMessage: string;
  bundle: JsonRecord | null;
  refresh: () => void;
};

export type LiveRoadViewModel = {
  roadId: string;
  centerline: Point2[];
  edgeIds: number[];
  blocked: boolean;
  roadClass: string;
  directionality: string;
  laneCount: number;
};

export type LiveAreaViewModel = {
  areaId: string;
  kind: string;
  polygon: Point2[];
  label: string | null;
};

export type LiveTrafficControlPointViewModel = {
  controlId: string;
  nodeId: number;
  controlType: string;
  controlledRoadIds: string[];
  stopLineIds: string[];
  protectedConflictZoneIds: string[];
  signalReady: boolean;
};

export type LiveTrafficQueueRecordViewModel = {
  vehicleId: number;
  nodeId: number;
  roadId: string | null;
  queueStartS: number;
  queueEndS: number;
  reason: string;
};

export type LiveTrafficRoadStateViewModel = {
  roadId: string;
  activeVehicleIds: number[];
  queuedVehicleIds: number[];
  occupancyCount: number;
  minSpacingM: number | null;
  congestionIntensity: number;
  congestionLevel: string;
  controlState: string;
  stopLineIds: string[];
  protectedConflictZoneIds: string[];
};

export type LiveNodeViewModel = {
  nodeId: number;
  position: Point2;
};

export type LiveVehicleViewModel = {
  vehicleId: number;
  position: Point2;
  state: string;
  stateClass: "moving" | "waiting" | "idle";
};

export type LiveRoutePreviewViewModel = {
  vehicleId: number;
  destinationNodeId: number;
  isActionable: boolean;
  reason: string | null;
  reasonCode: string | null;
  nodeIds: number[];
  edgeIds: number[];
  totalDistance: number | null;
};

export type LiveVehicleInspectionViewModel = {
  vehicleId: number;
  currentNodeId: number | null;
  exactPosition: Point2;
  operationalState: string;
  currentJobId: string | null;
  currentTaskIndex: number | null;
  currentTaskType: string | null;
  assignedResourceId: string | null;
  waitReason: string | null;
  trafficControlState: string | null;
  trafficControlDetail: string | null;
  etaSeconds: number | null;
  routeAheadNodeIds: number[];
  routeAheadEdgeIds: number[];
  recentCommands: JsonRecord[];
  diagnostics: Array<{
    code: string;
    severity: string;
    message: string;
  }>;
};

export type LiveAnalysisSignalViewModel = {
  code: string;
  severity: string;
  message: string;
  vehicleId: number | null;
};

export type LiveBundleViewModel = {
  bundleUrl: string;
  loadState: LoadState;
  loadMessage: string;
  selectedVehicleIds: number[];
  alerts: string[];
  sessionIdentity: {
    scenarioPath: string;
    scenarioName: string;
    surfaceName: string;
    apiVersion: string;
    playState: string;
    stepSeconds: string;
    simulatedTime: string;
    seed: string;
  };
  commandSurface: {
    sessionControlEndpoint: string;
    commandEndpoint: string;
    previewEndpoint: string;
  };
  map: {
    nodes: LiveNodeViewModel[];
    roads: LiveRoadViewModel[];
    areas: LiveAreaViewModel[];
    vehicles: LiveVehicleViewModel[];
    blockedEdgeIds: number[];
    environment: {
      family: string;
      archetypeId: string;
      displayName: string;
    };
    bounds: {
      minX: number;
      minY: number;
      maxX: number;
      maxY: number;
      width: number;
      height: number;
    };
  };
  commandCenter: {
    routePreviews: LiveRoutePreviewViewModel[];
    vehicleInspections: LiveVehicleInspectionViewModel[];
  };
  traffic: {
    sampleTimeS: number | null;
    roadStates: LiveTrafficRoadStateViewModel[];
    queueRecords: LiveTrafficQueueRecordViewModel[];
    controlPoints: LiveTrafficControlPointViewModel[];
  };
  analysis: {
    anomalySignals: LiveAnalysisSignalViewModel[];
  };
  utility: {
    frontendOwnedState: readonly string[];
    simulatorOwnedTruth: readonly string[];
    repoLayoutDecision: readonly string[];
  };
};

export function buildLiveBundleViewModel(resource: LiveBundleResource): LiveBundleViewModel {
  const bundle = resource.bundle;
  const metadata = readRecord(bundle, "metadata");
  const authoring = readRecord(bundle, "authoring");
  const sessionControl = readRecord(bundle, "session_control");
  const commandCenter = readRecord(bundle, "command_center");
  const snapshot = readRecord(bundle, "snapshot");
  const renderGeometry = readRecord(bundle, "render_geometry");
  const trafficBaseline = readRecord(bundle, "traffic_baseline");
  const trafficSnapshot = readRecord(bundle, "traffic_snapshot");
  const aiAssist = readRecord(commandCenter, "ai_assist");
  const worldModel = readRecord(renderGeometry, "world_model");
  const worldEnvironment = readRecord(worldModel, "environment");

  const roads = readArray(renderGeometry, "roads").flatMap((road, index) => {
    const roadRecord = isRecord(road) ? road : null;
    if (roadRecord === null) {
      return [];
    }
    return [
      {
        roadId: readString(roadRecord, "road_id", `road-${index}`),
        centerline: readPointList(readArray(roadRecord, "centerline")),
        edgeIds: readNumberList(roadRecord, "edge_ids"),
        blocked: readNumberArray(roadRecord, "edge_ids").some((edgeId) =>
          readNumberArray(snapshot, "blocked_edge_ids").includes(edgeId),
        ),
        roadClass: readString(roadRecord, "road_class", "connector"),
        directionality: readString(roadRecord, "directionality", "one_way"),
        laneCount: readNumber(roadRecord, "lane_count", 1),
      },
    ];
  });
  const nodes = readArray(renderGeometry, "intersections").flatMap((intersection, index) => {
    const intersectionRecord = isRecord(intersection) ? intersection : null;
    if (intersectionRecord === null) {
      return [];
    }

    const position = averagePoint(readPointList(readArray(intersectionRecord, "polygon")));
    if (position === null) {
      return [];
    }

    return [
      {
        nodeId: readNumber(intersectionRecord, "node_id", index + 1),
        position,
      },
    ];
  });

  const areas = readArray(renderGeometry, "areas").flatMap((area, index) => {
    const areaRecord = isRecord(area) ? area : null;
    if (areaRecord === null) {
      return [];
    }

    return [
      {
        areaId: readString(areaRecord, "area_id", `area-${index}`),
        kind: readString(areaRecord, "kind", "context"),
        polygon: readPointList(readArray(areaRecord, "polygon")),
        label: areaRecord.label === null || areaRecord.label === undefined ? null : String(areaRecord.label),
      },
    ];
  });

  const vehicles = readArray(snapshot, "vehicles").flatMap((vehicle, index) => {
    const vehicleRecord = isRecord(vehicle) ? vehicle : null;
    if (vehicleRecord === null) {
      return [];
    }
    const position = readPoint(vehicleRecord.position);
    if (position === null) {
      return [];
    }
    const state = readString(vehicleRecord, "operational_state", "idle");
    return [
      {
        vehicleId: readNumber(vehicleRecord, "vehicle_id", index + 1),
        position,
        state,
        stateClass: vehicleStateClass(state),
      },
    ];
  });

  const blockedEdgeIds = readNumberArray(snapshot, "blocked_edge_ids");
  const selectedVehicleIds = readNumberArray(commandCenter, "selected_vehicle_ids");
  const routePreviews = readArray(commandCenter, "route_previews").flatMap((preview, index) => {
    const previewRecord = isRecord(preview) ? preview : null;
    if (previewRecord === null) {
      return [];
    }

    return [
      {
        vehicleId: readNumber(previewRecord, "vehicle_id", index + 1),
        destinationNodeId: readNumber(previewRecord, "destination_node_id", -1),
        isActionable: Boolean(previewRecord.is_actionable),
        reason: readStringOrNull(previewRecord, "reason"),
        reasonCode: readStringOrNull(previewRecord, "reason_code"),
        nodeIds: readNumberList(previewRecord, "node_ids"),
        edgeIds: readNumberList(previewRecord, "edge_ids"),
        totalDistance: readNumberOrNull(previewRecord, "total_distance"),
      },
    ];
  });
  const vehicleInspections = readArray(commandCenter, "vehicle_inspections").flatMap((inspection, index) => {
    const inspectionRecord = isRecord(inspection) ? inspection : null;
    if (inspectionRecord === null) {
      return [];
    }

    return [
      {
        vehicleId: readNumber(inspectionRecord, "vehicle_id", index + 1),
        currentNodeId: readNumberOrNull(inspectionRecord, "current_node_id"),
        exactPosition: readPoint(inspectionRecord.exact_position) ?? ([0, 0] as Point2),
        operationalState: readString(inspectionRecord, "operational_state", "unknown"),
        currentJobId: readStringOrNull(inspectionRecord, "current_job_id"),
        currentTaskIndex: readNumberOrNull(inspectionRecord, "current_task_index"),
        currentTaskType: readStringOrNull(inspectionRecord, "current_task_type"),
        assignedResourceId: readStringOrNull(inspectionRecord, "assigned_resource_id"),
        waitReason: readStringOrNull(inspectionRecord, "wait_reason"),
        trafficControlState: readStringOrNull(inspectionRecord, "traffic_control_state"),
        trafficControlDetail: readStringOrNull(inspectionRecord, "traffic_control_detail"),
        etaSeconds: readNumberOrNull(inspectionRecord, "eta_s"),
        routeAheadNodeIds: readNumberList(inspectionRecord, "route_ahead_node_ids"),
        routeAheadEdgeIds: readNumberList(inspectionRecord, "route_ahead_edge_ids"),
        recentCommands: readArray(inspectionRecord, "recent_commands").flatMap((entry) =>
          isRecord(entry) ? [entry] : [],
        ),
        diagnostics: readArray(inspectionRecord, "diagnostics").flatMap((entry) => {
          const diagnostic = isRecord(entry) ? entry : null;
          if (diagnostic === null) {
            return [];
          }
          return [
            {
              code: readString(diagnostic, "code", "unknown"),
              severity: readString(diagnostic, "severity", "info"),
              message: readString(diagnostic, "message", "No detail available."),
            },
          ];
        }),
      },
    ];
  });
  const controlPoints = readArray(trafficBaseline, "control_points").flatMap((entry) =>
    isRecord(entry) ? [entry] : [],
  );
  const queueRecords = readArray(trafficBaseline, "queue_records").flatMap((entry) =>
    isRecord(entry) ? [entry] : [],
  );
  const trafficRoadStates = readArray(trafficSnapshot, "road_states").flatMap((entry) =>
    isRecord(entry) ? [entry] : [],
  );
  const anomalies = readArray(aiAssist, "anomalies").flatMap((entry) => (isRecord(entry) ? [entry] : []));
  const anomalySignals = anomalies.map((entry, index) => ({
    code: readString(entry, "code", `anomaly-${index + 1}`),
    severity: readString(entry, "severity", "info"),
    message: readString(entry, "message", "No detail available."),
    vehicleId: readNumberOrNull(entry, "vehicle_id"),
  }));
  const congestedRoadCount = trafficRoadStates.filter((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2).length;
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + readNumberList(roadState, "queued_vehicle_ids").length,
    0,
  );

  const alerts = [
    ...(blockedEdgeIds.length > 0 ? [`${blockedEdgeIds.length} blocked edge(s)`] : []),
    ...(congestedRoadCount > 0 ? [`${congestedRoadCount} congested road(s)`] : []),
    ...(queuedVehicleCount > 0 ? [`${queuedVehicleCount} queued vehicle(s)`] : []),
    ...(queueRecords.length > 0 ? [`${queueRecords.length} queue record(s)`] : []),
    ...(anomalies.length > 0 ? [`${anomalies.length} anomaly signal(s)`] : []),
  ];

  return {
    bundleUrl: resource.bundleUrl,
    loadState: resource.loadState,
    loadMessage: resource.loadMessage,
    selectedVehicleIds,
    alerts,
    sessionIdentity: {
      scenarioPath: readString(authoring, "source_scenario_path", "unknown scenario"),
      scenarioName: readString(authoring, "source_scenario_path", "unknown scenario")
        .split("/")
        .pop()
        ?.replace(/\.json$/u, "") ?? "live session",
      surfaceName: readString(metadata, "surface_name", "live_session_bundle"),
      apiVersion: numberToString(readNumber(metadata, "api_version", Number.NaN), "unknown"),
      playState: readString(sessionControl, "play_state", "paused"),
      stepSeconds: secondsToString(readNumber(sessionControl, "step_seconds", Number.NaN)),
      simulatedTime: secondsToString(readNumber(bundle, "simulated_time_s", Number.NaN)),
      seed: numberToString(readNumber(bundle, "seed", Number.NaN), "pending"),
    },
    commandSurface: {
      sessionControlEndpoint: readString(sessionControl, "session_control_endpoint", "unknown"),
      commandEndpoint: readString(sessionControl, "command_endpoint", "unknown"),
      previewEndpoint: readString(sessionControl, "route_preview_endpoint", "unknown"),
    },
    map: {
      nodes,
      roads,
      areas,
      vehicles,
      blockedEdgeIds,
      environment: {
        family: readString(worldEnvironment, "family", "unknown"),
        archetypeId: readString(worldEnvironment, "archetype_id", "unknown"),
        displayName: readString(worldEnvironment, "display_name", "unknown environment"),
      },
      bounds: padBounds(computeBounds(collectScenePoints(bundle)), 2),
    },
    commandCenter: {
      routePreviews,
      vehicleInspections,
    },
    traffic: {
      sampleTimeS: readNumberOrNull(trafficSnapshot, "timestamp_s"),
      roadStates: trafficRoadStates.flatMap((roadState, index) => {
        const roadStateRecord = isRecord(roadState) ? roadState : null;
        if (roadStateRecord === null) {
          return [];
        }

        return [
          {
            roadId: readString(roadStateRecord, "road_id", `road-${index}`),
            activeVehicleIds: readNumberList(roadStateRecord, "active_vehicle_ids"),
            queuedVehicleIds: readNumberList(roadStateRecord, "queued_vehicle_ids"),
            occupancyCount: readNumber(roadStateRecord, "occupancy_count", 0),
            minSpacingM: readNumberOrNull(roadStateRecord, "min_spacing_m"),
            congestionIntensity: readNumber(roadStateRecord, "congestion_intensity", 0),
            congestionLevel: readString(roadStateRecord, "congestion_level", "free"),
            controlState: readString(roadStateRecord, "control_state", "free_flow"),
            stopLineIds: readStringList(roadStateRecord, "stop_line_ids"),
            protectedConflictZoneIds: readStringList(roadStateRecord, "protected_conflict_zone_ids"),
          },
        ];
      }),
      queueRecords: queueRecords.flatMap((queueRecord) => {
        const queueRecordRecord = isRecord(queueRecord) ? queueRecord : null;
        if (queueRecordRecord === null) {
          return [];
        }

        return [
          {
            vehicleId: readNumber(queueRecordRecord, "vehicle_id", -1),
            nodeId: readNumber(queueRecordRecord, "node_id", -1),
            roadId: readStringOrNull(queueRecordRecord, "road_id"),
            queueStartS: readNumber(queueRecordRecord, "queue_start_s", 0),
            queueEndS: readNumber(queueRecordRecord, "queue_end_s", 0),
            reason: readString(queueRecordRecord, "reason", "queue"),
          },
        ];
      }),
      controlPoints: controlPoints.flatMap((controlPoint) => {
        const controlPointRecord = isRecord(controlPoint) ? controlPoint : null;
        if (controlPointRecord === null) {
          return [];
        }

        return [
          {
            controlId: readString(controlPointRecord, "control_id", "control"),
            nodeId: readNumber(controlPointRecord, "node_id", -1),
            controlType: readString(controlPointRecord, "control_type", "unknown"),
            controlledRoadIds: readStringList(controlPointRecord, "controlled_road_ids"),
            stopLineIds: readStringList(controlPointRecord, "stop_line_ids"),
            protectedConflictZoneIds: readStringList(controlPointRecord, "protected_conflict_zone_ids"),
            signalReady: Boolean(controlPointRecord.signal_ready),
          },
        ];
      }),
    },
    analysis: {
      anomalySignals,
    },
    utility: {
      frontendOwnedState: [
        "camera and viewport state",
        "scene mode and layer toggles",
        "selection and hover state",
        "popup and inspector state",
        "route preview and command form state",
        "session control UI state",
        "planning workflow drafts",
        "mode and panel state",
      ],
      simulatorOwnedTruth: [
        "runtime vehicle truth",
        "final route truth",
        "conflict and reservation truth",
        "topology truth",
        "deterministic progression semantics",
      ],
      repoLayoutDecision: [
        "Canonical Frontend v2 lives in a dedicated workspace.",
        "Legacy serious UI remains frozen as a compatibility path only.",
        "Python simulator stays authoritative; the frontend consumes derived surfaces.",
      ],
    },
  };
}

function vehicleStateClass(state: string): "moving" | "waiting" | "idle" {
  const normalized = state.toLowerCase();
  if (normalized.includes("wait") || normalized.includes("queue")) {
    return "waiting";
  }
  if (normalized.includes("move")) {
    return "moving";
  }
  return "idle";
}

function numberToString(value: number, fallback: string): string {
  return Number.isNaN(value) ? fallback : String(value);
}

function secondsToString(value: number): string {
  return Number.isNaN(value) ? "unknown" : `${value.toFixed(1)}s`;
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

function readStringOrNull(value: JsonRecord | null | undefined, key: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  const nested = value[key];
  return typeof nested === "string" && nested.trim().length > 0 ? nested : null;
}

function readNumber(value: JsonRecord | null | undefined, key: string, fallback: number): number {
  if (value === null || value === undefined) {
    return fallback;
  }
  const nested = value[key];
  return typeof nested === "number" && Number.isFinite(nested) ? nested : fallback;
}

function readNumberOrNull(value: JsonRecord | null | undefined, key: string): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const nested = value[key];
  return typeof nested === "number" && Number.isFinite(nested) ? nested : null;
}

function readNumberList(value: JsonRecord, key: string): number[] {
  return readArray(value, key).flatMap((entry) =>
    typeof entry === "number" && Number.isFinite(entry) ? [entry] : [],
  );
}

function readStringList(value: JsonRecord, key: string): string[] {
  return readArray(value, key).flatMap((entry) =>
    typeof entry === "string" && entry.trim().length > 0 ? [entry] : [],
  );
}

function readNumberArray(value: JsonRecord | null, key: string): number[] {
  return readArray(value, key).flatMap((entry) =>
    typeof entry === "number" && Number.isFinite(entry) ? [entry] : [],
  );
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

function readPointList(points: unknown[]): Point2[] {
  return points.flatMap((point) => {
    const resolved = readPoint(point);
    return resolved === null ? [] : [resolved];
  });
}

function averagePoint(points: Point2[]): Point2 | null {
  if (points.length === 0) {
    return null;
  }

  const total = points.reduce(
    (accumulator, point) => {
      accumulator.x += point[0];
      accumulator.y += point[1];
      return accumulator;
    },
    { x: 0, y: 0 },
  );
  return [total.x / points.length, total.y / points.length];
}

function collectScenePoints(bundle: JsonRecord | null): Point2[] {
  const points: Point2[] = [];
  const renderGeometry = readRecord(bundle, "render_geometry");
  const snapshot = readRecord(bundle, "snapshot");

  for (const road of readArray(renderGeometry, "roads")) {
    if (!isRecord(road)) {
      continue;
    }
    points.push(...readPointList(readArray(road, "centerline")));
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

  return points.length > 0 ? points : [[-10, -6], [10, 6]];
}

function computeBounds(points: Point2[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
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
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
    width: number;
    height: number;
  },
  padding: number,
): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  return {
    minX: bounds.minX - padding,
    minY: bounds.minY - padding,
    maxX: bounds.maxX + padding,
    maxY: bounds.maxY + padding,
    width: bounds.width + padding * 2,
    height: bounds.height + padding * 2,
  };
}
