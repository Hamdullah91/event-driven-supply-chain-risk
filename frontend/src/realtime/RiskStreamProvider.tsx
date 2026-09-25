import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { adaptRiskStreamMessage } from "../api/adapters";
import { environment } from "../config/environment";
import { useUiStore } from "../state/uiStore";
import { RiskStreamContext, type RiskStreamConnectionState } from "./riskStreamContext";
import { invalidateForRiskUpdate } from "./riskStreamInvalidation";
import { parseRiskStreamPayload } from "./riskStreamPayload";

const RECONNECT_DELAYS_MS = [1_000, 2_000, 5_000, 10_000, 30_000] as const;

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

  const value = useMemo(
    () => ({ connectionState, ...(lastUpdated ? { lastUpdated } : {}) }),
    [connectionState, lastUpdated],
  );

  return <RiskStreamContext.Provider value={value}>{children}</RiskStreamContext.Provider>;
}
