import { useCallback, useEffect, useRef, useState, type MouseEvent } from "react";

import { AnalyzeTab } from "./components/tabs/AnalyzeTab";
import { EditorTab } from "./components/tabs/EditorTab";
import { FleetTab } from "./components/tabs/FleetTab";
import { OperateTab } from "./components/tabs/OperateTab";
import { TrafficTab } from "./components/tabs/TrafficTab";
import { WorkspaceShell } from "./components/WorkspaceShell";
import { useAuthoring } from "./hooks/useAuthoring";
import { useLiveSession } from "./hooks/useLiveSession";
import { useRoutePreview } from "./hooks/useRoutePreview";
import {
  computeMinDisplayedSpacing,
  computeSceneBounds,
  defaultLayers,
  describeSelectedTarget,
  findDisplayedVehicleById,
  findEdgeById,
  findNodePosition,
  findVehicleById,
  fitViewportToBundle,
  formatMeters,
  formatMaybeNumber,
  formatSeconds,
  maxMotionTime,
  sampleDisplayedVehicles,
  sampleTrafficSnapshot,
  sessionActions,
  trafficRoadPressureScore,
  workspaceTabs,
  type DisplayedVehicle,
} from "./viewModel";
import type {
  AreaPayload,
  BundlePayload,
  DragState,
  HoverTarget,
  LayerState,
  LiveCommandDraft,
  MoveNodeEditOperation,
  NodePayload,
  Position3,
  RoutePlanDestination,
  RoutePlanEntry,
  SceneViewMode,
  RoadPayload,
  SelectedTarget,
  ViewportState,
  WorkspaceTab,
} from "./types";

function App(): JSX.Element {
  const minimapRef = useRef<SVGSVGElement | null>(null);
  const sceneRef = useRef<SVGSVGElement | null>(null);
  const liveSession = useLiveSession();
  const [layers, setLayers] = useState<LayerState>(defaultLayers);
  const [sceneViewMode, setSceneViewMode] = useState<SceneViewMode>("iso");
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("operate");
  const [selectedTarget, setSelectedTarget] = useState<SelectedTarget | null>(null);
  const [hoverTarget, setHoverTarget] = useState<HoverTarget | null>(null);
  const [routePlans, setRoutePlans] = useState<RoutePlanEntry[]>([]);
  const [activeRoutePlanId, setActiveRoutePlanId] = useState<string | null>(null);
  const [selectedRouteDestination, setSelectedRouteDestination] = useState<RoutePlanDestination | null>(null);
  const routePlanSequenceRef = useRef(0);
  const [liveCommandDraft, setLiveCommandDraft] = useState<LiveCommandDraft>({
    vehicleId: "",
    destinationNodeId: "",
    edgeId: "",
    nodeId: "",
    hazardLabel: "temporary closure",
    spawnVehicleType: "GENERIC",
    spawnPayload: "0",
    spawnVelocity: "0",
    spawnMaxPayload: "120",
    spawnMaxSpeed: "12",
    jobId: "live-injection",
    jobTaskNodeId: "",
    jobTaskDestinationNodeId: "",
    stepSeconds: "0.5",
  });
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<number[] | null>(null);
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [viewport, setViewport] = useState<ViewportState>({
    x: -20,
    y: -12,
    width: 40,
    height: 24,
  });
  const [motionClockS, setMotionClockS] = useState(0);

  const applyLoadedBundleWithViewport = useCallback(
    (bundlePayload: BundlePayload, message: string) => {
      setViewport(fitViewportToBundle(bundlePayload));
      setSelectedTarget(null);
      setHoverTarget(null);
      setDragState(null);
      liveSession.applyLoadedBundle(bundlePayload, message);
    },
    [liveSession.applyLoadedBundle],
  );

  const authoringState = useAuthoring({
    bundle: liveSession.bundle,
    applyLoadedBundle: applyLoadedBundleWithViewport,
  });
  const routePreview = useRoutePreview({
    bundle: liveSession.bundle,
    setLiveCommandMessage: liveSession.setLiveCommandMessage,
    selectedVehicleIds: selectedVehicleIds ?? [],
  });

  const bundle = applyTransactionToBundle(liveSession.bundle, authoringState.draftTransaction);
  const displayedVehicles = sampleDisplayedVehicles(bundle, motionClockS);
  const trafficSnapshot = sampleTrafficSnapshot(bundle, motionClockS);
  const trafficRoadStates = trafficSnapshot.road_states ?? [];
  const queuedVehicleCount = trafficRoadStates.reduce(
    (count, roadState) => count + (roadState.queued_vehicle_ids?.length ?? 0),
    0,
  );
  const congestedRoadCount = trafficRoadStates.filter(
    (roadState) => (roadState.congestion_intensity ?? 0) > 0.2,
  ).length;
  const minDisplayedSpacingM = computeMinDisplayedSpacing(displayedVehicles);
  const bounds = computeSceneBounds(bundle);
  const routePreviews = bundle?.command_center?.route_previews ?? [];
  const activeRoutePlan =
    routePlans.find((plan) => plan.id === activeRoutePlanId) ?? routePlans[0] ?? null;
  const activeRoutePreview = activeRoutePlan?.preview ?? null;
  const inspections = bundle?.command_center?.vehicle_inspections ?? [];
  const recentCommands = bundle?.command_center?.recent_commands ?? [];
  const suggestions = bundle?.command_center?.ai_assist?.suggestions ?? [];
  const anomalies = bundle?.command_center?.ai_assist?.anomalies ?? [];
  const explanations = bundle?.command_center?.ai_assist?.explanations ?? [];
  const commandCenterSelectedVehicleIds = bundle?.command_center?.selected_vehicle_ids ?? [];
  const effectiveSelectedVehicleIds = selectedVehicleIds ?? commandCenterSelectedVehicleIds;
  const selectedVehicleId =
    selectedTarget?.kind === "vehicle"
      ? selectedTarget.vehicleId
      : effectiveSelectedVehicleIds[0] ?? inspections[0]?.vehicle_id ?? null;
  const selectedVehicle = findDisplayedVehicleById(displayedVehicles, selectedVehicleId);
  const selectedInspection = selectedVehicleId
    ? inspections.find((inspection) => inspection.vehicle_id === selectedVehicleId) ?? null
    : null;
  const selectedRoutePreview =
    activeRoutePreview ??
    routePreviews.find((preview) => preview.vehicle_id === selectedVehicleId) ??
    routePreviews[0] ??
    null;
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
  const selectedHazardEdgeId =
    selectedTarget?.kind === "hazard" ? selectedTarget.edgeId : undefined;

  useEffect(() => {
    const motionEndTimeS = maxMotionTime(liveSession.bundle);
    if (motionEndTimeS <= 0.0) {
      setMotionClockS(0);
      return;
    }

    let frameId = 0;
    let lastTimestampMs: number | null = null;
    const tick = (timestampMs: number) => {
      if (lastTimestampMs === null) {
        lastTimestampMs = timestampMs;
      }
      const deltaS = (timestampMs - lastTimestampMs) / 1000;
      lastTimestampMs = timestampMs;
      setMotionClockS((current) => {
        const next = current + deltaS;
        return next > motionEndTimeS ? next % motionEndTimeS : next;
      });
      frameId = window.requestAnimationFrame(tick);
    };

    frameId = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frameId);
  }, [liveSession.bundle]);

  const initialBundleFitRef = useRef(false);
  useEffect(() => {
    if (initialBundleFitRef.current || !liveSession.bundle) {
      return;
    }
    setViewport(fitViewportToBundle(liveSession.bundle));
    initialBundleFitRef.current = true;
  }, [liveSession.bundle]);

  useEffect(() => {
    if (!bundle) {
      return;
    }
    setLiveCommandDraft((current) => ({
      ...current,
      vehicleId:
        current.vehicleId ||
        (effectiveSelectedVehicleIds[0] !== undefined
          ? String(effectiveSelectedVehicleIds[0])
          : current.vehicleId),
      destinationNodeId:
        current.destinationNodeId ||
        (routePreviews[0]?.destination_node_id !== undefined
          ? String(routePreviews[0].destination_node_id)
          : current.destinationNodeId),
      edgeId:
        current.edgeId ||
        (selectedTarget?.kind === "hazard"
          ? String(selectedTarget.edgeId)
          : selectedRoad?.edge_ids?.[0] !== undefined
            ? String(selectedRoad.edge_ids[0])
            : current.edgeId),
      nodeId:
        current.nodeId ||
        (selectedInspection?.current_node_id !== undefined
          ? String(selectedInspection.current_node_id)
          : current.nodeId),
      jobTaskNodeId:
        current.jobTaskNodeId ||
        (selectedInspection?.current_node_id !== undefined
          ? String(selectedInspection.current_node_id)
          : current.jobTaskNodeId),
      jobTaskDestinationNodeId:
        current.jobTaskDestinationNodeId ||
        (routePreviews[0]?.destination_node_id !== undefined
          ? String(routePreviews[0].destination_node_id)
          : current.jobTaskDestinationNodeId),
      stepSeconds:
        current.stepSeconds || String(bundle?.session_control?.step_seconds ?? 0.5),
    }));
  }, [
    bundle,
    bundle?.session_control?.step_seconds,
    effectiveSelectedVehicleIds,
    routePreviews,
    selectedInspection?.current_node_id,
    selectedRoad?.edge_ids,
      selectedHazardEdgeId,
      selectedTarget?.kind,
      setLiveCommandDraft,
    ]);

  const bootstrap = liveSession.bootstrap;
  const liveCommandMessage = liveSession.liveCommandMessage;
  const sessionControl = bundle?.session_control ?? null;
  const editCount = authoringState.draftTransaction.operations.length;
  const validationCount = authoringState.validationMessages.length;
  const minDisplayedSpacingLabel = formatMeters(minDisplayedSpacingM);
  const shellClassName = `shell shell-tab-${activeTab} ${activeTab === "editor" ? "shell-editor-focused" : ""}`;
  const bundleStatusTone =
    bootstrap.loadState === "loading"
      ? "loading"
      : bootstrap.loadState === "error"
        ? "error"
        : bootstrap.loadState === "loaded"
          ? "success"
          : "warning";
  const bundleStatusTitle =
    bootstrap.loadState === "loading"
      ? "Loading live bundle"
      : bootstrap.loadState === "error"
        ? "Live bundle needs attention"
        : bootstrap.loadState === "loaded"
          ? "Live bundle connected"
          : "No live bundle attached";
  const bundleStatusCopy = bootstrap.message;
  const bundleStatusAction =
    bootstrap.loadState === "loading"
      ? "The shell will settle into the loaded state as soon as the bundle arrives."
      : bootstrap.loadState === "error"
        ? "Check the bundle path and reconnect the live session when the endpoint is available."
        : bootstrap.loadState === "loaded"
          ? "Use Reconnect Bundle to refresh the current snapshot if the live session has advanced."
          : "Open the deck with a bundle URL to populate the shell, or reconnect once the live endpoint is ready.";

  function panView(deltaX: number, deltaY: number): void {
    setViewport((current) => ({
      ...current,
      x: current.x + deltaX * current.width,
      y: current.y + deltaY * current.height,
    }));
  }

  function zoomView(factor: number): void {
    setViewport((current) => {
      const nextWidth = current.width * factor;
      const nextHeight = current.height * factor;
      return {
        x: current.x + (current.width - nextWidth) / 2,
        y: current.y + (current.height - nextHeight) / 2,
        width: nextWidth,
        height: nextHeight,
      };
    });
  }

  function fitScene(): void {
    setViewport(fitViewportToBundle(bundle));
  }

  function focusSelectedVehicle(): void {
    if (!selectedVehicle?.position) {
      return;
    }
    const [x, y] = selectedVehicle.position;
    const nextWidth = Math.max(bounds.width * 0.32, 8);
    const nextHeight = Math.max(bounds.height * 0.32, 6);
    setViewport({
      x: x - nextWidth / 2,
      y: y - nextHeight / 2,
      width: nextWidth,
      height: nextHeight,
    });
  }

  function handleMinimapClick(event: MouseEvent<SVGSVGElement>): void {
    if (!minimapRef.current) {
      return;
    }
    const rect = minimapRef.current.getBoundingClientRect();
    const clickX = (event.clientX - rect.left) / rect.width;
    const clickY = (event.clientY - rect.top) / rect.height;
    const targetX = bounds.minX + clickX * bounds.width;
    const targetY = bounds.minY + clickY * bounds.height;
    setViewport((current) => ({
      ...current,
      x: targetX - current.width / 2,
      y: targetY - current.height / 2,
    }));
  }

  function toggleLayer(layer: keyof LayerState): void {
    setLayers((current) => ({
      ...current,
      [layer]: !current[layer],
    }));
  }

  function selectVehicle(
    vehicleId: number | undefined,
    options: { additive?: boolean } = {},
  ): void {
    if (vehicleId !== undefined) {
      setSelectedTarget({ kind: "vehicle", vehicleId });
      setSelectedVehicleIds((current) => {
        const currentSelection = current ?? [];
        if (options.additive) {
          if (currentSelection.includes(vehicleId)) {
            return currentSelection.filter((existingVehicleId) => existingVehicleId !== vehicleId);
          }
          return [...currentSelection, vehicleId];
        }
        return [vehicleId];
      });
    }
  }

  function selectAllVisibleVehicles(): void {
    const visibleVehicleIds = displayedVehicles
      .map((vehicle) => vehicle.vehicle_id)
      .filter((vehicleId): vehicleId is number => vehicleId !== undefined);
    if (visibleVehicleIds.length === 0) {
      return;
    }
    setSelectedVehicleIds(visibleVehicleIds);
    setSelectedTarget({ kind: "vehicle", vehicleId: visibleVehicleIds[0] });
  }

  function clearVehicleSelection(): void {
    setSelectedVehicleIds([]);
    if (selectedTarget?.kind === "vehicle") {
      setSelectedTarget(null);
    }
  }

  function selectRoad(roadId: string | undefined): void {
    if (roadId) {
      setSelectedTarget({ kind: "road", roadId });
    }
  }

  function selectArea(areaId: string | undefined): void {
    if (areaId) {
      setSelectedTarget({ kind: "area", areaId });
    }
  }

  function selectQueue(roadId: string | undefined): void {
    if (roadId) {
      setSelectedTarget({ kind: "queue", roadId });
    }
  }

  function selectHazard(edgeId: number | undefined): void {
    if (edgeId !== undefined) {
      setSelectedTarget({ kind: "hazard", edgeId });
    }
  }

  function selectRouteDestination(destination: RoutePlanDestination): void {
    setSelectedRouteDestination(destination);
  }

  function selectedPlanningVehicleId(): number | null {
    if (selectedTarget?.kind === "vehicle") {
      return selectedTarget.vehicleId;
    }
    return effectiveSelectedVehicleIds[0] ?? null;
  }

  async function createRoutePlanFromSelection(): Promise<void> {
    const vehicleId = selectedPlanningVehicleId();
    if (vehicleId === null) {
      liveSession.setLiveCommandMessage("Select a vehicle on the map before creating a plan.");
      return;
    }
    if (!selectedRouteDestination) {
      liveSession.setLiveCommandMessage("Select a destination place on the map before creating a plan.");
      return;
    }

    const previewResult = await routePreview.submitRoutePreview({
      vehicle_id: vehicleId,
      destination_node_id: selectedRouteDestination.nodeId,
      vehicle_ids: [vehicleId],
    });
    const preview =
      previewResult?.routePreviews.find((entry) => entry.vehicle_id === vehicleId) ??
      previewResult?.routePreviews[0] ??
      null;
    const planId = `plan-${vehicleId}-${selectedRouteDestination.nodeId}-${routePlanSequenceRef.current + 1}`;
    routePlanSequenceRef.current += 1;
    const nextPlan: RoutePlanEntry = {
      id: planId,
      vehicleId,
      destination: selectedRouteDestination,
      preview,
      committed: false,
    };
    setRoutePlans((current) => [...current, nextPlan]);
    setActiveRoutePlanId(planId);
    selectVehicle(vehicleId);
  }

  async function activateRoutePlan(planId: string): Promise<void> {
    const plan = routePlans.find((entry) => entry.id === planId);
    if (!plan) {
      return;
    }
    setActiveRoutePlanId(planId);
    selectVehicle(plan.vehicleId);
    setSelectedRouteDestination(plan.destination);
  }

  async function commitRoutePlan(planId: string): Promise<void> {
    const plan = routePlans.find((entry) => entry.id === planId);
    if (!plan) {
      return;
    }
    await submitLiveCommand({
      command_type: "assign_vehicle_destination",
      vehicle_id: plan.vehicleId,
      destination_node_id: plan.destination.nodeId,
      vehicle_ids: [plan.vehicleId],
    });
    setRoutePlans((current) =>
      current.map((entry) => (entry.id === planId ? { ...entry, committed: true } : entry)),
    );
    setActiveRoutePlanId(planId);
    selectVehicle(plan.vehicleId);
    setSelectedRouteDestination(plan.destination);
  }

  function parseDraftInteger(value: string): number | null {
    if (!value.trim()) {
      return null;
    }
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function parseDraftFloat(value: string): number | null {
    if (!value.trim()) {
      return null;
    }
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  async function submitLiveCommand(commandPayload: Record<string, unknown>): Promise<void> {
    const targetVehicleIds =
      commandPayload.vehicle_ids !== undefined
        ? commandPayload.vehicle_ids
        : effectiveSelectedVehicleIds;
    await liveSession.submitLiveCommand({
      ...commandPayload,
      selected_vehicle_ids: targetVehicleIds,
    });
  }

  function submitRoutePreview(previewPayload: Record<string, unknown>): void {
    const targetVehicleIds =
      previewPayload.vehicle_ids !== undefined
        ? previewPayload.vehicle_ids
        : effectiveSelectedVehicleIds;
    void routePreview.submitRoutePreview({
      ...previewPayload,
      selected_vehicle_ids: targetVehicleIds,
    });
  }

  function controlLiveSession(action: "play" | "pause" | "step"): void {
    const stepSeconds =
      parseDraftFloat(liveCommandDraft.stepSeconds) ?? sessionControl?.step_seconds ?? 0.5;
    void liveSession.controlLiveSession(action, {
      selectedVehicleIds: effectiveSelectedVehicleIds,
      deltaSeconds: stepSeconds,
    });
  }

  function resolveCommandVehicleIds(fallbackVehicleId: number | null = null): number[] {
    if (selectedVehicleIds !== null) {
      return selectedVehicleIds.length > 0
        ? selectedVehicleIds
        : fallbackVehicleId !== null
          ? [fallbackVehicleId]
          : [];
    }
    if (selectedTarget?.kind === "vehicle") {
      return [selectedTarget.vehicleId];
    }
    if (fallbackVehicleId !== null) {
      return [fallbackVehicleId];
    }
    return commandCenterSelectedVehicleIds;
  }

  function assignDestinationFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.destinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid vehicle id and destination node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitLiveCommand({
      command_type: "assign_vehicle_destination",
      vehicle_id: vehicleId,
      destination_node_id: destinationNodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function previewRouteFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.destinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid vehicle id and destination node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitRoutePreview({
      vehicle_id: vehicleId,
      destination_node_id: destinationNodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function repositionVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const nodeId = parseDraftInteger(liveCommandDraft.nodeId);
    if (vehicleId === null || nodeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid vehicle id and node id first.");
      return;
    }
    const vehicleIds = resolveCommandVehicleIds(vehicleId);
    submitLiveCommand({
      command_type: "reposition_vehicle",
      vehicle_id: vehicleId,
      node_id: nodeId,
      vehicle_ids: vehicleIds,
    });
  }

  function blockRoadFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "block_edge",
      edge_id: edgeId,
    });
  }

  function unblockRoadFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "unblock_edge",
      edge_id: edgeId,
    });
  }

  function spawnVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const nodeId = parseDraftInteger(liveCommandDraft.nodeId);
    const maxSpeed = parseDraftFloat(liveCommandDraft.spawnMaxSpeed);
    const maxPayload = parseDraftFloat(liveCommandDraft.spawnMaxPayload);
    const payload = parseDraftFloat(liveCommandDraft.spawnPayload) ?? 0;
    const velocity = parseDraftFloat(liveCommandDraft.spawnVelocity) ?? 0;
    if (vehicleId === null || nodeId === null || maxSpeed === null || maxPayload === null) {
      liveSession.setLiveCommandMessage("Enter valid spawn vehicle, node, max speed, and payload values first.");
      return;
    }
    submitLiveCommand({
      command_type: "spawn_vehicle",
      vehicle_id: vehicleId,
      node_id: nodeId,
      max_speed: maxSpeed,
      max_payload: maxPayload,
      vehicle_type: liveCommandDraft.spawnVehicleType || "GENERIC",
      payload,
      velocity,
    });
  }

  function removeVehicleFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    if (vehicleId === null) {
      liveSession.setLiveCommandMessage("Enter a valid vehicle id first.");
      return;
    }
    submitLiveCommand({
      command_type: "remove_vehicle",
      vehicle_id: vehicleId,
    });
  }

  function injectJobFromDraft(): void {
    const vehicleId = parseDraftInteger(liveCommandDraft.vehicleId);
    const destinationNodeId = parseDraftInteger(liveCommandDraft.jobTaskDestinationNodeId);
    if (vehicleId === null || destinationNodeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid vehicle id and job destination node id first.");
      return;
    }
    submitLiveCommand({
      command_type: "inject_job",
      vehicle_id: vehicleId,
      job: {
        id: liveCommandDraft.jobId || `live-job-${vehicleId}-${destinationNodeId}`,
        tasks: [
          {
            kind: "move",
            destination_node_id: destinationNodeId,
          },
        ],
      },
    });
  }

  function declareTemporaryHazardFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "declare_temporary_hazard",
      edge_id: edgeId,
      hazard_label: liveCommandDraft.hazardLabel || "temporary closure",
    });
  }

  function clearTemporaryHazardFromDraft(): void {
    const edgeId = parseDraftInteger(liveCommandDraft.edgeId);
    if (edgeId === null) {
      liveSession.setLiveCommandMessage("Enter a valid edge id first.");
      return;
    }
    submitLiveCommand({
      command_type: "clear_temporary_hazard",
      edge_id: edgeId,
    });
  }

  function upsertOperation(nextOperation: MoveNodeEditOperation | { kind: "set_road_centerline"; target_id: string; points: Position3[] } | { kind: "set_area_polygon"; target_id: string; points: Position3[] }): void {
    authoringState.setDraftTransaction((current) => {
      const nextOperations = current.operations.filter(
        (operation) =>
          !(
            operation.kind === nextOperation.kind &&
            operation.target_id === nextOperation.target_id
          ),
      );
      nextOperations.push(nextOperation as never);
      return {
        ...current,
        operations: nextOperations,
      };
    });
  }

  function beginNodeDrag(event: MouseEvent<SVGCircleElement>, node: NodePayload): void {
    if (!authoringState.editorEnabled || node.node_id === undefined) {
      return;
    }
    event.stopPropagation();
    const z = node.position?.[2] ?? 0;
    setSelectedTarget(null);
    setDragState({
      kind: "node",
      nodeId: node.node_id,
      z,
    });
  }

  function beginRoadPointDrag(
    event: MouseEvent<SVGCircleElement>,
    roadId: string,
    pointIndex: number,
    z: number,
  ): void {
    if (!authoringState.editorEnabled) {
      return;
    }
    event.stopPropagation();
    setDragState({
      kind: "road-point",
      roadId,
      pointIndex,
      z,
    });
  }

  function beginAreaPointDrag(
    event: MouseEvent<SVGCircleElement>,
    areaId: string,
    pointIndex: number,
    z: number,
  ): void {
    if (!authoringState.editorEnabled) {
      return;
    }
    event.stopPropagation();
    setDragState({
      kind: "area-point",
      areaId,
      pointIndex,
      z,
    });
  }

  function handleSceneMouseMove(event: MouseEvent<SVGSVGElement>): void {
    if (!dragState || !bundle) {
      return;
    }
    const scenePoint = clientPointToScene(event, sceneRef.current, viewport, dragState.z);
    if (!scenePoint) {
      return;
    }

    if (dragState.kind === "node") {
      upsertOperation({
        kind: "move_node",
        target_id: dragState.nodeId,
        position: scenePoint,
      });
      return;
    }

    if (dragState.kind === "road-point") {
      const road = (bundle.render_geometry?.roads ?? []).find(
        (entry) => entry.road_id === dragState.roadId,
      );
      if (!road?.centerline) {
        return;
      }
      const nextPoints = road.centerline.map((point) => [...point] as Position3);
      nextPoints[dragState.pointIndex] = scenePoint;
      upsertOperation({
        kind: "set_road_centerline",
        target_id: dragState.roadId,
        points: nextPoints,
      });
      return;
    }

    const area = (bundle.render_geometry?.areas ?? []).find(
      (entry) => entry.area_id === dragState.areaId,
    );
    if (!area?.polygon) {
      return;
    }
    const nextPoints = area.polygon.map((point) => [...point] as Position3);
    nextPoints[dragState.pointIndex] = scenePoint;
    upsertOperation({
      kind: "set_area_polygon",
      target_id: dragState.areaId,
      points: nextPoints,
    });
  }

  function stopDragging(): void {
    if (dragState) {
      liveSession.setLiveCommandMessage("Draft geometry edit staged. Save the scenario to persist it.");
    }
    setDragState(null);
  }

  function handleSceneMouseUp(): void {
    stopDragging();
  }

  function handleSceneMouseLeave(): void {
    setHoverTarget(null);
    stopDragging();
  }

  function applyTransactionToBundle(
    liveBundle: BundlePayload | null,
    draftTransaction: { operations: Array<{ kind: string; target_id: string | number; points?: Position3[]; position?: Position3 }> },
  ): BundlePayload | null {
    if (!liveBundle) {
      return null;
    }
    return liveBundle;
  }

  const sceneTabContent = (
    <OperateTab
      bundle={bundle}
      bootstrap={bootstrap}
      motionClockS={motionClockS}
      viewport={viewport}
      boundsLabel={formatMeters(bounds.width)}
      layers={layers}
      selectedTarget={selectedTarget}
      selectedVehicleIds={effectiveSelectedVehicleIds}
      selectedRouteDestination={selectedRouteDestination}
      routePlans={routePlans}
      activeRoutePlanId={activeRoutePlanId}
      activeRoutePreview={activeRoutePreview}
      isRoutePreviewing={routePreview.isPreviewing}
      liveCommandDraft={liveCommandDraft}
      setLiveCommandDraft={setLiveCommandDraft}
      liveCommandMessage={liveCommandMessage}
      sessionControl={sessionControl}
      editorEnabled={authoringState.editorEnabled}
      hoverTarget={hoverTarget}
      setHoverTarget={setHoverTarget}
      sceneRef={sceneRef}
      minimapRef={minimapRef}
      onPan={panView}
      onZoom={zoomView}
      onFit={fitScene}
      onFocusSelected={focusSelectedVehicle}
      onToggleLayer={toggleLayer}
      onSelectVehicle={selectVehicle}
      onSelectRoad={selectRoad}
      onSelectArea={selectArea}
      onSelectQueue={selectQueue}
      onSelectHazard={selectHazard}
      onSelectRouteDestination={selectRouteDestination}
      onMinimapClick={handleMinimapClick}
      onSceneMouseMove={handleSceneMouseMove}
      onSceneMouseUp={handleSceneMouseUp}
      onSceneMouseLeave={handleSceneMouseLeave}
      onBeginNodeDrag={beginNodeDrag}
      onBeginRoadPointDrag={beginRoadPointDrag}
      onBeginAreaPointDrag={beginAreaPointDrag}
      sceneViewMode={sceneViewMode}
      onSceneViewModeChange={setSceneViewMode}
      onControlLiveSession={controlLiveSession}
      onCreateRoutePlan={createRoutePlanFromSelection}
      onActivateRoutePlan={activateRoutePlan}
      onCommitRoutePlan={commitRoutePlan}
      onPreviewRouteFromDraft={previewRouteFromDraft}
      onAssignDestinationFromDraft={assignDestinationFromDraft}
      onRepositionVehicleFromDraft={repositionVehicleFromDraft}
    />
  );

  return (
    <WorkspaceShell
      shellClassName={shellClassName}
      bootstrap={bootstrap}
      selectedVehicleCount={effectiveSelectedVehicleIds.length}
      minDisplayedSpacingLabel={minDisplayedSpacingLabel}
      queuedVehicleCount={queuedVehicleCount}
      congestedRoadCount={congestedRoadCount}
      editCount={editCount}
      validationCount={validationCount}
      activeTab={activeTab}
      tabs={workspaceTabs}
      onTabChange={setActiveTab}
      bundleStatusTitle={bundleStatusTitle}
      bundleStatusCopy={bundleStatusCopy}
      bundleStatusAction={bundleStatusAction}
      bundleStatusTone={bundleStatusTone}
    >
      {sceneTabContent}
      <TrafficTab bundle={bundle} motionClockS={motionClockS} selectedTarget={selectedTarget} />
      <FleetTab
        bundle={bundle}
        motionClockS={motionClockS}
        selectedTarget={selectedTarget}
        selectedVehicleIds={effectiveSelectedVehicleIds}
        liveCommandDraft={liveCommandDraft}
        setLiveCommandDraft={setLiveCommandDraft}
        liveCommandMessage={liveCommandMessage}
        sessionControl={sessionControl}
        onSelectVisible={selectAllVisibleVehicles}
        onClearSelection={clearVehicleSelection}
        onSelectVehicle={selectVehicle}
        onSpawnVehicleFromDraft={spawnVehicleFromDraft}
        onRemoveVehicleFromDraft={removeVehicleFromDraft}
        onInjectJobFromDraft={injectJobFromDraft}
        onDeclareTemporaryHazardFromDraft={declareTemporaryHazardFromDraft}
        onClearTemporaryHazardFromDraft={clearTemporaryHazardFromDraft}
        onBlockRoadFromDraft={blockRoadFromDraft}
        onUnblockRoadFromDraft={unblockRoadFromDraft}
      />
      <EditorTab
        bundle={bundle}
        editorEnabled={authoringState.editorEnabled}
        draftTransaction={authoringState.draftTransaction}
        validationMessages={authoringState.validationMessages}
        editorMessage={authoringState.editorMessage}
        onToggleEditMode={authoringState.toggleEditMode}
        onSaveScenario={authoringState.saveScenario}
        onReloadScenario={authoringState.reloadScenario}
      />
      <AnalyzeTab
        bundle={bundle}
        motionClockS={motionClockS}
        selectedTarget={selectedTarget}
        selectedVehicleIds={effectiveSelectedVehicleIds}
      />
    </WorkspaceShell>
  );
}

function clientPointToScene(
  event: MouseEvent<SVGSVGElement>,
  svg: SVGSVGElement | null,
  viewport: ViewportState,
  z: number,
): Position3 | null {
  if (!svg) {
    return null;
  }
  const rect = svg.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    return null;
  }
  const x = viewport.x + ((event.clientX - rect.left) / rect.width) * viewport.width;
  const y = viewport.y + ((event.clientY - rect.top) / rect.height) * viewport.height;
  return [Math.round(x * 1000) / 1000, Math.round(y * 1000) / 1000, z];
}

function applyTransactionToBundle(bundle: BundlePayload | null, _draftTransaction: unknown): BundlePayload | null {
  return bundle;
}

export default App;
