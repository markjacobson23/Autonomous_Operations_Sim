# Phase B Acceptance Runbook

This note is the short operator-facing companion to `docs/execution_plan.md` step 63.
It explains how to launch the Phase B mining walkthrough, what each walkthrough proves, and what remains intentionally limited after Phase B.

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

### 1. World-form walkthrough

Proves the scene reads like a real environment rather than a thin operational overlay:

- fit scene uses the new world-aware framing inputs
- roads, structures, areas, and terrain-like context are readable together
- quiet-default map behavior still holds

### 2. Selection walkthrough

Proves world features have clearer identity without bloating the inspector:

- moving vehicles can still be selected and inspected
- roads, intersections, and semantic world features can be selected
- inspection reflects semantic role instead of raw geometry-only naming

### 3. Renderer stability walkthrough

Proves the derived render surface is stable and usable across map interactions:

- pan, zoom, fit, and focus remain coherent
- minimap stays useful and uncluttered
- previews, selection, and commands continue to behave normally

### 4. Foundation walkthrough

Proves Phase A operator flow still works on top of the richer world/render base:

- the operator loop remains intact
- the world/render contracts are cleaner and more trustworthy
- the project has a stronger base for later motion, traffic, and hazard work

## Known Limits After Phase B

- The frontend is still a consumer of simulator truth; it does not own runtime state, final route truth, or conflict truth.
- Phase B improves the world/render foundation, but it does not add Phase C motion or traffic realism.
- The inspector remains intentionally compact; it is not a raw debug dump.
- Editor and Analyze remain lighter-weight product homes, not full future-phase replacements.

## Acceptance Judgment

Phase B is complete when the mining walkthrough feels presentation-worthy, the world-form and selection walkthroughs feel semantically coherent, and the map remains the primary operator surface throughout.
