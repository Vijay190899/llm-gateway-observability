import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Frontend talks to the gateway over relative paths so there is no CORS and no
// build-time API URL. In dev, Vite proxies them to the local gateway; in the
// container, nginx proxies them to the gateway service.
const GATEWAY = process.env.GATEWAY_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/v1": GATEWAY,
      "/metrics": GATEWAY,
      "/health": GATEWAY,
    },
  },
});
