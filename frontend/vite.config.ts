import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    proxy: {
      "/scenarios": "http://localhost:8000",
      "/plan": "http://localhost:8000",
      "/templates": "http://localhost:8000",
      "/state": "http://localhost:8000",
      "/validate": "http://localhost:8000",
      "/disruptions": "http://localhost:8000",
      "/proposals": "http://localhost:8000",
      "/versions": "http://localhost:8000",
    },
  },
});