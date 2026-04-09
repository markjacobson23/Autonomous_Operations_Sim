# Step 28 Visual Presentation and Frontend Quality Upgrade

## Goal
Finish Step 28 cleanly by making the simulator viewer substantially better in UI/UX quality.

## Required implementation
Improve the viewer/frontend experience so that simulator state and actions are much easier to understand and interact with.

## Required design
- Reuse the existing:
  - visualization replay state
  - live sync surface
  - live viewer action/controller surfaces
  - command/session/runtime authority
- Improve one or more of:
  - rendering quality
  - layout
  - labels and readability
  - selected-object clarity
  - action/status visibility
  - general visual hierarchy
- If necessary, perform a bounded viewer/frontend refactor to a stack better suited for UI quality

## Required behavior
- The viewer is materially easier to understand than the current baseline
- The viewer continues to consume authoritative simulator surfaces rather than owning runtime truth
- Repeated runs with the same runtime inputs still remain deterministic
- Any new stable viewer-facing assumptions are testable

## Minimum expected scope
At minimum, Step 28 should deliver:
- clearly improved map/vehicle readability
- clearly improved action/status readability
- clearly improved selection/highlighting behavior
- an obviously better overall viewing experience than the current Tk baseline

## Design constraints
- Do not redesign the simulator core around the frontend
- Do not weaken replay/export determinism for presentation convenience
- Do not start performance/scaling work yet
- Do not overbuild a product-grade platform beyond this quality step
- Keep the implementation bounded and production-like

## Preferred strategy
- Optimize for actual UI/UX quality, not just incremental widget additions
- Be willing to choose the viewer stack that gives the best near-term quality ceiling
- Preserve clean authority boundaries:
  - simulator core owns runtime truth
  - viewer/frontend consumes sync/visualization surfaces
- If staying in Python gives the best result for now, that is fine
- If a bounded frontend split gives a clearly better result, that is also acceptable

## Tests to add
Add tests for:
- any new stable viewer-facing state assumptions
- deterministic use of sync/visualization surfaces where relevant
- repeated viewer-driving sequences remaining consistent where covered
- regression coverage for any newly formalized frontend/viewer data contracts

## Definition of done
All of the following must succeed:
- `python3 -m pytest`
- `python3 -m ruff check .`
- `python3 -m mypy autonomous_ops_sim tests`
