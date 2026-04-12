import { useEffect, useRef } from "react";

import type { LiveBundleViewModel } from "../adapters/liveBundle";
import type { FrontendModeId, LayerState } from "../state/frontendUiState";
import type { ViewBox } from "../adapters/mapViewport";
import type { SelectionTarget } from "../adapters/selectionModel";
import type { PointerEvent as ReactPointerEvent } from "react";

type LiveSceneCanvasProps = {
  model: LiveBundleViewModel;
  viewBox: ViewBox;
  sceneTransform: string;
  layers: LayerState;
  selectionTarget: SelectionTarget | null;
  selectedVehicleIds: number[];
  onPointerDown?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerMove?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerUp?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerLeave?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onWheelZoom?: (deltaY: number) => void;
  onSelectVehicle: (vehicleId: number, additive: boolean) => void;
  onSelectRoad: (roadId: string) => void;
  onSelectArea: (areaId: string) => void;
  activeRoutePreview: LiveBundleViewModel["commandCenter"]["routePreviews"][number] | null;
  activeMode: FrontendModeId;
};

export function LiveSceneCanvas({
  model,
  viewBox,
  sceneTransform,
  layers,
  selectionTarget,
  selectedVehicleIds,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onPointerLeave,
  onWheelZoom,
  onSelectVehicle,
  onSelectRoad,
  onSelectArea,
  activeRoutePreview,
  activeMode,
}: LiveSceneCanvasProps): JSX.Element {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const { bounds, nodes, roads, areas, vehicles } = model.map;
  const trafficRoadStates = model.traffic.roadStates;
  const trafficControlPoints = model.traffic.controlPoints;
  const trafficQueueRecords = model.traffic.queueRecords;
  const showTrafficOverlay =
    activeMode === "traffic" && (trafficRoadStates.length > 0 || trafficControlPoints.length > 0 || trafficQueueRecords.length > 0);
  const nodePositions = new Map(nodes.map((node) => [node.nodeId, node.position]));
  const previewPathPoints = layers.routes && activeRoutePreview !== null ? activeRoutePreview.pathPoints : [];
  const previewDestinationPoint = layers.routes && activeRoutePreview !== null ? activeRoutePreview.destinationPoint : null;
  const previewDiagnostics = layers.routes && activeRoutePreview !== null ? activeRoutePreview.renderDiagnostics : [];
  const selectedVehicleIdSet = new Set(selectedVehicleIds);

  useEffect(() => {
    const svgElement = svgRef.current;
    if (svgElement === null || onWheelZoom === undefined) {
      return undefined;
    }

    const handleWheel = (event: WheelEvent) => {
      event.preventDefault();
      onWheelZoom(event.deltaY);
    };

    svgElement.addEventListener("wheel", handleWheel, { passive: false });
    return () => {
      svgElement.removeEventListener("wheel", handleWheel);
    };
  }, [onWheelZoom]);

  const routeVisibilityMessage =
    activeRoutePreview !== null && layers.routes
      ? previewPathPoints.length > 0 || previewDestinationPoint !== null
        ? previewDiagnostics.length > 0
          ? previewDiagnostics[0]
          : null
        : "Route preview data could not be painted."
      : activeRoutePreview !== null && !layers.routes
        ? "Route layer is disabled, so the active preview is hidden."
        : null;

  return (
    <svg
      ref={svgRef}
      className="map-canvas"
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
      role="img"
      aria-label="Authoritative live map view"
      preserveAspectRatio="xMidYMid meet"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerLeave}
    >
      <defs>
        <radialGradient id="map-ground-vignette" cx="50%" cy="38%" r="85%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.02" />
          <stop offset="100%" stopColor="#3c484e" stopOpacity="0.08" />
        </radialGradient>
      </defs>
      <rect x={bounds.minX} y={bounds.minY} width={bounds.width} height={bounds.height} className="map-ground" />
      <rect
        x={bounds.minX}
        y={bounds.minY}
        width={bounds.width}
        height={bounds.height}
        className="map-ground-vignette"
      />
      <g transform={sceneTransform}>
        {layers.areas &&
          areas.map((area) => {
            if (area.polygon.length < 3) {
              return null;
            }
            const isSelected = selectionTarget?.kind === "area" && selectionTarget.areaId === area.areaId;
            return (
              <path
                key={area.areaId}
                d={pointsToClosedPath(area.polygon)}
                className={`area-surface area-surface-${areaKindToken(area.kind)}${isSelected ? " area-surface-selected" : ""}`}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  onSelectArea(area.areaId);
                }}
              />
            );
          })}
        {layers.routes && activeRoutePreview !== null && previewPathPoints.length > 0 ? (
          <g className="route-preview-layer">
            {previewPathPoints.length > 1 ? <path d={pointsToPath(previewPathPoints)} className="route-preview-path" /> : null}
            {previewPathPoints.map((point, index) => (
              <circle
                key={`route-preview-node-${activeRoutePreview.vehicleId}-${index}`}
                cx={point[0]}
                cy={point[1]}
                r={index === 0 ? 0.28 : 0.24}
                className={index === 0 ? "route-preview-node route-preview-node-start" : "route-preview-node"}
              />
            ))}
            {previewDestinationPoint !== null ? (
              <circle
                cx={previewDestinationPoint[0]}
                cy={previewDestinationPoint[1]}
                r={0.5}
                className="route-preview-destination"
              />
            ) : null}
          </g>
        ) : null}
        {layers.roads &&
          roads.map((road) => {
            if (road.centerline.length < 2) {
              return null;
            }
            const isSelected = selectionTarget?.kind === "road" && selectionTarget.roadId === road.roadId;
            return (
              <g key={road.roadId} className={isSelected ? "road-group road-group-selected" : "road-group"}>
                <path
                  d={pointsToPath(road.centerline)}
                  className="road-hit-target"
                  onPointerDown={(event) => {
                    event.stopPropagation();
                    onSelectRoad(road.roadId);
                  }}
                />
                <path
                  d={pointsToPath(road.centerline)}
                  className={
                    road.blocked
                      ? `road-path road-path-casing road-path-blocked${isSelected ? " road-path-selected" : ""}`
                      : `road-path road-path-casing${isSelected ? " road-path-selected" : ""}`
                  }
                  pointerEvents="none"
                />
                <path
                  d={pointsToPath(road.centerline)}
                  className={`road-path road-path-core${isSelected ? " road-path-core-selected" : ""}`}
                  pointerEvents="none"
                />
              </g>
            );
          })}
        {showTrafficOverlay ? (
          <g className="traffic-overlay-layer">
            {trafficRoadStates.map((roadState) => {
              const road = roads.find((entry) => entry.roadId === roadState.roadId) ?? null;
              if (road === null || road.centerline.length < 2 || roadState.congestionIntensity <= 0) {
                return null;
              }
              const isSelected = selectionTarget?.kind === "road" && selectionTarget.roadId === roadState.roadId;
              return (
                <path
                  key={`traffic-road-${roadState.roadId}`}
                  d={pointsToPath(road.centerline)}
                  className={`traffic-overlay-road${isSelected ? " traffic-overlay-road-selected" : ""}`}
                  style={{
                    strokeOpacity: Math.min(0.78, 0.12 + roadState.congestionIntensity * 0.72),
                    strokeWidth: 0.24 + roadState.congestionIntensity * 0.72,
                  }}
                />
              );
            })}
            {trafficControlPoints.map((controlPoint) => {
              const position = controlPoint.position ?? nodePositions.get(controlPoint.nodeId) ?? null;
              if (position === null) {
                return null;
              }
              return (
                <g key={controlPoint.controlId} className="traffic-control-point">
                  <circle
                    cx={position[0]}
                    cy={position[1]}
                    r={controlPoint.signalReady ? 0.42 : 0.34}
                    className={controlPoint.signalReady ? "traffic-control-point-ready" : "traffic-control-point-waiting"}
                  />
                </g>
              );
            })}
            {trafficQueueRecords.slice(0, 8).map((record, index) => {
              const position = record.position ?? nodePositions.get(record.nodeId) ?? null;
              if (position === null) {
                return null;
              }
              return (
                <circle
                  key={`traffic-queue-${record.vehicleId}-${index}`}
                  cx={position[0]}
                  cy={position[1]}
                  r={0.18}
                  className="traffic-queue-marker"
                />
              );
            })}
          </g>
        ) : null}
        {layers.vehicles &&
          vehicles.map((vehicle) => {
            const isSelected = selectedVehicleIdSet.has(vehicle.vehicleId);
            return (
              <g
                key={vehicle.vehicleId}
                transform={`translate(${vehicle.position[0]} ${vehicle.position[1]})`}
                className={isSelected ? "vehicle-group vehicle-group-selected" : "vehicle-group"}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  onSelectVehicle(vehicle.vehicleId, event.ctrlKey || event.metaKey || event.shiftKey);
                }}
              >
                {isSelected ? <circle className="vehicle-selection-ring" r="1.52" pointerEvents="none" /> : null}
                <circle className={`vehicle-core vehicle-core-${vehicle.stateClass}`} r={isSelected ? "0.72" : "0.55"} />
                <circle className={`vehicle-halo${isSelected ? " vehicle-halo-selected" : ""}`} r={isSelected ? "1.18" : "0.95"} />
                {layers.labels && (
                  <text className="vehicle-label" y="-1.1" textAnchor="middle">
                    {`${vehicle.vehicleId} · ${vehicle.state}`}
                  </text>
                )}
              </g>
            );
          })}
      </g>
      {routeVisibilityMessage !== null ? (
        <g className="map-canvas-diagnostic">
          <rect x={bounds.minX + 0.4} y={bounds.minY + 0.4} width={Math.min(bounds.width - 0.8, 8.8)} height={1.3} rx={0.18} />
          <text x={bounds.minX + 0.7} y={bounds.minY + 1.18}>
            {routeVisibilityMessage}
          </text>
        </g>
      ) : null}
    </svg>
  );
}

function pointsToPath(points: readonly (readonly [number, number])[]): string {
  if (points.length < 2) {
    return "";
  }
  const [first, ...rest] = points;
  const commands = [`M ${first[0]} ${first[1]}`];
  for (const point of rest) {
    commands.push(`L ${point[0]} ${point[1]}`);
  }
  return commands.join(" ");
}

function pointsToClosedPath(points: readonly (readonly [number, number])[]): string {
  const openPath = pointsToPath(points);
  return openPath.length > 0 ? `${openPath} Z` : openPath;
}

function areaKindToken(kind: string): string {
  return kind.trim().toLowerCase().replace(/[^a-z0-9]+/gu, "-");
}
