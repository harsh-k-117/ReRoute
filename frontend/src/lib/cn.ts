/**
 * frontend/src/lib/cn.ts - clsx + tailwind-merge helper (shadcn convention)
 *
 * Lane : P4 UX & story lead (single writer for this path)
 * Stack: Vite · React 18 · TypeScript · Tailwind · shadcn/ui · TanStack Query · Zustand · custom SVG + d3-scale · openapi-typescript · Playwright · NO map libraries, NO CDNs
 * Spec : shadcn/ui
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
