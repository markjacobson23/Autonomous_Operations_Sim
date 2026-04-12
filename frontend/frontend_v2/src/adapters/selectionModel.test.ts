import { describe, expect, it } from "vitest";

import { buildLiveBundleViewModel, type JsonRecord, type LiveBundleResource } from "./liveBundle";
import { buildSelectionPresentation, focusPointsForSelection } from "./selectionModel";
import type { FrontendUiState } from "../state/frontendUiState";

function makeResource(bundle: JsonRecord): LiveBundleResource {
  return {
    bundleUrl: "/live_session_bundle.json",
    loadState: "ready",
    loadMessage: "connected",
    bundle,
    refresh: () => undefined,
  };
}

function makeBundle(): JsonRecord {
  return {
    authoring: {
      source_scenario_path: "scenarios/world_model_samples/02_construction_yard_world.json",
    },
    metadata: {
      surface_name: "live_session_bundle",
      api_version: 2,
    },
    session_control: {
      play_state: "paused",
      step_seconds: 0.5,
      session_control_endpoint: "/api/live/session/control",
      command_endpoint: "/api/live/command",
      route_preview_endpoint: "/api/live/preview",
    },
    command_center: {
      ai_assist: {
        anomalies: [],
      },
      selected_vehicle_ids: [],
      route_previews: [],
      vehicle_inspections: [],
    },
    snapshot: {
      blocked_edge_ids: [],
      vehicles: [],
    },
    map_surface: {
      nodes: [
        { node_id: 1, position: [0, 0, 0], node_type: "DEPOT" },
        { node_id: 2, position: [4, 0, 0], node_type: "INTERSECTION" },
        { node_id: 3, position: [8, 0, 0], node_type: "LOADING_ZONE" },
      ],
      edges: [
        { edge_id: 11, start_node_id: 1, end_node_id: 2, distance: 4, speed_limit: 3 },
        { edge_id: 12, start_node_id: 2, end_node_id: 3, distance: 4, speed_limit: 3 },
      ],
    },
    render_geometry: {
      world_model: {
        environment: {
          family: "construction_yard",
          archetype_id: "construction_staging_yard",
          display_name: "Construction Yard",
        },
      },
      scene_frame: {
        frame_id: "scene-frame",
        environment_family: "construction_yard",
        scene_bounds: {
          min_x: -1.4,
          min_y: -2,
          max_x: 10.4,
          max_y: 4.2,
          width: 11.8,
          height: 6.2,
        },
        extents: [
          {
            extent_id: "scene:operational",
            source: "render_geometry",
            category: "operational",
            label: "Operational Geometry",
            feature_ids: ["yard-entry"],
            bounds: {
              min_x: 0,
              min_y: 0,
              max_x: 8,
              max_y: 3.5,
              width: 8,
              height: 3.5,
            },
          },
        ],
      },
      roads: [
        {
          road_id: "yard-entry",
          centerline: [
            [0, 0, 0],
            [4, 0, 0],
          ],
          edge_ids: [11, 12],
          road_class: "site_access",
          directionality: "two_way",
          lane_count: 2,
        },
      ],
      intersections: [
        {
          intersection_id: "staging-hub",
          node_id: 2,
          polygon: [
            [3.2, -0.8, 0],
            [4.8, -0.8, 0],
            [4.8, 0.8, 0],
            [3.2, 0.8, 0],
          ],
          intersection_type: "staging_junction",
        },
      ],
      areas: [
        {
          area_id: "staging-zone",
          category: "zone",
          kind: "staging_zone",
          group_id: "zone:zones",
          polygon: [
            [-0.8, -1.5, 0],
            [2.5, -1.5, 0],
            [2.5, 1.5, 0],
            [-0.8, 1.5, 0],
          ],
          label: "Staging",
        },
        {
          area_id: "site-office",
          category: "structure",
          kind: "office",
          group_id: "structure:buildings",
          polygon: [
            [1.4, 2, 0],
            [3.6, 2, 0],
            [3.6, 3.6, 0],
            [1.4, 3.6, 0],
          ],
          label: "Site Office",
        },
      ],
      lanes: [],
      merge_zones: [],
      stop_lines: [],
      turn_connectors: [],
    },
    traffic_baseline: {
      control_points: [],
      queue_records: [],
    },
    traffic_snapshot: {
      road_states: [],
      timestamp_s: 10,
    },
    simulated_time_s: 10,
    seed: 42,
  };
}

const baseUiState: FrontendUiState = {
  camera: { x: 0, y: 0, zoom: 1, sceneViewMode: "iso" },
  layers: {
    roads: true,
    vehicles: true,
    areas: true,
    labels: false,
    routes: true,
    hazards: false,
    reservations: false,
    intersections: false,
  },
  selection: { target: null, vehicleIds: [], hoveredTarget: null },
  popup: { open: false, targetLabel: null },
  inspector: { pinned: false, section: "summary" },
  planning: { draftStatus: "idle", draftLabel: null },
  modePanel: { activeMode: "operate" },
  editorGesture: { dragKind: "none", activeHandleId: null },
};

describe("selection model world feature alignment", () => {
  it("describes intersections as control-relevant scene features", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeBundle()));
    const presentation = buildSelectionPresentation(bundle, {
      ...baseUiState,
      selection: { ...baseUiState.selection, target: { kind: "intersection", intersectionId: "staging-hub" } },
    });

    expect(presentation).not.toBeNull();
    expect(presentation?.badge).toBe("staging junction");
    expect(presentation?.summary).toContain("junction");
    expect(presentation?.context).toContain("Construction Yard");
    expect(presentation?.details.map((detail) => detail.label)).toEqual(["Identity", "Role", "Feature", "Vertices"]);
    expect(presentation?.focusPoints).toHaveLength(4);
  });

  it("describes world-form areas using semantic categories instead of raw kinds", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeBundle()));
    const presentation = buildSelectionPresentation(bundle, {
      ...baseUiState,
      selection: { ...baseUiState.selection, target: { kind: "area", areaId: "site-office" } },
    });

    expect(presentation).not.toBeNull();
    expect(presentation?.badge).toBe("structure");
    expect(presentation?.summary).toContain("Built mass");
    expect(presentation?.context).toContain("structure surface");
    expect(presentation?.details.map((detail) => detail.label)).toContain("Group");
    expect(focusPointsForSelection(bundle, { kind: "area", areaId: "site-office" })).toHaveLength(4);
  });

  it.each([
    ["mine", "Mine Depot", "mine_depot"],
    ["construction_yard", "Construction Yard", "construction_staging_yard"],
    ["city_street", "City Street", "urban_delivery_corridor"],
  ])("stays aligned across %s scenes", (family, displayName, archetypeId) => {
    const bundleData = makeBundle();
    const renderGeometry = bundleData.render_geometry as any;
    renderGeometry.world_model.environment.family = family;
    renderGeometry.world_model.environment.display_name = displayName;
    renderGeometry.world_model.environment.archetype_id = archetypeId;
    const bundle = buildLiveBundleViewModel(makeResource(bundleData));

    const areaPresentation = buildSelectionPresentation(bundle, {
      ...baseUiState,
      selection: { ...baseUiState.selection, target: { kind: "area", areaId: "site-office" } },
    });
    const intersectionPresentation = buildSelectionPresentation(bundle, {
      ...baseUiState,
      selection: { ...baseUiState.selection, target: { kind: "intersection", intersectionId: "staging-hub" } },
    });

    expect(areaPresentation?.context).toContain(displayName);
    expect(areaPresentation?.summary).toContain("Built mass");
    expect(intersectionPresentation?.context).toContain(displayName);
    expect(intersectionPresentation?.summary).toContain("junction");
  });
});
