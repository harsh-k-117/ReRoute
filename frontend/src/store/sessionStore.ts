import { useSyncExternalStore } from "react";

type SessionState = { now: number; hoveredDelivery: string | null };
let state: SessionState = { now: 0, hoveredDelivery: null };
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((listener) => listener());

export const sessionStore = {
  get: () => state,
  setNow: (now: number) => { state = { ...state, now }; emit(); },
  setHovered: (hoveredDelivery: string | null) => { state = { ...state, hoveredDelivery }; emit(); },
  subscribe: (listener: () => void) => { listeners.add(listener); return () => listeners.delete(listener); },
};

export function useSessionStore() {
  return useSyncExternalStore(sessionStore.subscribe, sessionStore.get, sessionStore.get);
}