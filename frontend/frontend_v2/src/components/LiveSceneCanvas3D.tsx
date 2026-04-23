import { useEffect, useRef } from "react";

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import type { LiveBundleViewModel, LiveRoutePreviewViewModel, Point2 } from "../adapters/liveBundle";
import type { CameraState, SceneBounds } from "../adapters/mapViewport";
import type { FrontendModeId, LayerState } from "../state/frontendUiState";
import type { SelectionTarget } from "../adapters/selectionModel";

type LiveSceneCanvas3DProps = {
  model: LiveBundleViewModel;
  camera: CameraState;
  layers: LayerState;
  selectionTarget: SelectionTarget | null;
  selectedVehicleIds: number[];
  activeRoutePreview: LiveRoutePreviewViewModel | null;
  activeMode: FrontendModeId;
  onCameraChange: (camera: CameraState) => void;
  onSelectVehicle: (vehicleId: number, additive: boolean) => void;
  onSelectRoad: (roadId: string) => void;
  onSelectIntersection: (intersectionId: string) => void;
  onSelectArea: (areaId: string) => void;
};

type SelectableKind = "vehicle" | "road" | "intersection" | "area";

type SelectableMeta = {
  kind: SelectableKind;
  id: string | number;
};

const BASE_ORTHO_HEIGHT = 100;
const FIT_PADDING_FACTOR = 1.16;
const MIN_CAMERA_ZOOM_FACTOR = 0.36;
const MAX_CAMERA_ZOOM_FACTOR = 8.5;
const ISO_ORBIT_RADIUS_SCALE = 1.85;
const BIRDSEYE_ORBIT_RADIUS_SCALE = 1.45;

export function LiveSceneCanvas3D({
  model,
  camera,
  layers,
  selectionTarget,
  selectedVehicleIds,
  activeRoutePreview,
  activeMode,
  onCameraChange,
  onSelectVehicle,
  onSelectRoad,
  onSelectIntersection,
  onSelectArea,
}: LiveSceneCanvas3DProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.OrthographicCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const rootRef = useRef<THREE.Group | null>(null);
  const sceneBoundsRef = useRef<SceneBounds>(model.map.sceneFrame.sceneBounds);
  const fitZoomRef = useRef<number>(1);
  const syncSignatureRef = useRef<string>("");
  const cameraStateRef = useRef<CameraState>(camera);
  const pointerDownRef = useRef<{
    pointerId: number;
    clientX: number;
    clientY: number;
    additive: boolean;
  } | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return undefined;
    }
    const containerElement = container;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#cfd0cd");
    sceneRef.current = scene;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.setClearColor("#cfd0cd", 1);
    renderer.domElement.style.display = "block";
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.touchAction = "none";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const orthoCamera = new THREE.OrthographicCamera(-50, 50, 50, -50, 0.1, 5000);
    orthoCamera.up.set(0, 0, 1);
    cameraRef.current = orthoCamera;

    const ambient = new THREE.AmbientLight(0xffffff, 1.35);
    const keyLight = new THREE.DirectionalLight(0xfffaf2, 1.6);
    keyLight.position.set(130, -140, 180);
    const fillLight = new THREE.DirectionalLight(0xc9d6dc, 0.82);
    fillLight.position.set(-150, 100, 120);
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.28);
    rimLight.position.set(0, 0, 280);
    scene.add(ambient, keyLight, fillLight, rimLight);

    const root = new THREE.Group();
    root.name = "scene-root";
    scene.add(root);
    rootRef.current = root;

    const controls = new OrbitControls(orthoCamera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.enableRotate = true;
    controls.enablePan = true;
    controls.enableZoom = true;
    controls.screenSpacePanning = false;
    controls.minPolarAngle = 0.28;
    controls.maxPolarAngle = 1.18;
    controls.minAzimuthAngle = -Infinity;
    controls.maxAzimuthAngle = Infinity;
    controls.minZoom = 0.2;
    controls.maxZoom = 12;
    controls.addEventListener("change", () => {
      cameraStateRef.current = readCameraStateFromControls(
        controls,
        orthoCamera,
        fitZoomRef.current,
        cameraStateRef.current.sceneViewMode,
      );
      renderFrame();
      emitCameraState();
    });
    controlsRef.current = controls;

    const resizeObserver = new ResizeObserver(() => {
      resizeRenderer();
    });
    resizeObserver.observe(container);

    const handlePointerDown = (event: PointerEvent) => {
      if (event.button !== 0) {
        return;
      }

      pointerDownRef.current = {
        pointerId: event.pointerId,
        clientX: event.clientX,
        clientY: event.clientY,
        additive: event.shiftKey || event.metaKey || event.ctrlKey,
      };
    };

    const handlePointerUp = (event: PointerEvent) => {
      const pointerState = pointerDownRef.current;
      if (pointerState === null || pointerState.pointerId !== event.pointerId) {
        return;
      }

      pointerDownRef.current = null;
      const dx = Math.abs(event.clientX - pointerState.clientX);
      const dy = Math.abs(event.clientY - pointerState.clientY);
      if (dx > 6 || dy > 6) {
        return;
      }

      const selectable = raycastSelectable(event.clientX, event.clientY);
      if (selectable === null) {
        return;
      }

      switch (selectable.kind) {
        case "vehicle":
          onSelectVehicle(Number(selectable.id), pointerState.additive);
          break;
        case "road":
          onSelectRoad(String(selectable.id));
          break;
        case "intersection":
          onSelectIntersection(String(selectable.id));
          break;
        case "area":
          onSelectArea(String(selectable.id));
          break;
        default:
          break;
      }
    };

    const handlePointerCancel = () => {
      pointerDownRef.current = null;
    };

    renderer.domElement.addEventListener("pointerdown", handlePointerDown);
    renderer.domElement.addEventListener("pointerup", handlePointerUp);
    renderer.domElement.addEventListener("pointercancel", handlePointerCancel);
    renderer.domElement.addEventListener("pointerleave", handlePointerCancel);

    let rafId = 0;
    const animate = () => {
      controls.update();
      renderFrame();
      rafId = window.requestAnimationFrame(animate);
    };

    function resizeRenderer() {
      const width = Math.max(containerElement.clientWidth, 1);
      const height = Math.max(containerElement.clientHeight, 1);
      const aspect = width / height;
      renderer.setSize(width, height, false);
      orthoCamera.left = -(BASE_ORTHO_HEIGHT * aspect) / 2;
      orthoCamera.right = (BASE_ORTHO_HEIGHT * aspect) / 2;
      orthoCamera.top = BASE_ORTHO_HEIGHT / 2;
      orthoCamera.bottom = -BASE_ORTHO_HEIGHT / 2;
      orthoCamera.updateProjectionMatrix();
      fitZoomRef.current = computeFitZoom(sceneBoundsRef.current, aspect);
      controls.minZoom = fitZoomRef.current * MIN_CAMERA_ZOOM_FACTOR;
      controls.maxZoom = fitZoomRef.current * MAX_CAMERA_ZOOM_FACTOR;
      applyCameraState(cameraStateRef.current, false);
      renderFrame();
    }

    function applyCameraState(nextCamera: CameraState, emit = true) {
      const sceneBounds = sceneBoundsRef.current;
      const aspect = Math.max(containerElement.clientWidth, 1) / Math.max(containerElement.clientHeight, 1);
      const fitZoom = computeFitZoom(sceneBounds, aspect);
      fitZoomRef.current = fitZoom;
      const orbitRadius = computeOrbitRadius(sceneBounds, orbitRadiusScaleFor(nextCamera.sceneViewMode));
      const target = new THREE.Vector3(nextCamera.x, nextCamera.y, 0);
      const position = positionFromAngles(target, orbitRadius, nextCamera.azimuth, nextCamera.polar);
      orthoCamera.position.copy(position);
      orthoCamera.zoom = clamp(fitZoom * nextCamera.zoom, fitZoom * MIN_CAMERA_ZOOM_FACTOR, fitZoom * MAX_CAMERA_ZOOM_FACTOR);
      orthoCamera.updateProjectionMatrix();
      controls.target.copy(target);
      controls.minZoom = fitZoom * MIN_CAMERA_ZOOM_FACTOR;
      controls.maxZoom = fitZoom * MAX_CAMERA_ZOOM_FACTOR;
      controls.update();
      cameraStateRef.current = readCameraStateFromControls(controls, orthoCamera, fitZoom, nextCamera.sceneViewMode);
      syncSignatureRef.current = cameraSignature(cameraStateRef.current);
      if (emit) {
        emitCameraState();
      }
    }

    function emitCameraState() {
      const currentCamera = cameraRef.current;
      const currentControls = controlsRef.current;
      if (currentCamera === null || currentControls === null) {
        return;
      }

      const nextCamera = readCameraStateFromControls(
        currentControls,
        currentCamera,
        fitZoomRef.current,
        cameraStateRef.current.sceneViewMode,
      );
      const nextSignature = cameraSignature(nextCamera);
      if (nextSignature === syncSignatureRef.current) {
        return;
      }

      syncSignatureRef.current = nextSignature;
      cameraStateRef.current = nextCamera;
      onCameraChange(nextCamera);
    }

    function renderFrame() {
      renderer.render(scene, orthoCamera);
    }

    function raycastSelectable(clientX: number, clientY: number): SelectableMeta | null {
      const rect = renderer.domElement.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) {
        return null;
      }

      const pointer = new THREE.Vector2(
        ((clientX - rect.left) / rect.width) * 2 - 1,
        -(((clientY - rect.top) / rect.height) * 2 - 1),
      );
      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(pointer, orthoCamera);
      const hits = raycaster.intersectObjects(root.children, true);
      for (const hit of hits) {
        const meta = hit.object.userData.selectable as SelectableMeta | undefined;
        if (meta !== undefined) {
          return meta;
        }
      }

      return null;
    }

    buildScene(root, model, layers, selectionTarget, selectedVehicleIds, activeRoutePreview, activeMode);
    resizeRenderer();
    applyCameraState(camera, false);
    animate();

    return () => {
      window.cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener("pointerdown", handlePointerDown);
      renderer.domElement.removeEventListener("pointerup", handlePointerUp);
      renderer.domElement.removeEventListener("pointercancel", handlePointerCancel);
      renderer.domElement.removeEventListener("pointerleave", handlePointerCancel);
      controls.dispose();
      renderer.dispose();
      disposeObject3D(root);
      if (renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      controlsRef.current = null;
      rootRef.current = null;
    };
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (root === null) {
      return;
    }

    sceneBoundsRef.current = model.map.sceneFrame.sceneBounds;
    buildScene(root, model, layers, selectionTarget, selectedVehicleIds, activeRoutePreview, activeMode);
    cameraStateRef.current = camera;
    syncCameraToProps(camera);
    renderCurrentFrame();
  }, [activeMode, activeRoutePreview, layers, model, selectedVehicleIds, selectionTarget]);

  useEffect(() => {
    cameraStateRef.current = camera;
    syncCameraToProps(camera);
    renderCurrentFrame();
  }, [camera]);

  return <div ref={containerRef} className="map-canvas map-canvas-3d" role="img" aria-label="Axonometric 3D scene" />;

  function syncCameraToProps(nextCamera: CameraState) {
    const cameraObject = cameraRef.current;
    const controls = controlsRef.current;
    if (cameraObject === null || controls === null) {
      return;
    }

    const sceneBounds = sceneBoundsRef.current;
    const aspect = Math.max(containerRef.current?.clientWidth ?? 1, 1) / Math.max(containerRef.current?.clientHeight ?? 1, 1);
    const fitZoom = computeFitZoom(sceneBounds, aspect);
    fitZoomRef.current = fitZoom;
    const nextSignature = cameraSignature(nextCamera);
    if (nextSignature === syncSignatureRef.current) {
      return;
    }
    const orbitRadius = computeOrbitRadius(sceneBounds, orbitRadiusScaleFor(nextCamera.sceneViewMode));
    const target = new THREE.Vector3(nextCamera.x, nextCamera.y, 0);
    controls.target.copy(target);
    cameraObject.position.copy(positionFromAngles(target, orbitRadius, nextCamera.azimuth, nextCamera.polar));
    cameraObject.zoom = clamp(fitZoom * nextCamera.zoom, fitZoom * MIN_CAMERA_ZOOM_FACTOR, fitZoom * MAX_CAMERA_ZOOM_FACTOR);
    cameraObject.updateProjectionMatrix();
    controls.minZoom = fitZoom * MIN_CAMERA_ZOOM_FACTOR;
    controls.maxZoom = fitZoom * MAX_CAMERA_ZOOM_FACTOR;
    controls.update();
    cameraStateRef.current = readCameraStateFromControls(controls, cameraObject, fitZoom, nextCamera.sceneViewMode);
    syncSignatureRef.current = cameraSignature(cameraStateRef.current);
  }

  function renderCurrentFrame() {
    const renderer = rendererRef.current;
    const scene = sceneRef.current;
    const cameraObject = cameraRef.current;
    if (renderer === null || scene === null || cameraObject === null) {
      return;
    }

    renderer.render(scene, cameraObject);
  }
}

function buildScene(
  root: THREE.Group,
  model: LiveBundleViewModel,
  layers: LayerState,
  selectionTarget: SelectionTarget | null,
  selectedVehicleIds: number[],
  activeRoutePreview: LiveRoutePreviewViewModel | null,
  activeMode: FrontendModeId,
): void {
  disposeObject3D(root);

  const sceneBounds = model.map.sceneFrame.sceneBounds;
  const sceneCenter = boundsCenter(sceneBounds);
  const selectedVehicleIdSet = new Set(selectedVehicleIds);
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(sceneBounds.width + 40, sceneBounds.height + 40),
    new THREE.MeshStandardMaterial({
      color: "#b9b2a8",
      roughness: 1,
      metalness: 0,
    }),
  );
  ground.position.set(sceneCenter.x, sceneCenter.y, -0.42);
  root.add(ground);

  const backdrop = new THREE.Mesh(
    new THREE.PlaneGeometry(sceneBounds.width + 12, sceneBounds.height + 12),
    new THREE.MeshStandardMaterial({
      color: "#c6beb2",
      roughness: 1,
      metalness: 0,
      transparent: true,
      opacity: 0.42,
    }),
  );
  backdrop.position.set(sceneCenter.x, sceneCenter.y, -0.26);
  root.add(backdrop);

  if (layers.areas) {
    const areas = [...model.map.areas].sort((left, right) => {
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
    for (const area of areas) {
      if (area.polygon.length < 3) {
        continue;
      }

      const selected = selectionTarget?.kind === "area" && selectionTarget.areaId === area.areaId;
      const form = area.formType;
      const material = areaMaterial(area, selected);
      const shape = polygonToShape(area.polygon);
      const geometry =
        form === "flat"
          ? new THREE.ShapeGeometry(shape)
          : new THREE.ExtrudeGeometry(shape, {
              depth: form === "recessed" ? Math.max(area.depthHint, area.heightHint, 0.35) : Math.max(area.heightHint, 0.35),
              bevelEnabled: false,
              steps: 1,
            });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.z = form === "recessed" ? -Math.max(area.depthHint, area.heightHint, 0.35) : 0.04;
      mesh.userData.selectable = { kind: "area", id: area.areaId } satisfies SelectableMeta;
      root.add(mesh);

      const outline = new THREE.LineLoop(
        outlineGeometry(area.polygon, form === "recessed" ? mesh.position.z + Math.max(area.depthHint, area.heightHint, 0.35) : 0.06),
        new THREE.LineBasicMaterial({
          color: selected ? "#2f6072" : areaOutlineColor(area),
          transparent: true,
          opacity: selected ? 0.95 : 0.62,
        }),
      );
      root.add(outline);

      if (form !== "flat") {
        const hitMesh = new THREE.Mesh(
          geometry.clone(),
          new THREE.MeshBasicMaterial({
            color: "#000000",
            transparent: true,
            opacity: 0,
            depthWrite: false,
          }),
        );
        hitMesh.position.copy(mesh.position);
        hitMesh.userData.selectable = { kind: "area", id: area.areaId } satisfies SelectableMeta;
        root.add(hitMesh);
      }
    }
  }

  if (layers.intersections) {
    for (const intersection of model.map.intersections) {
      if (intersection.polygon.length < 3) {
        continue;
      }

      const selected = selectionTarget?.kind === "intersection" && selectionTarget.intersectionId === intersection.intersectionId;
      const shape = polygonToShape(intersection.polygon);
      const mesh = new THREE.Mesh(
        new THREE.ShapeGeometry(shape),
        new THREE.MeshStandardMaterial({
          color: selected ? "#7d8e97" : "#646e75",
          roughness: 1,
          metalness: 0,
          transparent: true,
          opacity: 0.88,
        }),
      );
      mesh.position.z = 0.1;
      mesh.userData.selectable = { kind: "intersection", id: intersection.intersectionId } satisfies SelectableMeta;
      root.add(mesh);

      const outline = new THREE.LineLoop(
        outlineGeometry(intersection.polygon, 0.14),
        new THREE.LineBasicMaterial({
          color: selected ? "#f0d659" : "#8b8f91",
          transparent: true,
          opacity: selected ? 0.95 : 0.72,
        }),
      );
      root.add(outline);
    }
  }

  if (layers.roads) {
    for (const road of model.map.roads) {
      if (road.centerline.length < 2) {
        continue;
      }

      const selected = selectionTarget?.kind === "road" && selectionTarget.roadId === road.roadId;
      const roadWidth = roadWidthForClass(road.roadClass, road.laneCount);
      for (let index = 0; index < road.centerline.length - 1; index += 1) {
        const start = road.centerline[index];
        const end = road.centerline[index + 1];
        const ribbon = roadSegmentMesh(start, end, roadWidth * 1.12, selected ? "#6f7a80" : "#4b5459", 0.06);
        const core = roadSegmentMesh(start, end, roadWidth * 0.72, selected ? "#f6f0aa" : road.blocked ? "#a1523d" : "#5e686f", 0.08);
        const hit = roadSegmentMesh(start, end, roadWidth * 1.28, "#000000", 0.12, true);
        ribbon.userData.selectable = { kind: "road", id: road.roadId } satisfies SelectableMeta;
        core.userData.selectable = { kind: "road", id: road.roadId } satisfies SelectableMeta;
        hit.userData.selectable = { kind: "road", id: road.roadId } satisfies SelectableMeta;
        root.add(ribbon, core, hit);
      }
    }
  }

  if (layers.vehicles) {
    for (const vehicle of model.map.vehicles) {
      const selected = selectedVehicleIdSet.has(vehicle.vehicleId);
      const vehicleMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.8, 0.5, 0.36),
        new THREE.MeshStandardMaterial({
          color: vehicleColor(vehicle.stateClass, selected),
          roughness: 0.92,
          metalness: 0.04,
          flatShading: true,
        }),
      );
      vehicleMesh.position.set(vehicle.position[0], vehicle.position[1], 1.32);
      vehicleMesh.rotation.z = Math.PI / 8;
      vehicleMesh.scale.setScalar(selected ? 1.16 : 1);
      vehicleMesh.userData.selectable = { kind: "vehicle", id: vehicle.vehicleId } satisfies SelectableMeta;
      root.add(vehicleMesh);
    }
  }

  if (layers.routes && activeRoutePreview !== null && activeRoutePreview.pathPoints.length > 0) {
    const preview = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(activeRoutePreview.pathPoints.map((point) => new THREE.Vector3(point[0], point[1], 1.55))),
      new THREE.LineBasicMaterial({
        color: activeRoutePreview.isActionable ? "#f0db39" : "#d38b3b",
        transparent: true,
        opacity: 0.96,
      }),
    );
    root.add(preview);

    for (const [index, point] of activeRoutePreview.pathPoints.entries()) {
      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(index === 0 ? 0.16 : 0.12, 16, 16),
        new THREE.MeshStandardMaterial({
          color: index === 0 ? "#f4f2bf" : "#f0db39",
          roughness: 0.9,
          metalness: 0,
        }),
      );
      marker.position.set(point[0], point[1], 1.58);
      root.add(marker);
    }

    if (activeRoutePreview.destinationPoint !== null) {
      const destination = new THREE.Mesh(
        new THREE.CylinderGeometry(0.18, 0.22, 0.28, 16),
        new THREE.MeshStandardMaterial({
          color: "#fff2a8",
          roughness: 0.88,
          metalness: 0,
        }),
      );
      destination.position.set(activeRoutePreview.destinationPoint[0], activeRoutePreview.destinationPoint[1], 1.52);
      root.add(destination);
    }
  }

  if (activeMode === "traffic") {
    const trafficOverlay = new THREE.Group();
    trafficOverlay.name = "traffic-overlay";
    for (const roadState of model.traffic.roadStates) {
      const road = model.map.roads.find((entry) => entry.roadId === roadState.roadId);
      if (road === undefined || road.centerline.length < 2 || roadState.congestionIntensity <= 0) {
        continue;
      }

      for (let index = 0; index < road.centerline.length - 1; index += 1) {
        const start = road.centerline[index];
        const end = road.centerline[index + 1];
        const congestion = roadSegmentMesh(
          start,
          end,
          roadWidthForClass(road.roadClass, road.laneCount) * 0.92,
          congestionColor(roadState.congestionIntensity),
          0.16,
        );
        trafficOverlay.add(congestion);
      }
    }
    root.add(trafficOverlay);
  }
}

function areaMaterial(area: LiveBundleViewModel["map"]["areas"][number], selected: boolean): THREE.MeshStandardMaterial {
  const colors = {
    flat: area.category === "boundary" ? "#d8d0c7" : "#d5d1c4",
    raised: area.category === "terrain" ? "#b89c77" : "#acaa99",
    recessed: area.category === "terrain" ? "#7b6a59" : "#6d6f70",
    structure_mass: "#e0ddd4",
  } as const;

  const color = selected ? "#d9c056" : colors[area.formType];
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.96,
    metalness: 0.02,
    flatShading: area.formType !== "flat",
    transparent: area.category === "boundary" || area.category === "hazard",
    opacity: area.category === "boundary" ? 0.42 : area.category === "hazard" ? 0.4 : 0.96,
  });
}

function areaOutlineColor(area: LiveBundleViewModel["map"]["areas"][number]): string {
  if (area.category === "boundary") {
    return "#808789";
  }
  if (area.category === "hazard") {
    return "#a35337";
  }
  if (area.formType === "recessed") {
    return "#51433a";
  }
  if (area.formType === "raised") {
    return "#8d745f";
  }
  if (area.formType === "structure_mass") {
    return "#8a8f95";
  }
  return "#8c8a81";
}

function vehicleColor(stateClass: "moving" | "waiting" | "idle", selected: boolean): string {
  if (selected) {
    return "#f2d44c";
  }

  switch (stateClass) {
    case "moving":
      return "#d7a93a";
    case "waiting":
      return "#7e9ba8";
    case "idle":
    default:
      return "#b9b1a6";
  }
}

function congestionColor(intensity: number): string {
  if (intensity >= 0.75) {
    return "#b45133";
  }
  if (intensity >= 0.45) {
    return "#d08d35";
  }
  return "#c6aa3c";
}

function roadWidthForClass(roadClass: string, laneCount: number): number {
  const laneWidth = Math.max(laneCount, 1) * 0.72;
  switch (roadClass) {
    case "haul":
      return Math.max(laneWidth, 2.1);
    case "service":
      return Math.max(laneWidth * 0.9, 1.2);
    case "connector":
      return Math.max(laneWidth * 0.85, 1.1);
    default:
      return Math.max(laneWidth, 1.3);
  }
}

function roadSegmentMesh(
  start: Point2,
  end: Point2,
  width: number,
  color: string,
  z: number,
  invisible = false,
): THREE.Mesh {
  const geometry = ribbonGeometry(start, end, width);
  const material = invisible
    ? new THREE.MeshBasicMaterial({ visible: false })
    : new THREE.MeshStandardMaterial({
        color,
        roughness: 0.94,
        metalness: 0.02,
      });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.z = z;
  return mesh;
}

function ribbonGeometry(start: Point2, end: Point2, width: number): THREE.BufferGeometry {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const length = Math.max(Math.hypot(dx, dy), 0.001);
  const ux = dx / length;
  const uy = dy / length;
  const px = -uy * width * 0.5;
  const py = ux * width * 0.5;
  const geometry = new THREE.BufferGeometry();
  const vertices = new Float32Array([
    start[0] + px,
    start[1] + py,
    0,
    start[0] - px,
    start[1] - py,
    0,
    end[0] + px,
    end[1] + py,
    0,
    end[0] - px,
    end[1] - py,
    0,
  ]);
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  geometry.setIndex([0, 1, 2, 2, 1, 3]);
  geometry.computeVertexNormals();
  return geometry;
}

function outlineGeometry(points: Point2[], z: number): THREE.BufferGeometry {
  const vectors = points.map(([x, y]) => new THREE.Vector3(x, y, z));
  return new THREE.BufferGeometry().setFromPoints([...vectors, vectors[0]]);
}

function polygonToShape(points: Point2[]): THREE.Shape {
  const shape = new THREE.Shape();
  points.forEach(([x, y], index) => {
    if (index === 0) {
      shape.moveTo(x, y);
    } else {
      shape.lineTo(x, y);
    }
  });
  shape.closePath();
  return shape;
}

function computeFitZoom(bounds: SceneBounds, aspect: number): number {
  const paddedWidth = Math.max(bounds.width * FIT_PADDING_FACTOR, 1);
  const paddedHeight = Math.max(bounds.height * FIT_PADDING_FACTOR, 1);
  const baseWidth = BASE_ORTHO_HEIGHT * aspect;
  const baseHeight = BASE_ORTHO_HEIGHT;
  return clamp(Math.min(baseWidth / paddedWidth, baseHeight / paddedHeight), 0.2, 8.5);
}

function computeOrbitRadius(bounds: SceneBounds, radiusMultiplier: number): number {
  return Math.max(bounds.width, bounds.height, 1) * radiusMultiplier;
}

function orbitRadiusScaleFor(sceneViewMode: CameraState["sceneViewMode"]): number {
  return sceneViewMode === "birdseye" ? BIRDSEYE_ORBIT_RADIUS_SCALE : ISO_ORBIT_RADIUS_SCALE;
}

function positionFromAngles(
  target: THREE.Vector3,
  radius: number,
  azimuth: number,
  polar: number,
): THREE.Vector3 {
  const sinPolar = Math.sin(polar);
  const x = target.x + radius * Math.cos(azimuth) * sinPolar;
  const y = target.y + radius * Math.sin(azimuth) * sinPolar;
  const z = target.z + radius * Math.cos(polar);
  return new THREE.Vector3(x, y, z);
}

function boundsCenter(bounds: SceneBounds): { x: number; y: number } {
  return {
    x: bounds.minX + bounds.width / 2,
    y: bounds.minY + bounds.height / 2,
  };
}

function cameraSignature(camera: CameraState): string {
  return [
    camera.x.toFixed(3),
    camera.y.toFixed(3),
    camera.zoom.toFixed(3),
    camera.azimuth.toFixed(3),
    camera.polar.toFixed(3),
    camera.sceneViewMode,
  ].join(":");
}

function readCameraStateFromControls(
  controls: OrbitControls,
  camera: THREE.OrthographicCamera,
  fitZoom: number,
  sceneViewMode: CameraState["sceneViewMode"],
): CameraState {
  const target = controls.target;
  return {
    x: target.x,
    y: target.y,
    zoom: clamp(camera.zoom / fitZoom, MIN_CAMERA_ZOOM_FACTOR, MAX_CAMERA_ZOOM_FACTOR),
    sceneViewMode,
    azimuth: controls.getAzimuthalAngle(),
    polar: controls.getPolarAngle(),
  };
}

function worldFormSortRank(formType: LiveBundleViewModel["map"]["areas"][number]["formType"]): number {
  switch (formType) {
    case "structure_mass":
      return 0;
    case "raised":
      return 1;
    case "flat":
      return 2;
    case "recessed":
      return 3;
    default:
      return 4;
  }
}

function areaSortRank(category: string): number {
  switch (category) {
    case "structure":
      return 0;
    case "terrain":
      return 1;
    case "zone":
      return 2;
    case "boundary":
      return 3;
    case "hazard":
      return 4;
    default:
      return 5;
  }
}

function disposeObject3D(object: THREE.Object3D): void {
  object.traverse((node: THREE.Object3D) => {
    if (node instanceof THREE.Mesh) {
      const geometry = node.geometry;
      geometry.dispose();
      if (Array.isArray(node.material)) {
        for (const material of node.material) {
          material.dispose();
        }
      } else {
        node.material.dispose();
      }
    }
    if (node instanceof THREE.LineSegments || node instanceof THREE.Line || node instanceof THREE.Points) {
      const geometry = node.geometry;
      geometry.dispose();
      const material = node.material;
      if (Array.isArray(material)) {
        for (const entry of material) {
          entry.dispose();
        }
      } else {
        material.dispose();
      }
    }
  });
  while (object.children.length > 0) {
    object.remove(object.children[0]);
  }
}

function clamp(value: number, minValue: number, maxValue: number): number {
  return Math.min(Math.max(value, minValue), maxValue);
}
