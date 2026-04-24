import { describe, expect, it } from "vitest";

import { buildLiveBundleViewModel, type JsonRecord, type LiveBundleResource } from "./liveBundle";

function makeResource(bundle: JsonRecord): LiveBundleResource {
  return {
    bundleUrl: "/live_session_bundle.json",
    loadState: "ready",
    loadMessage: "connected",
    bundle,
    refresh: () => undefined,
  };
}

function makeBaseBundle(): any {
  return {
    authoring: {
      source_scenario_path: "scenarios/test_scene.json",
    },
    metadata: {
      surface_name: "live_session_bundle",
      api_version: 2,
    },
    session_control: {
      play_state: "paused",
      step_seconds: 0.5,
      motion_authority: "unity",
      session_control_endpoint: "/api/live/session/control",
      command_endpoint: "/api/live/command",
      route_preview_endpoint: "/api/live/preview",
    },
    command_center: {
      ai_assist: {
        anomalies: [],
      },
      selected_vehicle_ids: [77],
      route_previews: [
        {
          vehicle_id: 77,
          destination_node_id: 3,
          is_actionable: true,
          reason: null,
          reason_code: null,
          node_ids: [1, 2, 3],
          edge_ids: [11, 12],
          total_distance: 14.2,
        },
      ],
      vehicle_inspections: [
        {
          vehicle_id: 77,
          current_node_id: 2,
          exact_position: [1, 2, 0],
          operational_state: "moving",
          current_job_id: null,
          current_task_index: null,
          current_task_type: null,
          assigned_resource_id: null,
          wait_reason: null,
          traffic_control_state: null,
          traffic_control_detail: null,
          eta_s: 3.4,
          route_ahead_node_ids: [2, 3],
          route_ahead_edge_ids: [12],
          recent_commands: [],
          diagnostics: [],
        },
      ],
    },
    snapshot: {
      blocked_edge_ids: [],
      vehicles: [
        {
          vehicle_id: 77,
          node_id: 2,
          position: [200, 200, 0],
          operational_state: "moving",
        },
      ],
    },
    map_surface: {
      nodes: [
        { node_id: 1, position: [0, 0, 0], node_type: "junction" },
        { node_id: 2, position: [10, 0, 0], node_type: "junction" },
        { node_id: 3, position: [10, 10, 0], node_type: "junction" },
      ],
      edges: [
        { edge_id: 11, start_node_id: 1, end_node_id: 2, distance: 10, speed_limit: 12 },
        { edge_id: 12, start_node_id: 2, end_node_id: 3, distance: 10, speed_limit: 12 },
      ],
    },
    render_geometry: {
      world_model: {
        environment: {
          family: "industrial",
          archetype_id: "test-yard",
          display_name: "Test Yard",
        },
      },
      scene_frame: {
        frame_id: "scene-frame",
        environment_family: "industrial",
        scene_bounds: {
          min_x: -2,
          min_y: -2,
          max_x: 12,
          max_y: 12,
          width: 14,
          height: 14,
        },
        extents: [
          {
            extent_id: "scene:operational",
            source: "render_geometry",
            category: "operational",
            label: "Operational Geometry",
            feature_ids: ["road-1"],
            bounds: {
              min_x: 0,
              min_y: 0,
              max_x: 10,
              max_y: 10,
              width: 10,
              height: 10,
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
              min_y: -2,
              max_x: 12,
              max_y: 12,
              width: 14,
              height: 14,
            },
          },
          {
            extent_id: "world:asset_layer:terrain-base",
            source: "world_model",
            category: "asset_layer",
            label: "Mine Gravel",
            feature_ids: ["terrain-base"],
            bounds: {
              min_x: -2,
              min_y: -2,
              max_x: 12,
              max_y: 12,
              width: 14,
              height: 14,
            },
          },
        ],
      },
      roads: [
        {
          road_id: "road-1",
          centerline: [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
          ],
          edge_ids: [11, 12],
          road_class: "connector",
          directionality: "one_way",
          lane_count: 1,
        },
      ],
      areas: [
        {
          area_id: "area-1",
          kind: "yard",
          form_type: "raised",
          height_hint: 0.72,
          depth_hint: 0.48,
          polygon: [
            [-2, -2, 0],
            [12, -2, 0],
            [12, 12, 0],
            [-2, 12, 0],
          ],
        },
      ],
      intersections: [
        {
          intersection_id: "intersection-1",
          node_id: 2,
          polygon: [
            [9, -1, 0],
            [11, -1, 0],
            [11, 1, 0],
            [9, 1, 0],
          ],
          intersection_type: "yard_junction",
        },
      ],
      lanes: [],
      merge_zones: [],
      stop_lines: [],
      turn_connectors: [],
    },
    traffic_baseline: {
      control_points: [
        {
          control_id: "control-1",
          node_id: 2,
          control_type: "signal",
          controlled_road_ids: ["road-1"],
          stop_line_ids: [],
          protected_conflict_zone_ids: [],
          signal_ready: true,
        },
      ],
      queue_records: [
        {
          vehicle_id: 77,
          node_id: 2,
          road_id: "road-1",
          queue_start_s: 1,
          queue_end_s: 3,
          reason: "queue",
        },
      ],
    },
    traffic_snapshot: {
      road_states: [
        {
          road_id: "road-1",
          active_vehicle_ids: [77],
          queued_vehicle_ids: [77],
          occupancy_count: 1,
          min_spacing_m: 2,
          congestion_intensity: 0.4,
          congestion_level: "busy",
          control_state: "yield",
          stop_line_ids: [],
          protected_conflict_zone_ids: [],
        },
      ],
      timestamp_s: 10,
    },
    operator_state: {
      motion_authority: "unity",
      vehicle_count: 1,
      blocked_vehicle_ids: [77],
      vehicles: [
        {
          vehicle_id: 77,
          current_node_id: 2,
          motion_authority: "unity",
          route_status: "blocked",
          route_progress: 0.5,
          current_target_node_id: 3,
          current_waypoint_index: 1,
          route_destination_node_id: 3,
          route_completed: false,
          embodiment_state: "blocked",
          blockage_reason: "blocked_edge",
          blockage_edge_id: 12,
          blockage_node_id: 3,
          exception_code: "movement_blocked",
          latest_route_progress: {
            route_status: "blocked",
          },
          latest_embodiment_status: {
            embodiment_state: "blocked",
          },
          latest_telemetry: {
            vehicle_id: 77,
          },
        },
      ],
    },
    simulated_time_s: 10,
    seed: 42,
  };
}

describe("live bundle adapter contracts", () => {
  it("prefers inspection runtime position and ignores moving vehicles for map bounds", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeBaseBundle()));

    expect(bundle.map.vehicles).toHaveLength(1);
    expect(bundle.map.vehicles[0]?.position).toEqual([1, 2]);
    expect(bundle.map.vehicles[0]?.positionSource).toBe("inspection_exact_position");
    expect(bundle.map.intersections).toHaveLength(1);
    expect(bundle.map.intersections[0]?.intersectionType).toBe("yard_junction");
    expect(bundle.map.areas[0]?.category).toBe("zone");
    expect(bundle.map.areas[0]?.formType).toBe("raised");
    expect(bundle.map.areas[0]?.heightHint).toBe(0.72);
    expect(bundle.map.areas[0]?.depthHint).toBe(0.48);
    expect(bundle.map.sceneFrame.environmentFamily).toBe("industrial");
    expect(bundle.map.sceneFrame.sceneBounds).toEqual({
      minX: -2,
      minY: -2,
      maxX: 12,
      maxY: 12,
      width: 14,
      height: 14,
    });
    expect(bundle.map.bounds).toEqual({
      minX: -4,
      minY: -4,
      maxX: 14,
      maxY: 14,
      width: 18,
      height: 18,
    });
  });

  it("resolves route preview geometry against canonical map_surface nodes", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeBaseBundle()));
    const preview = bundle.commandCenter.routePreviews[0];

    expect(preview).not.toBeUndefined();
    expect(preview?.pathPoints).toEqual([
      [0, 0],
      [10, 0],
      [10, 10],
    ]);
    expect(preview?.destinationPoint).toEqual([10, 10]);
    expect(preview?.renderDiagnostics).toHaveLength(0);
    expect(bundle.utility.renderDiagnostics).toHaveLength(0);
  });

  it("surfaces diagnostics when preview or traffic references cannot resolve", () => {
    const bundleData = structuredClone(makeBaseBundle());
    bundleData.command_center.route_previews[0].node_ids = [1, 99];
    bundleData.traffic_baseline.control_points[0].node_id = 999;
    bundleData.traffic_baseline.queue_records[0].node_id = 998;

    const bundle = buildLiveBundleViewModel(makeResource(bundleData));
    const preview = bundle.commandCenter.routePreviews[0];

    expect(preview?.pathPoints).toEqual([[0, 0]]);
    expect(preview?.renderDiagnostics.some((entry) => entry.includes("node 99"))).toBe(true);
    expect(bundle.traffic.controlPoints[0]?.renderDiagnostics.some((entry) => entry.includes("node 999"))).toBe(true);
    expect(bundle.traffic.queueRecords[0]?.renderDiagnostics.some((entry) => entry.includes("node 998"))).toBe(true);
    expect(bundle.utility.renderDiagnostics.some((entry) => entry.includes("node 99"))).toBe(true);
    expect(bundle.utility.renderDiagnostics.some((entry) => entry.includes("node 999"))).toBe(true);
  });

  it("keeps the session identity key stable across ordinary polling churn", () => {
    const firstBundle = makeBaseBundle();
    const secondBundle = structuredClone(firstBundle);
    secondBundle.session_control.play_state = "playing";
    secondBundle.simulated_time_s = 18.5;

    const first = buildLiveBundleViewModel(makeResource(firstBundle));
    const second = buildLiveBundleViewModel(makeResource(secondBundle));

    expect(first.sessionIdentity.key).toBe(second.sessionIdentity.key);
  });

  it("surfaces operator-owned unity state alongside the session bundle", () => {
    const bundle = buildLiveBundleViewModel(makeResource(makeBaseBundle()));

    expect(bundle.sessionIdentity.motionAuthority).toBe("unity");
    expect(bundle.operatorState.motionAuthority).toBe("unity");
    expect(bundle.operatorState.blockedVehicleIds).toEqual([77]);
    expect(bundle.operatorState.vehicleCount).toBe(1);
    expect(bundle.operatorState.vehicles[0]).toMatchObject({
      vehicleId: 77,
      currentNodeId: 2,
      routeStatus: "blocked",
      routeProgress: 0.5,
      embodimentState: "blocked",
      blockageReason: "blocked_edge",
      blockageEdgeId: 12,
      blockageNodeId: 3,
      exceptionCode: "movement_blocked",
    });
  });
});
