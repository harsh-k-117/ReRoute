export const VEHICLE_ROUTE_COLORS = [
  "#69A7FF",
  "#A78BFA",
  "#28B8B4",
  "#7C83F6",
  "#52C6D7",
  "#C4B5FD",
  "#2E9FCA",
  "#8B79D6",
];

export function vehicleRouteColor(vehicleId: string, vehicleIds: string[]): string {
  const index = [...new Set(vehicleIds)].sort().indexOf(vehicleId);
  return VEHICLE_ROUTE_COLORS[(index < 0 ? 0 : index) % VEHICLE_ROUTE_COLORS.length];
}
