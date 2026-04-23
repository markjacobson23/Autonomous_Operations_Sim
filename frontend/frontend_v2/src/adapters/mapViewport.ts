import type { Point2, SceneViewMode } from "../state/frontendUiState";

export type SceneBounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

export type CameraState = {
  x: number;
  y: number;
  zoom: number;
  sceneViewMode: SceneViewMode;
  azimuth: number;
  polar: number;
};

export type ViewBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type MinimapViewport = {
  x: number;
  y: number;
  width: number;
  height: number;
};

const minZoom = 0.65;
const maxZoom = 4;
const defaultIsoAzimuth = Math.PI / 4;
const defaultIsoPolar = 0.96;
const defaultBirdseyeAzimuth = Math.PI / 4;
const defaultBirdseyePolar = 0.34;

export function sceneViewPreset(sceneViewMode: SceneViewMode): Pick<CameraState, "azimuth" | "polar"> {
  if (sceneViewMode === "birdseye") {
    return {
      azimuth: defaultBirdseyeAzimuth,
      polar: defaultBirdseyePolar,
    };
  }

  return {
    azimuth: defaultIsoAzimuth,
    polar: defaultIsoPolar,
  };
}

export function createInitialCamera(bounds: SceneBounds, sceneViewMode: SceneViewMode = "iso"): CameraState {
  return fitCameraToBounds(bounds, {
    sceneViewMode,
    ...sceneViewPreset(sceneViewMode),
  });
}

export function fitCameraToBounds(
  bounds: SceneBounds,
  cameraSeed: Pick<CameraState, "sceneViewMode" | "azimuth" | "polar"> = {
    sceneViewMode: "iso",
    ...sceneViewPreset("iso"),
  },
): CameraState {
  return {
    x: bounds.minX + bounds.width / 2,
    y: bounds.minY + bounds.height / 2,
    zoom: 1,
    sceneViewMode: cameraSeed.sceneViewMode,
    azimuth: cameraSeed.azimuth,
    polar: cameraSeed.polar,
  };
}

export function focusPoints(
  points: Point2[],
  fallbackBounds: SceneBounds,
  cameraSeed: Pick<CameraState, "sceneViewMode" | "azimuth" | "polar"> = {
    sceneViewMode: "iso",
    ...sceneViewPreset("iso"),
  },
): CameraState {
  if (points.length === 0) {
    return fitCameraToBounds(fallbackBounds, cameraSeed);
  }

  const bounds = boundsFromPoints(points);
  const paddedBounds = padBounds(bounds, Math.max(Math.min(bounds.width, bounds.height) * 0.2, 2));
  const zoom = clamp(
    Math.min(fallbackBounds.width / paddedBounds.width, fallbackBounds.height / paddedBounds.height),
    minZoom,
    maxZoom,
  );
  return {
    x: paddedBounds.minX + paddedBounds.width / 2,
    y: paddedBounds.minY + paddedBounds.height / 2,
    zoom,
    sceneViewMode: cameraSeed.sceneViewMode,
    azimuth: cameraSeed.azimuth,
    polar: cameraSeed.polar,
  };
}

export function panCamera(camera: CameraState, deltaX: number, deltaY: number): CameraState {
  return {
    ...camera,
    x: camera.x + deltaX,
    y: camera.y + deltaY,
  };
}

export function zoomCamera(camera: CameraState, factor: number): CameraState {
  return {
    ...camera,
    zoom: clamp(camera.zoom * factor, minZoom, maxZoom),
  };
}

export function setSceneViewMode(camera: CameraState, sceneViewMode: SceneViewMode): CameraState {
  return {
    ...camera,
    sceneViewMode,
    ...sceneViewPreset(sceneViewMode),
  };
}

export function cameraToViewBox(camera: CameraState, bounds: SceneBounds): ViewBox {
  const width = bounds.width / camera.zoom;
  const height = bounds.height / camera.zoom;
  return {
    x: camera.x - width / 2,
    y: camera.y - height / 2,
    width,
    height,
  };
}

export function sceneTransform(camera: CameraState, viewBox: ViewBox): string {
  if (camera.sceneViewMode === "birdseye") {
    return "";
  }

  const centerX = viewBox.x + viewBox.width / 2;
  const centerY = viewBox.y + viewBox.height / 2;
  return [
    `translate(${centerX} ${centerY})`,
    "scale(1 0.9)",
    "skewX(-18)",
    `translate(${-centerX} ${-centerY})`,
  ].join(" ");
}

export function minimapViewport(bounds: SceneBounds, viewBox: ViewBox): MinimapViewport {
  const scaleX = 220 / bounds.width;
  const scaleY = 152 / bounds.height;
  return {
    x: (viewBox.x - bounds.minX) * scaleX,
    y: (viewBox.y - bounds.minY) * scaleY,
    width: viewBox.width * scaleX,
    height: viewBox.height * scaleY,
  };
}

export function worldPointFromMinimap(
  bounds: SceneBounds,
  localX: number,
  localY: number,
  minimapWidth: number,
  minimapHeight: number,
): Point2 {
  const x = bounds.minX + (localX / minimapWidth) * bounds.width;
  const y = bounds.minY + (localY / minimapHeight) * bounds.height;
  return [x, y];
}

export function boundsFromPoints(points: Point2[]): SceneBounds {
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

export function padBounds(bounds: SceneBounds, padding: number): SceneBounds {
  return {
    minX: bounds.minX - padding,
    minY: bounds.minY - padding,
    maxX: bounds.maxX + padding,
    maxY: bounds.maxY + padding,
    width: bounds.width + padding * 2,
    height: bounds.height + padding * 2,
  };
}

function clamp(value: number, minValue: number, maxValue: number): number {
  return Math.min(Math.max(value, minValue), maxValue);
}
