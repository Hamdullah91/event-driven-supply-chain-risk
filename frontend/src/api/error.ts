export type ApiErrorKind = "NETWORK" | "TIMEOUT" | "VALIDATION" | "NOT_FOUND" | "UNAUTHORIZED" | "SERVER" | "UNKNOWN";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly detail?: unknown;
  readonly retryable: boolean;

  constructor(input: { kind: ApiErrorKind; message: string; status?: number; detail?: unknown; retryable?: boolean }) {
    super(input.message);
    this.name = "ApiError";
    this.kind = input.kind;
    this.status = input.status;
    this.detail = input.detail;
    this.retryable = input.retryable ?? false;
  }
}

export function errorKindForStatus(status: number): ApiErrorKind {
  if (status === 400 || status === 422) return "VALIDATION";
  if (status === 401 || status === 403) return "UNAUTHORIZED";
  if (status === 404) return "NOT_FOUND";
  if (status >= 500) return "SERVER";
  return "UNKNOWN";
}

export function statusIsRetryable(status: number): boolean {
  return status === 408 || status === 429 || status >= 500;
}
