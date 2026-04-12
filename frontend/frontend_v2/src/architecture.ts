export const frontendV2Home = "frontend/frontend_v2/";

export const frontendOwnedState = [
  "camera and viewport state",
  "scene mode and layer toggles",
  "selection and hover state",
  "popup and inspector state",
  "route preview and command form state",
  "session control UI state",
  "planning workflow drafts",
  "mode and panel state",
] as const;

export const simulatorOwnedTruth = [
  "runtime vehicle truth",
  "final route truth",
  "conflict and reservation truth",
  "topology truth",
  "deterministic progression semantics",
] as const;

export const repoLayoutDecision = [
  "Canonical Frontend v2 lives in a dedicated workspace.",
  "Legacy serious UI remains frozen as a compatibility path only.",
  "Python simulator stays authoritative; the frontend consumes derived surfaces.",
] as const;
