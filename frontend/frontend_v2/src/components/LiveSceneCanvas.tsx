import { useEffect, useRef } from "react";

import type { LiveBundleViewModel, Point2 } from "../adapters/liveBundle";
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
  onSelectIntersection: (intersectionId: string) => void;
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
  onSelectIntersection,
  onSelectArea,
  activeRoutePreview,
  activeMode,
}: LiveSceneCanvasProps): JSX.Element {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const { bounds, nodes, roads, intersections, areas, vehicles, sceneFrame } = model.map;
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
  const orderedAreas = [...areas].sort((left, right) => {
    const formRank = worldFormSortRank(left.formType) - worldFormSortRank(right.formType);
    if (formRank !== 0) {
      return formRank;
    }
    const categoryRank = areaSortRank(left.category) - areaSortRank(right.category);
    if (categoryRank !== 0) {
      return categoryRank;
    }
    return left.areaId.localeCompare(right.areaId);
  });
  const hasWorldFormContext =
    sceneFrame.extents.some((extent) => extent.source === "world_model" && extent.category !== "operational") ||
    orderedAreas.some((area) => area.category !== "zone");

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
      <g transform={sceneTransform} className={hasWorldFormContext ? "scene-world-form-layer" : undefined}>
        {hasWorldFormContext ? (
          <rect
            x={sceneFrame.sceneBounds.minX}
            y={sceneFrame.sceneBounds.minY}
            width={sceneFrame.sceneBounds.width}
            height={sceneFrame.sceneBounds.height}
            className="scene-world-form-backdrop"
          />
        ) : null}
        {layers.areas &&
          orderedAreas.map((area) => {
            if (area.polygon.length < 3) {
              return null;
            }
            const isSelected = selectionTarget?.kind === "area" && selectionTarget.areaId === area.areaId;
            const worldFormGeometry = buildWorldFormGeometry(area.polygon, area.formType, area.heightHint, area.depthHint);
            const formToken = worldFormToken(area.formType);
            return (
              <g
                key={area.areaId}
                className={`world-form world-form-${formToken}${isSelected ? " world-form-selected" : ""}`}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  onSelectArea(area.areaId);
                }}
              >
                {worldFormGeometry.wallPath !== null ? (
                  <path
                    d={worldFormGeometry.wallPath}
                    fillRule="evenodd"
                    className={`world-form-wall world-form-wall-${formToken} world-form-wall-${area.category}`}
                    pointerEvents="none"
                  />
                ) : null}
                <path
                  d={pointsToClosedPath(worldFormGeometry.topPolygon)}
                  className={[
                    "area-surface",
                    `area-surface-${area.category}`,
                    `area-surface-kind-${areaKindToken(area.kind)}`,
                    "world-form-top",
                    `world-form-top-${formToken}`,
                    isSelected ? " area-surface-selected" : "",
                  ].join(" ")}
                />
              </g>
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
        {intersections.length > 0 ? (
          <g className="intersection-layer">
            {intersections.map((intersection) => {
              if (intersection.polygon.length < 3) {
                return null;
              }
              const isSelected =
                selectionTarget?.kind === "intersection" && selectionTarget.intersectionId === intersection.intersectionId;
              return (
                <path
                  key={intersection.intersectionId}
                  d={pointsToClosedPath(intersection.polygon)}
                  className={`intersection-footprint intersection-footprint-${intersectionKindToken(intersection.intersectionType)}${isSelected ? " intersection-footprint-selected" : ""}`}
                  onPointerDown={(event) => {
                    event.stopPropagation();
                    onSelectIntersection(intersection.intersectionId);
                  }}
                />
              );
            })}
          </g>
        ) : null}
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

function areaSortRank(category: string): number {
  switch (category) {
    case "terrain":
      return 0;
    case "boundary":
      return 1;
    case "zone":
      return 2;
    case "structure":
      return 3;
    case "surface":
      return 4;
    case "hazard":
      return 5;
    default:
      return 6;
  }
}

function worldFormSortRank(formType: string): number {
  switch (formType) {
    case "recessed":
      return 0;
    case "flat":
      return 1;
    case "raised":
      return 2;
    case "structure_mass":
      return 3;
    default:
      return 1;
  }
}

function intersectionKindToken(kind: string): string {
  return kind.trim().toLowerCase().replace(/[^a-z0-9]+/gu, "-");
}

function worldFormToken(formType: string): string {
  return formType.trim().toLowerCase().replace(/[^a-z0-9]+/gu, "-");
}

function buildWorldFormGeometry(
  points: readonly (readonly [number, number])[],
  formType: string,
  heightHint: number,
  depthHint: number,
): {
  topPolygon: Point2[];
  wallPath: string | null;
} {
  const topPolygon = offsetWorldPolygon(points, formType, heightHint, depthHint);
  return {
    topPolygon,
    wallPath: formType === "flat" ? null : buildWorldFormWallPath(points, topPolygon),
  };
}

function offsetWorldPolygon(
  points: readonly (readonly [number, number])[],
  formType: string,
  heightHint: number,
  depthHint: number,
): Point2[] {
  if (points.length < 3) {
    return points.map((point) => [point[0], point[1]] as Point2);
  }

  const offsetScale = worldFormOffsetScale(formType);
  const direction = formType === "recessed" ? 1 : -1;
  const offsetX = direction * depthHint * offsetScale.x;
  const offsetY = direction * heightHint * offsetScale.y;
  return points.map((point) => [point[0] + offsetX, point[1] + offsetY] as Point2);
}

function worldFormOffsetScale(formType: string): { x: number; y: number } {
  switch (formType) {
    case "structure_mass":
      return { x: 0.34, y: 0.24 };
    case "raised":
      return { x: 0.24, y: 0.18 };
    case "recessed":
      return { x: 0.26, y: 0.2 };
    case "flat":
    default:
      return { x: 0.08, y: 0.05 };
  }
}

function buildWorldFormWallPath(
  basePolygon: readonly (readonly [number, number])[],
  topPolygon: readonly (readonly [number, number])[],
): string {
  return `${pointsToClosedPath(basePolygon)} ${pointsToClosedPath([...topPolygon].reverse())}`;
}
