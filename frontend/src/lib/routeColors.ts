export const VEHICLE_ROUTE_COLORS = [
  "#54DCE8",
  "#F07879",
  "#B7A8F0",
  "#65C8AA",
  "#F1B866",
  "#B096DD",
  "#7DAAF5",
  "#EEA1C1",
];

export function vehicleRouteColor(vehicleId: string, vehicleIds: string[]): string {
  const index = [...new Set(vehicleIds)].sort().indexOf(vehicleId);
  return VEHICLE_ROUTE_COLORS[(index < 0 ? 0 : index) % VEHICLE_ROUTE_COLORS.length];
}
