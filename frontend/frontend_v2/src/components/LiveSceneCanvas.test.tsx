import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { buildLiveBundleViewModel, type JsonRecord, type LiveBundleResource } from "../adapters/liveBundle";
import { LiveSceneCanvas } from "./LiveSceneCanvas";

function makeResource(bundle: JsonRecord): LiveBundleResource {
  return {
    bundleUrl: "/live_session_bundle.json",
    loadState: "ready",
    loadMessage: "connected",
    bundle,
    refresh: () => undefined,
  };
}

function makeWorldAwareBundle(): JsonRecord {
  return {
    authoring: {
      source_scenario_path: "scenarios/world_model_samples/01_mine_depot_world.json",
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
        { node_id: 2, position: [5, 0, 0], node_type: "INTERSECTION" },
        { node_id: 3, position: [10, 0, 0], node_type: "LOADING_ZONE" },
      ],
      edges: [
        { edge_id: 11, start_node_id: 1, end_node_id: 2, distance: 5, speed_limit: 4 },
        { edge_id: 12, start_node_id: 2, end_node_id: 3, distance: 5, speed_limit: 4 },
      ],
    },
    render_geometry: {
      world_model: {
        environment: {
          family: "mine",
          archetype_id: "mine_depot",
          display_name: "Mine Depot",
        },
      },
      scene_frame: {
        frame_id: "scene-frame",
        environment_family: "mine",
        scene_bounds: {
          min_x: -2,
          min_y: -5,
          max_x: 12,
          max_y: 2,
          width: 14,
          height: 7,
        },
        extents: [
          {
            extent_id: "scene:operational",
            source: "render_geometry",
            category: "operational",
            label: "Operational Geometry",
            feature_ids: ["mine-spine"],
            bounds: {
              min_x: 0,
              min_y: 0,
              max_x: 10,
              max_y: 0,
              width: 10,
              height: 1,
            },
          },
          {
            extent_id: "world:boundary:boundaries",
            source: "world_model",
            category: "boundary",
            label: "Boundaries",
            feature_ids: ["mine-boundary"],
            bounds: {
              min_x: -2,
              min_y: -5,
              max_x: 12,
              max_y: 2,
              width: 14,
              height: 7,
            },
          },
        ],
      },
      roads: [
        {
          road_id: "mine-spine",
          centerline: [
            [0, 0, 0],
            [5, 0, 0],
            [10, 0, 0],
          ],
          edge_ids: [11, 12],
          road_class: "haul",
          directionality: "two_way",
          lane_count: 2,
        },
      ],
      intersections: [
        {
          intersection_id: "yard-junction",
          node_id: 2,
          polygon: [
            [4.2, -0.8, 0],
            [5.8, -0.8, 0],
            [5.8, 0.8, 0],
            [4.2, 0.8, 0],
          ],
          intersection_type: "yard_junction",
        },
      ],
      areas: [
        {
          area_id: "mine-depot",
          category: "zone",
          kind: "depot",
          group_id: "zone:zones",
          polygon: [
            [-1.2, -1.2, 0],
            [2.2, -1.2, 0],
            [2.2, 1.2, 0],
            [-1.2, 1.2, 0],
          ],
          label: "Depot",
        },
        {
          area_id: "haul-pad",
          category: "terrain",
          kind: "stockpile",
          group_id: "terrain:terrain_forms",
          polygon: [
            [6.8, -4.3, 0],
            [8.8, -4.3, 0],
            [8.8, -2.9, 0],
            [6.8, -2.9, 0],
          ],
          label: "Stockpile",
        },
        {
          area_id: "workshop",
          category: "structure",
          kind: "building",
          group_id: "structure:buildings",
          polygon: [
            [1.0, -3.2, 0],
            [3.8, -3.2, 0],
            [3.8, -1.8, 0],
            [1.0, -1.8, 0],
          ],
          label: "Workshop",
        },
        {
          area_id: "site-boundary",
          category: "boundary",
          kind: "site_boundary",
          group_id: "boundary:boundaries",
          polygon: [
            [-1.6, -5.2, 0],
            [11.8, -5.2, 0],
            [11.8, 2.1, 0],
            [-1.6, 2.1, 0],
          ],
          label: "Boundary",
        },
        {
          area_id: "blast-zone",
          category: "hazard",
          kind: "no_go_zone",
          group_id: "hazard:no_go_areas",
          polygon: [
            [8.5, -4.6, 0],
            [11.4, -4.6, 0],
            [11.4, -2.7, 0],
            [8.5, -2.7, 0],
          ],
          label: "Blast Zone",
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

describe("LiveSceneCanvas", () => {
  it("renders world-aware layers without enabling label clutter", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeWorldAwareBundle()));
    const markup = renderToStaticMarkup(
      <LiveSceneCanvas
        model={bundle}
        viewBox={{ x: -4, y: -6, width: 18, height: 14 }}
        sceneTransform=""
        layers={{
          roads: true,
          vehicles: true,
          areas: true,
          labels: false,
          routes: false,
          hazards: false,
          reservations: false,
          intersections: false,
        }}
        selectionTarget={null}
        selectedVehicleIds={[]}
        activeRoutePreview={null}
        activeMode="operate"
        onSelectVehicle={() => undefined}
        onSelectRoad={() => undefined}
        onSelectIntersection={() => undefined}
        onSelectArea={() => undefined}
      />
    );

    expect(markup).toContain("scene-world-form-backdrop");
    expect(markup).toContain("area-surface-structure");
    expect(markup).toContain("area-surface-terrain");
    expect(markup).toContain("area-surface-boundary");
    expect(markup).toContain("intersection-footprint-yard-junction");
    expect(markup).not.toContain("vehicle-label");
  });
});
