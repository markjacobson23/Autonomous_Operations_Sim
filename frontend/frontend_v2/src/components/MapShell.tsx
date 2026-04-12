import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent, type WheelEvent as ReactWheelEvent } from "react";

import type { LiveBundleViewModel } from "../adapters/liveBundle";
import {
  cameraToViewBox,
  createInitialCamera,
  minimapViewport,
  sceneTransform,
} from "../adapters/mapViewport";
import {
  buildSelectionPresentation,
  focusPointsForSelection,
  resolveActiveSelectionTarget,
  resolveSelectionVehicleIds,
} from "../adapters/selectionModel";
import type { FrontendUiActions, FrontendUiState } from "../state/frontendUiState";
import { LiveSceneCanvas } from "./LiveSceneCanvas";
import { MapMinimap } from "./MapMinimap";
import { SelectionPopup } from "./SelectionPopup";
import type { LiveRoutePreviewViewModel } from "../adapters/liveBundle";

type MapShellProps = {
  bundle: LiveBundleViewModel;
  uiState: FrontendUiState;
  actions: FrontendUiActions;
  activeRoutePreview: LiveRoutePreviewViewModel | null;
};

export function MapShell({ bundle, uiState, actions, activeRoutePreview }: MapShellProps): JSX.Element {
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
  const activeSelectionTarget = resolveActiveSelectionTarget(bundle, uiState);
  const selectedVehicleIds = resolveSelectionVehicleIds(bundle, uiState);
  const selectionPresentation = buildSelectionPresentation(bundle, uiState);
  const selectedPoints =
    selectedVehicleIds.length > 0
      ? selectedVehicleIds.flatMap((vehicleId) => {
          const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId);
          return vehicle === undefined ? [] : [vehicle.position];
        })
      : focusPointsForSelection(bundle, activeSelectionTarget);
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

  function commitSelection(target: NonNullable<typeof activeSelectionTarget>, vehicleIds: number[]) {
    const nextUiState = {
      ...uiState,
      selection: {
        ...uiState.selection,
        target,
        vehicleIds,
        hoveredTarget: null,
      },
    };
    const presentation = buildSelectionPresentation(bundle, nextUiState);
    actions.setSelection(target, vehicleIds, null);
    actions.setPopup(true, presentation?.title ?? null);
    actions.setInspector(false, "summary");
  }

  function handleSelectVehicle(vehicleId: number, additive: boolean) {
    const currentVehicleIds = selectedVehicleIds;
    const nextVehicleIds = additive
      ? currentVehicleIds.includes(vehicleId)
        ? currentVehicleIds.filter((id) => id !== vehicleId)
        : [...currentVehicleIds, vehicleId]
      : [vehicleId];

    if (nextVehicleIds.length === 0) {
      actions.setSelection(null, [], null);
      actions.setPopup(false, null);
      actions.setInspector(false, "summary");
      return;
    }

    commitSelection({ kind: "vehicle", vehicleId: nextVehicleIds[0] }, nextVehicleIds);
  }

  function handleSelectRoad(roadId: string) {
    commitSelection({ kind: "road", roadId }, []);
  }

  function handleSelectArea(areaId: string) {
    commitSelection({ kind: "area", areaId }, []);
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
            selectionTarget={activeSelectionTarget}
            selectedVehicleIds={selectedVehicleIds}
            activeRoutePreview={activeRoutePreview}
            activeMode={uiState.modePanel.activeMode}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={clearDragState}
            onPointerLeave={clearDragState}
            onWheel={handleWheel}
            onSelectVehicle={handleSelectVehicle}
            onSelectRoad={handleSelectRoad}
            onSelectArea={handleSelectArea}
          />
        ) : (
          <div className="map-loading">
            <strong>{bundle.loadState === "error" ? "Map unavailable" : "Loading live map..."}</strong>
            <span>{bundle.loadState === "error" ? bundle.loadMessage : "Waiting for the authoritative bundle."}</span>
          </div>
        )}
        <SelectionPopup presentation={selectionPresentation} />
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
