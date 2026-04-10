import type {
  AreaPayload,
  Bounds,
  BundlePayload,
  DragState,
  EditOperation,
  HoverTarget,
  LayerState,
  MotionSegmentPayload,
  NodePayload,
  EdgePayload,
  Position3,
  RecentCommandPayload,
  RouteDestinationMarker,
  RoutePreviewPayload,
  SelectedTarget,
  TrafficRoadStatePayload,
  TrafficSnapshotPayload,
  VehicleSnapshotPayload,
  ViewportState,
  WorkspaceTab,
} from "./types";

export const architecture = {
  primaryStack: "React + TypeScript + Vite",
  authority: "Python simulator remains authoritative",
  launchMode: "Live session + live authoring through versioned bundle surfaces",
} as const;

export const workspaceTabs: Array<{
  id: WorkspaceTab;
  label: string;
  summary: string;
}> = [
  { id: "operate", label: "Operate", summary: "Operator workflow, routing, and selection" },
  { id: "traffic", label: "Traffic", summary: "Pressure, queues, and closures" },
  { id: "fleet", label: "Fleet", summary: "Selection, batch actions, and control" },
  { id: "editor", label: "Editor", summary: "Scenario authoring and validation" },
  { id: "analyze", label: "Analyze", summary: "Diagnostics, review, and context" },
];

export const sessionActions = ["Launch Live Run", "Reconnect Bundle"];

export const defaultLayers: LayerState = {
  areas: true,
  roads: true,
  intersections: true,
  vehicles: true,
  routes: true,
  reservations: true,
  hazards: true,
};

export type DisplayedVehicle = VehicleSnapshotPayload & {
  heading_rad?: number;
  speed?: number;
};

export function clientPointToScene(
  event: MouseEvent,
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

export function fitViewportToBundle(bundle: BundlePayload | null): ViewportState {
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

export function computeSceneBounds(bundle: BundlePayload | null): Bounds {
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

export function toPointString(points: Position3[] | undefined): string {
  return (points ?? []).map(([x, y]) => `${x},${y}`).join(" ");
}

export function toSmoothPathString(points: Position3[] | undefined, closed = false): string {
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

export function toScaledPointString(points: Position3[] | undefined, bounds: Bounds): string {
  return (points ?? [])
    .map(([x, y]) => `${scaleX(x, bounds)},${scaleY(y, bounds)}`)
    .join(" ");
}

export function scaleX(x: number, bounds: Bounds): number {
  return ((x - bounds.minX) / bounds.width) * 100;
}

export function scaleY(y: number, bounds: Bounds): number {
  return ((y - bounds.minY) / bounds.height) * 100;
}

export function buildRoutePreviewPoints(
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

export function findVehicleById(
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

export function findDisplayedVehicleById(
  vehicles: DisplayedVehicle[],
  vehicleId: number | null,
): DisplayedVehicle | null {
  if (vehicleId === null) {
    return null;
  }
  return vehicles.find((vehicle) => vehicle.vehicle_id === vehicleId) ?? null;
}

export function findEdgeById(edges: EdgePayload[], edgeId: number | null): EdgePayload | null {
  if (edgeId === null) {
    return null;
  }
  return edges.find((edge) => edge.edge_id === edgeId) ?? null;
}

export function findNodePosition(nodes: NodePayload[], nodeId: number | undefined): Position3 | null {
  if (nodeId === undefined) {
    return null;
  }
  return nodes.find((node) => node.node_id === nodeId)?.position ?? null;
}

export function sampleDisplayedVehicles(
  bundle: BundlePayload | null,
  motionClockS: number,
): DisplayedVehicle[] {
  const baseVehicles = new Map<number, DisplayedVehicle>();
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

  const sampledVehicles = new Map<number, DisplayedVehicle>();
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

export function computeMinDisplayedSpacing(vehicles: DisplayedVehicle[]): number | null {
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

export function sampleTrafficSnapshot(
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
      control_state: queuedVehicleIds.length > 0 ? "yield" : "free_flow",
      stop_line_ids: [],
      protected_conflict_zone_ids: [],
    };
  });
  return {
    timestamp_s: motionClockS,
    road_states: roadStates,
  };
}

export function trafficRoadPressureScore(roadState: TrafficRoadStatePayload | null): number {
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

export function vehiclePresentationBadge(vehicle: VehicleSnapshotPayload): string {
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

export function renderVehicleEnvelope(
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

export function renderVehicleGlyph(
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

export function describeSelectedTarget(
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
  return "no target selected";
}

export function describeSelectedBadge(selectedTarget: SelectedTarget): string {
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

export function normalizeReviewLevel(value: string | undefined, fallback = "info"): string {
  return (value ?? fallback).trim().toLowerCase().replace(/\s+/g, "-");
}

export function reviewSeverityRank(value: string | undefined): number {
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

export function reviewPriorityRank(value: string | undefined): number {
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

export function describeEdgeTargetLabel(edgeId: number | undefined, roads: { edge_ids?: number[]; road_id?: string }[]): string | null {
  if (edgeId === undefined) {
    return null;
  }
  const road = roads.find((entry) => (entry.edge_ids ?? []).includes(edgeId));
  if (road?.road_id) {
    return `Edge ${edgeId} · Road ${road.road_id}`;
  }
  return `Edge ${edgeId}`;
}

export function describeOperation(operation: EditOperation): string {
  if (operation.kind === "move_node") {
    return `move node ${operation.target_id} to ${operation.position.join(", ")}`;
  }
  if (operation.kind === "set_road_centerline") {
    return `edit road ${operation.target_id} with ${operation.points.length} centerline point(s)`;
  }
  return `edit zone ${operation.target_id} with ${operation.points.length} polygon vertex/vertices`;
}

export function describeRecentCommand(command: RecentCommandPayload): string {
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

export function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function pointsEqual(left: Position3 | undefined, right: Position3): boolean {
  return (
    Array.isArray(left) &&
    left[0] === right[0] &&
    left[1] === right[1] &&
    left[2] === right[2]
  );
}

export function roundPointValue(value: number): number {
  return Math.round(value * 1000) / 1000;
}

export function formatMaybeNumber(value: number | null): string {
  return value === null ? "pending" : String(value);
}

export function formatSeconds(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(1)}s`;
}

export function formatMeters(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(2)}m`;
}

export function formatSpeedPerSecond(value: number | null): string {
  return value === null ? "pending" : `${value.toFixed(2)}m/s`;
}

export function formatHeadingDegrees(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "unknown";
  }
  const normalized = ((radiansToDegrees(value) % 360) + 360) % 360;
  return `${Math.round(normalized)} deg`;
}

export function maxMotionTime(bundle: BundlePayload | null): number {
  return Math.max(
    0,
    ...((bundle?.motion_segments ?? []).map((segment) => segment.end_time_s ?? 0)),
  );
}

export function radiansToDegrees(value: number): number {
  return (value * 180) / Math.PI;
}

function renderVehicleHeading(length: number, width: number): JSX.Element {
  return (
    <g className="vehicle-heading-group">
      <line x1={-length * 0.12} y1={0} x2={length * 0.3} y2={0} className="vehicle-heading" />
      <path
        d={`M ${length * 0.24} ${-width * 0.16} L ${length * 0.52} 0 L ${length * 0.24} ${width * 0.16} Z`}
        className="vehicle-heading"
      />
    </g>
  );
}

function renderWheelPair(frontX: number, rearX: number, y: number, radius: number): JSX.Element[] {
  return [
    <circle key={`rear-${rearX}`} cx={rearX} cy={y} r={radius} className="vehicle-wheel" />,
    <circle key={`front-${frontX}`} cx={frontX} cy={y} r={radius} className="vehicle-wheel" />,
  ];
}

export function spacingEnvelopeFromVehicle(
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

function sampleMotionSegmentPayload(
  segment: MotionSegmentPayload,
  timestampS: number,
): { position: Position3; headingRad: number; speed: number; progress: number } {
  const startTimeS = segment.start_time_s ?? 0;
  const endTimeS = segment.end_time_s ?? startTimeS;
  const durationS = Math.max((segment.duration_s ?? endTimeS - startTimeS), 0.0001);
  const boundedTimestampS = Math.min(Math.max(timestampS, startTimeS), endTimeS);
  const progress = Math.min(1, Math.max(0, (boundedTimestampS - startTimeS) / durationS));
  const pathPoints =
    (segment.path_points?.length ?? 0) >= 2
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
