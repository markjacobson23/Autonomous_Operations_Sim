import type { Dispatch, MouseEvent, Ref, RefObject, SetStateAction } from "react";

import {
  buildRoutePreviewPoints,
  clientPointToScene,
  computeSceneBounds,
  describeSelectedTarget,
  findEdgeById,
  findNodePosition,
  findVehicleById,
  formatHeadingDegrees,
  formatMeters,
  formatMaybeNumber,
  formatSpeedPerSecond,
  maxMotionTime,
  spacingEnvelopeFromVehicle,
  renderVehicleEnvelope,
  renderVehicleGlyph,
  sampleDisplayedVehicles,
  sampleTrafficSnapshot,
  scaleX,
  scaleY,
  toPointString,
  toScaledPointString,
  toSmoothPathString,
  trafficRoadPressureScore,
  vehiclePresentationBadge,
  type DisplayedVehicle,
} from "../viewModel";
import { PanelHeader } from "./shared/PanelHeader";
import type {
  AreaPayload,
  Bounds,
  BundlePayload,
  HoverTarget,
  LayerState,
  Position3,
  RouteDestinationMarker,
  RoutePreviewPayload,
  SelectedTarget,
  TrafficRoadStatePayload,
  ViewportState,
} from "../types";

type SceneViewportProps = {
  bundle: BundlePayload | null;
  motionClockS: number;
  viewport: ViewportState;
  layers: LayerState;
  selectedTarget: SelectedTarget | null;
  selectedVehicleIds: number[];
  editorEnabled: boolean;
  hoverTarget: HoverTarget | null;
  setHoverTarget: Dispatch<SetStateAction<HoverTarget | null>>;
  sceneRef: RefObject<SVGSVGElement | null>;
  minimapRef: RefObject<SVGSVGElement | null>;
  onPan: (deltaX: number, deltaY: number) => void;
  onZoom: (factor: number) => void;
  onFit: () => void;
  onFocusSelected: () => void;
  onToggleLayer: (layer: keyof LayerState) => void;
  onSelectVehicle: (vehicleId: number | undefined, options?: { additive?: boolean }) => void;
  onSelectRoad: (roadId: string | undefined) => void;
  onSelectArea: (areaId: string | undefined) => void;
  onSelectQueue: (roadId: string | undefined) => void;
  onSelectHazard: (edgeId: number | undefined) => void;
  onMinimapClick: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseMove: (event: MouseEvent<SVGSVGElement>) => void;
  onSceneMouseUp: () => void;
  onSceneMouseLeave: () => void;
  onBeginNodeDrag: (event: MouseEvent<SVGCircleElement>, node: { node_id?: number; position?: Position3 }) => void;
  onBeginRoadPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    roadId: string,
    pointIndex: number,
    z: number,
  ) => void;
  onBeginAreaPointDrag: (
    event: MouseEvent<SVGCircleElement>,
    areaId: string,
    pointIndex: number,
    z: number,
  ) => void;
};

export function SceneViewport({
  bundle,
  motionClockS,
  viewport,
  layers,
  selectedTarget,
  selectedVehicleIds,
  editorEnabled,
  hoverTarget,
  setHoverTarget,
  sceneRef,
  minimapRef,
  onPan,
  onZoom,
  onFit,
  onFocusSelected,
  onToggleLayer,
  onSelectVehicle,
  onSelectRoad,
  onSelectArea,
  onSelectQueue,
  onSelectHazard,
  onMinimapClick,
  onSceneMouseMove,
  onSceneMouseUp,
  onSceneMouseLeave,
  onBeginNodeDrag,
  onBeginRoadPointDrag,
  onBeginAreaPointDrag,
}: SceneViewportProps): JSX.Element {
  const bounds = computeSceneBounds(bundle);
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const trafficRoadById = new Map(
    trafficRoadStates
      .filter((state) => state.road_id)
      .map((state) => [state.road_id as string, state]),
  );
  const trafficRoadStatesRanked = [...trafficRoadStates].sort(
    (left, right) =>
      trafficRoadPressureScore(right) - trafficRoadPressureScore(left) ||
      (left.road_id ?? "").localeCompare(right.road_id ?? ""),
  );
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle"
      ? selectedTarget.vehicleId
      : selectedVehicleIds[0] ??
        bundle?.command_center?.vehicle_inspections?.[0]?.vehicle_id ??
        null;
  const selectedVehicle = findVehicleById(bundle, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? (bundle?.command_center?.vehicle_inspections ?? []).find(
        (inspection) => inspection.vehicle_id === selectedVehicleId,
      ) ?? null
    : null;
  const selectedRoad =
    selectedTarget?.kind === "road"
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedArea =
    selectedTarget?.kind === "area"
      ? (bundle?.render_geometry?.areas ?? []).find(
          (area) => area.area_id === selectedTarget.areaId,
        ) ?? null
      : null;
  const selectedQueueRecord =
    selectedTarget?.kind === "queue"
      ? (bundle?.traffic_baseline?.queue_records ?? []).find(
          (record) => record.road_id === selectedTarget.roadId,
        ) ?? null
      : null;
  const selectedHazardEdge =
    selectedTarget?.kind === "hazard"
      ? findEdgeById(bundle?.map_surface?.edges ?? [], selectedTarget.edgeId)
      : null;
  const blockedEdgeIds = [...(bundle?.snapshot?.blocked_edge_ids ?? [])].sort(
    (left, right) => left - right,
  );
  const routePreviews = bundle?.command_center?.route_previews ?? [];
  const selectedRoutePreviewRoadIds = new Set(
    (bundle?.render_geometry?.roads ?? [])
      .filter((road) =>
        routePreviews.some(
          (preview) =>
            selectedVehicleIds.includes(preview.vehicle_id ?? -1) &&
            (preview.edge_ids ?? []).some((edgeId) => (road.edge_ids ?? []).includes(edgeId)),
        ),
      )
      .map((road) => road.road_id)
      .filter((roadId): roadId is string => Boolean(roadId)),
  );
  const routeDestinationMarkers = [...routePreviews.reduce((markers, preview) => {
    const destinationNodeId = preview.destination_node_id;
    if (destinationNodeId === undefined) {
      return markers;
    }
    const position = findNodePosition(bundle?.map_surface?.nodes ?? [], destinationNodeId);
    if (!position) {
      return markers;
    }
    const selected = routePreviews[0]?.vehicle_id !== undefined
      ? routePreviews[0].vehicle_id === preview.vehicle_id
      : false;
    const existingMarker = markers.get(destinationNodeId);
    if (!existingMarker || (!existingMarker.selected && selected)) {
      markers.set(destinationNodeId, {
        destinationNodeId,
        position,
        selected,
        previewVehicleId: preview.vehicle_id,
      });
    }
    return markers;
  }, new Map<number, RouteDestinationMarker>()).values()];
  const selectedRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === selectedVehicleId) ??
    routePreviews[0] ??
    null;
  const selectedVehicleInspections = (bundle?.command_center?.vehicle_inspections ?? []).filter(
    (inspection) => selectedVehicleIds.includes(inspection.vehicle_id ?? -1),
  );
  const selectedFleetVehicles = selectedVehicleIds
    .map(
      (vehicleId) =>
        displayedVehicles.find((vehicle) => vehicle.vehicle_id === vehicleId) ??
        findVehicleById(bundle, vehicleId),
    )
    .filter(
      (
        vehicle,
      ): vehicle is DisplayedVehicle => vehicle !== null,
    );
  const selectedFleetPrimaryVehicle =
    selectedFleetVehicles[0] ?? displayedVehicles.find((vehicle) => vehicle.vehicle_id === selectedVehicleId) ?? selectedVehicle ?? null;
  const selectedFleetPrimaryVehicleId = selectedFleetPrimaryVehicle?.vehicle_id ?? null;
  const selectedFleetPrimaryInspection =
    selectedFleetPrimaryVehicleId !== null
      ? selectedVehicleInspections.find(
          (inspection) => inspection.vehicle_id === selectedFleetPrimaryVehicleId,
        ) ?? selectedInspection
      : selectedInspection;
  const selectedRoutePreviewRoadIdsLabel =
    selectedRoutePreviewRoadIds.size > 0
      ? Array.from(selectedRoutePreviewRoadIds).join(", ")
      : "none";

  const minimapRect = {
    x: ((viewport.x - bounds.minX) / bounds.width) * 100,
    y: ((viewport.y - bounds.minY) / bounds.height) * 100,
    width: (viewport.width / bounds.width) * 100,
    height: (viewport.height / bounds.height) * 100,
  };
  const minimapViewportCoverage = `${Math.max(1, Math.round((viewport.width / bounds.width) * 100))}% wide · ${Math.max(
    1,
    Math.round((viewport.height / bounds.height) * 100),
  )}% tall`;
  const minimapSelectedVehicleLabel =
    selectedVehicle !== null
      ? `Selected ${selectedVehicle.display_name ?? selectedVehicle.role_label ?? vehiclePresentationBadge(selectedVehicle)}`
      : selectedVehicleIds.length > 0
        ? `Fleet ${selectedVehicleIds.length} selected`
        : "No selected vehicle yet";
  const minimapBlockedContextLabel =
    selectedTarget?.kind === "hazard"
      ? `Blocked edge ${selectedTarget.edgeId}`
      : blockedEdgeIds.length > 0
        ? `${blockedEdgeIds.length} blocked edge${blockedEdgeIds.length === 1 ? "" : "s"}`
        : "No blocked edges yet";
  const operateSelectedVehicleSummary =
    selectedVehicle !== null
      ? `${selectedVehicle.display_name ?? selectedVehicle.role_label ?? vehiclePresentationBadge(selectedVehicle)} · ${
          selectedInspection?.operational_state ??
          selectedVehicle.operational_state ??
          "state unknown"
        }`
      : selectedVehicleIds.length > 0
        ? `Fleet selection active · ${selectedVehicleIds.length} vehicle(s)`
        : "No vehicle selected yet";
  const operateSelectedContextSummary =
    selectedInspection !== null
      ? `Node ${formatMaybeNumber(selectedInspection.current_node_id ?? null)} · ETA ${formatMaybeNumber(selectedInspection.eta_s ?? null)}s · ${selectedInspection.current_job_id ?? "no job"}`
      : "Select a vehicle on the map or from the roster to open inspection details.";
  const operateSelectedTargetSummary = describeSelectedTarget(selectedTarget, selectedVehicleId);
  const operateRoutePreviewSummary =
    selectedRoutePreview !== null
      ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id ?? null)} · Node ${formatMaybeNumber(selectedRoutePreview.destination_node_id ?? null)} · ${
          selectedRoutePreview.is_actionable ? "actionable" : "pending"
        }`
      : "Waiting for route preview";
  const operateRoutePreviewDetail =
    selectedRoutePreview !== null
      ? `${selectedRoutePreview.reason ?? "No reason provided"}${
          selectedRoutePreview.total_distance !== undefined
            ? ` · ${formatMeters(selectedRoutePreview.total_distance)}`
            : ""
        }`
      : "Choose a vehicle and destination, then preview the route to populate node, edge, and distance details.";
  const selectedRoadTraffic =
    selectedRoad?.road_id !== undefined
      ? trafficRoadById.get(selectedRoad.road_id) ?? null
      : null;
  const selectedQueueTraffic =
    typeof selectedQueueRecord?.road_id === "string"
      ? trafficRoadById.get(selectedQueueRecord.road_id) ?? null
      : null;
  const trafficFocusRoadState =
    selectedRoadTraffic ?? trafficRoadStatesRanked[0] ?? null;
  const trafficFocusRoad =
    trafficFocusRoadState?.road_id !== undefined
      ? (bundle?.render_geometry?.roads ?? []).find(
          (road) => road.road_id === trafficFocusRoadState.road_id,
        ) ?? selectedRoad
      : selectedRoad;
  const trafficMonitoringRoadStates = (() => {
    const states: TrafficRoadStatePayload[] = [];
    const seenRoadIds = new Set<string>();
    if (trafficFocusRoadState?.road_id) {
      states.push(trafficFocusRoadState);
      seenRoadIds.add(trafficFocusRoadState.road_id);
    }
    for (const roadState of trafficRoadStatesRanked) {
      if (!roadState.road_id || seenRoadIds.has(roadState.road_id)) {
        continue;
      }
      states.push(roadState);
      seenRoadIds.add(roadState.road_id);
      if (states.length >= 5) {
        break;
      }
    }
    return states;
  })();
  const trafficQueueRecords = [...(bundle?.traffic_baseline?.queue_records ?? [])].sort(
    (left, right) => {
      const leftRoadState =
        typeof left.road_id === "string" ? trafficRoadById.get(left.road_id) ?? null : null;
      const rightRoadState =
        typeof right.road_id === "string" ? trafficRoadById.get(right.road_id) ?? null : null;
      const leftVehicleCount =
        left.vehicle_ids?.length ?? (left.vehicle_id !== undefined ? 1 : 0);
      const rightVehicleCount =
        right.vehicle_ids?.length ?? (right.vehicle_id !== undefined ? 1 : 0);
      return (
        trafficRoadPressureScore(rightRoadState) +
        rightVehicleCount * 10 -
        (trafficRoadPressureScore(leftRoadState) + leftVehicleCount * 10) ||
        (left.road_id ?? "").localeCompare(right.road_id ?? "") ||
        (left.node_id ?? 0) - (right.node_id ?? 0)
      );
    },
  );
  const selectedFleetStateCounts = selectedFleetVehicles.reduce<Record<string, number>>(
    (counts, vehicle) => {
      const operationalState = (vehicle.operational_state ?? "unknown").split("_").join(" ");
      counts[operationalState] = (counts[operationalState] ?? 0) + 1;
      return counts;
    },
    {},
  );
  const selectedFleetStateEntries = Object.entries(selectedFleetStateCounts).sort(
    (left, right) => right[1] - left[1] || left[0].localeCompare(right[0]),
  );
  const selectedFleetStateSummary =
    selectedFleetStateEntries.length > 0
      ? selectedFleetStateEntries
          .slice(0, 3)
          .map(([state, count]) => `${count} ${state}`)
          .join(" · ")
      : "No vehicles selected yet";
  const selectedFleetRoutePreview =
    routePreviews.find((preview) => preview.vehicle_id === selectedFleetPrimaryVehicleId) ??
    routePreviews.find((preview) => selectedVehicleIds.includes(preview.vehicle_id ?? -1)) ??
    null;
  const selectedFleetRouteSummary = selectedFleetRoutePreview
    ? `Node ${formatMaybeNumber(selectedFleetRoutePreview.destination_node_id ?? null)}${
        selectedFleetRoutePreview.total_distance !== undefined
          ? ` · ${formatMeters(selectedFleetRoutePreview.total_distance)}`
          : ""
      }`
    : "Waiting for route preview";
  const selectedFleetRouteDetail = selectedFleetRoutePreview
    ? `${selectedFleetRoutePreview.is_actionable ? "Actionable" : "Pending"}${
        selectedFleetRoutePreview.reason ? ` · ${selectedFleetRoutePreview.reason}` : ""
      }`
    : selectedFleetPrimaryInspection?.route_ahead_node_ids?.length
      ? `Inspection sees ${selectedFleetPrimaryInspection.route_ahead_node_ids.length} upcoming node(s)`
      : "Select a vehicle first to surface route and inspection context.";

  const minimapBlockedLabel = selectedTarget?.kind === "hazard"
    ? `Blocked edge ${selectedTarget.edgeId}`
    : blockedEdgeIds.length > 0
      ? `${blockedEdgeIds.length} blocked edge${blockedEdgeIds.length === 1 ? "" : "s"}`
      : "No blocked edges yet";

  function stopDragging(): void {
    setHoverTarget(hoverTarget ? null : null);
  }

  return (
    <section className="stage panel" aria-labelledby="scene-title">
      <PanelHeader
        eyebrow="Scene Region"
        title="Operations Viewport"
        titleId="scene-title"
        lede="Scene layers, route previews, and live vehicle state stay layered into one operator view."
        meta={
          <div className="status-stack">
            <span className="status-pill">Camera controls active</span>
            <span className="status-pill secondary">Selection active</span>
            <span className="status-pill accent">Layer toggles active</span>
          </div>
        }
      />

      <div className="scene-toolbar" aria-label="Scene toolbar">
        <div className="tool-group">
          <button className="scene-button" type="button" onClick={() => onPan(0, -0.18)}>
            Pan Up
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(-0.18, 0)}>
            Pan Left
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(0.18, 0)}>
            Pan Right
          </button>
          <button className="scene-button" type="button" onClick={() => onPan(0, 0.18)}>
            Pan Down
          </button>
        </div>
        <div className="tool-group">
          <button className="scene-button" type="button" onClick={() => onZoom(0.82)}>
            Zoom In
          </button>
          <button className="scene-button" type="button" onClick={() => onZoom(1.2)}>
            Zoom Out
          </button>
          <button className="scene-button" type="button" onClick={onFit}>
            Fit Scene
          </button>
          <button
            className="scene-button"
            type="button"
            onClick={onFocusSelected}
            disabled={selectedVehicle === null}
          >
            Focus Selected
          </button>
        </div>
      </div>

      <div className="layer-toolbar" aria-label="Layer toggles">
        {Object.entries(layers).map(([layer, enabled]) => (
          <button
            key={layer}
            className={`layer-chip ${enabled ? "layer-chip-active" : ""}`}
            type="button"
            onClick={() => onToggleLayer(layer as keyof LayerState)}
          >
            {layer}
          </button>
        ))}
      </div>

      <div className="stage-grid">
        <div className="stage-canvas-frame">
          <div className="scene-rim scene-rim-top" aria-hidden="true" />
          <div className="scene-rim scene-rim-bottom" aria-hidden="true" />
          <svg
            ref={sceneRef as unknown as Ref<SVGSVGElement>}
            className="stage-canvas"
            viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
            aria-label="Simulation scene graph"
            onMouseLeave={() => {
              setHoverTarget(null);
              stopDragging();
              onSceneMouseLeave();
            }}
            onMouseMove={onSceneMouseMove}
            onMouseUp={onSceneMouseUp}
          >
            <rect
              x={bounds.minX}
              y={bounds.minY}
              width={bounds.width}
              height={bounds.height}
              className="scene-backdrop"
            />

            {layers.areas &&
              (bundle?.render_geometry?.areas ?? []).map((area, index) => (
                <polygon
                  key={area.area_id ?? `area-${index}`}
                  points={toPointString(area.polygon)}
                  className={`scene-area scene-area-${area.kind ?? "generic"} ${
                    selectedTarget?.kind === "area" && selectedTarget.areaId === area.area_id
                      ? "selected"
                      : ""
                  }`}
                  onClick={() => onSelectArea(area.area_id)}
                  onMouseEnter={() =>
                    setHoverTarget({
                      label: area.label ?? area.area_id ?? "zone",
                      detail: area.kind ?? "zone",
                    })
                  }
                />
              ))}

            {layers.roads &&
              (bundle?.render_geometry?.roads ?? []).map((road, index) => {
                const roadPath = toSmoothPathString(road.centerline);
                if (!roadPath) {
                  return null;
                }
                const roadWidth = Math.min(Math.max((road.width_m ?? 1.4) * 0.34, 0.4), 1.72);
                const roadTraffic = trafficRoadById.get(road.road_id ?? "");
                return (
                  <g key={road.road_id ?? `road-${index}`}>
                    <path
                      d={roadPath}
                      className={`scene-road-heatmap scene-road-heatmap-${
                        roadTraffic?.congestion_level ?? "free"
                      }`}
                      strokeWidth={roadWidth + 0.34}
                      style={{
                        opacity: Math.max(0.05, (roadTraffic?.congestion_intensity ?? 0) * 0.38),
                      }}
                      aria-hidden="true"
                    />
                    <path
                      d={roadPath}
                      className={`scene-road scene-road-${road.road_class ?? "connector"} ${
                        selectedTarget?.kind === "road" && selectedTarget.roadId === road.road_id
                          ? "selected"
                          : ""
                      }`}
                      strokeWidth={roadWidth}
                      onClick={() => onSelectRoad(road.road_id)}
                      onMouseEnter={() => {
                        setHoverTarget({
                          label: road.road_id ?? "road",
                          detail: roadTraffic
                            ? `${road.directionality ?? "unknown"} · ${
                                road.lane_count ?? 0
                              } lane(s) · ${roadTraffic.congestion_level} · ${
                                roadTraffic.queued_vehicle_ids?.length ?? 0
                              } queued`
                            : `${road.directionality ?? "unknown"} · ${
                                road.lane_count ?? 0
                              } lane(s)`,
                        });
                      }}
                    />
                  </g>
                );
              })}

            {layers.intersections &&
              (bundle?.render_geometry?.intersections ?? []).map((intersection, index) => {
                const controlPoint = (bundle?.traffic_baseline?.control_points ?? []).find(
                  (point) => point.node_id === intersection.node_id,
                );
                const intersectionPath = toSmoothPathString(intersection.polygon, true);
                if (!intersectionPath) {
                  return null;
                }
                return (
                  <path
                    key={intersection.intersection_id ?? `intersection-${index}`}
                    d={intersectionPath}
                    className="scene-intersection"
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: intersection.intersection_id ?? "intersection",
                        detail: controlPoint
                          ? `${controlPoint.control_type} · ${
                              controlPoint.controlled_road_ids?.length ?? 0
                            } road(s) · ${
                              controlPoint.stop_line_ids?.length ?? 0
                            } stop line(s)`
                          : intersection.intersection_type ?? "intersection",
                      })
                    }
                  />
                );
              })}

            {layers.roads &&
              (bundle?.render_geometry?.lanes ?? []).map((lane, index) => (
                <polyline
                  key={lane.lane_id ?? `lane-${index}`}
                  points={toPointString(lane.centerline)}
                  className={`scene-lane scene-lane-${lane.directionality ?? "forward"}`}
                  onMouseEnter={() =>
                    setHoverTarget({
                      label: lane.lane_id ?? "lane",
                      detail: `${lane.lane_role ?? "travel"} · ${lane.directionality ?? "forward"}`,
                    })
                  }
                />
              ))}

            {layers.roads &&
              (bundle?.render_geometry?.turn_connectors ?? []).map((connector, index) => (
                <polyline
                  key={connector.connector_id ?? `connector-${index}`}
                  points={toPointString(connector.centerline)}
                  className="scene-turn-connector"
                  onMouseEnter={() =>
                    setHoverTarget({
                      label: connector.connector_id ?? "connector",
                      detail: connector.connector_type ?? "turn connector",
                    })
                  }
                />
              ))}

            {layers.roads &&
              (bundle?.render_geometry?.stop_lines ?? []).map((stopLine, index) => (
                <line
                  key={stopLine.stop_line_id ?? `stop-line-${index}`}
                  x1={stopLine.segment?.[0]?.[0] ?? 0}
                  y1={stopLine.segment?.[0]?.[1] ?? 0}
                  x2={stopLine.segment?.[1]?.[0] ?? 0}
                  y2={stopLine.segment?.[1]?.[1] ?? 0}
                  className="scene-stop-line"
                  onMouseEnter={() =>
                    setHoverTarget({
                      label: stopLine.stop_line_id ?? "stop line",
                      detail: stopLine.control_kind ?? "stop control",
                    })
                  }
                />
              ))}

            {layers.roads &&
              (bundle?.render_geometry?.merge_zones ?? []).map((zone, index) => (
                <polygon
                  key={zone.merge_zone_id ?? `merge-zone-${index}`}
                  points={toPointString(zone.polygon)}
                  className="scene-merge-zone"
                  onMouseEnter={() =>
                    setHoverTarget({
                      label: zone.merge_zone_id ?? "merge zone",
                      detail: `${zone.kind ?? "merge"} · ${(zone.lane_ids ?? []).length} lane(s)`,
                    })
                  }
                />
              ))}

            {layers.reservations &&
              (bundle?.traffic_baseline?.queue_records ?? []).map((record, queueIndex) => {
                const road = (bundle?.render_geometry?.roads ?? []).find(
                  (entry) => entry.road_id === record.road_id,
                );
                const roadTraffic =
                  typeof record.road_id === "string"
                    ? trafficRoadById.get(record.road_id) ?? null
                    : null;
                const roadPath = toSmoothPathString(road?.centerline);
                if (!roadPath) {
                  return null;
                }
                const roadWidth = Math.min(Math.max((road?.width_m ?? 1.4) * 0.34, 0.4), 1.72);
                return (
                  <path
                    key={`reservation-${queueIndex}`}
                    d={roadPath}
                    className={`scene-reservation scene-queue-overlay ${
                      selectedTarget?.kind === "queue" &&
                      selectedTarget.roadId === record.road_id
                        ? "selected"
                        : selectedRoutePreviewRoadIds.has(record.road_id ?? "")
                          ? "selected preview"
                          : ""
                    }`}
                    strokeWidth={roadWidth + 0.42}
                    onClick={() => onSelectQueue(record.road_id ?? undefined)}
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: `Queue ${record.road_id ?? "road"}`,
                        detail: `${roadTraffic?.queued_vehicle_ids?.length ?? 0} vehicle(s) queued`,
                      })
                    }
                  />
                );
              })}

            {layers.vehicles &&
              displayedVehicles.map((vehicle, vehicleIndex) => {
                const position = vehicle.position ?? [0, 0, 0];
                const isSelected = selectedVehicleIds.includes(vehicle.vehicle_id ?? -1);
                const vehicleSpeed = vehicle.speed ?? 0;
                const isMoving = vehicleSpeed > 0.05 || vehicle.operational_state === "moving";
                const isRouteTracked = selectedRoutePreview?.vehicle_id === vehicle.vehicle_id;
                const routeContextLabel = isRouteTracked
                  ? `Route to node ${formatMaybeNumber(selectedRoutePreview?.destination_node_id ?? null)}`
                  : vehicle.lane_selection_reason ?? null;
                const motionContextLabel =
                  isSelected && (isMoving || routeContextLabel !== null)
                    ? `${formatHeadingDegrees(vehicle.heading_rad ?? null)} · ${formatSpeedPerSecond(
                        vehicleSpeed,
                      )}${routeContextLabel !== null ? ` · ${routeContextLabel}` : ""}`
                    : null;
                const vehicleLabel = `${vehiclePresentationBadge(vehicle)} ${vehicle.vehicle_id ?? vehicleIndex}`;
                const labelWidth = Math.max(1.12, vehicleLabel.length * 0.22 + 0.34);
                const labelY = position[1] - Math.max((vehicle.body_length_m ?? 1.12) * 0.72, 1.08);
                const labelHeight = motionContextLabel ? 0.8 : 0.46;
                const labelTextY = motionContextLabel ? labelY - 0.12 : labelY;
                const labelSecondaryY = labelY + 0.27;
                const selectionEnvelopeLength = Math.max(
                  vehicle.spacing_envelope_m ?? spacingEnvelopeFromVehicle(vehicle),
                  0.9,
                );
                const selectionEnvelopeWidth = Math.max((vehicle.body_width_m ?? 0.62) * 1.9, 1);
                return (
                  <g
                    key={vehicle.vehicle_id ?? `vehicle-${vehicleIndex}`}
                    className={[
                      "scene-vehicle",
                      isSelected ? "selected" : "",
                      isMoving ? "moving" : "settled",
                      isRouteTracked ? "route-following" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={(event) =>
                      onSelectVehicle(vehicle.vehicle_id, {
                        additive: event.shiftKey || event.metaKey || event.ctrlKey,
                      })
                    }
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: `Vehicle ${vehicle.vehicle_id ?? vehicleIndex}`,
                        detail: `${vehicle.operational_state ?? "unknown_state"} · ${
                          vehicle.lane_id ?? "lane-unassigned"
                        } · ${formatMeters(vehicle.spacing_envelope_m ?? null)} envelope`,
                      })
                    }
                  >
                    {isSelected ? (
                      <rect
                        x={position[0] - selectionEnvelopeLength * 0.56}
                        y={position[1] - selectionEnvelopeWidth * 0.5}
                        width={selectionEnvelopeLength * 1.12}
                        height={selectionEnvelopeWidth}
                        rx={0.28}
                        className="vehicle-selection-ring"
                      />
                    ) : null}
                    <g
                      transform={`translate(${position[0]} ${position[1]}) rotate(${((vehicle.heading_rad ?? 0) * 180) / Math.PI})`}
                    >
                      {isMoving ? (
                        <line
                          x1={-Math.max((vehicle.body_length_m ?? 1.12) * 0.42, 0.42)}
                          y1={0}
                          x2={Math.max((vehicle.body_length_m ?? 1.12) * 0.24, 0.26)}
                          y2={0}
                          className="vehicle-motion-trail"
                        />
                      ) : null}
                      {renderVehicleEnvelope(vehicle)}
                      {renderVehicleGlyph(vehicle)}
                    </g>
                    <g className="vehicle-label">
                      <rect
                        x={position[0] - labelWidth * 0.5}
                        y={labelY - 0.24}
                        width={labelWidth}
                        height={labelHeight}
                        rx={0.16}
                        className="vehicle-label-bg"
                      />
                      <text x={position[0]} y={labelTextY} className="vehicle-label-text">
                        {vehicleLabel}
                      </text>
                      {motionContextLabel !== null ? (
                        <text x={position[0]} y={labelSecondaryY} className="vehicle-label-secondary">
                          {motionContextLabel}
                        </text>
                      ) : null}
                    </g>
                  </g>
                );
              })}

            {layers.routes &&
              routeDestinationMarkers.map((marker) => (
                <g
                  key={`route-destination-${marker.destinationNodeId}`}
                  className={`scene-destination scene-route-endpoint ${
                    marker.selected ? "selected" : ""
                  }`}
                  transform={`translate(${marker.position[0]} ${marker.position[1]})`}
                >
                  <circle r={marker.selected ? 1.08 : 0.86} className="scene-destination-threshold" />
                  <circle r={marker.selected ? 0.38 : 0.3} className="scene-destination-core" />
                </g>
              ))}

            {layers.routes &&
              routePreviews.map((preview, previewIndex) => {
                const routePoints = buildRoutePreviewPoints(
                  preview,
                  bundle?.map_surface?.nodes ?? [],
                );
                const routePath = toSmoothPathString(routePoints);
                if (!routePath) {
                  return null;
                }
                return (
                  <path
                    key={`route-preview-${previewIndex}`}
                    d={routePath}
                    className={`scene-route-preview ${
                      preview.vehicle_id === selectedVehicleId ? "selected" : ""
                    }`}
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: `Route preview V${preview.vehicle_id ?? "?"}`,
                        detail: preview.reason ?? "actionable preview",
                      })
                    }
                  />
                );
              })}

            {layers.hazards &&
              blockedEdgeIds.map((edgeId, blockedIndex) => {
                const edge = findEdgeById(bundle?.map_surface?.edges ?? [], edgeId);
                const start = edge
                  ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                  : null;
                const end = edge
                  ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                  : null;
                if (!start || !end) {
                  return null;
                }
                return (
                  <line
                    key={`hazard-${blockedIndex}`}
                    x1={start[0]}
                    y1={start[1]}
                    x2={end[0]}
                    y2={end[1]}
                    className={`scene-hazard ${
                      selectedTarget?.kind === "hazard" &&
                      selectedTarget.edgeId === edgeId
                        ? "selected"
                        : ""
                    }`}
                    onClick={() => onSelectHazard(edgeId)}
                    onMouseEnter={() =>
                      setHoverTarget({
                        label: `Blocked edge ${edgeId}`,
                        detail: "Conflict / hazard overlay",
                      })
                    }
                  />
                );
              })}

            {editorEnabled &&
              (bundle?.map_surface?.nodes ?? []).map((node, index) => {
                if (node.node_id === undefined || !node.position) {
                  return null;
                }
                return (
                  <circle
                    key={node.node_id ?? `node-handle-${index}`}
                    cx={node.position[0]}
                    cy={node.position[1]}
                    r={0.32}
                    className="scene-edit-handle node"
                    onMouseDown={(event) => onBeginNodeDrag(event, node)}
                  />
                );
              })}

            {editorEnabled &&
              selectedRoad?.centerline?.map((point, index) => (
                <circle
                  key={`${selectedRoad.road_id ?? "road"}-point-${index}`}
                  cx={point[0]}
                  cy={point[1]}
                  r={0.3}
                  className="scene-edit-handle road"
                  onMouseDown={(event) =>
                    onBeginRoadPointDrag(
                      event,
                      selectedRoad.road_id ?? "road",
                      index,
                      point[2] ?? 0,
                    )
                  }
                />
              ))}

            {editorEnabled &&
              selectedArea?.polygon?.map((point, index) => (
                <circle
                  key={`${selectedArea.area_id ?? "area"}-point-${index}`}
                  cx={point[0]}
                  cy={point[1]}
                  r={0.3}
                  className="scene-edit-handle area"
                  onMouseDown={(event) =>
                    onBeginAreaPointDrag(
                      event,
                      selectedArea.area_id ?? "area",
                      index,
                      point[2] ?? 0,
                    )
                  }
                />
              ))}
          </svg>

          <div className="scene-overlay-shell">
            <div className="scene-overlay-primary">
              <div className="scene-legend">
                <span className="legend-item">
                  <span className="legend-swatch road" />
                  Roads
                </span>
                <span className="legend-item">
                  <span className="legend-swatch traffic" />
                  Traffic heatmap
                </span>
                <span className="legend-item">
                  <span className="legend-swatch vehicle" />
                  Vehicles
                </span>
                <span className="legend-item">
                  <span className="legend-swatch hazard" />
                  Hazards
                </span>
                <span className="legend-item">
                  <span className="legend-swatch handle" />
                  Edit handles
                </span>
              </div>
              <div className="focus-card">
                <strong>Stop lines and yield controls are visible</strong>
                <p>
                  Traffic snapshots now carry control-state overlays and inspection reasons, so
                  dense corridors stay legible while still showing why vehicles are waiting.
                </p>
              </div>
            </div>
            {hoverTarget ? (
              <div className="scene-overlay-secondary">
                <div className="hover-card" aria-live="polite">
                  <strong>{hoverTarget.label}</strong>
                  <p>{hoverTarget.detail}</p>
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <aside className="overview-panel">
          <div className="overview-card operate-route-planning">
            <p className="eyebrow">Route Planning</p>
            <h3>Primary Operator Workflow</h3>
            <div className="selection-strip">
              <span className="selection-pill">
                Fleet selection: {selectedVehicleIds.length} vehicle(s)
              </span>
              <span className="selection-pill">
                Route preview:{" "}
                {selectedRoutePreview?.vehicle_id !== undefined
                  ? `V${formatMaybeNumber(selectedRoutePreview.vehicle_id)}`
                  : "waiting for preview"}
              </span>
              <span className="selection-pill">
                Destination node:{" "}
                {selectedRoutePreview?.destination_node_id !== undefined
                  ? formatMaybeNumber(selectedRoutePreview.destination_node_id)
                  : "not set yet"}
              </span>
              <span className="selection-pill">Current target: {operateSelectedTargetSummary}</span>
            </div>
            <p className="operate-route-hint">
              Select a vehicle in the scene, confirm the route preview, then use the primary action
              to commit or refine the destination without leaving the map.
            </p>
            <div className="operate-context-grid">
              <section className="operate-context-card">
                <p className="operate-card-label">Selected Context</p>
                <strong>{operateSelectedVehicleSummary}</strong>
                <p>{operateSelectedContextSummary}</p>
                <ul className="mini-list">
                  <li>Current target: {operateSelectedTargetSummary}</li>
                  <li>
                    Selection source:{" "}
                    {selectedVehicleIds.length > 1
                      ? `${selectedVehicleIds.length} vehicles`
                      : "single vehicle focus"}
                  </li>
                </ul>
              </section>
              <div className="route-preview-summary operate-context-card">
                <div className="preview-badge">
                  <span className="preview-label">Route Preview</span>
                  <strong>{operateRoutePreviewSummary}</strong>
                </div>
                <p className="operate-route-preview-detail">{operateRoutePreviewDetail}</p>
                <ul className="mini-list">
                  <li>Actionable: {selectedRoutePreview?.is_actionable ? "yes" : "no"}</li>
                  <li>Reason: {selectedRoutePreview?.reason ?? "none"}</li>
                  <li>Distance: {formatMeters(selectedRoutePreview?.total_distance ?? null)}</li>
                  <li>Edges: {(selectedRoutePreview?.edge_ids ?? []).join(", ") || "none"}</li>
                  <li>Nodes: {(selectedRoutePreview?.node_ids ?? []).join(" → ") || "none"}</li>
                </ul>
              </div>
            </div>
            <div className="overview-card overview-card-minimap">
              <p className="eyebrow">Overview</p>
              <h3>Minimap Navigation</h3>
              <div className="minimap-card-head">
                <div className="minimap-card-copy">
                  <span className="minimap-card-label">Scene camera</span>
                  <p className="minimap-card-summary">{minimapViewportCoverage}</p>
                </div>
                <span className="minimap-orientation-pill">North-up</span>
              </div>
              <div className="minimap-context-strip" aria-label="Minimap context">
                <span className="selection-pill minimap-context-pill">{minimapSelectedVehicleLabel}</span>
                <span className="selection-pill minimap-context-pill">Viewport window</span>
                <span
                  className={`selection-pill minimap-context-pill ${
                    blockedEdgeIds.length > 0 || selectedTarget?.kind === "hazard"
                      ? "minimap-context-pill-alert"
                      : ""
                  }`}
                >
                  {minimapBlockedContextLabel}
                </span>
              </div>
          <svg
            ref={minimapRef as unknown as Ref<SVGSVGElement>}
                className="minimap"
                viewBox={`0 0 100 100`}
                aria-label="Scene minimap"
                aria-describedby="minimap-caption"
                onClick={onMinimapClick}
              >
                <rect x={0} y={0} width={100} height={100} className="minimap-bg" />
                {(bundle?.render_geometry?.roads ?? []).map((road, index) => (
                  <polyline
                    key={road.road_id ?? `minimap-road-${index}`}
                    points={toScaledPointString(road.centerline, bounds)}
                    className="minimap-road"
                  />
                ))}
                {layers.hazards &&
                  blockedEdgeIds.map((edgeId) => {
                    const edge = findEdgeById(bundle?.map_surface?.edges ?? [], edgeId);
                    const start = edge
                      ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.start_node_id)
                      : null;
                    const end = edge
                      ? findNodePosition(bundle?.map_surface?.nodes ?? [], edge.end_node_id)
                      : null;
                    if (!start || !end) {
                      return null;
                    }
                    return (
                      <line
                        key={`minimap-hazard-${edgeId}`}
                        x1={scaleX(start[0], bounds)}
                        y1={scaleY(start[1], bounds)}
                        x2={scaleX(end[0], bounds)}
                        y2={scaleY(end[1], bounds)}
                        className={`minimap-hazard ${
                          selectedTarget?.kind === "hazard" && selectedTarget.edgeId === edgeId
                            ? "selected"
                            : ""
                        }`}
                      />
                    );
                  })}
                {displayedVehicles.map((vehicle, index) => {
                  const isPrimarySelected = vehicle.vehicle_id === selectedVehicleId;
                  const isSelectedFleetVehicle = selectedVehicleIds.includes(vehicle.vehicle_id ?? -1);
                  return (
                    <g
                      key={vehicle.vehicle_id ?? `minimap-vehicle-${index}`}
                      className={`minimap-vehicle ${
                        isPrimarySelected
                          ? "selected"
                          : isSelectedFleetVehicle
                            ? "fleet-selected"
                            : ""
                      }`}
                    >
                      {isPrimarySelected ? (
                        <circle
                          cx={scaleX(vehicle.position?.[0] ?? 0, bounds)}
                          cy={scaleY(vehicle.position?.[1] ?? 0, bounds)}
                          r={3.1}
                          className="minimap-vehicle-halo"
                        />
                      ) : null}
                      <circle
                        cx={scaleX(vehicle.position?.[0] ?? 0, bounds)}
                        cy={scaleY(vehicle.position?.[1] ?? 0, bounds)}
                        r={isPrimarySelected ? 2.05 : isSelectedFleetVehicle ? 1.75 : 1.25}
                        className="minimap-vehicle-core"
                      />
                    </g>
                  );
                })}
                {routeDestinationMarkers.map((marker) => (
                  <g
                    key={`minimap-route-destination-${marker.destinationNodeId}`}
                    className={`minimap-destination ${marker.selected ? "selected" : ""}`}
                  >
                    <circle
                      cx={scaleX(marker.position[0], bounds)}
                      cy={scaleY(marker.position[1], bounds)}
                      r={marker.selected ? 2.0 : 1.55}
                      className="minimap-destination-threshold"
                    />
                    <circle
                      cx={scaleX(marker.position[0], bounds)}
                      cy={scaleY(marker.position[1], bounds)}
                      r={marker.selected ? 0.85 : 0.62}
                      className="minimap-destination-core"
                    />
                  </g>
                ))}
                <rect
                  x={minimapRect.x}
                  y={minimapRect.y}
                  width={minimapRect.width}
                  height={minimapRect.height}
                  rx={1.1}
                  ry={1.1}
                  className="minimap-viewport minimap-viewport-shadow"
                />
                <rect
                  x={minimapRect.x}
                  y={minimapRect.y}
                  width={minimapRect.width}
                  height={minimapRect.height}
                  rx={1.1}
                  ry={1.1}
                  className="minimap-viewport"
                />
              </svg>
              <p id="minimap-caption" className="minimap-caption">
                Click anywhere on the minimap to recenter the main scene. The window mirrors the
                current camera frame.
              </p>
            </div>

            <div className="overview-card">
              <p className="eyebrow">Layer Summary</p>
              <ul className="mini-list">
                <li>
                  Roads: {layers.roads ? "visible" : "hidden"} · Areas: {layers.areas ? "visible" : "hidden"}
                </li>
                <li>
                  Intersections: {layers.intersections ? "visible" : "hidden"} · Vehicles:{" "}
                  {layers.vehicles ? "visible" : "hidden"}
                </li>
                <li>
                  Routes: {layers.routes ? "visible" : "hidden"} · Reservations:{" "}
                  {layers.reservations ? "visible" : "hidden"}
                </li>
                <li>Hazards: {layers.hazards ? "visible" : "hidden"}</li>
                <li>Selection: {operateSelectedTargetSummary}</li>
              </ul>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
