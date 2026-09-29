import { act, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RiskStreamProvider } from "./RiskStreamProvider";
import { useRiskStream } from "./riskStreamContext";
import { STABLE_CONNECTION_RESET_MS } from "./riskStreamBackoff";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];

  readonly url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  openFromServer() {
    this.onopen?.(new Event("open"));
  }

  closeFromServer() {
    this.onclose?.(new CloseEvent("close"));
  }

  close() {
    // Provider cleanup intentionally closes the transport without simulating another server close.
  }
}

function ConnectionState() {
  const stream = useRiskStream();
  return <span>{stream.connectionState}</span>;
}

beforeEach(() => {
  vi.useFakeTimers();
  FakeWebSocket.instances = [];
  vi.stubGlobal("WebSocket", FakeWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("RiskStreamProvider reconnection", () => {
  it("escalates reconnect delay during flapping and resets only after a stable connection", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><RiskStreamProvider><ConnectionState /></RiskStreamProvider></QueryClientProvider>);

    expect(FakeWebSocket.instances).toHaveLength(1);
    act(() => FakeWebSocket.instances[0].openFromServer());
    expect(screen.getByText("CONNECTED")).toBeInTheDocument();

    act(() => FakeWebSocket.instances[0].closeFromServer());
    expect(screen.getByText("RECONNECTING")).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(999));
    expect(FakeWebSocket.instances).toHaveLength(1);
    act(() => vi.advanceTimersByTime(1));
    expect(FakeWebSocket.instances).toHaveLength(2);

    act(() => FakeWebSocket.instances[1].openFromServer());
    act(() => FakeWebSocket.instances[1].closeFromServer());
    act(() => vi.advanceTimersByTime(1_999));
    expect(FakeWebSocket.instances).toHaveLength(2);
    act(() => vi.advanceTimersByTime(1));
    expect(FakeWebSocket.instances).toHaveLength(3);

    act(() => FakeWebSocket.instances[2].openFromServer());
    act(() => vi.advanceTimersByTime(STABLE_CONNECTION_RESET_MS));
    act(() => FakeWebSocket.instances[2].closeFromServer());
    act(() => vi.advanceTimersByTime(999));
    expect(FakeWebSocket.instances).toHaveLength(3);
    act(() => vi.advanceTimersByTime(1));
    expect(FakeWebSocket.instances).toHaveLength(4);
  });
});
