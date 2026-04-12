import type { LiveBundleViewModel } from "../adapters/liveBundle";
import type { CameraState, MinimapViewport } from "../adapters/mapViewport";
import type { MouseEvent as ReactMouseEvent } from "react";

type MapMinimapProps = {
  model: LiveBundleViewModel;
  camera: CameraState;
  viewport: MinimapViewport;
  onCenterAt: (x: number, y: number) => void;
};

export function MapMinimap({ model, camera, viewport, onCenterAt }: MapMinimapProps): JSX.Element {
  const { bounds, roads, intersections, areas, vehicles } = model.map;
  const scaleX = 220 / bounds.width;
  const scaleY = 152 / bounds.height;

  function handleClick(event: ReactMouseEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      return;
    }
    const localX = ((event.clientX - rect.left) / rect.width) * 220;
    const localY = ((event.clientY - rect.top) / rect.height) * 152;
    const worldX = bounds.minX + (localX / scaleX);
    const worldY = bounds.minY + (localY / scaleY);
    onCenterAt(worldX, worldY);
  }

  return (
    <section className="panel overview-card-minimap">
      <div className="minimap-card-head">
        <div>
          <p className="panel-kicker">Minimap</p>
          <h3>Scene context</h3>
        </div>
        <span className="minimap-orientation-pill">{camera.sceneViewMode}</span>
      </div>
      <svg
        className="minimap"
        viewBox="0 0 220 152"
        preserveAspectRatio="xMidYMid meet"
        onClick={handleClick}
        role="img"
        aria-label="Map minimap"
      >
        <rect x="0" y="0" width="220" height="152" className="minimap-bg" />
        {areas.map((area) => (
          <path
            key={area.areaId}
            d={pointsToMinimapPath(area.polygon, bounds)}
            className={`minimap-area minimap-area-${area.category}`}
          />
        ))}
        {intersections.map((intersection) => (
          <path
            key={intersection.intersectionId}
            d={pointsToMinimapPath(intersection.polygon, bounds)}
            className={`minimap-intersection minimap-intersection-${intersectionKindToken(intersection.intersectionType)}`}
          />
        ))}
        {roads.map((road) => (
          <path key={road.roadId} d={pointsToMinimapPath(road.centerline, bounds)} className="minimap-road" />
        ))}
        {vehicles.map((vehicle) => (
          <circle
            key={vehicle.vehicleId}
            cx={(vehicle.position[0] - bounds.minX) * scaleX}
            cy={(vehicle.position[1] - bounds.minY) * scaleY}
            r="3"
            className="minimap-vehicle-core"
          />
        ))}
        <rect x={viewport.x} y={viewport.y} width={viewport.width} height={viewport.height} className="minimap-viewport-shadow" />
      </svg>
      <div className="minimap-context-strip">
        <span>{areas.length} areas</span>
        <span>{intersections.length} intersections</span>
        <span>{roads.length} roads</span>
        <span>{vehicles.length} vehicles</span>
      </div>
      <p className="minimap-caption">Click to re-center the main map.</p>
    </section>
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

function intersectionKindToken(kind: string): string {
  return kind.trim().toLowerCase().replace(/[^a-z0-9]+/gu, "-");
}

function pointsToMinimapPath(
  points: readonly (readonly [number, number])[],
  bounds: LiveBundleViewModel["map"]["bounds"],
): string {
  if (points.length < 2) {
    return "";
  }

  const scaleX = 220 / bounds.width;
  const scaleY = 152 / bounds.height;
  const [first, ...rest] = points;
  const commands = [`M ${(first[0] - bounds.minX) * scaleX} ${(first[1] - bounds.minY) * scaleY}`];
  for (const point of rest) {
    commands.push(`L ${(point[0] - bounds.minX) * scaleX} ${(point[1] - bounds.minY) * scaleY}`);
  }
  return commands.join(" ");
}
