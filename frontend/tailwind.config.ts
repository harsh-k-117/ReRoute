/**
 * frontend/tailwind.config.ts - Tailwind config; colors come from styles/tokens.css
 *
 * Lane : P4 UX & story lead (single writer for this path)
 * Stack: Vite · React 18 · TypeScript · Tailwind · shadcn/ui · TanStack Query · Zustand · custom SVG + d3-scale · openapi-typescript · Playwright · NO map libraries, NO CDNs
 * Rule : green/amber/red are RESERVED for kept/moved/broken only.
 */
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        kept: "var(--color-kept)",
        moved: "var(--color-moved)",
        broken: "var(--color-broken)",
      },
    },
  },
  plugins: [],
} satisfies Config;
