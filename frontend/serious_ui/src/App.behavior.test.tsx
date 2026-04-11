import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";
import type { BundlePayload } from "./types";

const bundleUrl = "/api/live/bundle";

function jsonResponse(payload: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(payload), {
    status: init.status ?? 200,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
}

function buildBundle(overrides: Partial<BundlePayload> = {}): BundlePayload {
  const base: BundlePayload = {
    metadata: { surface_name: "serious-ui-fixture" },
    seed: 42,
    simulated_time_s: 12.5,
    summary: {
      completed_job_count: 1,
      completed_task_count: 2,
      trace_event_count: 4,
    },
    command_center: {
      selected_vehicle_ids: [7],
      recent_commands: [
        {
          command_type: "assign_vehicle_destination",
          vehicle_id: 7,
          destination_node_id: 2,
        },
      ],
      route_previews: [],
      vehicle_inspections: [
        {
          vehicle_id: 7,
          operational_state: "idle",
          current_node_id: 1,
          current_job_id: "job-7",
          wait_reason: "none",
          eta_s: 3.5,
          traffic_control_state: "clear",
          traffic_control_detail: "No control detail",
          route_ahead_node_ids: [1, 2],
          route_ahead_edge_ids: [1],
          diagnostics: [
            {
              severity: "info",
              code: "inspect_ok",
            },
          ],
        },
      ],
      ai_assist: {
        suggestions: [
          {
            suggestion_id: "suggest-1",
            kind: "route",
            priority: "high",
            summary: "Route vehicle 7 through node 2",
            target_vehicle_id: 7,
          },
        ],
        anomalies: [
          {
            anomaly_id: "anom-1",
            severity: "warning",
            summary: "Minor queue pressure at road r-1",
            vehicle_id: 7,
          },
        ],
        explanations: [
          {
            vehicle_id: 7,
            summary: "Vehicle 7 is currently staged at node 1.",
          },
        ],
      },
    },
    map_surface: {
      nodes: [
        { node_id: 1, position: [0, 0, 0] },
        { node_id: 2, position: [10, 0, 0] },
      ],
      edges: [
        {
          edge_id: 1,
          start_node_id: 1,
          end_node_id: 2,
          distance: 10,
        },
      ],
    },
    render_geometry: {
      roads: [
        {
          road_id: "r-1",
          edge_ids: [1],
          centerline: [
            [0, 0, 0],
            [10, 0, 0],
          ],
          road_class: "connector",
          directionality: "forward",
          lane_count: 1,
          width_m: 4,
        },
      ],
      areas: [
        {
          area_id: "yard",
          kind: "yard",
          polygon: [
            [0, 0, 0],
            [5, 0, 0],
            [5, 5, 0],
          ],
          label: "Work Yard",
        },
      ],
    },
    traffic_baseline: {
      queue_records: [
        {
          road_id: "r-1",
          node_id: 1,
          reason: "queued",
          vehicle_ids: [7],
          queue_start_s: 0,
          queue_end_s: 999,
        },
      ],
      control_points: [],
    },
    snapshot: {
      simulated_time_s: 12.5,
      blocked_edge_ids: [1],
      vehicles: [
        {
          vehicle_id: 7,
          node_id: 1,
          position: [0, 0, 0],
          operational_state: "idle",
          vehicle_type: "GENERIC",
          presentation_key: "haul_truck",
          display_name: "Truck 7",
          role_label: "Lead truck",
          body_length_m: 1.2,
          body_width_m: 0.8,
          spacing_envelope_m: 1.8,
        },
      ],
    },
    authoring: {
      mode: "live",
      save_endpoint: "/api/live/authoring/save",
      reload_endpoint: "/api/live/authoring/reload",
      validate_endpoint: "/api/live/authoring/validate",
      source_scenario_path: "scenarios/source.json",
      working_scenario_path: "scenarios/working.json",
      editable_node_count: 1,
      editable_road_count: 1,
      editable_area_count: 1,
    },
    session_control: {
      play_state: "paused",
      step_seconds: 0.5,
      route_preview_endpoint: "/api/live/preview",
      command_endpoint: "/api/live/command",
      session_control_endpoint: "/api/live/session/control",
    },
    motion_segments: [],
  };

  return {
    ...base,
    ...overrides,
    command_center: {
      ...base.command_center,
      ...(overrides.command_center ?? {}),
      ai_assist: {
        ...base.command_center?.ai_assist,
        ...(overrides.command_center?.ai_assist ?? {}),
      },
    },
    map_surface: {
      ...base.map_surface,
      ...(overrides.map_surface ?? {}),
    },
    render_geometry: {
      ...base.render_geometry,
      ...(overrides.render_geometry ?? {}),
    },
    traffic_baseline: {
      ...base.traffic_baseline,
      ...(overrides.traffic_baseline ?? {}),
    },
    snapshot: {
      ...base.snapshot,
      ...(overrides.snapshot ?? {}),
    },
    authoring: {
      ...base.authoring,
      ...(overrides.authoring ?? {}),
    },
    session_control: {
      ...base.session_control,
      ...(overrides.session_control ?? {}),
    },
  };
}

function buildCityStreetBundle(): BundlePayload {
  return buildBundle({
    metadata: { surface_name: "Proof-of-Life City Street" },
    seed: 5201,
    simulated_time_s: 18.5,
    command_center: {
      selected_vehicle_ids: [201, 202],
      recent_commands: [
        {
          command_type: "assign_vehicle_destination",
          vehicle_id: 201,
          destination_node_id: 122,
        },
      ],
      route_previews: [
        {
          vehicle_id: 201,
          destination_node_id: 122,
          start_node_id: 121,
          is_actionable: true,
          reason: "Route is clear",
          total_distance: 12.0,
          node_ids: [121, 122],
          edge_ids: [1028, 1029],
        },
        {
          vehicle_id: 202,
          destination_node_id: 123,
          start_node_id: 111,
          is_actionable: false,
          reason: "Waiting for intersection clearance",
          total_distance: 16.0,
          node_ids: [111, 112, 113, 123],
          edge_ids: [1008, 1010, 1032],
        },
      ],
      vehicle_inspections: [
        {
          vehicle_id: 201,
          operational_state: "moving",
          current_node_id: 121,
          current_job_id: "courier-201",
          wait_reason: "none",
          eta_s: 4.2,
          traffic_control_state: "clear",
          traffic_control_detail: "No control delay",
          route_ahead_node_ids: [121, 122],
          route_ahead_edge_ids: [1028, 1029],
          diagnostics: [{ severity: "info", code: "moving_ok" }],
        },
        {
          vehicle_id: 202,
          operational_state: "moving",
          current_node_id: 111,
          current_job_id: "courier-202",
          wait_reason: "none",
          eta_s: 8.1,
          traffic_control_state: "yield",
          traffic_control_detail: "Approaching clearance point",
          route_ahead_node_ids: [111, 112, 113, 123],
          route_ahead_edge_ids: [1008, 1010, 1032],
          diagnostics: [{ severity: "info", code: "moving_ok" }],
        },
      ],
    },
    map_surface: {
      nodes: [
        { node_id: 100, position: [0.0, 0.0, 0.0], node_type: "DEPOT" },
        { node_id: 101, position: [4.0, 0.0, 0.0], node_type: "INTERSECTION" },
        { node_id: 111, position: [4.0, 4.0, 0.0], node_type: "INTERSECTION" },
        { node_id: 121, position: [4.0, 8.0, 0.0], node_type: "LOADING_ZONE" },
        { node_id: 122, position: [8.0, 8.0, 0.0], node_type: "UNLOADING_ZONE" },
        { node_id: 123, position: [12.0, 8.0, 0.0], node_type: "JOB_SITE" },
      ],
      edges: [
        { edge_id: 1000, start_node_id: 100, end_node_id: 101, distance: 4.0, speed_limit: 3.8 },
        { edge_id: 1022, start_node_id: 101, end_node_id: 111, distance: 4.0, speed_limit: 3.2 },
        { edge_id: 1024, start_node_id: 111, end_node_id: 121, distance: 4.0, speed_limit: 3.2 },
        { edge_id: 1028, start_node_id: 121, end_node_id: 122, distance: 4.0, speed_limit: 3.2 },
        { edge_id: 1032, start_node_id: 122, end_node_id: 123, distance: 4.0, speed_limit: 3.2 },
      ],
    },
    render_geometry: {
      roads: [
        {
          road_id: "north-avenue",
          edge_ids: [1000],
          centerline: [
            [0.0, 0.0, 0.0],
            [4.0, 0.0, 0.0],
          ],
          road_class: "arterial",
          directionality: "two_way",
          lane_count: 2,
          width_m: 2.0,
        },
        {
          road_id: "center-street",
          edge_ids: [1022, 1024],
          centerline: [
            [4.0, 0.0, 0.0],
            [4.0, 4.0, 0.0],
            [4.0, 8.0, 0.0],
          ],
          road_class: "collector",
          directionality: "two_way",
          lane_count: 1,
          width_m: 1.6,
        },
        {
          road_id: "library-street",
          edge_ids: [1028],
          centerline: [
            [4.0, 8.0, 0.0],
            [8.0, 8.0, 0.0],
          ],
          road_class: "collector",
          directionality: "two_way",
          lane_count: 1,
          width_m: 1.6,
        },
        {
          road_id: "east-spur",
          edge_ids: [1032],
          centerline: [
            [8.0, 8.0, 0.0],
            [12.0, 8.0, 0.0],
          ],
          road_class: "collector",
          directionality: "two_way",
          lane_count: 1,
          width_m: 1.6,
        },
      ],
      intersections: [
        {
          intersection_id: "north-market",
          node_id: 101,
          polygon: [
            [3.5, -0.5, 0.0],
            [4.5, -0.5, 0.0],
            [4.5, 0.5, 0.0],
            [3.5, 0.5, 0.0],
          ],
          intersection_type: "junction",
        },
        {
          intersection_id: "city-center",
          node_id: 111,
          polygon: [
            [3.5, 3.5, 0.0],
            [4.5, 3.5, 0.0],
            [4.5, 4.5, 0.0],
            [3.5, 4.5, 0.0],
          ],
          intersection_type: "signalized",
        },
        {
          intersection_id: "library-plaza",
          node_id: 121,
          polygon: [
            [3.5, 7.5, 0.0],
            [4.5, 7.5, 0.0],
            [4.5, 8.5, 0.0],
            [3.5, 8.5, 0.0],
          ],
          intersection_type: "loading_bay",
        },
        {
          intersection_id: "east-yard",
          node_id: 123,
          polygon: [
            [11.5, 7.5, 0.0],
            [12.5, 7.5, 0.0],
            [12.5, 8.5, 0.0],
            [11.5, 8.5, 0.0],
          ],
          intersection_type: "job_site",
        },
      ],
      areas: [
        {
          area_id: "south-depot",
          kind: "depot",
          label: "South Depot",
          polygon: [
            [-0.9, 7.1, 0.0],
            [1.1, 7.1, 0.0],
            [1.1, 9.1, 0.0],
            [-0.9, 9.1, 0.0],
          ],
        },
        {
          area_id: "market-square",
          kind: "plaza",
          label: "Market Square",
          polygon: [
            [2.6, 2.6, 0.0],
            [5.4, 2.6, 0.0],
            [5.4, 5.4, 0.0],
            [2.6, 5.4, 0.0],
          ],
        },
        {
          area_id: "library-plaza-area",
          kind: "loading_bay",
          label: "Library Plaza",
          polygon: [
            [2.8, 6.8, 0.0],
            [5.2, 6.8, 0.0],
            [5.2, 9.2, 0.0],
            [2.8, 9.2, 0.0],
          ],
        },
        {
          area_id: "clinic-corner-area",
          kind: "unloading_bay",
          label: "Clinic Corner",
          polygon: [
            [6.8, 6.8, 0.0],
            [9.2, 6.8, 0.0],
            [9.2, 9.2, 0.0],
            [6.8, 9.2, 0.0],
          ],
        },
        {
          area_id: "east-yard-area",
          kind: "job_site",
          label: "East Yard",
          polygon: [
            [10.8, 6.8, 0.0],
            [13.2, 6.8, 0.0],
            [13.2, 9.2, 0.0],
            [10.8, 9.2, 0.0],
          ],
        },
      ],
    },
    traffic_baseline: {
      queue_records: [
        {
          road_id: "center-street",
          node_id: 111,
          reason: "yield",
          vehicle_ids: [203],
          queue_start_s: 0,
          queue_end_s: 999,
        },
      ],
      control_points: [],
    },
    snapshot: {
      simulated_time_s: 18.5,
      blocked_edge_ids: [1022],
      vehicles: [
        {
          vehicle_id: 201,
          node_id: 121,
          position: [4.0, 8.0, 0.0],
          operational_state: "moving",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 201",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
        {
          vehicle_id: 202,
          node_id: 111,
          position: [4.0, 4.0, 0.0],
          operational_state: "moving",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 202",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
        {
          vehicle_id: 203,
          node_id: 111,
          position: [4.1, 4.1, 0.0],
          operational_state: "waiting",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 203",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
        {
          vehicle_id: 204,
          node_id: 100,
          position: [0.0, 0.0, 0.0],
          operational_state: "idle",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 204",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
        {
          vehicle_id: 205,
          node_id: 122,
          position: [8.0, 8.0, 0.0],
          operational_state: "idle",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 205",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
        {
          vehicle_id: 206,
          node_id: 123,
          position: [12.0, 8.0, 0.0],
          operational_state: "idle",
          vehicle_type: "GENERIC",
          presentation_key: "car",
          display_name: "Courier 206",
          role_label: "Parcel carrier",
          body_length_m: 1.2,
          body_width_m: 0.7,
          spacing_envelope_m: 1.6,
          primary_color: "rgba(41, 79, 180, 0.96)",
          accent_color: "rgba(220, 229, 255, 0.96)",
        },
      ],
    },
    motion_segments: [
      {
        vehicle_id: 201,
        segment_index: 1,
        edge_id: 1028,
        road_id: "library-street",
        start_node_id: 121,
        end_node_id: 122,
        start_time_s: 0,
        end_time_s: 40,
        duration_s: 40,
        distance: 4,
        start_position: [4.0, 8.0, 0.0],
        end_position: [8.0, 8.0, 0.0],
        path_points: [
          [4.0, 8.0, 0.0],
          [6.0, 8.0, 0.0],
          [8.0, 8.0, 0.0],
        ],
        body_length_m: 1.2,
        body_width_m: 0.7,
        spacing_envelope_m: 1.6,
        heading_rad: 0,
        nominal_speed: 3.2,
        peak_speed: 3.2,
        profile_kind: "constant",
      },
      {
        vehicle_id: 202,
        segment_index: 2,
        edge_id: 1022,
        road_id: "center-street",
        start_node_id: 101,
        end_node_id: 111,
        start_time_s: 0,
        end_time_s: 40,
        duration_s: 40,
        distance: 4,
        start_position: [4.0, 0.0, 0.0],
        end_position: [4.0, 4.0, 0.0],
        path_points: [
          [4.0, 0.0, 0.0],
          [4.0, 2.0, 0.0],
          [4.0, 4.0, 0.0],
        ],
        body_length_m: 1.2,
        body_width_m: 0.7,
        spacing_envelope_m: 1.6,
        heading_rad: Math.PI / 2,
        nominal_speed: 2.8,
        peak_speed: 2.8,
        profile_kind: "constant",
      },
    ],
  });
}

function makeFetchMock(routePreviewBundle?: BundlePayload, loadedBundleOverride?: BundlePayload) {
  const loadedBundle = loadedBundleOverride ?? buildBundle();
  const previewBundle = routePreviewBundle ?? buildBundle({
    command_center: {
      route_previews: [
        {
          vehicle_id: 7,
          destination_node_id: 2,
          start_node_id: 1,
          is_actionable: true,
          reason: "Route is clear",
          total_distance: 10,
          node_ids: [1, 2],
          edge_ids: [1],
        },
      ],
    },
  });
  const saveBundle = buildBundle();
  const reloadBundle = buildBundle();
  const validatePayload = {
    validation_messages: [
      {
        severity: "warning",
        code: "geometry_shift",
        message: "Check staged node move.",
        target_kind: "node",
        target_id: 1,
      },
    ],
  };

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";

    if (url === bundleUrl && method === "GET") {
      return jsonResponse(loadedBundle);
    }
    if (url === "/api/live/preview" && method === "POST") {
      return jsonResponse({
        ok: true,
        bundle: previewBundle,
        route_previews: previewBundle.command_center?.route_previews ?? [],
      });
    }
    if (url === "/api/live/session/control" && method === "POST") {
      return jsonResponse({
        ok: true,
        bundle: loadedBundle,
        session_advance: {},
      });
    }
    if (url === "/api/live/command" && method === "POST") {
      return jsonResponse({
        ok: true,
        bundle: loadedBundle,
        command_result: {
          message: "Command accepted.",
        },
      });
    }
    if (url === "/api/live/authoring/validate" && method === "POST") {
      return jsonResponse(validatePayload);
    }
    if (url === "/api/live/authoring/save" && method === "POST") {
      return jsonResponse({
        ok: true,
        bundle: saveBundle,
        validation_messages: [],
      });
    }
    if (url === "/api/live/authoring/reload" && method === "GET") {
      return jsonResponse({
        ok: true,
        bundle: reloadBundle,
      });
    }
    throw new Error(`Unexpected fetch: ${method} ${url}`);
  });

  return fetchMock;
}

beforeEach(() => {
  window.history.pushState({}, "", `/?bundle=${encodeURIComponent(bundleUrl)}`);
  vi.stubGlobal("fetch", makeFetchMock());
  vi.spyOn(SVGSVGElement.prototype, "getBoundingClientRect").mockReturnValue({
    x: 0,
    y: 0,
    left: 0,
    top: 0,
    right: 100,
    bottom: 100,
    width: 100,
    height: 100,
    toJSON: () => ({}),
  } as DOMRect);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("serious ui behavior", () => {
  it("renders a loaded bundle, drives route preview, and wires live session controls", async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => expect(screen.getByText("serious-ui-fixture")).toBeInTheDocument());
    expect(screen.getByText("Operate")).toBeInTheDocument();
    expect(screen.getByText("Traffic")).toBeInTheDocument();
    expect(screen.getByText("Fleet")).toBeInTheDocument();
    const routePlanningRegion = screen.getByRole("region", { name: "route-planning" });
    expect(routePlanningRegion).toBeVisible();
    expect(within(routePlanningRegion).getByRole("heading", { name: "Primary Operator Workflow" })).toBeVisible();
    expect(within(routePlanningRegion).getByLabelText("Vehicle ID")).toBeVisible();
    expect(within(routePlanningRegion).getByLabelText("Destination Node")).toBeVisible();
    expect(within(routePlanningRegion).getByRole("button", { name: "Preview Route" })).toBeVisible();
    expect(within(routePlanningRegion).getByRole("button", { name: "Assign Destination" })).toBeVisible();

    const destinationInput = screen.getByLabelText("Destination Node");
    await user.clear(destinationInput);
    await user.type(destinationInput, "2");
    await user.click(screen.getByRole("button", { name: "Preview Route" }));

    await waitFor(() => expect(screen.getAllByText(/Route preview loaded\./i)).not.toHaveLength(0));
    await waitFor(() => expect(screen.getAllByText(/V7 · Node 2 · actionable/i)).not.toHaveLength(0));

    await user.click(screen.getByRole("button", { name: "Play" }));
    await waitFor(() =>
      expect(screen.getAllByText(/Session refresh set to play mode\./i)).not.toHaveLength(0),
    );

    await user.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() => expect(screen.getAllByText(/Session refresh paused\./i)).not.toHaveLength(0));

    await user.click(screen.getByRole("button", { name: "Single-Step" }));
    await waitFor(() => expect(screen.getAllByText(/Single-step completed\./i)).not.toHaveLength(0));
  });

  it("renders the proof-of-life city street scenario as a readable multi-vehicle live scene", async () => {
    vi.stubGlobal("fetch", makeFetchMock(undefined, buildCityStreetBundle()));
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() =>
      expect(screen.getByText("Proof-of-Life City Street")).toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Proof-of-life scene: 6 vehicles, 2 moving, 1 waiting/i),
      ).toBeInTheDocument(),
    );
    expect(screen.getAllByText("Market Square").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Library Plaza").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Clinic Corner/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Courier 201 · en route to Clinic Corner/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Clinic Corner · node 122/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Fleet 6 · Moving 2/i)).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Fit Scene" }));
    await waitFor(() =>
      expect(screen.getByText(/current camera frame, with selected vehicles and destination markers/i)).toBeInTheDocument(),
    );
  });

  it("shows the bootstrap error state when the bundle cannot load", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === bundleUrl) {
        return Promise.reject(new Error("Network down"));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await waitFor(() => expect(screen.getByText(/Live bundle needs attention/i)).toBeInTheDocument());
    expect(screen.getByText(/Live bundle bootstrap failed/i)).toBeInTheDocument();
  });

  it("validates, saves, and reloads authoring edits from a real drag gesture", async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => expect(screen.getByText("Scenario Authoring")).toBeInTheDocument());
    await user.click(
      screen.getByRole("button", { name: /Editor Scenario authoring and validation/i }),
    );
    await user.click(screen.getByRole("button", { name: "Edit Scene" }));

    const sceneSvg = screen.getByLabelText("Simulation scene graph");
    const nodeHandle = document.querySelector("circle.scene-edit-handle.node");
    expect(nodeHandle).not.toBeNull();

    if (!nodeHandle) {
      throw new Error("Expected a node handle");
    }

    fireEvent.mouseDown(nodeHandle, { clientX: 10, clientY: 10 });
    fireEvent.mouseMove(sceneSvg, { clientX: 24, clientY: 24 });
    fireEvent.mouseUp(sceneSvg, { clientX: 24, clientY: 24 });

    await waitFor(() => expect(screen.getByText(/Check staged node move\./i)).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Save Scenario" })).not.toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Save Scenario" }));
    await waitFor(() => expect(screen.getByText(/Scenario changes saved and live bundle reloaded\./i)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Reload Scenario" }));
    await waitFor(() => expect(screen.getByText(/Working scenario reloaded and draft edits cleared\./i)).toBeInTheDocument());
  });
});
