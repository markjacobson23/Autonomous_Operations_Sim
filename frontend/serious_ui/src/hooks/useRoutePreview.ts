import { useCallback, useState, type Dispatch, type SetStateAction } from "react";

import { sendLiveRoutePreview } from "../api/liveClient";
import type { BundlePayload, JsonRecord, RoutePreviewPayload } from "../types";

export type UseRoutePreviewResult = {
  isPreviewing: boolean;
  previewError: string | null;
  submitRoutePreview: (
    payload: JsonRecord,
  ) => Promise<{ bundle: BundlePayload | null; routePreviews: RoutePreviewPayload[] } | null>;
};

export function useRoutePreview({
  bundle,
  setLiveCommandMessage,
  selectedVehicleIds,
}: {
  bundle: BundlePayload | null;
  setLiveCommandMessage: Dispatch<SetStateAction<string>>;
  selectedVehicleIds: number[];
}): UseRoutePreviewResult {
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const submitRoutePreview = useCallback(
    async (payload: JsonRecord) => {
      const endpoint = bundle?.session_control?.route_preview_endpoint ?? "/api/live/preview";
      const selected_vehicle_ids =
        Array.isArray(payload.selected_vehicle_ids) && payload.selected_vehicle_ids.length > 0
          ? payload.selected_vehicle_ids
          : selectedVehicleIds;
      const requestPayload = {
        ...payload,
        selected_vehicle_ids,
      };
      setIsPreviewing(true);
      setPreviewError(null);
      setLiveCommandMessage("Requesting a route preview from the Python session...");
      try {
        const response = await sendLiveRoutePreview(endpoint, requestPayload);
        setLiveCommandMessage(
          response.ok ? "Route preview loaded." : "Route preview response returned.",
        );
        return {
          bundle: response.bundle ?? null,
          routePreviews:
            response.route_previews ??
            response.bundle?.command_center?.route_previews ??
            [],
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Route preview request failed";
        setPreviewError(message);
        setLiveCommandMessage(`Route preview request failed. ${message}`);
        return null;
      } finally {
        setIsPreviewing(false);
      }
    },
    [bundle, selectedVehicleIds, setLiveCommandMessage],
  );

  return {
    isPreviewing,
    previewError,
    submitRoutePreview,
  };
}
