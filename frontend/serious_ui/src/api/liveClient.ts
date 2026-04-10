import type {
  BundlePayload,
  EditTransaction,
  RoutePreviewPayload,
  SessionControlPayload,
  ValidationMessage,
} from "../types";

type JsonRecord = Record<string, unknown>;

type ApiResponse<T> = T & {
  ok?: boolean;
  message?: string;
  validation_messages?: ValidationMessage[];
  bundle?: BundlePayload;
  route_previews?: RoutePreviewPayload[];
};

async function requestJson<TResponse>(
  url: string,
  init: RequestInit = {},
): Promise<TResponse> {
  const response = await fetch(url, init);
  const payload = (await response.json().catch(() => null)) as TResponse | null;
  if (!response.ok) {
    const responseRecord = payload as Record<string, unknown> | null;
    const message =
      responseRecord !== null &&
      typeof responseRecord.message === "string"
        ? responseRecord.message
        : `Request failed with ${response.status}`;
    throw new Error(message);
  }
  if (payload === null) {
    throw new Error("Response did not include JSON.");
  }
  return payload;
}

export async function loadLiveBundle(bundleUrl: string): Promise<BundlePayload> {
  return requestJson<BundlePayload>(bundleUrl);
}

export async function sendLiveCommand(
  endpoint: string,
  payload: JsonRecord,
): Promise<ApiResponse<{ command_result?: JsonRecord | null; command_results?: JsonRecord[] }>> {
  return requestJson<ApiResponse<{ command_result?: JsonRecord | null; command_results?: JsonRecord[] }>>(
    endpoint,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}

export async function sendLiveRoutePreview(
  endpoint: string,
  payload: JsonRecord,
): Promise<ApiResponse<{ route_previews?: RoutePreviewPayload[] }>> {
  return requestJson<ApiResponse<{ route_previews?: RoutePreviewPayload[] }>>(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function sendSessionControl(
  endpoint: string,
  payload: SessionControlPayload & JsonRecord,
): Promise<ApiResponse<{ session_advance?: JsonRecord }>> {
  return requestJson<ApiResponse<{ session_advance?: JsonRecord }>>(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function validateAuthoringEdits(
  endpoint: string,
  transaction: EditTransaction,
): Promise<{ ok?: boolean; validation_messages?: ValidationMessage[] }> {
  return requestJson<{ ok?: boolean; validation_messages?: ValidationMessage[] }>(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(transaction),
  });
}

export async function saveAuthoringEdits(
  endpoint: string,
  transaction: EditTransaction,
): Promise<{ ok?: boolean; bundle?: BundlePayload; validation_messages?: ValidationMessage[] }> {
  return requestJson<{ ok?: boolean; bundle?: BundlePayload; validation_messages?: ValidationMessage[] }>(
    endpoint,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(transaction),
    },
  );
}

export async function reloadAuthoringState(
  endpoint: string,
): Promise<{ ok?: boolean; bundle?: BundlePayload }> {
  return requestJson<{ ok?: boolean; bundle?: BundlePayload }>(endpoint);
}

export type { ApiResponse };
