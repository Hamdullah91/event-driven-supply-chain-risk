import type { QueryClient } from "@tanstack/react-query";
import type { RiskStreamMessage } from "../domain/types";

export async function invalidateForRiskUpdate(queryClient: QueryClient, message: Extract<RiskStreamMessage, { type: "risk.updated" }>): Promise<void> {
  const tasks = [
    queryClient.invalidateQueries({ queryKey: ["company-risk", message.companyId] }),
    queryClient.invalidateQueries({ queryKey: ["company-exposure", message.companyId] }),
    queryClient.invalidateQueries({ queryKey: ["company-blast-radius", message.companyId] }),
    queryClient.invalidateQueries({ queryKey: ["risk-history", message.companyId] }),
  ];

  if (message.eventId) {
    tasks.push(
      queryClient.invalidateQueries({ queryKey: ["event", message.eventId] }),
      queryClient.invalidateQueries({ queryKey: ["event-blast-radius", message.eventId] }),
      queryClient.invalidateQueries({ queryKey: ["events"] }),
    );
  }

  await Promise.all(tasks);
}
