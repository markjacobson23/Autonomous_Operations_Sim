import type { LiveBundleViewModel, Point2 } from "./liveBundle";
import type { FrontendUiState } from "../state/frontendUiState";

export type SelectionTarget =
  | { kind: "vehicle"; vehicleId: number }
  | { kind: "road"; roadId: string }
  | { kind: "area"; areaId: string };

export type SelectionDetail = {
  label: string;
  value: string;
};

export type SelectionPresentation = {
  target: SelectionTarget | null;
  title: string;
  badge: string;
  summary: string;
  context: string;
  details: SelectionDetail[];
  notes: string[];
  focusPoints: Point2[];
};

export function resolveActiveSelectionTarget(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): SelectionTarget | null {
  if (uiState.selection.target !== null) {
    return uiState.selection.target;
  }

  if (uiState.selection.vehicleIds.length > 0) {
    return { kind: "vehicle", vehicleId: uiState.selection.vehicleIds[0] };
  }

  if (bundle.selectedVehicleIds.length > 0) {
    return { kind: "vehicle", vehicleId: bundle.selectedVehicleIds[0] };
  }

  return null;
}

export function resolveSelectionVehicleIds(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): number[] {
  if (uiState.selection.vehicleIds.length > 0) {
    return uniqueNumbers(uiState.selection.vehicleIds);
  }

  if (uiState.selection.target?.kind === "vehicle") {
    return [uiState.selection.target.vehicleId];
  }

  if (uiState.selection.target !== null) {
    return [];
  }

  return uniqueNumbers(bundle.selectedVehicleIds);
}

export function buildSelectionPresentation(
  bundle: LiveBundleViewModel,
  uiState: FrontendUiState,
): SelectionPresentation | null {
  const target = resolveActiveSelectionTarget(bundle, uiState);
  if (target === null) {
    return null;
  }

  switch (target.kind) {
    case "vehicle":
      return buildVehiclePresentation(bundle, target.vehicleId);
    case "road":
      return buildRoadPresentation(bundle, target.roadId);
    case "area":
      return buildAreaPresentation(bundle, target.areaId);
    default:
      return null;
  }
}

export function focusPointsForSelection(
  bundle: LiveBundleViewModel,
  selection: SelectionTarget | null,
): Point2[] {
  if (selection === null) {
    return [];
  }

  switch (selection.kind) {
    case "vehicle": {
      const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === selection.vehicleId);
      return vehicle === undefined ? [] : [vehicle.position];
    }
    case "road": {
      const road = bundle.map.roads.find((entry) => entry.roadId === selection.roadId);
      return road === undefined ? [] : road.centerline;
    }
    case "area": {
      const area = bundle.map.areas.find((entry) => entry.areaId === selection.areaId);
      return area === undefined ? [] : area.polygon;
    }
    default:
      return [];
  }
}

function buildVehiclePresentation(bundle: LiveBundleViewModel, vehicleId: number): SelectionPresentation {
  const vehicle = bundle.map.vehicles.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const inspection = bundle.commandCenter.vehicleInspections.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const routePreview = bundle.commandCenter.routePreviews.find((entry) => entry.vehicleId === vehicleId) ?? null;
  const hasInspection = inspection !== null;
  const hasRoutePreview = routePreview !== null;
  const title = vehicle === null ? `Vehicle ${vehicleId}` : `Vehicle ${vehicle.vehicleId}`;
  const badge = inspection?.operationalState ?? vehicle?.state ?? "unknown";
  const summary =
    hasInspection && inspection.currentTaskType !== null
      ? humanize(inspection.currentTaskType)
      : hasRoutePreview
        ? routePreview.isActionable
          ? `Route preview to node ${routePreview.destinationNodeId}`
          : `Route preview blocked: ${humanize(routePreview.reason ?? "not available")}`
        : "No active route preview.";

  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "State", value: badge },
  ];
  if (hasInspection && inspection.currentTaskType !== null) {
    details.push({ label: "Task", value: humanize(inspection.currentTaskType) });
  }
  if (hasInspection && inspection.currentJobId !== null) {
    details.push({ label: "Job", value: inspection.currentJobId });
  }
  if (hasInspection && inspection.etaSeconds !== null) {
    details.push({ label: "ETA", value: `${inspection.etaSeconds.toFixed(1)}s` });
  }

  const notes = [
    hasInspection && inspection.currentNodeId !== null ? `Node ${inspection.currentNodeId}` : null,
    hasInspection && inspection.waitReason !== null ? `Waiting because of ${humanize(inspection.waitReason)}` : null,
    hasInspection && inspection.trafficControlDetail !== null ? inspection.trafficControlDetail : null,
    hasRoutePreview && routePreview.reason !== null ? `Preview: ${humanize(routePreview.reason)}` : null,
  ].filter((item): item is string => item !== null);

  const context = [
    hasInspection && inspection.currentNodeId !== null ? `Node ${inspection.currentNodeId}` : null,
    hasInspection && inspection.assignedResourceId !== null ? `Resource ${inspection.assignedResourceId}` : null,
    hasInspection && inspection.waitReason !== null ? `Wait ${humanize(inspection.waitReason)}` : null,
  ]
    .filter((item): item is string => item !== null)
    .join(" · ");

  return {
    target: { kind: "vehicle", vehicleId },
    title,
    badge,
    summary,
    context: context.length > 0 ? context : "No extra context available.",
    details,
    notes,
    focusPoints: vehicle === null ? [] : [vehicle.position],
  };
}

function buildRoadPresentation(bundle: LiveBundleViewModel, roadId: string): SelectionPresentation {
  const road = bundle.map.roads.find((entry) => entry.roadId === roadId) ?? null;
  const title = road === null ? `Road ${roadId}` : formatRoadLabel(road);
  const badge = road?.blocked === true ? "Blocked" : "Open";
  const summary = road === null ? "Road geometry" : describeRoadImportance(road);
  const context = road === null ? "Road detail unavailable." : describeRoadContext(bundle, road);
  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "State", value: badge },
  ];

  if (road !== null) {
    details.push({ label: "Class", value: humanize(road.roadClass) });
    details.push({ label: "Direction", value: humanize(road.directionality) });
    details.push({ label: "Lanes", value: String(road.laneCount) });
  }

  const notes = road === null ? [] : [describeRoadImportance(road), describeRoadContext(bundle, road)];

  return {
    target: { kind: "road", roadId },
    title,
    badge,
    summary,
    context,
    details,
    notes,
    focusPoints: road === null ? [] : road.centerline,
  };
}

function buildAreaPresentation(bundle: LiveBundleViewModel, areaId: string): SelectionPresentation {
  const area = bundle.map.areas.find((entry) => entry.areaId === areaId) ?? null;
  const title = area === null ? `Area ${areaId}` : formatAreaLabel(area);
  const badge = area === null ? "Area" : humanize(area.kind);
  const summary = area === null ? "Environmental context" : describeAreaImportance(area.kind);
  const context = area === null ? "Area detail unavailable." : `World form: ${bundle.map.environment.displayName}`;
  const details: SelectionDetail[] = [
    { label: "Identity", value: title },
    { label: "Type", value: badge },
  ];

  if (bundle.map.environment.displayName !== "unknown environment") {
    details.push({ label: "Environment", value: bundle.map.environment.displayName });
  }
  if (area !== null && area.label !== null) {
    details.push({ label: "Label", value: area.label });
  }

  const notes = area === null ? [] : [describeAreaImportance(area.kind), `Part of the ${bundle.map.environment.displayName} surface.`];

  return {
    target: { kind: "area", areaId },
    title,
    badge,
    summary,
    context,
    details,
    notes,
    focusPoints: area === null ? [] : area.polygon,
  };
}

function describeRoadImportance(road: {
  blocked: boolean;
  directionality: string;
  laneCount: number;
  roadClass: string;
}): string {
  if (road.blocked) {
    return "Blocked roadway matters because it can redirect live traffic.";
  }
  if (road.directionality === "two_way") {
    return "Bidirectional roadway matters because it carries live traffic both ways.";
  }
  if (road.laneCount > 1) {
    return "Multi-lane roadway matters because it carries more operational flow.";
  }
  return `This ${humanize(road.roadClass)} is part of the live routing surface.`;
}

function describeRoadContext(bundle: LiveBundleViewModel, road: { blocked: boolean }): string {
  const blockedCount = bundle.map.blockedEdgeIds.length;
  if (road.blocked) {
    return `Current context: blocked, with ${blockedCount} blocked edge(s) in the bundle.`;
  }
  return blockedCount > 0
    ? `Current context: ${blockedCount} blocked edge(s) elsewhere in the bundle.`
    : "Current context: open and available for routing.";
}

function describeAreaImportance(kind: string): string {
  const normalized = kind.toLowerCase();
  if (normalized.includes("depot") || normalized.includes("yard") || normalized.includes("loading")) {
    return "Operational area that usually frames staging or loading activity.";
  }
  if (normalized.includes("building") || normalized.includes("office") || normalized.includes("warehouse")) {
    return "Built area that gives the map its world form and local context.";
  }
  return "Context surface that helps anchor the world form around the route network.";
}

function formatRoadLabel(road: { roadClass: string; directionality: string }): string {
  return `${humanize(road.roadClass)} ${humanize(road.directionality)} road`;
}

function formatAreaLabel(area: { kind: string; label: string | null; areaId: string }): string {
  return area.label ?? `${humanize(area.kind)} ${area.areaId}`;
}

function humanize(value: string): string {
  return value.replace(/[_-]+/gu, " ").replace(/\s+/gu, " ").trim();
}

function uniqueNumbers(values: number[]): number[] {
  const result: number[] = [];
  const seen = new Set<number>();
  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }
  return result;
}
