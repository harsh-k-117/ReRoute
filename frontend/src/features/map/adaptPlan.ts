// The ONLY file that knows contract-v1 field names. If the contract differs,
// edit the two "PlanLike" shapes and the mapping below; nothing else changes.

import type { MapRoute } from './timeline';

export interface PlanStopLike {
  delivery_id?: string | null;
  location_id: string;
  kind: string;
  arrival: number;
  service_start: number;
  depart: number;
  load_after: number;
  window_open?: number | null;
  window_close?: number | null;
}
export interface PlanRouteLike {
  vehicle_id: string;
  stops: PlanStopLike[];
}
export interface PlanLike { routes: PlanRouteLike[] }
export interface ScenarioLike {
  start_time: number;
  vehicles: { id: string; capacity: number; start_location_id: string }[];
}

export function toMapRoutes(plan: PlanLike, scenario: ScenarioLike): MapRoute[] {
  const cap = new Map(scenario.vehicles.map((v) => [v.id, v.capacity]));
  return plan.routes.map((r) => {
    const origin = r.stops.find((stop) => stop.kind === 'depot_start');
    const firstOrigin = scenario.vehicles.find((vehicle) => vehicle.id === r.vehicle_id)?.start_location_id ?? '';
    const stops = r.stops.filter((stop) => stop.kind === 'delivery' || stop.kind === 'pickup');
    return {
      vehicleId: r.vehicle_id,
      capacity: cap.get(r.vehicle_id) ?? 0,
      originLocationId: origin?.location_id ?? firstOrigin,
      originDepart: origin?.depart ?? scenario.start_time,
      initialLoad: origin?.load_after ?? 0,
      stops: stops.map((s, index) => ({
        key: s.delivery_id ?? `${r.vehicle_id}-stop-${index}`,
        locationId: s.location_id,
        kind: s.kind === 'pickup' ? 'pickup' : 'delivery',
        arrival: s.arrival,
        start: s.service_start,
        depart: s.depart,
        loadAfter: s.load_after,
        windowOpen: s.window_open ?? undefined,
        windowClose: s.window_close ?? undefined,
      })),
    };
  });
}
