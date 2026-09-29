import { environment } from "../config/environment";
import { ApiError, errorKindForStatus, statusIsRetryable } from "./error";

const DEFAULT_TIMEOUT_MS = 15_000;

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  timeoutMs?: number;
};

function requestUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${environment.apiBaseUrl}${normalizedPath}`;
}

function readErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timeoutId = window.setTimeout(() => controller.abort("timeout"), timeoutMs);
  const externalSignal = options.signal;
  const abortFromExternal = () => controller.abort(externalSignal?.reason);
  externalSignal?.addEventListener("abort", abortFromExternal, { once: true });

  try {
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");
    let body: BodyInit | undefined;
    if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(options.body);
    }

    const response = await fetch(requestUrl(path), {
      ...options,
      body,
      headers,
      signal: controller.signal,
    });

    const payload: unknown = response.status === 204 ? undefined : await response.json().catch(() => undefined);
    if (!response.ok) {
      throw new ApiError({
        kind: errorKindForStatus(response.status),
        status: response.status,
        message: readErrorMessage(payload, `Request failed with status ${response.status}.`),
        detail: payload,
        retryable: statusIsRetryable(response.status),
      });
    }
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (controller.signal.aborted) {
      const timedOut = controller.signal.reason === "timeout";
      throw new ApiError({
        kind: timedOut ? "TIMEOUT" : "NETWORK",
        message: timedOut ? "The request timed out." : "The request was cancelled.",
        retryable: timedOut,
      });
    }
    throw new ApiError({ kind: "NETWORK", message: "The backend could not be reached.", detail: error, retryable: true });
  } finally {
    window.clearTimeout(timeoutId);
    externalSignal?.removeEventListener("abort", abortFromExternal);
  }
}
