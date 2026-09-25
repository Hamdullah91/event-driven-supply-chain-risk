import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const backendTarget = process.env.VITE_DEV_BACKEND_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: backendTarget, changeOrigin: true },
      "/companies": { target: backendTarget, changeOrigin: true },
      "/risk": { target: backendTarget, changeOrigin: true },
      "/health": { target: backendTarget, changeOrigin: true },
      "/risk-stream": { target: backendTarget, changeOrigin: true, ws: true },
    },
  },
});
