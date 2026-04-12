import { describe, expect, it } from "vitest";

import { cameraToViewBox, fitCameraToBounds, focusPoints, minimapViewport } from "./mapViewport";

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

    const camera = fitCameraToBounds(bounds, "iso");
    const viewBox = cameraToViewBox(camera, bounds);
    const viewport = minimapViewport(bounds, viewBox);

    expect(camera).toMatchObject({
      x: 10,
      y: 5,
      zoom: 1,
      sceneViewMode: "iso",
    });
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
      "birdseye",
    );

    expect(camera.x).toBeCloseTo(8.5);
    expect(camera.y).toBeCloseTo(4.5);
    expect(camera.sceneViewMode).toBe("birdseye");
    expect(camera.zoom).toBeCloseTo(4);
  });
});
