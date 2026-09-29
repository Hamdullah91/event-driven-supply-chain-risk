export const RECONNECT_DELAYS_MS = [1_000, 2_000, 5_000, 10_000, 30_000] as const;
export const STABLE_CONNECTION_RESET_MS = 30_000;

export function reconnectDelayForAttempt(attempt: number): number {
  const normalizedAttempt = Math.max(1, Math.floor(attempt));
  return RECONNECT_DELAYS_MS[Math.min(normalizedAttempt - 1, RECONNECT_DELAYS_MS.length - 1)];
}
