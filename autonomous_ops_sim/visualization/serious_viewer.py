from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import json
from pathlib import Path
from typing import Any


SERIOUS_VIEWER_FOUNDATION_VERSION = 1


@dataclass(frozen=True)
class ViewerFoundationPlan:
    """Chosen medium-term viewer direction on top of the Simulation API."""

    foundation_version: int
    recommended_stack: str
    rendering_strategy: str
    transport_surface: str
    rationale: tuple[str, ...]


def build_viewer_foundation_plan() -> ViewerFoundationPlan:
    """Return the selected viewer foundation direction for the next phase."""

    return ViewerFoundationPlan(
        foundation_version=SERIOUS_VIEWER_FOUNDATION_VERSION,
        recommended_stack="web_client",
        rendering_strategy="responsive_svg_scene",
        transport_surface="simulation_api_bundle_json",
        rationale=(
            "Higher rendering and interaction ceiling than the Tk prototype.",
            "Consumes the versioned Simulation API boundary without simulator rewrites.",
            "Keeps future paths open for richer browser or external frontend clients.",
        ),
    )


def load_simulation_api_bundle(path: str | Path) -> dict[str, Any]:
    """Load and validate one exported Simulation API bundle JSON file."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Simulation API bundle must decode to an object")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Simulation API bundle is missing metadata")
    if metadata.get("api_version") != 1:
        raise ValueError(
            "Unsupported Simulation API version: "
            f"{metadata.get('api_version')}"
        )
    surface_name = metadata.get("surface_name")
    if surface_name not in {"replay_bundle", "live_session_bundle", "live_sync_bundle"}:
        raise ValueError(f"Unsupported Simulation API surface: {surface_name}")
    return payload


def build_serious_viewer_html(
    bundle: dict[str, Any],
    *,
    title: str | None = None,
) -> str:
    """Render a standalone serious-viewer HTML document from a Simulation API bundle."""

    metadata = _require_object(bundle, "metadata")
    surface_name = _require_string(metadata, "surface_name")
    plan = build_viewer_foundation_plan()
    viewer_title = title or f"Autonomous Ops Serious Viewer ({surface_name})"
    script_payload = html.escape(json.dumps(bundle, sort_keys=True))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(viewer_title)}</title>
  <style>
    :root {{
      --bg: #f3efe4;
      --panel: rgba(255, 252, 245, 0.9);
      --panel-strong: #fffaf0;
      --ink: #1e2a36;
      --muted: #5e6a73;
      --accent: #0d6c74;
      --accent-soft: #d5ece8;
      --alert: #c65b3d;
      --alert-soft: #f7dfd6;
      --line: #cdbfa9;
      --node: #9c7a4d;
      --vehicle: #0b5fff;
      --vehicle-selected: #d94841;
      --edge: #7f8b92;
      --edge-blocked: #c65b3d;
      --shadow: 0 20px 48px rgba(36, 42, 48, 0.12);
      --radius: 18px;
      --mono: "SFMono-Regular", "Menlo", monospace;
      --sans: "Avenir Next", "Segoe UI", sans-serif;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(13, 108, 116, 0.12), transparent 30%),
        radial-gradient(circle at bottom right, rgba(198, 91, 61, 0.12), transparent 28%),
        linear-gradient(180deg, #f9f6ef 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: var(--sans);
    }}

    .shell {{
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr);
      min-height: 100vh;
      gap: 20px;
      padding: 22px;
    }}

    .stage,
    .sidebar {{
      background: var(--panel);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(105, 96, 78, 0.14);
      border-radius: 24px;
      box-shadow: var(--shadow);
    }}

    .stage {{
      padding: 18px 18px 14px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .sidebar {{
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      flex-wrap: wrap;
    }}

    h1 {{
      margin: 0;
      font-size: 1.55rem;
      letter-spacing: -0.03em;
    }}

    .eyebrow,
    .meta,
    .tiny {{
      color: var(--muted);
    }}

    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 0.73rem;
      margin-bottom: 6px;
    }}

    .badge-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .badge {{
      border-radius: 999px;
      padding: 8px 12px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.8rem;
      font-weight: 700;
    }}

    .badge.alert {{
      background: var(--alert-soft);
      color: var(--alert);
    }}

    .viewport {{
      position: relative;
      flex: 1;
      min-height: 420px;
      border-radius: 20px;
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.72), rgba(242,236,224,0.92)),
        repeating-linear-gradient(
          0deg,
          rgba(94, 106, 115, 0.04),
          rgba(94, 106, 115, 0.04) 1px,
          transparent 1px,
          transparent 48px
        ),
        repeating-linear-gradient(
          90deg,
          rgba(94, 106, 115, 0.04),
          rgba(94, 106, 115, 0.04) 1px,
          transparent 1px,
          transparent 48px
        );
      border: 1px solid rgba(105, 96, 78, 0.12);
    }}

    svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}

    .card {{
      background: var(--panel-strong);
      border: 1px solid rgba(105, 96, 78, 0.14);
      border-radius: var(--radius);
      padding: 14px;
    }}

    .card h2 {{
      margin: 0 0 10px;
      font-size: 0.95rem;
      letter-spacing: 0.01em;
    }}

    .timeline-header,
    .inspector-row {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
    }}

    .timeline-input {{
      width: 100%;
      accent-color: var(--accent);
    }}

    .list,
    .inspector-list {{
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}

    .list li,
    .inspector-item {{
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(213, 236, 232, 0.45);
      color: var(--ink);
      font-size: 0.9rem;
    }}

    .list li strong,
    .inspector-item strong {{
      display: block;
      margin-bottom: 2px;
    }}

    .mono {{
      font-family: var(--mono);
      font-size: 0.82rem;
    }}

    .footer-note {{
      font-size: 0.83rem;
      color: var(--muted);
      line-height: 1.45;
    }}

    .vehicle-chip {{
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease;
    }}

    .vehicle-chip:hover {{
      transform: scale(1.04);
    }}

    .overlay {{
      position: absolute;
      left: 16px;
      bottom: 16px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      pointer-events: none;
    }}

    .overlay-pill {{
      pointer-events: auto;
      border-radius: 999px;
      background: rgba(255, 250, 240, 0.92);
      border: 1px solid rgba(105, 96, 78, 0.16);
      padding: 8px 11px;
      font-size: 0.8rem;
    }}

    @media (max-width: 980px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}

      .viewport {{
        min-height: 360px;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="stage">
      <div class="topbar">
        <div>
          <div class="eyebrow">Serious Viewer Foundation</div>
          <h1>{html.escape(viewer_title)}</h1>
          <div class="meta">Medium-term path: {html.escape(plan.recommended_stack)} via {html.escape(plan.transport_surface)}</div>
        </div>
        <div class="badge-row">
          <span class="badge" id="surfaceBadge"></span>
          <span class="badge" id="seedBadge"></span>
          <span class="badge alert" id="timelineBadge"></span>
        </div>
      </div>
      <div class="viewport">
        <svg id="viewerScene" viewBox="0 0 1200 720" aria-label="Simulation viewer scene"></svg>
        <div class="overlay">
          <div class="overlay-pill" id="overlayTrigger"></div>
          <div class="overlay-pill" id="overlayEdges"></div>
          <div class="overlay-pill" id="overlayVehicles"></div>
        </div>
      </div>
      <div class="card">
        <div class="timeline-header">
          <h2>Timeline</h2>
          <div class="mono" id="timelineLabel"></div>
        </div>
        <div class="badge-row" style="margin-bottom:10px">
          <button class="badge" id="playButton" type="button">Play</button>
          <button class="badge" id="pauseButton" type="button">Pause</button>
        </div>
        <input class="timeline-input" id="timelineInput" type="range" min="0" value="0">
      </div>
    </section>
    <aside class="sidebar">
      <section class="card">
        <h2>Operational Overlay</h2>
        <ul class="list" id="overlayList"></ul>
      </section>
      <section class="card">
        <h2>Vehicle Inspector</h2>
        <div class="tiny" id="inspectorHint">Select a vehicle from the scene or list.</div>
        <div class="inspector-list" id="vehicleList"></div>
      </section>
      <section class="card">
        <h2>Foundation Rationale</h2>
        <ul class="list">
          <li>{html.escape(plan.rationale[0])}</li>
          <li>{html.escape(plan.rationale[1])}</li>
          <li>{html.escape(plan.rationale[2])}</li>
        </ul>
      </section>
      <div class="footer-note">
        This viewer intentionally consumes only the versioned Simulation API bundle. It is a higher-ceiling frontend foundation, not a new simulator authority surface.
      </div>
    </aside>
  </div>
  <script id="simulation-api-bundle" type="application/json">{script_payload}</script>
  <script>
    const bundle = JSON.parse(document.getElementById("simulation-api-bundle").textContent);
    const metadata = bundle.metadata;
    const surfaceName = metadata.surface_name;
    const mapSurface = bundle.map_surface;
    const renderGeometry = bundle.render_geometry || {{ roads: [], intersections: [], areas: [] }};
    const motionSegments = Array.isArray(bundle.motion_segments) ? bundle.motion_segments : [];
    const timelineEntries = buildTimelineEntries(bundle);
    let selectedVehicleId = null;
    let timelineIndex = Math.max(0, timelineEntries.length - 1);
    let currentTimeS = resolveFinalTime(bundle, timelineEntries);
    let isPlaying = false;
    let lastAnimationTimestampMs = null;

    document.getElementById("surfaceBadge").textContent = surfaceName.replaceAll("_", " ");
    document.getElementById("seedBadge").textContent = `seed ${{String(bundle.seed)}}`;
    document.getElementById("timelineBadge").textContent = `${{motionSegments.length}} motion segments`;

    const slider = document.getElementById("timelineInput");
    slider.max = String(Math.max(1, Math.round(currentTimeS * 1000.0)));
    slider.value = String(Math.round(currentTimeS * 1000.0));
    slider.addEventListener("input", (event) => {{
      currentTimeS = Number(event.target.value) / 1000.0;
      timelineIndex = findTimelineIndexForTime(currentTimeS);
      render();
    }});
    document.getElementById("playButton").addEventListener("click", () => {{
      if (currentTimeS >= resolveFinalTime(bundle, timelineEntries)) {{
        currentTimeS = 0.0;
      }}
      isPlaying = true;
      lastAnimationTimestampMs = null;
      window.requestAnimationFrame(tickPlayback);
    }});
    document.getElementById("pauseButton").addEventListener("click", () => {{
      isPlaying = false;
      lastAnimationTimestampMs = null;
    }});

    function buildTimelineEntries(payload) {{
      if (payload.metadata.surface_name === "replay_bundle") {{
        return payload.replay_timeline.map((frame) => ({{
          kind: "replay_frame",
          timestamp_s: frame.timestamp_s,
          label: `${{frame.trigger.source}}:${{frame.trigger.event_name}}`,
          blocked_edge_ids: frame.blocked_edge_ids,
          vehicles: frame.vehicles,
          trigger: frame.trigger,
        }}));
      }}
      if (payload.metadata.surface_name === "live_sync_bundle") {{
        const initial = {{
          kind: "snapshot",
          timestamp_s: payload.snapshot.simulated_time_s,
          label: "live snapshot",
          blocked_edge_ids: payload.snapshot.blocked_edge_ids,
          vehicles: payload.snapshot.vehicles,
          trigger: {{ source: "snapshot", event_name: "live_snapshot" }},
        }};
        return [initial].concat(payload.updates.map((update) => ({{
          kind: "live_update",
          timestamp_s: update.timestamp_s,
          label: `${{update.trigger.source}}:${{update.trigger.event_name}}`,
          blocked_edge_ids: update.blocked_edge_ids,
          vehicles: update.vehicles,
          trigger: update.trigger,
        }})));
      }}

      const initial = {{
        kind: "snapshot",
        timestamp_s: payload.snapshot.simulated_time_s,
        label: "live snapshot",
        blocked_edge_ids: payload.snapshot.blocked_edge_ids,
        vehicles: payload.snapshot.vehicles,
        trigger: {{ source: "snapshot", event_name: "live_snapshot" }},
      }};
      const sessions = payload.session_history.map((sessionStep) => ({{
        kind: "session_step",
        timestamp_s: sessionStep.completed_at_s,
        label: `session:${{sessionStep.sequence}}`,
        blocked_edge_ids: payload.snapshot.blocked_edge_ids,
        vehicles: payload.snapshot.vehicles,
        trigger: {{ source: "session", event_name: "session_advance", session_step: sessionStep }},
      }}));
      return [initial].concat(sessions);
    }}

    function resolveFinalTime(payload, entries) {{
      if (typeof payload.final_time_s === "number") {{
        return payload.final_time_s;
      }}
      if (typeof payload.simulated_time_s === "number") {{
        return payload.simulated_time_s;
      }}
      if (payload.snapshot && typeof payload.snapshot.simulated_time_s === "number") {{
        return payload.snapshot.simulated_time_s;
      }}
      if (entries.length === 0) {{
        return 0.0;
      }}
      return Number(entries[entries.length - 1].timestamp_s);
    }}

    function findTimelineIndexForTime(timestampS) {{
      let index = 0;
      for (let currentIndex = 0; currentIndex < timelineEntries.length; currentIndex += 1) {{
        if (Number(timelineEntries[currentIndex].timestamp_s) > timestampS) {{
          break;
        }}
        index = currentIndex;
      }}
      return index;
    }}

    function timelineEntryForTime(timestampS) {{
      return timelineEntries[findTimelineIndexForTime(timestampS)];
    }}

    function buildSceneBounds(nodes) {{
      const xs = nodes.map((node) => Number(node.position[0]));
      const ys = nodes.map((node) => Number(node.position[1]));
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      return {{
        minX, maxX, minY, maxY,
        width: Math.max(1, maxX - minX),
        height: Math.max(1, maxY - minY),
      }};
    }}

    function project(position, bounds) {{
      const pad = 90;
      const usableWidth = 1200 - pad * 2;
      const usableHeight = 720 - pad * 2;
      const x = pad + ((Number(position[0]) - bounds.minX) / bounds.width) * usableWidth;
      const y = 720 - (pad + ((Number(position[1]) - bounds.minY) / bounds.height) * usableHeight);
      return {{ x, y }};
    }}

    function render() {{
      const current = timelineEntryForTime(currentTimeS);
      const sampledVehicles = sampleVehiclesAtTime(currentTimeS, current.vehicles);
      const svg = document.getElementById("viewerScene");
      svg.innerHTML = "";

      const bounds = buildSceneBounds(mapSurface.nodes);
      const edgeGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const areaGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const intersectionGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const nodeGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const vehicleGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const blockedEdges = new Set(current.blocked_edge_ids);

      for (const area of renderGeometry.areas || []) {{
        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        const points = area.polygon.map((position) => {{
          const point = project(position, bounds);
          return `${{point.x}},${{point.y}}`;
        }}).join(" ");
        polygon.setAttribute("points", points);
        polygon.setAttribute("fill", area.kind.includes("building") ? "rgba(94, 106, 115, 0.2)" : "rgba(13, 108, 116, 0.1)");
        polygon.setAttribute("stroke", "rgba(30, 42, 54, 0.2)");
        polygon.setAttribute("stroke-width", "2");
        areaGroup.appendChild(polygon);
      }}

      for (const intersection of renderGeometry.intersections || []) {{
        const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        const points = intersection.polygon.map((position) => {{
          const point = project(position, bounds);
          return `${{point.x}},${{point.y}}`;
        }}).join(" ");
        polygon.setAttribute("points", points);
        polygon.setAttribute("fill", "rgba(205, 191, 169, 0.45)");
        polygon.setAttribute("stroke", "rgba(126, 107, 72, 0.4)");
        polygon.setAttribute("stroke-width", "2");
        intersectionGroup.appendChild(polygon);
      }}

      for (const road of renderGeometry.roads || []) {{
        const points = road.centerline.map((position) => project(position, bounds));
        const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        path.setAttribute(
          "points",
          points.map((point) => `${{point.x}},${{point.y}}`).join(" "),
        );
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", road.directionality === "two_way" ? "#73818a" : "#81929b");
        path.setAttribute("stroke-width", String(Math.max(8, Number(road.width_m) * 7)));
        path.setAttribute("stroke-linecap", "round");
        path.setAttribute("stroke-linejoin", "round");
        edgeGroup.appendChild(path);

        if (road.directionality === "two_way") {{
          const laneMark = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
          laneMark.setAttribute(
            "points",
            points.map((point) => `${{point.x}},${{point.y}}`).join(" "),
          );
          laneMark.setAttribute("fill", "none");
          laneMark.setAttribute("stroke", "rgba(255, 250, 240, 0.8)");
          laneMark.setAttribute("stroke-width", "2");
          laneMark.setAttribute("stroke-dasharray", "10 8");
          laneMark.setAttribute("stroke-linecap", "round");
          laneMark.setAttribute("stroke-linejoin", "round");
          edgeGroup.appendChild(laneMark);
        }}
      }}

      for (const edge of mapSurface.edges) {{
        const startNode = mapSurface.nodes.find((node) => node.node_id === edge.start_node_id);
        const endNode = mapSurface.nodes.find((node) => node.node_id === edge.end_node_id);
        const start = project(startNode.position, bounds);
        const end = project(endNode.position, bounds);
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", String(start.x));
        line.setAttribute("y1", String(start.y));
        line.setAttribute("x2", String(end.x));
        line.setAttribute("y2", String(end.y));
        line.setAttribute("stroke", blockedEdges.has(edge.edge_id) ? "var(--edge-blocked)" : "var(--edge)");
        line.setAttribute("stroke-width", blockedEdges.has(edge.edge_id) ? "10" : "7");
        line.setAttribute("stroke-linecap", "round");
        edgeGroup.appendChild(line);
      }}

      for (const node of mapSurface.nodes) {{
        const point = project(node.position, bounds);
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", String(point.x));
        circle.setAttribute("cy", String(point.y));
        circle.setAttribute("r", "10");
        circle.setAttribute("fill", "var(--node)");
        nodeGroup.appendChild(circle);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(point.x + 14));
        label.setAttribute("y", String(point.y - 14));
        label.setAttribute("fill", "var(--ink)");
        label.setAttribute("font-size", "16");
        label.textContent = `${{node.node_type}} #${{node.node_id}}`;
        nodeGroup.appendChild(label);
      }}

      sampledVehicles.forEach((vehicle) => {{
        const point = project(vehicle.position, bounds);
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("class", "vehicle-chip");
        group.addEventListener("click", () => {{
          selectedVehicleId = vehicle.vehicle_id;
          renderInspector(current);
          render();
        }});

        const body = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        body.setAttribute("cx", String(point.x));
        body.setAttribute("cy", String(point.y));
        body.setAttribute("r", selectedVehicleId === vehicle.vehicle_id ? "18" : "14");
        body.setAttribute("fill", selectedVehicleId === vehicle.vehicle_id ? "var(--vehicle-selected)" : "var(--vehicle)");
        body.setAttribute("stroke", "white");
        body.setAttribute("stroke-width", "4");
        group.appendChild(body);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", String(point.x + 20));
        label.setAttribute("y", String(point.y + 6));
        label.setAttribute("fill", "var(--ink)");
        label.setAttribute("font-size", "18");
        label.textContent = `V${{vehicle.vehicle_id}}`;
        group.appendChild(label);
        vehicleGroup.appendChild(group);
      }});

      svg.appendChild(areaGroup);
      svg.appendChild(edgeGroup);
      svg.appendChild(intersectionGroup);
      svg.appendChild(nodeGroup);
      svg.appendChild(vehicleGroup);

      document.getElementById("timelineLabel").textContent =
        `time ${{Number(currentTimeS).toFixed(2)}}s  keyframe ${{timelineIndex + 1}} / ${{timelineEntries.length}}`;
      document.getElementById("overlayTrigger").textContent = `trigger ${{
        current.label
      }}`;
      document.getElementById("overlayEdges").textContent = `blocked edges ${{
        current.blocked_edge_ids.length
      }}`;
      document.getElementById("overlayVehicles").textContent = `vehicles ${{
        sampledVehicles.length
      }}`;
      slider.value = String(Math.round(currentTimeS * 1000.0));

      renderOverlay(current);
      renderInspector(sampledVehicles);
      if (selectedVehicleId === null && sampledVehicles.length > 0) {{
        selectedVehicleId = sampledVehicles[0].vehicle_id;
        renderInspector(sampledVehicles);
      }}
    }}

    function renderOverlay(current) {{
      const overlayList = document.getElementById("overlayList");
      const commandCount = Array.isArray(bundle.command_results) ? bundle.command_results.length : 0;
      const traceCount = Array.isArray(bundle.trace_events) ? bundle.trace_events.length : 0;
      const sessionCount = Array.isArray(bundle.session_history) ? bundle.session_history.length : 0;
      const lines = [
        {{
          label: "Current trigger",
          value: current.label,
        }},
        {{
          label: "Roads",
          value: String((renderGeometry.roads || []).length),
        }},
        {{
          label: "Areas",
          value: String((renderGeometry.areas || []).length),
        }},
        {{
          label: "Command results",
          value: String(commandCount),
        }},
        {{
          label: "Trace events",
          value: String(traceCount),
        }},
        {{
          label: "Session steps",
          value: String(sessionCount),
        }},
        {{
          label: "Blocked edges",
          value: current.blocked_edge_ids.join(", ") || "none",
        }},
      ];
      overlayList.innerHTML = lines.map((item) =>
        `<li><strong>${{escapeHtml(item.label)}}</strong>${{escapeHtml(item.value)}}</li>`
      ).join("");
    }}

    function renderInspector(vehicles) {{
      const vehicleList = document.getElementById("vehicleList");
      const inspectorHint = document.getElementById("inspectorHint");
      const selectedVehicle = vehicles.find((vehicle) => vehicle.vehicle_id === selectedVehicleId) || null;
      if (!selectedVehicle) {{
        inspectorHint.textContent = "No vehicle selected for this timeline step.";
      }} else {{
        inspectorHint.textContent = `Inspecting vehicle ${{selectedVehicle.vehicle_id}} at ${{Number(currentTimeS).toFixed(2)}}s`;
      }}

      vehicleList.innerHTML = vehicles.map((vehicle) => {{
        const selected = vehicle.vehicle_id === selectedVehicleId;
        const buttonBackground = selected
          ? "rgba(198, 91, 61, 0.14)"
          : "rgba(213, 236, 232, 0.45)";
        return `
          <button
            class="inspector-item"
            style="text-align:left;border:none;cursor:pointer;background:${{buttonBackground}}"
            onclick="window.__selectVehicle(${{vehicle.vehicle_id}})"
          >
            <strong>Vehicle ${{vehicle.vehicle_id}}</strong>
            node ${{vehicle.node_id}} | ${{vehicle.operational_state}} | speed ${{Number(vehicle.speed || 0).toFixed(2)}} | [${{vehicle.position.map((value) => Number(value).toFixed(2)).join(", ")}}]
          </button>
        `;
      }}).join("");
    }}

    function sampleVehiclesAtTime(timestampS, baseVehicles) {{
      const sampled = new Map(baseVehicles.map((vehicle) => [vehicle.vehicle_id, {{
        ...vehicle,
        speed: 0.0,
        heading_rad: 0.0,
        is_interpolated: false,
      }}]));

      for (const segment of motionSegments) {{
        if (!(Number(segment.start_time_s) <= timestampS && timestampS <= Number(segment.end_time_s))) {{
          continue;
        }}
        const durationS = Number(segment.duration_s);
        if (durationS <= 0.0) {{
          continue;
        }}
        const normalized = Math.max(
          0.0,
          Math.min(1.0, (timestampS - Number(segment.start_time_s)) / durationS),
        );
        const eased = smoothstep(normalized);
        sampled.set(segment.vehicle_id, {{
          vehicle_id: segment.vehicle_id,
          node_id: segment.start_node_id,
          position: lerpPosition(segment.start_position, segment.end_position, eased),
          operational_state: "moving",
          speed: Number(segment.nominal_speed) * smoothstepDerivative(normalized),
          heading_rad: Number(segment.heading_rad),
          is_interpolated: true,
        }});
      }}

      return Array.from(sampled.values()).sort((left, right) => left.vehicle_id - right.vehicle_id);
    }}

    function smoothstep(progress) {{
      return progress * progress * (3.0 - 2.0 * progress);
    }}

    function smoothstepDerivative(progress) {{
      return 6.0 * progress * (1.0 - progress);
    }}

    function lerpPosition(startPosition, endPosition, progress) {{
      return [
        Number(startPosition[0]) + (Number(endPosition[0]) - Number(startPosition[0])) * progress,
        Number(startPosition[1]) + (Number(endPosition[1]) - Number(startPosition[1])) * progress,
        Number(startPosition[2]) + (Number(endPosition[2]) - Number(startPosition[2])) * progress,
      ];
    }}

    function tickPlayback(timestampMs) {{
      if (!isPlaying) {{
        return;
      }}
      if (lastAnimationTimestampMs === null) {{
        lastAnimationTimestampMs = timestampMs;
      }}
      const deltaS = (timestampMs - lastAnimationTimestampMs) / 1000.0;
      lastAnimationTimestampMs = timestampMs;
      currentTimeS = Math.min(resolveFinalTime(bundle, timelineEntries), currentTimeS + deltaS);
      timelineIndex = findTimelineIndexForTime(currentTimeS);
      render();
      if (currentTimeS >= resolveFinalTime(bundle, timelineEntries)) {{
        isPlaying = false;
        lastAnimationTimestampMs = null;
        return;
      }}
      window.requestAnimationFrame(tickPlayback);
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }}

    window.__selectVehicle = function(vehicleId) {{
      selectedVehicleId = vehicleId;
      render();
    }};

    render();
  </script>
</body>
</html>
"""


def export_serious_viewer_html(
    bundle: dict[str, Any],
    output_path: str | Path,
    *,
    title: str | None = None,
) -> Path:
    """Write a standalone serious-viewer HTML document to disk."""

    path = Path(output_path)
    path.write_text(build_serious_viewer_html(bundle, title=title), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for serious-viewer export."""

    parser = argparse.ArgumentParser(
        prog="autonomous-ops-serious-viewer",
        description="Export a standalone serious-viewer HTML file from a Simulation API bundle.",
    )
    parser.add_argument(
        "bundle_path",
        help="Path to a replay_bundle/live_session_bundle/live_sync_bundle JSON file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output HTML path. Defaults beside the JSON input.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional document title override.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for serious-viewer export."""

    parser = build_parser()
    args = parser.parse_args(argv)
    bundle_path = Path(args.bundle_path)
    bundle = load_simulation_api_bundle(bundle_path)
    output_path = (
        Path(args.output)
        if args.output is not None
        else bundle_path.with_suffix(".viewer.html")
    )
    export_serious_viewer_html(bundle, output_path, title=args.title)
    print(output_path)
    return 0


def _require_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


__all__ = [
    "SERIOUS_VIEWER_FOUNDATION_VERSION",
    "ViewerFoundationPlan",
    "build_parser",
    "build_serious_viewer_html",
    "build_viewer_foundation_plan",
    "export_serious_viewer_html",
    "load_simulation_api_bundle",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
