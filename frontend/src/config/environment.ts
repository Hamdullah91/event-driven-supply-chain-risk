export type DataMode = "demo" | "live";

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function resolveDataMode(value: string | undefined): DataMode {
  return value?.trim().toLowerCase() === "demo" ? "demo" : "live";
}

function deriveWebSocketBase(apiBaseUrl: string): string {
  if (apiBaseUrl) {
    return apiBaseUrl.replace(/^http:/, "ws:").replace(/^https:/, "wss:");
  }
  if (typeof window === "undefined") return "";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}`;
}

const apiBaseUrl = stripTrailingSlash(import.meta.env.VITE_API_BASE_URL?.trim() ?? "");
const explicitWsBase = stripTrailingSlash(import.meta.env.VITE_WS_BASE_URL?.trim() ?? "");

export const environment = Object.freeze({
  dataMode: resolveDataMode(import.meta.env.VITE_DATA_MODE),
  apiBaseUrl,
  wsBaseUrl: explicitWsBase || deriveWebSocketBase(apiBaseUrl),
});
