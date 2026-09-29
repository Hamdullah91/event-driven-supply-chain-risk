import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/error";

function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 2) return false;
  if (error instanceof ApiError) return error.retryable;
  return false;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: shouldRetry,
    },
    mutations: { retry: false },
  },
});
