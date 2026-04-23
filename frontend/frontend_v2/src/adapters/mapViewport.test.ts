import { describe, expect, it } from "vitest";

import {
  cameraToViewBox,
  fitCameraToBounds,
  focusPoints,
  minimapViewport,
  sceneViewPreset,
  setSceneViewMode,
} from "./mapViewport";

describe("map viewport contracts", () => {
  it("fits scene bounds around the full environment geometry", () => {
    const bounds = {
      minX: 0,
      minY: 0,
      maxX: 20,
      maxY: 10,
      width: 20,
      height: 10,
    };

    const camera = fitCameraToBounds(bounds, { sceneViewMode: "iso", ...sceneViewPreset("iso") });
    const viewBox = cameraToViewBox(camera, bounds);
    const viewport = minimapViewport(bounds, viewBox);

    expect(camera.x).toBe(10);
    expect(camera.y).toBe(5);
    expect(camera.zoom).toBe(1);
    expect(camera.sceneViewMode).toBe("iso");
    expect(camera.azimuth).toBeCloseTo(Math.PI / 4);
    expect(camera.polar).toBeCloseTo(0.96);
    expect(viewBox).toEqual({
      x: 0,
      y: 0,
      width: 20,
      height: 10,
    });
    expect(viewport).toEqual({
      x: 0,
      y: 0,
      width: 220,
      height: 152,
    });
  });

  it("focuses a selected point with padded framing", () => {
    const currentCamera = {
      x: 3,
      y: 4,
      zoom: 2,
      sceneViewMode: "birdseye" as const,
      azimuth: 1.21,
      polar: 0.57,
    };
    const selectedPoint = [[8, 4] as const];
    const camera = focusPoints(
      selectedPoint,
      {
        minX: 0,
        minY: 0,
        maxX: 20,
        maxY: 20,
        width: 20,
        height: 20,
      },
      currentCamera,
    );

    expect(camera.x).toBeCloseTo(8.5);
    expect(camera.y).toBeCloseTo(4.5);
    expect(camera.sceneViewMode).toBe("birdseye");
    expect(camera.zoom).toBeCloseTo(4);
    expect(camera.azimuth).toBeCloseTo(currentCamera.azimuth);
    expect(camera.polar).toBeCloseTo(currentCamera.polar);
  });

  it("preserves user rotation when fitting but resets to preset intentionally when asked", () => {
    const currentCamera = {
      x: 3,
      y: 4,
      zoom: 2.5,
      sceneViewMode: "iso" as const,
      azimuth: 1.72,
      polar: 0.82,
    };
    const fitted = fitCameraToBounds(
      {
        minX: 0,
        minY: 0,
        maxX: 20,
        maxY: 20,
        width: 20,
        height: 20,
      },
      currentCamera,
    );
    const reset = setSceneViewMode(currentCamera, "birdseye");

    expect(fitted.azimuth).toBeCloseTo(currentCamera.azimuth);
    expect(fitted.polar).toBeCloseTo(currentCamera.polar);
    expect(fitted.zoom).toBe(1);
    expect(reset.azimuth).not.toBeCloseTo(currentCamera.azimuth);
    expect(reset.polar).not.toBeCloseTo(currentCamera.polar);
    expect(reset.sceneViewMode).toBe("birdseye");
  });
});
