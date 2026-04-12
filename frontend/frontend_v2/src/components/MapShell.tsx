import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent, type WheelEvent as ReactWheelEvent } from "react";

import type { LiveBundleViewModel } from "../adapters/liveBundle";
import {
  cameraToViewBox,
  createInitialCamera,
  minimapViewport,
  sceneTransform,
} from "../adapters/mapViewport";
import type { FrontendUiActions, FrontendUiState } from "../state/frontendUiState";
import { LiveSceneCanvas } from "./LiveSceneCanvas";
import { MapMinimap } from "./MapMinimap";

type MapShellProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  actions: FrontendUiActions;
};

export function MapShell({ bundle, uiState, actions }: MapShellProps): JSX.Element {
  const initialFitDoneRef = useRef(false);
  const [dragState, setDragState] = useState<{
    pointerId: number;
    lastClientX: number;
    lastClientY: number;
  } | null>(null);

  useEffect(() => {
    if (bundle.loadState !== "ready") {
      initialFitDoneRef.current = false;
      return;
    }

    if (!initialFitDoneRef.current) {
      actions.fitScene(bundle.map.bounds);
      initialFitDoneRef.current = true;
      return;
    }
  }, [actions, bundle.loadState, bundle.map.bounds]);

  const camera = initialFitDoneRef.current
    ? uiState.camera
    : createInitialCamera(bundle.map.bounds, uiState.camera.sceneViewMode);
  const viewBox = cameraToViewBox(camera, bundle.map.bounds);
  const viewport = minimapViewport(bundle.map.bounds, viewBox);
  const selectedPoints = collectSelectedPoints(bundle, uiState);
  const canFocusSelected = selectedPoints.length > 0;

  function handlePointerDown(event: ReactPointerEvent<SVGSVGElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragState({
      pointerId: event.pointerId,
      lastClientX: event.clientX,
      lastClientY: event.clientY,
    });
  }

  function handlePointerMove(event: ReactPointerEvent<SVGSVGElement>) {
    if (dragState === null || dragState.pointerId !== event.pointerId) {
      return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      return;
    }

    const deltaClientX = event.clientX - dragState.lastClientX;
    const deltaClientY = event.clientY - dragState.lastClientY;
    const worldDeltaX = (-deltaClientX / rect.width) * viewBox.width;
    const worldDeltaY = (-deltaClientY / rect.height) * viewBox.height;
    actions.panCamera(worldDeltaX, worldDeltaY);
    setDragState({
      pointerId: event.pointerId,
      lastClientX: event.clientX,
      lastClientY: event.clientY,
    });
  }

  function clearDragState() {
    setDragState(null);
  }

  function handleWheel(event: ReactWheelEvent<SVGSVGElement>) {
    event.preventDefault();
    const factor = event.deltaY > 0 ? 0.92 : 1.08;
    actions.zoomCamera(factor);
  }

  function handleCenterAt(worldX: number, worldY: number) {
    actions.setCamera({
      ...camera,
      x: worldX,
      y: worldY,
    });
  }

  function handlePan(directionX: number, directionY: number) {
    const stepX = viewBox.width * 0.18 * directionX;
    const stepY = viewBox.height * 0.18 * directionY;
    actions.panCamera(stepX, stepY);
  }

  function handleZoom(factor: number) {
    actions.zoomCamera(factor);
  }

  function handleFit() {
    actions.fitScene(bundle.map.bounds);
  }

  function handleFocusSelected() {
    actions.focusPoints(selectedPoints, bundle.map.bounds);
  }

  function handleSceneModeChange(sceneViewMode: FrontendUiState["camera"]["sceneViewMode"]) {
    actions.setSceneViewMode(sceneViewMode);
  }

  function handleToggleLayer(layer: keyof FrontendUiState["layers"]) {
    actions.toggleLayer(layer);
  }

  const shellCursorClass = dragState === null ? "map-shell-cursor-grab" : "map-shell-cursor-grabbing";

  return (
    <section className={`map-shell panel ${shellCursorClass}`}>
      <div className="map-shell-toolbar">
        <div className="map-shell-toolbar-group">
          <button type="button" className="scene-button-primary" onClick={() => handlePan(-1, 0)}>
            Pan Left
          </button>
          <button type="button" className="scene-button-primary" onClick={() => handlePan(1, 0)}>
            Pan Right
          </button>
          <button type="button" className="scene-button-primary" onClick={() => handlePan(0, -1)}>
            Pan Up
          </button>
          <button type="button" className="scene-button-primary" onClick={() => handlePan(0, 1)}>
            Pan Down
          </button>
        </div>

        <div className="map-shell-toolbar-group">
          <button type="button" className="scene-button-primary" onClick={() => handleZoom(1.12)}>
            Zoom In
          </button>
          <button type="button" className="scene-button-primary" onClick={() => handleZoom(0.9)}>
            Zoom Out
          </button>
          <button type="button" className="scene-button-primary" onClick={handleFit}>
            Fit Scene
          </button>
          <button type="button" className="scene-button-primary" onClick={handleFocusSelected} disabled={!canFocusSelected}>
            Focus Selected
          </button>
        </div>

        <div className="map-shell-toolbar-group">
          <button
            type="button"
            className={`scene-button-primary ${uiState.camera.sceneViewMode === "iso" ? "scene-button-active" : ""}`}
            onClick={() => handleSceneModeChange("iso")}
          >
            Iso
          </button>
          <button
            type="button"
            className={`scene-button-primary ${uiState.camera.sceneViewMode === "birdseye" ? "scene-button-active" : ""}`}
            onClick={() => handleSceneModeChange("birdseye")}
          >
            Birdseye
          </button>
        </div>
      </div>

      <div className="map-shell-stage">
        {bundle.loadState === "ready" ? (
          <LiveSceneCanvas
            model={bundle}
            viewBox={viewBox}
            sceneTransform={sceneTransform(camera, viewBox)}
            layers={uiState.layers}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={clearDragState}
            onPointerLeave={clearDragState}
            onWheel={handleWheel}
          />
        ) : (
          <div className="map-loading">
            <strong>{bundle.loadState === "error" ? "Map unavailable" : "Loading live map..."}</strong>
            <span>{bundle.loadState === "error" ? bundle.loadMessage : "Waiting for the authoritative bundle."}</span>
          </div>
        )}
      </div>

      <div className="map-shell-footer">
        <div className="layer-controls">
          <span className="layer-controls-label">Layers</span>
          {Object.entries(uiState.layers).map(([layer, enabled]) => (
            <button
              key={layer}
              type="button"
              className={`layer-chip ${enabled ? "layer-chip-active" : ""}`}
              onClick={() => handleToggleLayer(layer as keyof FrontendUiState["layers"])}
            >
              {layer}
            </button>
          ))}
        </div>

        <MapMinimap model={bundle} camera={camera} viewport={viewport} onCenterAt={handleCenterAt} />
      </div>
    </section>
  );
}

function collectSelectedPoints(bundle: LiveBundleViewModel, uiState: FrontendUiState): Array<readonly [number, number]> {
  const selectedIds = uiState.selection.vehicleIds.length > 0 ? uiState.selection.vehicleIds : bundle.selectedVehicleIds;
  if (selectedIds.length === 0) {
    return [];
  }

  const vehicleLookup = new Map(bundle.map.vehicles.map((vehicle) => [vehicle.vehicleId, vehicle.position]));
  return selectedIds.flatMap((vehicleId) => {
    const position = vehicleLookup.get(vehicleId);
    return position === undefined ? [] : [position];
  });
}
