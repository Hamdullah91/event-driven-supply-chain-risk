import { createContext, useContext } from "react";

export type RiskStreamConnectionState = "CONNECTING" | "CONNECTED" | "RECONNECTING" | "DISCONNECTED" | "ERROR";

export type RiskStreamContextValue = {
  connectionState: RiskStreamConnectionState;
  lastUpdated?: string;
};

export const RiskStreamContext = createContext<RiskStreamContextValue>({ connectionState: "DISCONNECTED" });

export function useRiskStream(): RiskStreamContextValue {
  return useContext(RiskStreamContext);
}
