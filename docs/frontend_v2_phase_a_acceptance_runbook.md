# Frontend v2 Phase A Acceptance Runbook

This note is the short operator-facing companion to `docs/execution_plan.md` step 55.
It explains how to launch the mining live run, what each walkthrough proves, and what remains intentionally limited after Phase A.

## Launch

1. Build the Frontend v2 workspace:

   ```bash
   cd frontend/frontend_v2
   npm run build
   ```

2. Launch a live mining session from the repo root:

   ```bash
   python3 -m autonomous_ops_sim.cli live --scenario scenarios/showpiece_pack/01_mine_ore_shift.json
   ```

   The live app serves Frontend v2 at `/frontend_v2/index.html?bundle=/live_session_bundle.json`.
   Add `--no-browser` if you want the command to print the launch path instead of opening a browser.

## What The Walkthroughs Prove

### 1. Baseline map walkthrough

Proves the product opens as a quiet, map-first surface and that the map controls are usable:

- live bundle loads
- pan, zoom, fit, and focus work
- minimap is integrated
- the default map stays readable instead of noisy

### 2. Inspection walkthrough

Proves selection and inspection are map-driven and compact:

- moving vehicles can be selected and inspected
- roads and areas can be selected and inspected
- traffic context appears when the traffic mode surface is active
- the map remains readable while inspection details are shown

### 3. Golden operator workflow

Proves the core command loop is real and grounded in simulator truth:

- select a vehicle
- set a destination
- create a preview
- inspect the preview
- commit the command
- observe the result after the bundle refreshes

### 4. Mode walkthrough

Proves each Frontend v2 mode has a real product role:

- Operate for command and preview work
- Traffic for congestion and queue context
- Fleet for multi-vehicle understanding and batch hooks
- Editor for authoring baseline, validation, save/reload surface
- Analyze for explanation, anomaly surfacing, and diagnostics aggregation

## Known Limits After Phase A

- Editor mode is a baseline home, not a full authoring tool yet.
- Analyze mode is an explanation surface, not a deep AI assistant.
- Fleet batch actions are hooks for later work, not completed fleet operations.
- Traffic mode is a readable baseline, not a full traffic analyst workstation.
- The frontend remains a consumer of authoritative simulator truth; it does not own runtime state, final route truth, or conflict truth.

## Acceptance Judgment

Phase A is complete when the mining walkthrough feels externally presentable, the mode surfaces feel intentional, and the map remains the primary operator surface throughout.
