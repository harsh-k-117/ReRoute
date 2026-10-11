/**
 * frontend/src/main.tsx - React entry: QueryClientProvider + App
 *
 * Lane : P4 UX & story lead (single writer for this path)
 * Stack: Vite · React 18 · TypeScript · Tailwind · shadcn/ui · TanStack Query · Zustand · custom SVG + d3-scale · openapi-typescript · Playwright · NO map libraries, NO CDNs
 * Spec : TanStack Query
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles/globals.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
