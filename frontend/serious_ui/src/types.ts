export type Position3 = [number, number, number];
export type JsonRecord = Record<string, unknown>;

export type ViewportState = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type LayerState = {
  areas: boolean;
  roads: boolean;
  intersections: boolean;
  vehicles: boolean;
  routes: boolean;
  reservations: boolean;
  hazards: boolean;
};

export type BundleSummaryPayload = {
  completed_job_count?: number;
  completed_task_count?: number;
  trace_event_count?: number;
} | null;

export type DiagnosticPayload = {
  code?: string;
  severity?: string;
  message?: string;
};

export type AIAssistPayload = {
  explanations?: ExplanationPayload[];
  suggestions?: SuggestionPayload[];
  anomalies?: AnomalyPayload[];
};

export type ExplanationPayload = {
  vehicle_id?: number;
  summary?: string;
};

export type SuggestionPayload = {
  suggestion_id?: string;
  kind?: string;
  priority?: string;
  summary?: string;
  target_vehicle_id?: number | null;
  target_edge_id?: number | null;
};

export type AnomalyPayload = {
  anomaly_id?: string;
  severity?: string;
  summary?: string;
  vehicle_id?: number | null;
};

export type RecentCommandPayload = {
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

export type RoutePreviewPayload = {
  vehicle_id?: number;
  destination_node_id?: number;
  start_node_id?: number;
  is_actionable?: boolean;
  reason?: string | null;
  total_distance?: number | null;
  node_ids?: number[];
  edge_ids?: number[];
};

export type VehicleInspectionPayload = {
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

export type CommandCenterPayload = {
  selected_vehicle_ids?: number[];
  recent_commands?: RecentCommandPayload[];
  route_previews?: RoutePreviewPayload[];
  vehicle_inspections?: VehicleInspectionPayload[];
  ai_assist?: AIAssistPayload;
  session_control?: SessionControlPayload;
};

export type RoadPayload = {
  road_id?: string;
  edge_ids?: number[];
  centerline?: Position3[];
  road_class?: string;
  directionality?: string;
  lane_count?: number;
  width_m?: number;
};

export type IntersectionPayload = {
  intersection_id?: string;
  node_id?: number;
  polygon?: Position3[];
  intersection_type?: string;
};

export type AreaPayload = {
  area_id?: string;
  kind?: string;
  polygon?: Position3[];
  label?: string | null;
};

export type LanePayload = {
  lane_id?: string;
  road_id?: string;
  lane_index?: number;
  directionality?: string;
  lane_role?: string;
  centerline?: Position3[];
  width_m?: number;
};

export type TurnConnectorPayload = {
  connector_id?: string;
  from_lane_id?: string;
  to_lane_id?: string;
  connector_type?: string;
  centerline?: Position3[];
};

export type StopLinePayload = {
  stop_line_id?: string;
  lane_id?: string;
  control_kind?: string;
  segment?: Position3[];
};

export type MergeZonePayload = {
  merge_zone_id?: string;
  lane_ids?: string[];
  kind?: string;
  polygon?: Position3[];
};

export type RenderGeometryPayload = {
  roads?: RoadPayload[];
  intersections?: IntersectionPayload[];
  areas?: AreaPayload[];
  lanes?: LanePayload[];
  turn_connectors?: TurnConnectorPayload[];
  stop_lines?: StopLinePayload[];
  merge_zones?: MergeZonePayload[];
};

export type NodePayload = {
  node_id?: number;
  position?: Position3;
  node_type?: string;
};

export type EdgePayload = {
  edge_id?: number;
  start_node_id?: number;
  end_node_id?: number;
  distance?: number;
  speed_limit?: number;
};

export type MapSurfacePayload = {
  nodes?: NodePayload[];
  edges?: EdgePayload[];
};

export type VehicleSnapshotPayload = {
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

export type MotionSegmentPayload = {
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

export type TrafficControlPointPayload = {
  control_id?: string;
  node_id?: number;
  control_type?: string;
  controlled_road_ids?: string[];
  stop_line_ids?: string[];
  protected_conflict_zone_ids?: string[];
  signal_ready?: boolean;
};

export type TrafficRoadStatePayload = {
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

export type TrafficSnapshotPayload = {
  timestamp_s?: number;
  road_states?: TrafficRoadStatePayload[];
};

export type TrafficBaselinePayload = {
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

export type AuthoringPayload = {
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

export type SessionControlPayload = {
  play_state?: "paused" | "playing" | string;
  step_seconds?: number;
  route_preview_endpoint?: string;
  command_endpoint?: string;
  session_control_endpoint?: string;
};

export type BundlePayload = {
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

export type BootstrapSummary = {
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

export type SelectedTarget =
  | { kind: "vehicle"; vehicleId: number }
  | { kind: "road"; roadId: string }
  | { kind: "area"; areaId: string }
  | { kind: "queue"; roadId: string }
  | { kind: "hazard"; edgeId: number };

export type RouteDestinationMarker = {
  destinationNodeId: number;
  position: Position3;
  selected: boolean;
  previewVehicleId?: number;
};

export type HoverTarget = {
  label: string;
  detail: string;
};

export type Bounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

export type ValidationMessage = {
  severity?: string;
  code?: string;
  message?: string;
  target_kind?: string | null;
  target_id?: string | number | null;
};

export type MoveNodeEditOperation = {
  kind: "move_node";
  target_id: number;
  position: Position3;
};

export type RoadEditOperation = {
  kind: "set_road_centerline";
  target_id: string;
  points: Position3[];
};

export type AreaEditOperation = {
  kind: "set_area_polygon";
  target_id: string;
  points: Position3[];
};

export type EditOperation = MoveNodeEditOperation | RoadEditOperation | AreaEditOperation;

export type EditTransaction = {
  label: string;
  operations: EditOperation[];
};

export type LiveCommandDraft = {
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

export type DragState =
  | { kind: "node"; nodeId: number; z: number }
  | { kind: "road-point"; roadId: string; pointIndex: number; z: number }
  | { kind: "area-point"; areaId: string; pointIndex: number; z: number };

export type WorkspaceTab = "operate" | "traffic" | "fleet" | "editor" | "analyze";
