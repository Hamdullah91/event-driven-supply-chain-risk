import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { adaptRiskStreamMessage } from "../api/adapters";
import type { ConnectionEstablishedDto, RiskUpdatedDto } from "../api/dtos";
import { environment } from "../config/environment";
import { useUiStore } from "../state/uiStore";
import { invalidateForRiskUpdate } from "./riskStreamInvalidation";

export type RiskStreamConnectionState = "CONNECTING" | "CONNECTED" | "RECONNECTING" | "DISCONNECTED" | "ERROR";

type RiskStreamContextValue = {
  connectionState: RiskStreamConnectionState;
  lastUpdated?: string;
};

const RiskStreamContext = createContext<RiskStreamContextValue>({ connectionState: "DISCONNECTED" });
const RECONNECT_DELAYS_MS = [1_000, 2_000, 5_000, 10_000, 30_000] as const;

function isHop(value: unknown): value is 1 | 2 | 3 { return value === 1 || value === 2 || value === 3; }
function isNumber(value: unknown): value is number { return typeof value === "number" && Number.isFinite(value); }

export function parseRiskStreamPayload(raw: string): ConnectionEstablishedDto | RiskUpdatedDto | null {
  let value: unknown;
  try { value = JSON.parse(raw); } catch { return null; }
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;

  if (record.type === "connection.established" && typeof record.message === "string") {
    return { type: "connection.established", message: record.message };
  }

  if (
    record.type === "risk.updated"
    && typeof record.company_id === "string"
    && isNumber(record.risk_score)
    && typeof record.risk_level === "string"
    && isNumber(record.contributing_event_count)
    && isHop(record.max_hops)
    && typeof record.timestamp === "string"
  ) {
    return {
      type: "risk.updated",
      company_id: record.company_id,
      risk_score: record.risk_score,
      risk_level: record.risk_level,
      contributing_event_count: record.contributing_event_count,
      max_hops: record.max_hops,
      timestamp: record.timestamp,
      ...(typeof record.event_id === "string" ? { event_id: record.event_id } : {}),
      ...(typeof record.trigger_event_type === "string" ? { trigger_event_type: record.trigger_event_type } : {}),
    };
  }

  return null;
}

export function RiskStreamProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [connectionState, setConnectionState] = useState<RiskStreamConnectionState>("CONNECTING");
  const [lastUpdated, setLastUpdated] = useState<string>();
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<number | null>(null);
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    let socket: WebSocket | null = null;

    const connect = () => {
      if (stopped.current) return;
      const base = environment.wsBaseUrl.replace(/\/+$/, "");
      if (!base) {
        setConnectionState("DISCONNECTED");
        return;
      }

      setConnectionState(reconnectAttempt.current > 0 ? "RECONNECTING" : "CONNECTING");
      socket = new WebSocket(`${base}/risk-stream`);

      socket.onopen = () => {
        reconnectAttempt.current = 0;
        setConnectionState("CONNECTED");
      };

      socket.onmessage = (event) => {
        if (typeof event.data !== "string") return;
        const dto = parseRiskStreamPayload(event.data);
        if (!dto) return;
        const message = adaptRiskStreamMessage(dto);
        if (message.type === "connection.established") {
          setConnectionState("CONNECTED");
          return;
        }

        setLastUpdated(message.timestamp);
        useUiStore.getState().setNewRiskNotification({
          companyId: message.companyId,
          ...(message.eventId ? { eventId: message.eventId } : {}),
          timestamp: message.timestamp,
        });
        void invalidateForRiskUpdate(queryClient, message);
      };

      socket.onerror = () => {
        if (!stopped.current) setConnectionState("ERROR");
      };

      socket.onclose = () => {
        if (stopped.current) {
          setConnectionState("DISCONNECTED");
          return;
        }
        reconnectAttempt.current += 1;
        setConnectionState("RECONNECTING");
        const delay = RECONNECT_DELAYS_MS[Math.min(reconnectAttempt.current - 1, RECONNECT_DELAYS_MS.length - 1)];
        reconnectTimer.current = window.setTimeout(connect, delay);
      };
    };

    connect();
    return () => {
      stopped.current = true;
      if (reconnectTimer.current !== null) window.clearTimeout(reconnectTimer.current);
      socket?.close();
    };
  }, [queryClient]);

  const value = useMemo(() => ({ connectionState, ...(lastUpdated ? { lastUpdated } : {}) }), [connectionState, lastUpdated]);
  return <RiskStreamContext.Provider value={value}>{children}</RiskStreamContext.Provider>;
}

export function useRiskStream(): RiskStreamContextValue { return useContext(RiskStreamContext); }
