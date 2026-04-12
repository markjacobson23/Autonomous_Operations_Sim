import type { LiveBundleViewModel } from "../adapters/liveBundle";
import type { LayerState } from "../state/frontendUiState";
import type { ViewBox } from "../adapters/mapViewport";
import type { SelectionTarget } from "../adapters/selectionModel";
import type { PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent } from "react";

type LiveSceneCanvasProps = {
  model: LiveBundleViewModel;
  viewBox: ViewBox;
  sceneTransform: string;
  layers: LayerState;
  selectionTarget: SelectionTarget | null;
  onPointerDown?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerMove?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerUp?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onPointerLeave?: (event: ReactPointerEvent<SVGSVGElement>) => void;
  onWheel?: (event: ReactWheelEvent<SVGSVGElement>) => void;
  onSelectVehicle: (vehicleId: number) => void;
  onSelectRoad: (roadId: string) => void;
  onSelectArea: (areaId: string) => void;
};

export function LiveSceneCanvas({
  model,
  viewBox,
  sceneTransform,
  layers,
  selectionTarget,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onPointerLeave,
  onWheel,
  onSelectVehicle,
  onSelectRoad,
  onSelectArea,
}: LiveSceneCanvasProps): JSX.Element {
  const { bounds, roads, areas, vehicles } = model.map;

  return (
    <svg
      className="map-canvas"
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
      role="img"
      aria-label="Authoritative live map view"
      preserveAspectRatio="xMidYMid meet"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerLeave}
      onWheel={onWheel}
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
                />
                <path
                  d={pointsToPath(road.centerline)}
                  className={`road-path road-path-core${isSelected ? " road-path-core-selected" : ""}`}
                />
              </g>
            );
          })}
        {layers.vehicles &&
          vehicles.map((vehicle) => {
            const isSelected =
              selectionTarget?.kind === "vehicle" && selectionTarget.vehicleId === vehicle.vehicleId;
            return (
              <g
                key={vehicle.vehicleId}
                transform={`translate(${vehicle.position[0]} ${vehicle.position[1]})`}
                className={isSelected ? "vehicle-group vehicle-group-selected" : "vehicle-group"}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  onSelectVehicle(vehicle.vehicleId);
                }}
              >
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
