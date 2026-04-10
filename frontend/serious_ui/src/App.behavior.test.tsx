import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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

function makeFetchMock(routePreviewBundle?: BundlePayload) {
  const loadedBundle = buildBundle();
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
