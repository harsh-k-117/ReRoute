/**
 * frontend/vite.config.ts - Vite config: React plugin, @/ alias, dev proxy to FastAPI
 *
 * Lane : P4 UX & story lead (single writer for this path)
 * Stack: Vite · React 18 · TypeScript · Tailwind · shadcn/ui · TanStack Query · Zustand · custom SVG + d3-scale · openapi-typescript · Playwright · NO map libraries, NO CDNs
 */
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: { proxy: { "/api": "http://localhost:8000" } },
});
