export type JsonRecord = Record<string, unknown>;

export type LoadState = "loading" | "ready" | "error";

export type Point2 = readonly [number, number];

export type SceneBoundsPayload = {
  min_x?: number;
  min_y?: number;
  max_x?: number;
  max_y?: number;
  width?: number;
  height?: number;
};

export type SceneExtentPayload = {
  extent_id?: string;
  source?: string;
  category?: string;
  label?: string;
  feature_ids?: string[];
  bounds?: SceneBoundsPayload;
};

export type SceneFramePayload = {
  frame_id?: string;
  environment_family?: string;
  scene_bounds?: SceneBoundsPayload;
  extents?: SceneExtentPayload[];
};

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
  category: string;
  kind: string;
  formType: "flat" | "raised" | "recessed" | "structure_mass";
  heightHint: number;
  depthHint: number;
  polygon: Point2[];
  label: string | null;
  groupId: string | null;
};

export type LiveIntersectionViewModel = {
  intersectionId: string;
  nodeId: number;
  polygon: Point2[];
  intersectionType: string;
};

export type LiveTrafficControlPointViewModel = {
  controlId: string;
  nodeId: number;
  position: Point2 | null;
  controlType: string;
  controlledRoadIds: string[];
  stopLineIds: string[];
  protectedConflictZoneIds: string[];
  signalReady: boolean;
  renderDiagnostics: string[];
};

export type LiveTrafficQueueRecordViewModel = {
  vehicleId: number;
  nodeId: number;
  position: Point2 | null;
  roadId: string | null;
  queueStartS: number;
  queueEndS: number;
  reason: string;
  renderDiagnostics: string[];
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
  positionSource: "inspection_exact_position" | "snapshot_position" | "canonical_node_position" | "unavailable";
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
  pathPoints: Point2[];
  destinationPoint: Point2 | null;
  renderDiagnostics: string[];
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

export type LiveOperatorVehicleStatusViewModel = {
  vehicleId: number;
  currentNodeId: number;
  motionAuthority: string;
  routeStatus: string | null;
  routeProgress: number | null;
  currentTargetNodeId: number | null;
  currentWaypointIndex: number | null;
  routeDestinationNodeId: number | null;
  routeCompleted: boolean | null;
  embodimentState: string | null;
  blockageReason: string | null;
  blockageEdgeId: number | null;
  blockageNodeId: number | null;
  exceptionCode: string | null;
};

export type LiveOperatorStateViewModel = {
  motionAuthority: string;
  vehicleCount: number;
  blockedVehicleIds: number[];
  vehicles: LiveOperatorVehicleStatusViewModel[];
};

export type LiveBundleViewModel = {
  bundleUrl: string;
  loadState: LoadState;
  loadMessage: string;
  selectedVehicleIds: number[];
  alerts: string[];
  sessionIdentity: {
    key: string;
    scenarioPath: string;
    scenarioName: string;
    surfaceName: string;
    apiVersion: string;
    motionAuthority: string;
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
    intersections: LiveIntersectionViewModel[];
    areas: LiveAreaViewModel[];
    vehicles: LiveVehicleViewModel[];
    blockedEdgeIds: number[];
    environment: {
      family: string;
      archetypeId: string;
      displayName: string;
    };
    sceneFrame: {
      frameId: string;
      environmentFamily: string;
      sceneBounds: {
        minX: number;
        minY: number;
        maxX: number;
        maxY: number;
        width: number;
        height: number;
      };
      extents: Array<{
        extentId: string;
        source: string;
        category: string;
        label: string;
        featureIds: string[];
        bounds: {
          minX: number;
          minY: number;
          maxX: number;
          maxY: number;
          width: number;
          height: number;
        };
      }>;
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
  operatorState: LiveOperatorStateViewModel;
  utility: {
    frontendOwnedState: readonly string[];
    simulatorOwnedTruth: readonly string[];
    repoLayoutDecision: readonly string[];
    renderDiagnostics: readonly string[];
  };
};

type InspectionRecord = {
  currentNodeId: number | null;
  exactPosition: Point2 | null;
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

export function buildLiveBundleViewModel(resource: LiveBundleResource): LiveBundleViewModel {
  const bundle = resource.bundle;
  const metadata = readRecord(bundle, "metadata");
  const authoring = readRecord(bundle, "authoring");
  const sessionControl = readRecord(bundle, "session_control");
  const commandCenter = readRecord(bundle, "command_center");
  const operatorState = readRecord(bundle, "operator_state");
  const snapshot = readRecord(bundle, "snapshot");
  const mapSurface = readRecord(bundle, "map_surface");
  const renderGeometry = readRecord(bundle, "render_geometry");
  const trafficBaseline = readRecord(bundle, "traffic_baseline");
  const trafficSnapshot = readRecord(bundle, "traffic_snapshot");
  const aiAssist = readRecord(commandCenter, "ai_assist");
  const worldModel = readRecord(renderGeometry, "world_model");
  const worldEnvironment = readRecord(worldModel, "environment");
  const sceneFrame = resolveSceneFrame(renderGeometry, bundle);

  const nodes = readArray(mapSurface, "nodes").flatMap((node, index) => {
    const nodeRecord = isRecord(node) ? node : null;
    if (nodeRecord === null) {
      return [];
    }

    const position = readPoint(nodeRecord.position);
    if (position === null) {
      return [];
    }

    return [
      {
        nodeId: readNumber(nodeRecord, "node_id", index + 1),
        position,
      },
    ];
  });
  const nodePositionsById = new Map<number, Point2>(nodes.map((node) => [node.nodeId, node.position]));

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
        blocked: readNumberArray(snapshot, "blocked_edge_ids").some((edgeId) =>
          readNumberArray(roadRecord, "edge_ids").includes(edgeId),
        ),
        roadClass: readString(roadRecord, "road_class", "connector"),
        directionality: readString(roadRecord, "directionality", "one_way"),
        laneCount: readNumber(roadRecord, "lane_count", 1),
      },
    ];
  });

  const intersections = readArray(renderGeometry, "intersections").flatMap((intersection, index) => {
    const intersectionRecord = isRecord(intersection) ? intersection : null;
    if (intersectionRecord === null) {
      return [];
    }

    return [
      {
        intersectionId: readString(intersectionRecord, "intersection_id", `intersection-${index}`),
        nodeId: readNumber(intersectionRecord, "node_id", index + 1),
        polygon: readPointList(readArray(intersectionRecord, "polygon")),
        intersectionType: readString(intersectionRecord, "intersection_type", "junction"),
      },
    ];
  });

  const areas = readArray(renderGeometry, "areas").flatMap((area, index) => {
    const areaRecord = isRecord(area) ? area : null;
    if (areaRecord === null) {
      return [];
    }
    const areaKind = readString(areaRecord, "kind", "context");

    return [
      {
        areaId: readString(areaRecord, "area_id", `area-${index}`),
        category: readString(areaRecord, "category", classifyAreaCategory(areaKind)),
        kind: areaKind,
        formType: readAreaFormType(readStringOrNull(areaRecord, "form_type"), areaKind),
        heightHint: readNumber(areaRecord, "height_hint", defaultAreaHeightHint(areaKind)),
        depthHint: readNumber(areaRecord, "depth_hint", defaultAreaDepthHint(areaKind)),
        polygon: readPointList(readArray(areaRecord, "polygon")),
        label: areaRecord.label === null || areaRecord.label === undefined ? null : String(areaRecord.label),
        groupId: readStringOrNull(areaRecord, "group_id"),
      },
    ];
  });

  const inspectionsByVehicleId = new Map<number, InspectionRecord>();
  const vehicleInspections = readArray(commandCenter, "vehicle_inspections").flatMap((inspection, index) => {
    const inspectionRecord = isRecord(inspection) ? inspection : null;
    if (inspectionRecord === null) {
      return [];
    }

    const vehicleId = readNumber(inspectionRecord, "vehicle_id", index + 1);
    const normalizedInspection: InspectionRecord = {
      currentNodeId: readNumberOrNull(inspectionRecord, "current_node_id"),
      exactPosition: readPoint(inspectionRecord.exact_position),
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
    };

    inspectionsByVehicleId.set(vehicleId, normalizedInspection);
    return [
      {
        vehicleId,
        currentNodeId: normalizedInspection.currentNodeId,
        exactPosition: normalizedInspection.exactPosition ?? nodePositionsById.get(normalizedInspection.currentNodeId ?? -1) ?? ([0, 0] as Point2),
        operationalState: normalizedInspection.operationalState,
        currentJobId: normalizedInspection.currentJobId,
        currentTaskIndex: normalizedInspection.currentTaskIndex,
        currentTaskType: normalizedInspection.currentTaskType,
        assignedResourceId: normalizedInspection.assignedResourceId,
        waitReason: normalizedInspection.waitReason,
        trafficControlState: normalizedInspection.trafficControlState,
        trafficControlDetail: normalizedInspection.trafficControlDetail,
        etaSeconds: normalizedInspection.etaSeconds,
        routeAheadNodeIds: normalizedInspection.routeAheadNodeIds,
        routeAheadEdgeIds: normalizedInspection.routeAheadEdgeIds,
        recentCommands: normalizedInspection.recentCommands,
        diagnostics: normalizedInspection.diagnostics,
      },
    ];
  });

  const selectedVehicleIds = readNumberArray(commandCenter, "selected_vehicle_ids");
  const renderDiagnostics: string[] = [];

  const routePreviews = readArray(commandCenter, "route_previews").flatMap((preview, index) => {
    const previewRecord = isRecord(preview) ? preview : null;
    if (previewRecord === null) {
      return [];
    }

    const vehicleId = readNumber(previewRecord, "vehicle_id", index + 1);
    const destinationNodeId = readNumber(previewRecord, "destination_node_id", -1);
    const nodeIds = readNumberList(previewRecord, "node_ids");
    const edgeIds = readNumberList(previewRecord, "edge_ids");
    const resolvedGeometry = resolveRoutePreviewGeometry(nodePositionsById, vehicleId, destinationNodeId, nodeIds);
    renderDiagnostics.push(...resolvedGeometry.renderDiagnostics);

    return [
      {
        vehicleId,
        destinationNodeId,
        isActionable: Boolean(previewRecord.is_actionable),
        reason: readStringOrNull(previewRecord, "reason"),
        reasonCode: readStringOrNull(previewRecord, "reason_code"),
        nodeIds,
        edgeIds,
        totalDistance: readNumberOrNull(previewRecord, "total_distance"),
        pathPoints: resolvedGeometry.pathPoints,
        destinationPoint: resolvedGeometry.destinationPoint,
        renderDiagnostics: resolvedGeometry.renderDiagnostics,
      },
    ];
  });

  const trafficControlPoints = readArray(trafficBaseline, "control_points").flatMap((controlPoint) => {
    const controlPointRecord = isRecord(controlPoint) ? controlPoint : null;
    if (controlPointRecord === null) {
      return [];
    }

    const nodeId = readNumber(controlPointRecord, "node_id", -1);
    const position = nodePositionsById.get(nodeId) ?? null;
    const diagnostics = position === null ? [`Control point ${readString(controlPointRecord, "control_id", "control")} could not resolve node ${nodeId}.`] : [];
    renderDiagnostics.push(...diagnostics);

    return [
      {
        controlId: readString(controlPointRecord, "control_id", "control"),
        nodeId,
        position,
        controlType: readString(controlPointRecord, "control_type", "unknown"),
        controlledRoadIds: readStringList(controlPointRecord, "controlled_road_ids"),
        stopLineIds: readStringList(controlPointRecord, "stop_line_ids"),
        protectedConflictZoneIds: readStringList(controlPointRecord, "protected_conflict_zone_ids"),
        signalReady: Boolean(controlPointRecord.signal_ready),
        renderDiagnostics: diagnostics,
      },
    ];
  });

  const trafficQueueRecords = readArray(trafficBaseline, "queue_records").flatMap((queueRecord) => {
    const queueRecordRecord = isRecord(queueRecord) ? queueRecord : null;
    if (queueRecordRecord === null) {
      return [];
    }

    const nodeId = readNumber(queueRecordRecord, "node_id", -1);
    const position = nodePositionsById.get(nodeId) ?? null;
    const diagnostics = position === null ? [`Queue record for vehicle ${readNumber(queueRecordRecord, "vehicle_id", -1)} could not resolve node ${nodeId}.`] : [];
    renderDiagnostics.push(...diagnostics);

    return [
      {
        vehicleId: readNumber(queueRecordRecord, "vehicle_id", -1),
        nodeId,
        position,
        roadId: readStringOrNull(queueRecordRecord, "road_id"),
        queueStartS: readNumber(queueRecordRecord, "queue_start_s", 0),
        queueEndS: readNumber(queueRecordRecord, "queue_end_s", 0),
        reason: readString(queueRecordRecord, "reason", "queue"),
        renderDiagnostics: diagnostics,
      },
    ];
  });

  const liveVehicles = readArray(snapshot, "vehicles").flatMap((vehicle, index) => {
    const vehicleRecord = isRecord(vehicle) ? vehicle : null;
    if (vehicleRecord === null) {
      return [];
    }

    const vehicleId = readNumber(vehicleRecord, "vehicle_id", index + 1);
    const inspection = inspectionsByVehicleId.get(vehicleId) ?? null;
    const snapshotPosition = readPoint(vehicleRecord.position);
    const exactPosition = inspection?.exactPosition ?? null;
    const canonicalNodePosition =
      inspection?.currentNodeId !== null && inspection?.currentNodeId !== undefined
        ? nodePositionsById.get(inspection.currentNodeId) ?? null
        : null;
    const position = exactPosition ?? snapshotPosition ?? canonicalNodePosition;
    const positionSource: LiveVehicleViewModel["positionSource"] =
      exactPosition !== null
        ? "inspection_exact_position"
        : snapshotPosition !== null
          ? "snapshot_position"
          : canonicalNodePosition !== null
            ? "canonical_node_position"
            : "unavailable";

    if (position === null) {
      renderDiagnostics.push(`Vehicle ${vehicleId} could not resolve a runtime position.`);
      return [];
    }

    const state = inspection?.operationalState ?? readString(vehicleRecord, "operational_state", "unknown");

    return [
      {
        vehicleId,
        position,
        state,
        stateClass: vehicleStateClass(state),
        positionSource,
      },
    ];
  });

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

  const operatorVehicles = readArray(operatorState, "vehicles").flatMap((entry, index) => {
    const operatorVehicle = isRecord(entry) ? entry : null;
    if (operatorVehicle === null) {
      return [];
    }

    return [
      {
        vehicleId: readNumber(operatorVehicle, "vehicle_id", index + 1),
        currentNodeId: readNumber(operatorVehicle, "current_node_id", -1),
        motionAuthority: readString(
          operatorVehicle,
          "motion_authority",
          readString(sessionControl, "motion_authority", "python"),
        ),
        routeStatus: readStringOrNull(operatorVehicle, "route_status"),
        routeProgress: readNumberOrNull(operatorVehicle, "route_progress"),
        currentTargetNodeId: readNumberOrNull(operatorVehicle, "current_target_node_id"),
        currentWaypointIndex: readNumberOrNull(operatorVehicle, "current_waypoint_index"),
        routeDestinationNodeId: readNumberOrNull(operatorVehicle, "route_destination_node_id"),
        routeCompleted: readBooleanOrNull(operatorVehicle, "route_completed"),
        embodimentState: readStringOrNull(operatorVehicle, "embodiment_state"),
        blockageReason: readStringOrNull(operatorVehicle, "blockage_reason"),
        blockageEdgeId: readNumberOrNull(operatorVehicle, "blockage_edge_id"),
        blockageNodeId: readNumberOrNull(operatorVehicle, "blockage_node_id"),
        exceptionCode: readStringOrNull(operatorVehicle, "exception_code"),
      },
    ];
  });
  const blockedVehicleIds = readNumberArray(operatorState, "blocked_vehicle_ids");
  const operatorMotionAuthority = readString(
    operatorState,
    "motion_authority",
    readString(sessionControl, "motion_authority", "python"),
  );

  const blockedEdgeIds = readNumberArray(snapshot, "blocked_edge_ids");
  const congestedRoadCount = trafficRoadStates.filter((roadState) => readNumber(roadState, "congestion_intensity", 0) > 0.2).length;
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + readNumberList(roadState, "queued_vehicle_ids").length,
    0,
  );
  const alerts = [
    ...(blockedEdgeIds.length > 0 ? [`${blockedEdgeIds.length} blocked edge(s)`] : []),
    ...(congestedRoadCount > 0 ? [`${congestedRoadCount} congested road(s)`] : []),
    ...(queuedVehicleCount > 0 ? [`${queuedVehicleCount} queued vehicle(s)`] : []),
    ...(trafficQueueRecords.length > 0 ? [`${trafficQueueRecords.length} queue record(s)`] : []),
    ...(anomalies.length > 0 ? [`${anomalies.length} anomaly signal(s)`] : []),
  ];

  return {
    bundleUrl: resource.bundleUrl,
    loadState: resource.loadState,
    loadMessage: resource.loadMessage,
    selectedVehicleIds,
    alerts,
    sessionIdentity: {
      key: buildSessionIdentityKey({
        scenarioPath: readString(authoring, "source_scenario_path", "unknown scenario"),
        surfaceName: readString(metadata, "surface_name", "live_session_bundle"),
        apiVersion: numberToString(readNumber(metadata, "api_version", Number.NaN), "unknown"),
        seed: numberToString(readNumber(bundle, "seed", Number.NaN), "pending"),
        sessionControlEndpoint: readString(sessionControl, "session_control_endpoint", "unknown"),
        commandEndpoint: readString(sessionControl, "command_endpoint", "unknown"),
        previewEndpoint: readString(sessionControl, "route_preview_endpoint", "unknown"),
      }),
      scenarioPath: readString(authoring, "source_scenario_path", "unknown scenario"),
      scenarioName: readString(authoring, "source_scenario_path", "unknown scenario")
        .split("/")
        .pop()
        ?.replace(/\.json$/u, "") ?? "live session",
      surfaceName: readString(metadata, "surface_name", "live_session_bundle"),
      apiVersion: numberToString(readNumber(metadata, "api_version", Number.NaN), "unknown"),
      motionAuthority: readString(sessionControl, "motion_authority", "python"),
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
      intersections,
      areas,
      vehicles: liveVehicles,
      blockedEdgeIds,
      environment: {
        family: readString(worldEnvironment, "family", "unknown"),
        archetypeId: readString(worldEnvironment, "archetype_id", "unknown"),
        displayName: readString(worldEnvironment, "display_name", "unknown environment"),
      },
      sceneFrame,
      bounds: padBounds(sceneFrame.sceneBounds, 2),
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
      queueRecords: trafficQueueRecords,
      controlPoints: trafficControlPoints,
    },
    analysis: {
      anomalySignals,
    },
    operatorState: {
      motionAuthority: operatorMotionAuthority,
      vehicleCount: readNumber(operatorState, "vehicle_count", operatorVehicles.length),
      blockedVehicleIds,
      vehicles: operatorVehicles,
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
      renderDiagnostics,
    },
  };
}

function buildSessionIdentityKey(input: {
  scenarioPath: string;
  surfaceName: string;
  apiVersion: string;
  seed: string;
  sessionControlEndpoint: string;
  commandEndpoint: string;
  previewEndpoint: string;
}): string {
  return [
    input.scenarioPath,
    input.surfaceName,
    input.apiVersion,
    input.seed,
    input.sessionControlEndpoint,
    input.commandEndpoint,
    input.previewEndpoint,
  ].join("|");
}

function resolveRoutePreviewGeometry(
  nodePositionsById: Map<number, Point2>,
  vehicleId: number,
  destinationNodeId: number,
  nodeIds: number[],
): {
  pathPoints: Point2[];
  destinationPoint: Point2 | null;
  renderDiagnostics: string[];
} {
  const diagnostics: string[] = [];
  const pathPoints: Point2[] = [];

  for (const nodeId of nodeIds) {
    const position = nodePositionsById.get(nodeId) ?? null;
    if (position === null) {
      diagnostics.push(`Route preview for vehicle ${vehicleId} could not resolve node ${nodeId}.`);
      continue;
    }
    pathPoints.push(position);
  }

  const destinationPoint = nodePositionsById.get(destinationNodeId) ?? null;
  if (destinationNodeId >= 0 && destinationPoint === null) {
    diagnostics.push(`Route preview for vehicle ${vehicleId} could not resolve destination node ${destinationNodeId}.`);
  }
  if (nodeIds.length === 0) {
    diagnostics.push(`Route preview for vehicle ${vehicleId} did not include any route nodes.`);
  }

  return {
    pathPoints,
    destinationPoint,
    renderDiagnostics: diagnostics,
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

function readBooleanOrNull(value: JsonRecord | null | undefined, key: string): boolean | null {
  if (value === null || value === undefined) {
    return null;
  }
  const nested = value[key];
  return typeof nested === "boolean" ? nested : null;
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

function classifyAreaCategory(kind: string): string {
  const normalized = kind.trim().toLowerCase();
  if (
    [
      "building",
      "maintenance_building",
      "office",
      "warehouse",
      "crusher",
      "gatehouse",
      "wall",
      "barrier",
    ].includes(normalized)
  ) {
    return "structure";
  }
  if (
    [
      "berm",
      "stockpile",
      "hill",
      "mountain",
      "pit",
      "trench",
      "embankment",
      "cut",
      "basin",
      "retaining_wall",
    ].includes(normalized)
  ) {
    return "terrain";
  }
  if (["sidewalk", "walkway", "pedestrian_route", "sidewalk_zone"].includes(normalized)) {
    return "surface";
  }
  if (["site_boundary", "boundary", "perimeter", "boundary_surface"].includes(normalized)) {
    return "boundary";
  }
  if (["no_go", "no_go_area", "no_go_zone", "hazard_zone", "blast_zone", "hazard_exclusion"].includes(normalized)) {
    return "hazard";
  }
  return "zone";
}

function readAreaFormType(
  value: string | null,
  kind: string,
): "flat" | "raised" | "recessed" | "structure_mass" {
  if (value === "raised" || value === "recessed" || value === "structure_mass") {
    return value;
  }
  return defaultAreaFormType(kind);
}

function defaultAreaFormType(kind: string): "flat" | "raised" | "recessed" | "structure_mass" {
  const normalized = kind.trim().toLowerCase();
  if (["building", "maintenance_building", "office", "warehouse", "crusher", "gatehouse", "wall", "barrier"].includes(normalized)) {
    return "structure_mass";
  }
  if (["berm", "stockpile", "hill", "mountain", "embankment", "retaining_wall"].includes(normalized)) {
    return "raised";
  }
  if (["pit", "trench", "cut", "basin"].includes(normalized)) {
    return "recessed";
  }
  return "flat";
}

function defaultAreaHeightHint(kind: string): number {
  const normalized = kind.trim().toLowerCase();
  if (
    ["building", "maintenance_building", "office", "warehouse", "crusher", "gatehouse", "wall", "barrier"].includes(normalized)
  ) {
    return normalized === "crusher" || normalized === "warehouse" || normalized === "maintenance_building" || normalized === "office"
      ? 1.8
      : 1.55;
  }
  if (
    ["berm", "stockpile", "hill", "mountain", "pit", "trench", "embankment", "cut", "basin", "retaining_wall"].includes(normalized)
  ) {
    return ["pit", "trench", "cut", "basin"].includes(normalized) ? 1.35 : 0.95;
  }
  if (["site_boundary", "boundary", "perimeter", "boundary_surface"].includes(normalized)) {
    return 0.28;
  }
  if (["sidewalk", "walkway", "pedestrian_route", "sidewalk_zone"].includes(normalized)) {
    return 0.12;
  }
  if (["no_go", "no_go_area", "no_go_zone", "hazard_zone", "blast_zone", "hazard_exclusion"].includes(normalized)) {
    return 0.16;
  }
  return 0.18;
}

function defaultAreaDepthHint(kind: string): number {
  const normalized = kind.trim().toLowerCase();
  if (
    ["building", "maintenance_building", "office", "warehouse", "crusher", "gatehouse", "wall", "barrier"].includes(normalized)
  ) {
    return normalized === "crusher" || normalized === "warehouse" || normalized === "maintenance_building" || normalized === "office"
      ? 1.02
      : 0.84;
  }
  if (
    ["berm", "stockpile", "hill", "mountain", "pit", "trench", "embankment", "cut", "basin", "retaining_wall"].includes(normalized)
  ) {
    return ["pit", "trench", "cut", "basin"].includes(normalized) ? 1.08 : 0.82;
  }
  if (["site_boundary", "boundary", "perimeter", "boundary_surface"].includes(normalized)) {
    return 0.18;
  }
  if (["sidewalk", "walkway", "pedestrian_route", "sidewalk_zone"].includes(normalized)) {
    return 0.08;
  }
  if (["no_go", "no_go_area", "no_go_zone", "hazard_zone", "blast_zone", "hazard_exclusion"].includes(normalized)) {
    return 0.12;
  }
  return 0.12;
}

function collectScenePoints(bundle: JsonRecord | null): Point2[] {
  const points: Point2[] = [];
  const mapSurface = readRecord(bundle, "map_surface");
  const renderGeometry = readRecord(bundle, "render_geometry");

  for (const node of readArray(mapSurface, "nodes")) {
    if (!isRecord(node)) {
      continue;
    }
    const position = readPoint(node.position);
    if (position !== null) {
      points.push(position);
    }
  }

  for (const road of readArray(renderGeometry, "roads")) {
    if (!isRecord(road)) {
      continue;
    }
    points.push(...readPointList(readArray(road, "centerline")));
  }

  for (const intersection of readArray(renderGeometry, "intersections")) {
    if (!isRecord(intersection)) {
      continue;
    }
    points.push(...readPointList(readArray(intersection, "polygon")));
  }

  for (const area of readArray(renderGeometry, "areas")) {
    if (!isRecord(area)) {
      continue;
    }
    points.push(...readPointList(readArray(area, "polygon")));
  }

  return points.length > 0 ? points : [[-10, -6], [10, 6]];
}

function resolveSceneFrame(
  renderGeometry: JsonRecord | null,
  bundle: JsonRecord | null,
): LiveBundleViewModel["map"]["sceneFrame"] {
  const sceneFrameRecord = readRecord(renderGeometry, "scene_frame");
  if (sceneFrameRecord !== null) {
    return {
      frameId: readString(sceneFrameRecord, "frame_id", "scene-frame"),
      environmentFamily: readString(sceneFrameRecord, "environment_family", "unknown"),
      sceneBounds: readSceneBounds(sceneFrameRecord.scene_bounds),
      extents: readArray(sceneFrameRecord, "extents").flatMap((extent, index) => {
        const extentRecord = isRecord(extent) ? extent : null;
        if (extentRecord === null) {
          return [];
        }
        return [
          {
            extentId: readString(extentRecord, "extent_id", `extent-${index + 1}`),
            source: readString(extentRecord, "source", "render_geometry"),
            category: readString(extentRecord, "category", "operational"),
            label: readString(extentRecord, "label", "Scene extent"),
            featureIds: readStringList(extentRecord, "feature_ids"),
            bounds: readSceneBounds(extentRecord.bounds),
          },
        ];
      }),
    };
  }

  const points = collectScenePoints(bundle);
  const fallback = padBounds(computeBounds(points), 2);
  return {
    frameId: "scene-frame",
    environmentFamily: readString(readRecord(readRecord(renderGeometry, "world_model"), "environment"), "family", "unknown"),
    sceneBounds: {
      minX: fallback.minX,
      minY: fallback.minY,
      maxX: fallback.maxX,
      maxY: fallback.maxY,
      width: fallback.width,
      height: fallback.height,
    },
    extents: [],
  };
}

function readSceneBounds(boundsRecord: unknown): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
} {
  const record = isRecord(boundsRecord) ? boundsRecord : null;
  return {
    minX: readNumber(record, "min_x", 0),
    minY: readNumber(record, "min_y", 0),
    maxX: readNumber(record, "max_x", 0),
    maxY: readNumber(record, "max_y", 0),
    width: Math.max(readNumber(record, "width", 1), 1),
    height: Math.max(readNumber(record, "height", 1), 1),
  };
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
