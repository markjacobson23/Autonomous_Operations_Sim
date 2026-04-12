import { useMemo, useReducer } from "react";

import type { SceneBounds } from "../adapters/mapViewport";
import { fitCameraToBounds, focusPoints, panCamera, setSceneViewMode, zoomCamera } from "../adapters/mapViewport";

export type FrontendModeId = "operate" | "traffic" | "fleet" | "editor" | "analyze";

export type SceneViewMode = "birdseye" | "iso";

export type LayerState = {
  roads: boolean;
  vehicles: boolean;
  areas: boolean;
  labels: boolean;
  routes: boolean;
  hazards: boolean;
  reservations: boolean;
  intersections: boolean;
};

export type FrontendUiState = {
  camera: {
    x: number;
    y: number;
    zoom: number;
    sceneViewMode: SceneViewMode;
  };
  layers: LayerState;
  selection: {
    vehicleIds: number[];
    hoveredTarget: string | null;
  };
  popup: {
    open: boolean;
    targetLabel: string | null;
  };
  inspector: {
    pinned: boolean;
    section: "summary" | "details";
  };
  planning: {
    draftStatus: "idle";
    draftLabel: string | null;
  };
  modePanel: {
    activeMode: FrontendModeId;
  };
  editorGesture: {
    dragKind: "none";
    activeHandleId: string | null;
  };
};

type FrontendUiAction =
  | { type: "set_mode"; mode: FrontendModeId }
  | { type: "set_camera"; camera: FrontendUiState["camera"] }
  | { type: "pan_camera"; deltaX: number; deltaY: number }
  | { type: "zoom_camera"; factor: number }
  | { type: "fit_scene"; bounds: SceneBounds }
  | { type: "focus_points"; points: Point2[]; fallbackBounds: SceneBounds }
  | { type: "set_scene_view_mode"; sceneViewMode: SceneViewMode }
  | { type: "set_layers"; layers: LayerState }
  | { type: "set_selection"; vehicleIds: number[]; hoveredTarget: string | null }
  | { type: "set_popup"; open: boolean; targetLabel: string | null }
  | { type: "set_inspector"; pinned: boolean; section: FrontendUiState["inspector"]["section"] }
  | { type: "set_planning"; draftStatus: "idle"; draftLabel: string | null }
  | { type: "set_editor_gesture"; dragKind: "none"; activeHandleId: string | null };

const defaultLayers: LayerState = {
  roads: true,
  vehicles: true,
  areas: true,
  labels: false,
  routes: false,
  hazards: false,
  reservations: false,
  intersections: false,
};

export function createDefaultFrontendUiState(): FrontendUiState {
  return {
    camera: {
      x: 0,
      y: 0,
      zoom: 1,
      sceneViewMode: "iso",
    },
    layers: defaultLayers,
    selection: {
      vehicleIds: [],
      hoveredTarget: null,
    },
    popup: {
      open: false,
      targetLabel: null,
    },
    inspector: {
      pinned: false,
      section: "summary",
    },
    planning: {
      draftStatus: "idle",
      draftLabel: null,
    },
    modePanel: {
      activeMode: "operate",
    },
    editorGesture: {
      dragKind: "none",
      activeHandleId: null,
    },
  };
}

function frontendUiStateReducer(
  state: FrontendUiState,
  action: FrontendUiAction,
): FrontendUiState {
  switch (action.type) {
    case "set_mode":
      return {
        ...state,
        modePanel: {
          activeMode: action.mode,
        },
      };
    case "set_camera":
      return {
        ...state,
        camera: action.camera,
      };
    case "pan_camera":
      return {
        ...state,
        camera: panCamera(state.camera, action.deltaX, action.deltaY),
      };
    case "zoom_camera":
      return {
        ...state,
        camera: zoomCamera(state.camera, action.factor),
      };
    case "fit_scene":
      return {
        ...state,
        camera: fitCameraToBounds(action.bounds, state.camera.sceneViewMode),
      };
    case "focus_points":
      return {
        ...state,
        camera: focusPoints(action.points, action.fallbackBounds, state.camera.sceneViewMode),
      };
    case "set_scene_view_mode":
      return {
        ...state,
        camera: setSceneViewMode(state.camera, action.sceneViewMode),
      };
    case "set_layers":
      return {
        ...state,
        layers: action.layers,
      };
    case "set_selection":
      return {
        ...state,
        selection: {
          vehicleIds: action.vehicleIds,
          hoveredTarget: action.hoveredTarget,
        },
      };
    case "set_popup":
      return {
        ...state,
        popup: {
          open: action.open,
          targetLabel: action.targetLabel,
        },
      };
    case "set_inspector":
      return {
        ...state,
        inspector: {
          pinned: action.pinned,
          section: action.section,
        },
      };
    case "set_planning":
      return {
        ...state,
        planning: {
          draftStatus: action.draftStatus,
          draftLabel: action.draftLabel,
        },
      };
    case "set_editor_gesture":
      return {
        ...state,
        editorGesture: {
          dragKind: action.dragKind,
          activeHandleId: action.activeHandleId,
        },
      };
    default:
      return state;
  }
}

export function useFrontendUiState(): {
  state: FrontendUiState;
  actions: FrontendUiActions;
} {
  const [state, dispatch] = useReducer(frontendUiStateReducer, undefined, createDefaultFrontendUiState);

  return useMemo(
    () => ({
      state,
      actions: {
        setMode: (mode: FrontendModeId) => dispatch({ type: "set_mode", mode }),
        setCamera: (camera: FrontendUiState["camera"]) => dispatch({ type: "set_camera", camera }),
        panCamera: (deltaX: number, deltaY: number) => dispatch({ type: "pan_camera", deltaX, deltaY }),
        zoomCamera: (factor: number) => dispatch({ type: "zoom_camera", factor }),
        fitScene: (bounds: SceneBounds) => dispatch({ type: "fit_scene", bounds }),
        focusPoints: (points: Point2[], fallbackBounds: SceneBounds) =>
          dispatch({ type: "focus_points", points, fallbackBounds }),
        setSceneViewMode: (sceneViewMode: SceneViewMode) =>
          dispatch({ type: "set_scene_view_mode", sceneViewMode }),
        setLayers: (layers: LayerState) => dispatch({ type: "set_layers", layers }),
        toggleLayer: (layer: keyof LayerState) =>
          dispatch({
            type: "set_layers",
            layers: {
              ...state.layers,
              [layer]: !state.layers[layer],
            },
          }),
        setSelection: (vehicleIds: number[], hoveredTarget: string | null) =>
          dispatch({ type: "set_selection", vehicleIds, hoveredTarget }),
      },
    }),
    [state],
  );
}

export type FrontendUiActions = {
  setMode: (mode: FrontendModeId) => void;
  setCamera: (camera: FrontendUiState["camera"]) => void;
  panCamera: (deltaX: number, deltaY: number) => void;
  zoomCamera: (factor: number) => void;
  fitScene: (bounds: SceneBounds) => void;
  focusPoints: (points: Point2[], fallbackBounds: SceneBounds) => void;
  setSceneViewMode: (sceneViewMode: SceneViewMode) => void;
  setLayers: (layers: LayerState) => void;
  toggleLayer: (layer: keyof LayerState) => void;
  setSelection: (vehicleIds: number[], hoveredTarget: string | null) => void;
};

export type Point2 = readonly [number, number];
