import type { QueryClient } from "@tanstack/react-query";
import type { RiskStreamMessage } from "../domain/types";

export type RiskUpdateIdentity = {
  companyId: string;
  eventId?: string;
};

function riskUpdateQueryPrefixes(update: RiskUpdateIdentity): readonly (readonly string[])[] {
  const prefixes: Array<readonly string[]> = [
    ["company-risk", update.companyId],
    ["company-exposure", update.companyId],
    ["company-blast-radius", update.companyId],
    ["risk-history", update.companyId],
  ];

  if (update.eventId) {
    prefixes.push(
      ["event", update.eventId],
      ["event-blast-radius", update.eventId],
      ["events"],
    );
  }

  return prefixes;
}

export async function invalidateForRiskUpdate(
  queryClient: QueryClient,
  message: Extract<RiskStreamMessage, { type: "risk.updated" }>,
): Promise<void> {
  await Promise.all(
    riskUpdateQueryPrefixes(message).map((queryKey) => queryClient.invalidateQueries({ queryKey, refetchType: "none" })),
  );
}

export async function refetchForRiskUpdate(queryClient: QueryClient, update: RiskUpdateIdentity): Promise<void> {
  await Promise.all(
    riskUpdateQueryPrefixes(update).map((queryKey) => queryClient.refetchQueries({ queryKey, type: "active" })),
  );
}
