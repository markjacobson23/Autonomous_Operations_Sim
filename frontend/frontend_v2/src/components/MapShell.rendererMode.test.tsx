import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { buildLiveBundleViewModel, type JsonRecord, type LiveBundleResource } from "../adapters/liveBundle";
import { createDefaultFrontendUiState, type FrontendUiActions } from "../state/frontendUiState";
import { MapShell } from "./MapShell";

vi.mock("./LiveSceneCanvas", () => ({
  LiveSceneCanvas: () => <div data-testid="svg-scene" />,
}));

vi.mock("./LiveSceneCanvas3D", () => ({
  LiveSceneCanvas3D: () => <div data-testid="three-scene" />,
}));

vi.mock("./MapMinimap", () => ({
  MapMinimap: () => <div data-testid="minimap" />,
}));

vi.mock("./SelectionPopup", () => ({
  SelectionPopup: () => <div data-testid="selection-popup" />,
}));

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
      source_scenario_path: "scenarios/phase_b_showcase/01_mine_phase_b_showcase.json",
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
      nodes: [{ node_id: 1, position: [0, 0, 0], node_type: "INTERSECTION" }],
      edges: [],
    },
    render_geometry: {
      world_model: {
        environment: {
          family: "mine",
          archetype_id: "phase_b_showcase",
          display_name: "Phase B Showcase",
        },
      },
      scene_frame: {
        frame_id: "scene-frame",
        environment_family: "mine",
        scene_bounds: {
          min_x: -12,
          min_y: -12,
          max_x: 12,
          max_y: 12,
          width: 24,
          height: 24,
        },
        extents: [],
      },
      roads: [],
      intersections: [],
      areas: [],
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

function makeActions(): FrontendUiActions {
  const noop = () => undefined;
  return {
    setMode: noop,
    setCamera: noop as FrontendUiActions["setCamera"],
    panCamera: noop as FrontendUiActions["panCamera"],
    zoomCamera: noop as FrontendUiActions["zoomCamera"],
    fitScene: noop as FrontendUiActions["fitScene"],
    focusPoints: noop as FrontendUiActions["focusPoints"],
    setSceneViewMode: noop as FrontendUiActions["setSceneViewMode"],
    setLayers: noop as FrontendUiActions["setLayers"],
    toggleLayer: noop as FrontendUiActions["toggleLayer"],
    setSelection: noop as FrontendUiActions["setSelection"],
    setPopup: noop as FrontendUiActions["setPopup"],
    setInspector: noop as FrontendUiActions["setInspector"],
  };
}

function renderShell(sceneRendererQuery: string): string {
  (globalThis as { window?: { location: { search: string } } }).window = {
    location: { search: sceneRendererQuery },
  };

  const bundle = buildLiveBundleViewModel(makeResource(makeBundle()));
  return renderToStaticMarkup(
    <MapShell
      bundle={bundle}
      uiState={createDefaultFrontendUiState()}
      actions={makeActions()}
      activeRoutePreview={null}
    />,
  );
}

afterEach(() => {
  delete (globalThis as { window?: unknown }).window;
});

describe("MapShell renderer toggle", () => {
  it("defaults to the SVG renderer", () => {
    const markup = renderShell("");
    expect(markup).toContain("svg-scene");
    expect(markup).not.toContain("three-scene");
  });

  it("honors the Three.js renderer query toggle", () => {
    const markup = renderShell("?sceneRenderer=three");
    expect(markup).toContain("three-scene");
    expect(markup).not.toContain("svg-scene");
  });
});
