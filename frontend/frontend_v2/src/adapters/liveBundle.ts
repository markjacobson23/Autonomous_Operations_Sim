export type JsonRecord = Record<string, unknown>;

export type LoadState = "loading" | "ready" | "error";

export type Point2 = readonly [number, number];

export type LiveBundleResource = {
  bundleUrl: string;
  loadState: LoadState;
  loadMessage: string;
  bundle: JsonRecord | null;
};

export type LiveRoadViewModel = {
  roadId: string;
  centerline: Point2[];
  blocked: boolean;
};

export type LiveAreaViewModel = {
  areaId: string;
  kind: string;
  polygon: Point2[];
  label: string | null;
};

export type LiveVehicleViewModel = {
  vehicleId: number;
  position: Point2;
  state: string;
  stateClass: "moving" | "waiting" | "idle";
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
    roads: LiveRoadViewModel[];
    areas: LiveAreaViewModel[];
    vehicles: LiveVehicleViewModel[];
    blockedEdgeIds: number[];
    bounds: {
      minX: number;
      minY: number;
      maxX: number;
      maxY: number;
      width: number;
      height: number;
    };
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
  const aiAssist = readRecord(commandCenter, "ai_assist");

  const roads = readArray(renderGeometry, "roads").flatMap((road, index) => {
    const roadRecord = isRecord(road) ? road : null;
    if (roadRecord === null) {
      return [];
    }
    return [
      {
        roadId: readString(roadRecord, "road_id", `road-${index}`),
        centerline: readPointList(readArray(roadRecord, "centerline")),
        blocked: readNumberArray(roadRecord, "edge_ids").some((edgeId) =>
          readNumberArray(snapshot, "blocked_edge_ids").includes(edgeId),
        ),
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
  const trafficRoadStates = readArray(trafficBaseline, "road_states").flatMap((entry) =>
    isRecord(entry) ? [entry] : [],
  );
  const anomalies = readArray(aiAssist, "anomalies").flatMap((entry) => (isRecord(entry) ? [entry] : []));

  const alerts = [
    ...(blockedEdgeIds.length > 0 ? [`${blockedEdgeIds.length} blocked edge(s)`] : []),
    ...(trafficRoadStates.some((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2)
      ? [`${trafficRoadStates.filter((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2).length} congested road(s)`]
      : []),
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
      roads,
      areas,
      vehicles,
      blockedEdgeIds,
      bounds: padBounds(computeBounds(collectScenePoints(bundle)), 2),
    },
    utility: {
      frontendOwnedState: [
        "camera and viewport state",
        "scene mode and layer toggles",
        "selection and hover state",
        "popup and inspector state",
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

function readNumber(value: JsonRecord | null | undefined, key: string, fallback: number): number {
  if (value === null || value === undefined) {
    return fallback;
  }
  const nested = value[key];
  return typeof nested === "number" && Number.isFinite(nested) ? nested : fallback;
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
