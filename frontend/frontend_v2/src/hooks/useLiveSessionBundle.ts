import { useEffect, useState } from "react";

import type { LiveBundleResource, LoadState, JsonRecord } from "../adapters/liveBundle";

export function useLiveSessionBundle(): LiveBundleResource {
  const [bundle, setBundle] = useState<JsonRecord | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadMessage, setLoadMessage] = useState("Connecting to live session bundle...");
  const [bundleUrl] = useState(() => {
    return new URLSearchParams(window.location.search).get("bundle") ?? "/live_session_bundle.json";
  });

  useEffect(() => {
    const controller = new AbortController();
    const resolvedBundleUrl = new URL(bundleUrl, window.location.href).toString();

    async function loadBundle() {
      setLoadState("loading");
      setLoadMessage(`Connecting to ${bundleUrl}...`);
      try {
        const response = await fetch(resolvedBundleUrl, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }

        const payload: unknown = await response.json();
        if (!isRecord(payload)) {
          throw new Error("Live bundle did not decode to an object");
        }

        setBundle(payload);
        setLoadState("ready");
        setLoadMessage("Live session connected");
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setBundle(null);
        setLoadState("error");
        setLoadMessage(error instanceof Error ? error.message : "Unable to load live bundle");
      }
    }

    void loadBundle();
    return () => controller.abort();
  }, [bundleUrl]);

  return {
    bundleUrl,
    loadState,
    loadMessage,
    bundle,
  };
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
