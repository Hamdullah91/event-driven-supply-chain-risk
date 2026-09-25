import { QueryClientProvider } from "@tanstack/react-query";
import { HashRouter } from "react-router-dom";

import { DemoApp } from "./app/DemoApp";
import { LiveApp } from "./app/LiveApp";
import { environment } from "./config/environment";
import { queryClient } from "./query/queryClient";

export default function App() {
  if (environment.dataMode === "demo") return <DemoApp />;

  return (
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <LiveApp />
      </HashRouter>
    </QueryClientProvider>
  );
}
